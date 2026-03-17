"""
Get-dialogs command (F5) — list the user's Telegram dialogs.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from src.config import load_config, resolve_outdir
from src._lib import create_client, get_dialogs
from src.errors import format_error_and_exit


def run_get_dialogs(*, limit: int | None = None, outdir: str | None = None) -> None:
    """Load config, fetch dialogs, print table, and optionally save JSON."""
    config = load_config()
    resolved_outdir = resolve_outdir(outdir, config)
    client = create_client(config["api_id"], config["api_hash"], config["session"])

    kwargs = {}
    if limit is not None:
        kwargs["limit"] = limit

    result = asyncio.run(_fetch_dialogs(client, **kwargs))

    if not result.ok:
        format_error_and_exit(result.error)

    dialogs = result.payload
    _print_table(dialogs)

    if resolved_outdir is not None:
        _save_json(dialogs, resolved_outdir)


def _print_table(dialogs: list) -> None:
    """Print dialogs as a human-readable table."""
    print(f"  {'TYPE':<12} {'ID':<18} {'NAME'}")
    print(f"  {'-' * 12} {'-' * 18} {'-' * 42}")
    for d in dialogs:
        name = d.name
        if d.username:
            name += f"  @{d.username}"
        print(f"  {d.type:<12} {d.id:<18} {name}")
    print(f"\n{len(dialogs)} dialogs found.")


def _save_json(dialogs: list, outdir: Path) -> None:
    """Save dialogs as dialogs.json in the output directory."""
    outdir.mkdir(parents=True, exist_ok=True)
    filepath = outdir / "dialogs.json"
    data = [
        {
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "username": d.username,
            "unread_count": d.unread_count,
        }
        for d in dialogs
    ]
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {filepath}")


async def _fetch_dialogs(client, **kwargs):
    """Connect, fetch dialogs, disconnect."""
    async with client:
        return await get_dialogs(client, **kwargs)
