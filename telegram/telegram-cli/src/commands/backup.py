"""
Backup command (F1) — retrieve messages from a dialog.

Supports full and incremental backup with pagination (T19),
rate-limit handling, --estimate mode (T10/T20), resumable backup (T22),
atomic writes (T21), and structured progress output (T23).
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_config
from src._lib import create_client, count_messages, read_messages
from src.errors import format_error_and_exit
from telegram_lib import get_dialogs, download_media, get_members

logger = logging.getLogger("telegram_cli")

# Pagination settings
PAGE_SIZE = 100
AVG_PAGE_FETCH_MS = 800
COOLDOWN_OVERHEAD_MS = 200


# ---------------------------------------------------------------------------
# Atomic write (T21)
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data) -> None:
    """Write JSON to *path* atomically via temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            f.write("\n")
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Resumable scan (T22)
# ---------------------------------------------------------------------------


def _scan_existing(output_path: Path) -> set[int]:
    """Return set of message IDs already saved in *output_path*.

    If the file doesn't exist or is not valid JSON, returns an empty set.
    """
    if not output_path.is_file():
        return set()
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {m["id"] for m in data if isinstance(m, dict) and "id" in m}
    except (json.JSONDecodeError, OSError, KeyError):
        pass
    return set()


def _latest_timestamp(output_path: Path) -> datetime | None:
    """Return the latest message timestamp from the existing file, or None."""
    if not output_path.is_file():
        return None
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            dates = []
            for m in data:
                if isinstance(m, dict) and "date" in m:
                    dates.append(datetime.fromisoformat(m["date"]))
            return max(dates) if dates else None
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    return None


# ---------------------------------------------------------------------------
# Progress output (T23)
# ---------------------------------------------------------------------------


def _is_tty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _progress_start(dialog_id, dialog_name, limit, since, output):
    """Stage 1 — print start info."""
    parts = [f"Backup: dialog={dialog_id}, limit={limit}"]
    if since:
        parts.append(f"since={since}")
    if output:
        parts.append(f"output={output}")
    print(" | ".join(parts))


def _progress_local_scan(local_count, latest_ts, new_count):
    """Stage 2 — print local scan result."""
    ts_str = latest_ts.isoformat() if latest_ts else "none"
    print(
        f"Local: {local_count} messages (latest: {ts_str}). "
        f"To download: {new_count} new messages."
    )


def _progress_estimate(new_count, pages):
    """Stage 3 — print time estimate for remaining download."""
    per_page_s = (AVG_PAGE_FETCH_MS + COOLDOWN_OVERHEAD_MS) / 1000
    total_s = pages * per_page_s
    minutes = total_s / 60
    if minutes < 1:
        time_str = f"{total_s:.0f} seconds"
    else:
        time_str = f"{minutes:.0f} minutes"
    print(
        f"Estimated time: \u2248 {time_str} "
        f"({new_count} messages, {pages} pages)."
    )


def _progress_bar(current_page, total_pages, fetched, total, elapsed, tty):
    """Stage 4 — print progress bar."""
    if total == 0:
        pct = 100
    else:
        pct = min(100, int(fetched / total * 100))
    bar_len = 16
    filled = int(bar_len * pct / 100)
    bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
    remaining_s = (elapsed / max(fetched, 1)) * (total - fetched) if fetched else 0
    line = (
        f"[{bar}] {pct}% | {fetched}/{total} messages "
        f"| {_fmt_time(elapsed)} elapsed | \u2248 {_fmt_time(remaining_s)} left"
    )
    if tty:
        print(f"\r{line}", end="", flush=True)
    else:
        print(line)


def _progress_bar_files(fetched: int, total: int, elapsed: float, tty: bool) -> None:
    """Print a progress bar for file downloads (mirrors _progress_bar)."""
    if total == 0:
        pct = 100
    else:
        pct = min(100, int(fetched / total * 100))
    bar_len = 16
    filled = int(bar_len * pct / 100)
    bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
    remaining_s = (elapsed / max(fetched, 1)) * (total - fetched) if fetched else 0
    line = (
        f"[{bar}] {pct}% | {fetched}/{total} files"
        f" | {_fmt_time(elapsed)} elapsed | \u2248 {_fmt_time(remaining_s)} left"
    )
    if tty:
        print(f"\r{line}", end="", flush=True)
    else:
        print(line)


