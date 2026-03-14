#!/usr/bin/env python3
"""
Generate a Telegram session string.

Reads TG_API_ID, TG_API_HASH, and TG_PHONE from the .env.telegram file,
connects to Telegram, and prints a session string that you must add back
to .env.telegram as the TG_SESSION value.

Usage:
    python3 tools/generate_session.py
"""

import asyncio
import sys
from pathlib import Path

from dotenv import dotenv_values
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession


def _find_env_file() -> Path:
    """Look for .env.telegram in the script's parent directory or cwd."""
    candidates = [
        Path(__file__).resolve().parent.parent / ".env.telegram",
        Path.cwd() / ".env.telegram",
    ]
    for p in candidates:
        if p.exists():
            return p
    sys.exit(
        "Error: .env.telegram not found.\n"
        "Copy .env.telegram.example to .env.telegram and fill in your values:\n"
        "  cp .env.telegram.example .env.telegram"
    )


async def main() -> None:
    env_path = _find_env_file()
    env = dotenv_values(env_path)

    api_id_str = env.get("TG_API_ID", "").strip()
    api_hash = env.get("TG_API_HASH", "").strip()
    phone = env.get("TG_PHONE", "").strip()

    if not api_id_str or api_id_str == "12345":
        sys.exit("Error: TG_API_ID in .env.telegram is not set or still has the example value.")
    if not api_hash or api_hash == "your_api_hash_here":
        sys.exit("Error: TG_API_HASH in .env.telegram is not set or still has the example value.")
    if not phone or phone == "+1234567890":
        sys.exit("Error: TG_PHONE in .env.telegram is not set or still has the example value.")

    api_id = int(api_id_str)
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    print(f"Sending confirmation code to {phone}...")
    await client.send_code_request(phone)
    code = input("Enter the code Telegram sent to your app: ").strip()

    try:
        await client.sign_in(phone, code)
    except SessionPasswordNeededError:
        password = input("Enter your 2FA password: ").strip()
        await client.sign_in(password=password)

    session_string = client.session.save()
    await client.disconnect()

    print("\n" + "=" * 60)
    print("Your session string (treat it like a password!):")
    print(session_string)
    print("=" * 60)
    print(f"\nNow open {env_path} and set:")
    print(f"  TG_SESSION={session_string}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
