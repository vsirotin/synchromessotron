"""
Init command (F10) — interactive session setup.

Creates or updates config.yaml by generating a Telegram session string
through an interactive login flow.

Decision tree:
1. Show interruption guidance
2. Search for config in default position
3. If found → inform and quit
4. If not found → ask user:
   a. Do you have it elsewhere? → recommend copy and quit
   b. Do you have credentials noted? → offer example file creation
   c. Otherwise → continue to credential prompts
5. Authenticate with Telegram

Requirements:
- F10-a: Detect existing config with informed guidance
- F10-b: Show user guidance about Ctrl+C
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
    """Run the interactive init flow with decision tree."""
    config_path = _find_config_file()

    # Step 1: Show interruption guidance
    print("ℹ  To interrupt at any time, press Ctrl+C\n")

    # Step 2: Search for config in default position
    if config_path.exists():
        _inform_config_found(config_path)
        return

    # Step 3: Config not found — ask if user has it elsewhere
    if _ask_has_config_elsewhere():
        return

    # Step 4: Ask if user has credentials noted
    if _ask_has_credentials_noted():
        # User said yes — offer example file creation
        if _ask_create_example_file():
            _create_example_config(config_path)
            return
        # User said no — continue to credential prompts
    # else: User said no — continue to credential prompts

    # Step 5: Prompt for credentials and authenticate
    config = _prompt_credentials()
    asyncio.run(_do_auth(config, config_path))


def _inform_config_found(config_path: Path) -> None:
    """
    Config found in default position.
    Inform user and exit gracefully.
    """
    print(f"ℹ  Found config.yaml at: {config_path}")
    print("  No need to set up again. Run 'telegram-cli whoami' to verify your session.")
    sys.exit(0)


def _ask_has_config_elsewhere() -> bool:
    """
    Ask user if they have config.yaml in another location.
    
    Returns:
        True if user answered yes (and we should exit after recommending copy)
        False if user answered no (continue to next decision)
    """
    try:
        response = input(
            "Do you have config.yaml in another location? [y/N]: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)

    if response in ("y", "yes"):
        print("\n➜ Please copy config.yaml to the current directory:")
        print(f"  cp /path/to/config.yaml ./config.yaml")
        print("  Then run 'telegram-cli init' again.\n")
        sys.exit(0)

    return False


def _ask_has_credentials_noted() -> bool:
    """
    Ask user if they have api_id, api_hash, and session noted somewhere.
    
    Returns:
        True if user answered yes
        False if user answered no
    """
    try:
        response = input(
            "Do you have api_id, api_hash, and session noted somewhere? [y/N]: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)

    return response in ("y", "yes")


def _ask_create_example_file() -> bool:
    """
    Ask user if they want us to create an example config file.
    
    Returns:
        True if user answered yes
        False if user answered no (continue to credential prompts)
    """
    try:
        response = input(
            "Should I create an example config.yaml.example for you to fill in? [y/N]: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.")
        sys.exit(1)

    return response in ("y", "yes")


def _create_example_config(config_path: Path) -> None:
    """
    Create a template config.yaml.example.
    
    Exit codes:
    - 0: Success
    - 1: User cancelled
    - 2: File creation error
    """
    example_path = config_path.parent / "config.yaml.example"

    example_content = """\
# telegram-cli configuration template
# 1. Rename this file to config.yaml
# 2. Fill in your Telegram credentials
# 3. Run 'telegram-cli init' to complete setup

telegram:
  api_id: YOUR_API_ID_HERE
  api_hash: YOUR_API_HASH_HERE
  phone: YOUR_PHONE_NUMBER_HERE
  session: null  # Generated automatically by 'telegram-cli init'
"""

    try:
        example_path.write_text(example_content, encoding="utf-8")
        print(f"\n✓ Example config created: {example_path}")
        print("  Steps:")
        print(f"    1. Edit config.yaml.example (fill in YOUR_API_ID_HERE, etc.)")
        print(f"    2. Rename to config.yaml")
        print(f"    3. Run 'telegram-cli init' again\n")
        sys.exit(0)
    except OSError as exc:
        print(f"✗ Error: Cannot create example config: {exc}", file=sys.stderr)
        sys.exit(2)


def _prompt_credentials() -> dict:
    """
    F10-b, F10-d: Prompt user for api_id, api_hash, and phone.
    
    Gracefully handle Ctrl+C with user-friendly message (no tracebacks).
    
    Exit codes:
    - Returns dict on success
    - 1 on KeyboardInterrupt/EOFError
    - 1 on validation error
    """
    print("Setting up Telegram credentials.\n")
    try:
        api_id_str = input("Enter your api_id: ").strip()
        try:
            api_id = int(api_id_str)
        except ValueError:
            print("✗ Error: api_id must be a number.", file=sys.stderr)
            sys.exit(1)

        api_hash = input("Enter your api_hash: ").strip()
        if not api_hash:
            print("✗ Error: api_hash cannot be empty.", file=sys.stderr)
            sys.exit(1)

        phone = input("Enter your phone number (e.g. +1234567890): ").strip()
        if not phone:
            print("✗ Error: phone cannot be empty.", file=sys.stderr)
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