def _progress_done(total_downloaded, elapsed, output_dir, pauses):
    """Stage 5 — print final report."""
    if _is_tty():
        print()  # newline after progress bar
    
    parts = [f"Done. {total_downloaded} messages saved"]
    
    if output_dir:
        # Show the directory containing both messages.json and messages.md
        output_dir = Path(output_dir) if not isinstance(output_dir, Path) else output_dir
        parts.append(f"to {output_dir}/")
        parts.append("(messages.json + messages.md)")
    
    parts.append(
        f"Total time: {_fmt_time(elapsed)}"
        + (f" ({pauses} rate-limit pauses)" if pauses else "")
        + "."
    )
    print(" ".join(parts))


def _fmt_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


# ---------------------------------------------------------------------------
# Estimate mode (T10, T20)
# ---------------------------------------------------------------------------


def _run_estimate(dialog_id: int, since: datetime | None, limit: int) -> None:
    """Print time estimate and exit without performing backup."""
    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    result = asyncio.run(_async_estimate(client, dialog_id, since))

    if not result.ok:
        format_error_and_exit(result.error)

    total = result.payload
    effective = min(total, limit) if limit else total
    pages = math.ceil(effective / PAGE_SIZE) if effective else 0
    per_page_s = (AVG_PAGE_FETCH_MS + COOLDOWN_OVERHEAD_MS) / 1000
    total_s = pages * per_page_s
    minutes = total_s / 60

    if minutes < 1:
        time_str = f"{total_s:.0f} seconds"
    else:
        time_str = f"{minutes:.0f} minutes"

    print(
        f"\u2248 {time_str} ({effective} messages, {pages} pages, "
        f"estimated {per_page_s:.1f} s/page incl. rate-limit pauses)"
    )


async def _async_estimate(client, dialog_id, since):
    """Connect, count, disconnect."""
    async with client:
        return await count_messages(client, dialog_id, since=since)


# ---------------------------------------------------------------------------
# Full backup with pagination (T19)
# ---------------------------------------------------------------------------


async def _async_get_dialog_name(client, dialog_id: int) -> str:
    """Fetch dialog name from Telegram API, return dialog_id as fallback."""
    try:
        result = await get_dialogs(client, limit=500)
        if result.ok:
            for dialog in result.payload:
                if dialog.id == dialog_id:
                    # Clean up dialog name for folder naming (remove special chars)
                    name = dialog.name.replace("/", "_").replace("\\", "_")
                    return name if name else str(dialog_id)
    except Exception as e:
        logger.warning(f"Failed to fetch dialog name: {e}")
    # Fallback: use dialog_id as name
    return str(dialog_id)


def _get_media_category(media_type: str | None) -> str | None:
    """Map semantic media type string to our subdirectory category.

    Expects values produced by telegram_lib.messages._get_media_type:
    "photo", "video", "audio", "voice", "gif", "document", "webpage".

    Returns:
        Category name ("media", "files", "music", "voice", "links", "gifs") or None.
    """
    if not media_type:
        return None

    _MAP = {
        "photo": "media",
        "video": "media",
        "audio": "music",
        "voice": "voice",
        "gif": "gifs",
        "document": "files",
        "webpage": "links",
    }
    return _MAP.get(media_type, "media")


