#!/usr/bin/env python3
"""
VK setup helper for Synchromessotron.

Commands:

  python3 tools/vk_auth.py token

      Authenticates with your VK account (phone/email + password) and prints
      an access token with messages permission. Copy the token and use it in
      Step 6c to build VK_CREDS.

  python3 tools/vk_auth.py list

      Uses VK_CREDS (already exported) to list your recent conversations with
      their peer_ids. Use this to find the peer_id for the chat you want to sync.

  python3 tools/vk_auth.py test PEER_ID

      Reads the last 3 messages from the conversation and optionally sends a
      test message. Use this to verify credentials before proceeding to Step 7.

Usage:
  python3 tools/vk_auth.py token
  python3 tools/vk_auth.py list
  python3 tools/vk_auth.py test 123456789
"""

import json
import os
import sys


def get_vk_session():
    """Build a vk_api session from the VK_CREDS environment variable."""
    import vk_api

    raw = os.environ.get("VK_CREDS")
    if not raw:
        print("Error: VK_CREDS environment variable is not set.", file=sys.stderr)
        print(
            "  Run 'python3 tools/vk_auth.py token' first to obtain your token,",
            file=sys.stderr,
        )
        print(
            "  then export it: export VK_CREDS='{\"token\": \"YOUR_TOKEN\"}'",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        creds = json.loads(raw)
        token = creds["token"]
    except (json.JSONDecodeError, KeyError):
        print(
            "Error: VK_CREDS must be a JSON object with a 'token' key.",
            file=sys.stderr,
        )
        sys.exit(1)
    session = vk_api.VkApi(token=token)
    return session.get_api()


def _get_token_from_env() -> str | None:
    """Return token from VK_CREDS env var if present and valid JSON, else None."""
    raw = os.environ.get("VK_CREDS")
    if not raw:
        return None
    try:
        creds = json.loads(raw)
        token = creds.get("token")
        if isinstance(token, str) and token.strip():
            return token
    except json.JSONDecodeError:
        return None
    return None


def _is_token_valid(token: str) -> bool:
    """Check whether a VK token is accepted by a lightweight API call."""
    import vk_api

    try:
        vk = vk_api.VkApi(token=token).get_api()
        vk.users.get()
        return True
    except Exception:
        return False


def cmd_token():
    """Authenticate interactively and print an access token."""
    import getpass

    import vk_api

    existing_token = _get_token_from_env()
    if existing_token and _is_token_valid(existing_token):
        print("\n✓ VK_CREDS already contains a valid token.")
        print("No new login is required right now.")
        print("\nCurrent VK_CREDS export command:")
        print(f'  export VK_CREDS=\'{{"token": "{existing_token}"}}\'\n')
        return

    login = input("VK login (phone number or email): ").strip()
    # Using input() instead of getpass so you can see what you type.
    # Switch back to getpass.getpass() once auth works.
    password = input("VK password (visible): ").strip()

    def handle_captcha(captcha):
        url = captcha.get_url()
        print(f"\nCaptcha required. Open this URL in a browser: {url}")
        code = input("Enter the captcha code: ").strip()
        return captcha.try_again(code)

    def handle_2fa():
        # vk_api expects a (code, remember_device) tuple.
        # VK sends an OTP via SMS/app for new-device logins both before and
        # after the password step — this handler covers both cases.
        code = input(
            "VK sent a confirmation code (SMS or app notification). "
            "Enter it here: "
        ).strip()
        return code, True  # (code, remember_device)

    try:
        session = vk_api.VkApi(
            login=login,
            password=password,
            captcha_handler=handle_captcha,
            auth_handler=handle_2fa,
        )
        # Prefer cached auth if vk_api already has one; forced reauth can
        # trigger additional account lockouts after repeated failed attempts.
        session.auth(reauth=False)
    except vk_api.AuthError as e:
        print(f"\nOriginal VK AuthError: {e}", file=sys.stderr)
        err = str(e)
        if (
            "password_bruteforce" in err
            or "falsche Passwort" in err
            or "wrong password" in err.lower()
        ):
            print(
                "\nVK is blocking login due to too many recent failed attempts.",
                file=sys.stderr,
            )
            print(
                "\nThis is a VK-side temporary lock, not necessarily a wrong current password.\n"
                "Recommended recovery steps:\n"
                "  1. Stop retrying for at least 2 hours (more attempts can extend the lock).\n"
                "  2. In VK mobile app, check security/recent activity and approve\n"
                "     any pending login confirmation.\n"
                "  3. If you already have a previously issued token, reuse it in\n"
                "     VK_CREDS and continue with\n"
                "     'python3 tools/vk_auth.py list' (no password login needed).\n"
                "  4. Optionally retry from a different network (for example mobile hotspot).\n"
                "  5. If lock persists after cooldown, contact VK support from your\n"
                "     account help page.\n"
                "\nThen run this script again.",
                file=sys.stderr,
            )
        else:
            print(f"\nAuthentication failed: {e}", file=sys.stderr)
        sys.exit(1)

    token = session.token["access_token"]
    print("\n✓ Authenticated successfully.")
    print("\nYour VK access token (copy it — treat it like a password):")
    print(token)
    print()
    print("Now export it as VK_CREDS (Step 6c):")
    print(f'  export VK_CREDS=\'{{"token": "{token}"}}\'\n')


def cmd_list():
    """List recent VK conversations with their peer_ids."""
    import vk_api

    vk = get_vk_session()
    try:
        result = vk.messages.getConversations(count=30, extended=1)
    except vk_api.ApiError as e:
        print(f"Error fetching conversations: {e}", file=sys.stderr)
        sys.exit(1)

    profiles = {p["id"]: p for p in result.get("profiles", [])}
    groups = {g["id"]: g for g in result.get("groups", [])}

    print(f"\n  {'TYPE':<12} {'PEER_ID':<16} {'NAME'}")
    print(f"  {'-'*12} {'-'*16} {'-'*45}")

    for item in result.get("items", []):
        peer = item["conversation"]["peer"]
        peer_id = peer["id"]
        peer_type = peer["type"]

        if peer_type == "user":
            p = profiles.get(peer_id, {})
            name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            label = "User"
        elif peer_type == "chat":
            name = item["conversation"].get("chat_settings", {}).get("title", "")
            label = "Chat"
        elif peer_type == "group":
            g = groups.get(-peer_id, {})
            name = g.get("name", "")
            label = "Group"
        else:
            name = ""
            label = peer_type.capitalize()

        last = item.get("last_message", {})
        text = last.get("text", "")[:40]
        print(f"  {label:<12} {peer_id:<16} {name}  {text}")

    print()


def cmd_test(peer_id: int):
    """Read recent messages and optionally send a test message."""
    import vk_api

    vk = get_vk_session()
    try:
        result = vk.messages.getHistory(peer_id=peer_id, count=3, rev=0)
    except vk_api.ApiError as e:
        print(f"Error fetching messages: {e}", file=sys.stderr)
        sys.exit(1)

    items = list(reversed(result.get("items", [])))
    if not items:
        print(f"No messages found in conversation {peer_id}.")
    else:
        print(f"\n✓ Conversation peer_id={peer_id}")
        print()
        print("  Last 3 messages (oldest first):")
        print("  " + "-" * 60)
        for msg in items:
            from datetime import datetime

            ts = datetime.fromtimestamp(msg["date"], tz=datetime.UTC).strftime(
                "%Y-%m-%d %H:%M"
            )
            text = msg.get("text", "(no text)")
            from_id = msg.get("from_id", "?")
            print(f"  [{ts}] id={from_id}: {text}")
        print("  " + "-" * 60)

    test_text = input("\nSend a test message (press Enter to skip): ").strip()
    if test_text:
        try:
            import random

            vk.messages.send(peer_id=peer_id, message=test_text, random_id=random.randint(0, 2**31))
            print("✓ Message sent.")
        except vk_api.ApiError as e:
            print(f"Error sending message: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("(skipped)")
    print()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "token":
        cmd_token()
    elif cmd == "list":
        cmd_list()
    elif cmd == "test":
        if len(sys.argv) < 3:
            print("Usage: python3 tools/vk_auth.py test PEER_ID", file=sys.stderr)
            sys.exit(1)
        try:
            peer_id = int(sys.argv[2])
        except ValueError:
            print(f"Error: PEER_ID must be an integer, got: {sys.argv[2]}", file=sys.stderr)
            sys.exit(1)
        cmd_test(peer_id)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Use 'token', 'list', or 'test PEER_ID'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
