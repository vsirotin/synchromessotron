"""
Init command (F10) — interactive session setup.

Creates or updates config.yaml by generating a Telegram session string
through an interactive login flow.

Requirements:
- F10-a: Detect existing config and offer choices (exit or create example)
- F10-b: Show user guidance about Ctrl+C before credentials
- F10-c: Handle login code with graceful Ctrl+C support
- F10-d: Graceful error handling — no tracebacks
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

    # F10-a: Detect existing config and offer choices
    if config_path.exists():
        _handle_existing_config(config_path)
        return  # Exit after user's choice

    # F10-b: Show interruption guidance before starting credential input
    print("ℹ  To interrupt at any time, press Ctrl+C\n")

    # Prompt for new credentials
    config = _prompt_credentials()

    asyncio.run(_do_auth(config, config_path))


def _handle_existing_config(config_path: Path) -> None:
    """
    F10-a: Handle existing config.yaml.
    
    Offer user two options:
    [A] Exit and let user copy existing config elsewhere
    [B] Create example config.yaml.example for reference
    """
    print("ℹ  Found existing config.yaml. Either:")
    print("  - Copy it to this directory and run 'telegram-cli init' again, or")
    print("  - Choose option [B] below.")
    
    try:
        user_choice = input("  [A] Exit now  [B] Create example config.yaml here  [Enter for A]: ").strip().upper()
    except KeyboardInterrupt:
        # F10-d: Graceful Ctrl+C handling
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)

    if user_choice == "B":
        _create_example_config(config_path)
    else:
        # Default to [A] if empty or invalid input
        # Just exit gracefully
        sys.exit(0)


def _create_example_config(config_path: Path) -> None:
    """
    F10-a (option B): Create a template config.yaml.example.
    """
    example_path = config_path.parent / "config.yaml.example"
    
    example_content = """\
# telegram-cli configuration template
# Rename this to config.yaml and fill in your credentials

telegram:
  api_id: YOUR_API_ID_HERE
  api_hash: YOUR_API_HASH_HERE
  phone: YOUR_PHONE_NUMBER_HERE
  session: null  # Generated automatically by 'telegram-cli init'
"""
    
    try:
        example_path.write_text(example_content, encoding="utf-8")
        print("✓ Example config created as config.yaml.example")
        print("  Edit it with your credentials and rename to config.yaml, then re-run 'telegram-cli init'.")
        sys.exit(0)
    except OSError as exc:
        print(f"Error [INTERNAL_ERROR]: Cannot create example config: {exc}", file=sys.stderr)
        sys.exit(1)


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
    """
    F10-b, F10-d: Prompt user for api_id, api_hash, and phone.
    Gracefully handle Ctrl+C with user-friendly message (no tracebacks).
    """
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

    except KeyboardInterrupt:
        # F10-d: Graceful cancellation message
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)
    except EOFError:
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)

    return {"api_id": api_id, "api_hash": api_hash, "phone": phone}


async def _do_auth(config: dict, config_path: Path) -> None:
    """
    F10-c, F10-d: Connect to Telegram, authenticate, and save the session string.
    
    Handle login code callback with graceful Ctrl+C support.
    Catch all exceptions and display user-friendly error messages (no tracebacks).
    """
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
        # F10-c: Code callback with graceful Ctrl+C handling
        def code_callback():
            """Prompt for login code, handle Ctrl+C gracefully."""
            try:
                return input("Enter the login code sent to your Telegram app (or press Ctrl+C to cancel): ").strip()
            except KeyboardInterrupt:
                raise KeyboardInterrupt("User cancelled during code input")

        def password_callback():
            """Prompt for 2FA password, handle Ctrl+C gracefully."""
            try:
                return input("Enter your 2FA password (or press Ctrl+C to cancel): ").strip()
            except KeyboardInterrupt:
                raise KeyboardInterrupt("User cancelled during password input")

        await client.start(
            phone=lambda: config["phone"],
            code_callback=code_callback,
            password=password_callback,
        )
    except KeyboardInterrupt as exc:
        # F10-d: Graceful Ctrl+C handling
        await client.disconnect()
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)
    except Exception as exc:
        # F10-d: Graceful error handling — only show error code and message, no traceback
        await client.disconnect()
        error_msg = str(exc).lower()
        if "banned" in error_msg or "deactivated" in error_msg:
            print(f"Error [AUTH_FAILED]: Account is deactivated or banned. Contact Telegram support.", file=sys.stderr)
        else:
            print(f"Error [AUTH_FAILED]: Authentication failed.", file=sys.stderr)
        sys.exit(2)

    session_string = client.session.save()
    await client.disconnect()

    config["session"] = session_string
    try:
        save_config(config, config_path)
    except OSError as exc:
        print(f"Error [INTERNAL_ERROR]: Cannot save config.yaml: {exc}", file=sys.stderr)
        sys.exit(1)

    print("✓ Session created and saved to config.yaml")
    print("  Run 'python3 telegram-cli.pyz whoami' to verify.")