def _generate_messages_md(messages: list[dict]) -> str:
    """Generate markdown representation of messages."""
    if not messages:
        return "# Messages\n\nNo messages.\n"
    
    lines = ["# Messages\n"]
    for msg in messages:
        sender = msg.get("sender_name") or f"User {msg.get('sender_id')}"
        date = msg.get("date", "")
        text = msg.get("text", "(no text)")
        has_media = msg.get("has_media", False)
        media_indicator = " [MEDIA]" if has_media else ""
        lines.append(f"## {sender} ({date}){media_indicator}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines)


def run_backup(
    *,
    dialog_id: int,
    since: str | None = None,
    limit: int = 100,
    outdir: str | None = None,
    media: bool = False,
    files: bool = False,
    music: bool = False,
    voice: bool = False,
    links: bool = False,
    gifs: bool = False,
    members: bool = False,
    estimate: bool = False,
) -> None:
    """Main entry point for the backup command."""
    since_dt = _parse_since(since)

    if estimate:
        _run_estimate(dialog_id, since_dt, limit)
        return

    config = load_config()
    client = create_client(config["api_id"], config["api_hash"], config["session"])
    
    # Determine output directory: use outdir if provided, otherwise default
    base_output_dir = Path(outdir) if outdir else Path("./synchromessotron")
    
    # Build enabled media categories from flags
    enabled_categories = set()
    if media:
        enabled_categories.add("media")
    if files:
        enabled_categories.add("files")
    if music:
        enabled_categories.add("music")
    if voice:
        enabled_categories.add("voice")
    if links:
        enabled_categories.add("links")
    if gifs:
        enabled_categories.add("gifs")
    if members:
        enabled_categories.add("members")
    
    # Fetch dialog name and determine output file path
    # This will happen in _async_backup where we're in the proper async context
    result = asyncio.run(
        _async_backup(client, dialog_id, since_dt, limit, base_output_dir, enabled_categories)
    )
    
    if not isinstance(result, tuple):
        # result is a TgResult with error
        format_error_and_exit(result.error)
        return
    
    messages, file_paths, pauses, elapsed, output_dir, members_data = result

    # Serialize all messages (both with and without media)
    data = [_message_to_dict(m, file_paths.get(m.id)) for m in messages]
    
    # DEBUG: Verify message counts
    logger.info(f"DEBUG: run_backup received {len(messages)} messages, converting to data now...")

    # Merge with existing data and write to main output directory
    existing_data = _load_existing_data(output_dir / "messages.json")
    merged = _merge_messages(existing_data, data)
    
    # DEBUG: Log message counts before and after merge
    logger.info(f"DEBUG: Writing messages.json | input_msgs={len(messages)} | data_list={len(data)} | existing={len(existing_data)} | merged={len(merged)}")
    
    _atomic_write_json(output_dir / "messages.json", merged)
    
    # Generate messages.md file
    md_content = _generate_messages_md(merged)
    messages_md_path = output_dir / "messages.md"
    messages_md_path.write_text(md_content, encoding="utf-8")
    
    # If media categories are enabled, create subdirectories organized by media type
    if enabled_categories:
        # Group fetched messages by media category
        by_category: dict[str, list] = {cat: [] for cat in enabled_categories if cat != "members"}
        
        for msg in data:
            media_type = msg.get("media_type")
            if media_type:
                category = _get_media_category(media_type)
                if category and category in by_category:
                    by_category[category].append(msg)
        
        # Create subdirectories and save media category files
        for category, cat_messages in by_category.items():
            if cat_messages:  # Only create directory if there are messages in this category
                cat_dir = output_dir / category
                cat_dir.mkdir(parents=True, exist_ok=True)
                
                # Load existing data for this category
                cat_data_path = cat_dir / "messages.json"
                existing_cat_data = _load_existing_data(cat_data_path)
                merged_cat = _merge_messages(existing_cat_data, cat_messages)
                
                # Write category-specific files
                _atomic_write_json(cat_data_path, merged_cat)
                
                # Generate category-specific markdown
                cat_md = _generate_messages_md(merged_cat)
                cat_md_path = cat_dir / "messages.md"
                cat_md_path.write_text(cat_md, encoding="utf-8")
        
        # Save members if requested
        if "members" in enabled_categories and members_data:
            members_dir = output_dir / "members"
            members_dir.mkdir(parents=True, exist_ok=True)
            members_json_path = members_dir / "members.json"
            _atomic_write_json(members_json_path, members_data)
    
    _progress_done(len(data), elapsed, output_dir, pauses)


async def _async_backup(
    client, dialog_id, since_dt, limit, base_output_dir, enabled_categories=None,
):
    """Connect, fetch dialog info, paginate, download media, extract members, disconnect. 
    Returns (messages, file_paths, pauses, elapsed, output_dir, members_data) or TgResult on error."""
    if enabled_categories is None:
        enabled_categories = set()
    
    async with client:
        # Fetch dialog name first
        dialog_name = await _async_get_dialog_name(client, dialog_id)
        dialog_dir_name = f"{dialog_name}_{dialog_id}"
        output_dir = base_output_dir / dialog_dir_name
        
        # T11 — check output dir write permission
        _check_output_writable(output_dir / "messages.json")
        
        # T22 — scan existing
        existing_ids: set[int] = _scan_existing(output_dir / "messages.json")
        latest_local: datetime | None = _latest_timestamp(output_dir / "messages.json")
        
        # Determine total for progress
        count_result = await count_messages(client, dialog_id, since=since_dt)
        if not count_result.ok:
            return count_result

        total_remote = count_result.payload
        effective_total = min(total_remote, limit) if limit else total_remote
        new_to_fetch = max(0, effective_total - len(existing_ids))
        pages = math.ceil(new_to_fetch / PAGE_SIZE) if new_to_fetch else 0

        # T23 — progress stages 1-3
        _progress_start(dialog_id, dialog_name, limit, since_dt, output_dir / "messages.json")
        _progress_local_scan(len(existing_ids), latest_local, new_to_fetch)
        _progress_estimate(new_to_fetch, pages)

        # Resume point: use latest_local as since if we have existing data
        resume_since = latest_local if (existing_ids and latest_local) else since_dt

        # T19 — pagination loop
        all_messages = []
        pauses = 0
        tty = _is_tty()
        start_time = time.monotonic()
        fetched_count = 0
        page_num = 0

        remaining = new_to_fetch
        while remaining > 0:
            page_limit = min(PAGE_SIZE, remaining)
            result = await read_messages(
                client, dialog_id, since=resume_since, limit=page_limit, for_pagination=True,
            )

            if not result.ok:
                err = result.error
                if err.code.value == "RATE_LIMITED" and err.retry_after:
                    pauses += 1
                    await asyncio.sleep(err.retry_after)
                    continue  # retry same page
                return result  # non-recoverable error

            page_msgs = result.payload
            if not page_msgs:
                # No more messages available
                logger.debug(f"Pagination ended: no messages returned despite remaining={remaining}")
                break  # no more messages

            # KEY FIX: Always process ALL messages from the page, not just "new" ones
            # because on first fetch resume_since points to BEFORE first batch of messages
            new_msgs = [m for m in page_msgs if m.id not in existing_ids]
            if not new_msgs:
                # All messages on this page already exist - stop pagination
                print(f"[PAGINATION] All remaining messages already exist (existing_ids={len(existing_ids)}), stopping", file=sys.stderr)
                logger.info(f"All remaining messages already exist (existing_ids={len(existing_ids)}), stopping pagination")
                break
            
            all_messages.extend(new_msgs)
            # Track collected IDs so boundary-message overlaps are deduplicated
            # even if the library returns the same message on two adjacent pages.
            existing_ids.update(m.id for m in new_msgs)
            fetched_count += len(new_msgs)
            page_num += 1
            remaining -= len(new_msgs)
            
            # DEBUG: Log page fetch details TO STDERR
            msg = f"[PAGINATION] Page {page_num}: fetched {len(page_msgs)}, new {len(new_msgs)}, total_collected={len(all_messages)}, remaining={remaining}"
            print(msg, file=sys.stderr)
            logger.info(msg)

            # Update resume_since to the earliest (oldest) message date in this page
            # In Telegram, messages are typically returned newest-first
            if page_msgs:
                oldest_in_page = page_msgs[-1] if page_msgs else page_msgs[0]
                resume_since = oldest_in_page.date
                logger.debug(f"Next request will use resume_since={resume_since}")

            # T23 — progress bar (stage 4)
            elapsed = time.monotonic() - start_time
            _progress_bar(page_num, pages, fetched_count, new_to_fetch, elapsed, tty)

        elapsed = time.monotonic() - start_time
        
        # Show final progress bar at 100% completion
        if tty:
            _progress_bar(pages, pages, new_to_fetch, new_to_fetch, elapsed, tty)
        
        # Download media files for messages that have media
        ENABLE_MEDIA_DOWNLOADS = True
        file_paths = {}  # message_id -> relative_file_path mapping
        download_stats = {"attempted": 0, "success": 0, "failed": 0}
        if enabled_categories and ENABLE_MEDIA_DOWNLOADS:
            _CAT_DIR = {
                "media": output_dir / "media",
                "files": output_dir / "files",
                "music": output_dir / "music",
                "voice": output_dir / "voice",
                "gifs": output_dir / "gifs",
            }
            # Collect list of (msg, category, target_dir) to download
            to_download = []
            for msg in all_messages:
                if msg.has_media and msg.media_type:
                    category = _get_media_category(msg.media_type)
                    if category and category in enabled_categories and category in _CAT_DIR:
                        to_download.append((msg, _CAT_DIR[category]))

            total_files = len(to_download)
            if total_files > 0:
                print(f"Downloading files: {total_files} total.")
                dl_start = time.monotonic()
                for i, (msg, target_dir) in enumerate(to_download, 1):
                    target_dir.mkdir(parents=True, exist_ok=True)
                    download_stats["attempted"] += 1

                    download_result = await download_media(
                        client, dialog_id, msg.id, dest_dir=str(target_dir)
                    )

                    if download_result.ok:
                        media_result = download_result.payload
                        full_path = Path(media_result.file_path)
                        file_paths[msg.id] = full_path.name
                        download_stats["success"] += 1
                    else:
                        error = download_result.error
                        logger.warning(
                            f"Failed to download msg {msg.id}: "
                            f"{error.code.value if error.code else '?'} - "
                            f"{error.message if error else 'unknown error'}"
                        )
                        download_stats["failed"] += 1

                    dl_elapsed = time.monotonic() - dl_start
                    _progress_bar_files(i, total_files, dl_elapsed, tty)

                if tty:
                    # Show final bar then move to new line
                    dl_elapsed = time.monotonic() - dl_start
                    _progress_bar_files(total_files, total_files, dl_elapsed, tty)
                    print()
                logger.info(
                    f"File downloads: {download_stats['success']} ok, "
                    f"{download_stats['failed']} failed, {total_files} total"
                )
        
        # Extract members if requested
        members_data = []
        if "members" in enabled_categories:
            members_result = await get_members(client, dialog_id)
            if members_result.ok:
                members_list = members_result.payload
                members_data = [
                    {
                        "id": m.id,
                        "name": m.name,
                        "username": m.username,
                        "photo_file_path": m.photo_file_path,
                    }
                    for m in members_list
                ]
        
        return (all_messages, file_paths, pauses, elapsed, output_dir, members_data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_since(since: str | None) -> datetime | None:
    """Parse ISO 8601 string to datetime or return None."""
    if since is None:
        return None
    try:
        dt = datetime.fromisoformat(since)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        print(f"Error: Invalid --since timestamp: {since}", file=sys.stderr)
        sys.exit(1)


def _check_output_writable(output_path: Path) -> None:
    """T11 — check that we can write to the output directory."""
    parent = output_path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = parent / ".telegram-cli-write-test"
        test_file.touch()
        test_file.unlink()
    except OSError as exc:
        print(f"Error: Output directory not writable: {exc}", file=sys.stderr)
        sys.exit(2)


def _message_to_dict(msg, file_path: str | None = None) -> dict:
    """Convert a MessageInfo to a JSON-serializable dict."""
    msg_dict = {
        "id": msg.id,
        "dialog_id": msg.dialog_id,
        "text": msg.text,
        "date": msg.date.isoformat(),
        "sender_id": msg.sender_id,
        "sender_name": msg.sender_name,
        "has_media": msg.has_media,
        "media_type": msg.media_type,
    }
    # Add file_path if available (for media messages)
    if file_path:
        msg_dict["file_path"] = file_path
    return msg_dict


def _load_existing_data(output_path: Path) -> list[dict]:
    """Load existing JSON array from output file, or return empty list."""
    if not output_path.is_file():
        return []
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _merge_messages(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new messages into existing, deduplicate by ID, sort by date."""
    by_id = {m["id"]: m for m in existing}
    for m in new:
        by_id[m["id"]] = m
    return sorted(by_id.values(), key=lambda m: m.get("date", ""))
