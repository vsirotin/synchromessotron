"""
Init command (F10) — interactive session setup.

Creates or updates config.yaml by generating a Telegram session string
through an interactive login flow.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from src.config import load_config, save_config, _find_config_file
from src._lib import create_client

logger = logging.getLogger("telegram_cli")


def run_init() -> None:
    """Run the interactive init flow."""
    config_path = _find_config_file()

    if config_path.exists():
        config = _load_existing_config(config_path)
    else:
        config = _prompt_credentials()

    asyncio.run(_do_auth(config, config_path))


def _load_existing_config(config_path: Path) -> dict:
    """Load existing config, reusing api_id, api_hash, phone."""
    import yaml
    try:
        text = config_path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        tg = data.get("telegram", {})
        for key in ("api_id", "api_hash", "phone"):
            if key not in tg:
                print(f"Error: Missing '{key}' in existing config.yaml.", file=sys.stderr)
                sys.exit(1)
        tg["api_id"] = int(tg["api_id"])
        return tg
    except (yaml.YAMLError, OSError) as exc:
        print(f"Error: Cannot read config.yaml: {exc}", file=sys.stderr)
        sys.exit(1)


def _prompt_credentials() -> dict:
    """Prompt user for api_id, api_hash, and phone."""
    print("Setting up telegram-cli credentials.\n")
    try:
        api_id_str = input("Enter your api_id: ").strip()
        try:
            api_id = int(api_id_str)
        except ValueError:
            print("Error: api_id must be a number.", file=sys.stderr)
            sys.exit(1)

        api_hash = input("Enter your api_hash: ").strip()
        if not api_hash:
            print("Error: api_hash cannot be empty.", file=sys.stderr)
            sys.exit(1)

        phone = input("Enter your phone number (e.g. +1234567890): ").strip()
        if not phone:
            print("Error: phone cannot be empty.", file=sys.stderr)
            sys.exit(1)

    except (EOFError, KeyboardInterrupt):
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)

    return {"api_id": api_id, "api_hash": api_hash, "phone": phone}


async def _do_auth(config: dict, config_path: Path) -> None:
    """Connect to Telegram, authenticate, and save the session string."""
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    client = TelegramClient(
        StringSession(),
        config["api_id"],
        config["api_hash"],
    )

    try:
        await client.connect()
    except Exception as exc:
        print(f"Error [NETWORK_ERROR]: Cannot connect to Telegram: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        await client.start(
            phone=lambda: config["phone"],
            code_callback=lambda: input("Enter the login code sent to your Telegram app: ").strip(),
            password=lambda: input("Enter your 2FA password: ").strip(),
        )
    except Exception as exc:
        print(f"Error [AUTH_FAILED]: Authentication failed: {exc}", file=sys.stderr)
        await client.disconnect()
        sys.exit(2)

    session_string = client.session.save()
    await client.disconnect()

    config["session"] = session_string
    save_config(config, config_path)

    print("✓ Session created and saved to config.yaml")
    print("  Run 'python3 telegram-cli.pyz whoami' to verify.")
