#!/usr/bin/env python3
"""
Telegram setup helper for Synchromessotron.

Commands:

  python3 tools/tg_check.py list

      Lists your 50 most recent Telegram dialogs with their numeric IDs.
      Use this to find the ID of the group or chat you want to sync.
      Requires the TG_CREDS environment variable.

  python3 tools/tg_check.py test <dialog_id>

      Shows the last 3 messages from the given dialog and lets you send
      a test message to confirm write access works.
      Requires the TG_CREDS environment variable.

Examples:

  python3 tools/tg_check.py list
  python3 tools/tg_check.py test -1001234567890
  python3 tools/tg_check.py test me
"""

import asyncio
import json
import os
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession


def _load_creds() -> dict:
    raw = os.environ.get("TG_CREDS")
    if not raw:
        sys.exit(
            "Error: TG_CREDS environment variable is not set.\n"
            "Set it with: export TG_CREDS='"
            '{"api_id": 12345, "api_hash": "...", "session": "..."}\''
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"Error: TG_CREDS is not valid JSON: {e}")


def _make_client(creds: dict) -> TelegramClient:
    return TelegramClient(StringSession(creds["session"]), creds["api_id"], creds["api_hash"])


async def cmd_list() -> None:
    """List all dialogs with their IDs."""
    creds = _load_creds()
    async with _make_client(creds) as client:
        me = await client.get_me()
        print(
            f"\n✓ Logged in as: {me.first_name} {me.last_name or ''}"
            f" (@{me.username or 'no username'}, id={me.id})\n"
        )
        print(f"  {'TYPE':<12} {'ID':<18} NAME")
        print(f"  {'-'*12} {'-'*18} {'-'*45}")
        async for dialog in client.iter_dialogs(limit=50):
            e = dialog.entity
            kind = type(e).__name__
            uname = f"  @{e.username}" if getattr(e, "username", None) else ""
            print(f"  {kind:<12} {str(dialog.id):<18} {dialog.name}{uname}")
        print()
    print("Copy the ID (including the minus sign for groups/channels)")
    print("and use it as account_id in your config.yaml.\n")


async def cmd_test(dialog_id: str) -> None:
    """Show last 3 messages and send an optional test message."""
    creds = _load_creds()
    async with _make_client(creds) as client:
        # Resolve dialog — accept numeric IDs and string handles like "me" or "@username"
        entity_ref = int(dialog_id) if dialog_id.lstrip("-").isdigit() else dialog_id
        try:
            entity = await client.get_entity(entity_ref)
        except ValueError as e:
            sys.exit(f"Error: could not find dialog {dialog_id!r}: {e}")

        title = getattr(entity, "title", None) or getattr(entity, "first_name", dialog_id)
        print(f"\n✓ Dialog: {title}  (id={dialog_id})\n")

        messages = await client.get_messages(entity, limit=3)
        if not messages:
            print("  (no messages in this dialog yet)\n")
        else:
            print("  Last 3 messages (oldest first):")
            print(f"  {'-'*60}")
            for msg in reversed(messages):
                ts = msg.date.astimezone().strftime("%Y-%m-%d %H:%M")
                sender = ""
                if msg.sender:
                    sender = (
                        getattr(msg.sender, "first_name", None)
                        or getattr(msg.sender, "title", None)
                        or "?"
                    )
                text = msg.text or "(media / no text)"
                # Truncate long messages for display
                if len(text) > 80:
                    text = text[:77] + "..."
                print(f"  [{ts}] {sender}: {text}")
            print(f"  {'-'*60}\n")

        text = input("Send a test message (press Enter to skip): ").strip()
        if text:
            await client.send_message(entity, text)
            print("✓ Message sent.\n")
        else:
            print("Skipped.\n")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "test"):
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "list":
        asyncio.run(cmd_list())
    elif sys.argv[1] == "test":
        if len(sys.argv) < 3:
            sys.exit("Usage: python3 tools/tg_check.py test <dialog_id>\n"
                     "Example: python3 tools/tg_check.py test -1001234567890")
        asyncio.run(cmd_test(sys.argv[2]))


if __name__ == "__main__":
    main()
