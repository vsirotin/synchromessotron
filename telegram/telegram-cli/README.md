# telegram-cli

Command-line interface for Telegram — backup dialogs, send/edit/delete messages, download media, and check connectivity from the terminal.

## Overview

| Command | What it does |
|---------|-------------|
| `backup` | Full or incremental message backup |
| `send` | Send a message to a dialog |
| `edit` | Edit a previously sent message |
| `delete` | Delete own messages |
| `get-dialogs` | List the user's dialogs |
| `download-media` | Download a media file from a message |
| `ping` | Check Telegram availability |
| `whoami` | Validate session and show user info |

> **Terminology:** In the Telegram API the term **"dialog"** denotes any conversation the user participates in — a one-to-one chat with another user, a group, or a channel.

---

## Getting Started

### Step 1 — Create a Telegram application

1. Open <https://my.telegram.org/apps> in a browser and sign in with your phone number.
2. Click **API development tools**.
3. Fill in the **Create new application** form. The App title and Short name can be anything, e.g. `synchromessotron` / `syncbot`. Platform can be left as `Other`.

   ![Create new application dialog](docs/images/telegram1.png)

4. Click **Create application**.
5. You will see your **App api_id** (a number) and **App api_hash** (a long hex string). Note both values — you will need them in the next step.

   ![api_id and api_hash](docs/images/telegram2.png)

### Step 2 — Create the credentials file

Your credentials are stored in a local file `.env.telegram` which is **excluded from version control** (listed in `.gitignore`). It will never be committed.

Copy the example file and fill in your real values:

```bash
cp .env.telegram.example .env.telegram
```

Open `.env.telegram` in your editor and set your values:

```dotenv
TG_API_ID=12345
TG_API_HASH=your_api_hash_here
TG_PHONE=+1234567890
TG_SESSION=
```

Replace `12345` with your real api_id, `your_api_hash_here` with your real api_hash, and `+1234567890` with your Telegram phone number (with country code). Leave `TG_SESSION` empty for now.

> **Security:** The `.env.telegram` file is matched by the `.env.*` pattern in `.gitignore` and will never be committed. Never share this file.

### Step 3 — Generate a session string

Run the session generation script:

```bash
python3 tools/generate_session.py
```

The script reads your `api_id`, `api_hash`, and phone number from `.env.telegram`, then:

1. Sends a confirmation code to your Telegram app — type it when prompted.
2. If you have Two-Step Verification enabled, asks for your **2FA password**.

> **What is the 2FA password?** It is a password *you chose yourself* when you enabled Two-Step Verification in Telegram. To check or change it: open Telegram → **Settings → Privacy and Security → Two-Step Verification**.

The script prints a session string. Copy it and add it to your `.env.telegram` file:

```dotenv
TG_SESSION=your_generated_session_string_here
```

**Treat the session string like a password.**

### Step 4 — Install telegram-cli

```bash
cd synchromessotron/telegram/telegram-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Step 5 — Run unit tests

```bash
pytest tests/unit/
```

All tests should pass. No credentials or network needed.

### Step 6 — Verify the setup

```bash
telegram-cli whoami
```

**Expected result:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [SESSION_INVALID]: Session is invalid or revoked` | Session string is wrong, expired, or was revoked from another device. | Re-run `python3 tools/generate_session.py` and update `TG_SESSION` in `.env.telegram`. |
| `Error [AUTH_FAILED]: User account is deactivated or banned` | Telegram account is suspended. | Contact Telegram support. |
| `Error [NETWORK_ERROR]: ...` | No internet connection or Telegram is blocked. | Check your network; try again later. |

```bash
telegram-cli ping
```

**Expected result:**

```
✓ Telegram is reachable (42.3 ms)
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [NETWORK_ERROR]: ...` | Device is offline or Telegram is blocked in your region. | Check your internet connection or try a VPN. |

---

## Command Reference

### get-dialogs — List dialogs

```bash
telegram-cli get-dialogs [--limit=N] [--output=FILE]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | all | Maximum number of dialogs to return. |
| `--output` | stdout | Write JSON to this file instead of printing a table. |

**Expected result:**

```
  TYPE         ID                 NAME
  ------------ ------------------ ------------------------------------------
  User         123456789          Your Name  @yourhandle
  Channel      -1001234567890     Family Group  @familygroup
  Chat         -987654321         Old Project

3 dialogs found.
```

With `--output=dialogs.json`, no table is printed; the JSON file is written silently.

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [SESSION_INVALID]: ...` | Session expired. | Re-generate the session (Step 3). |
| `Error [NETWORK_ERROR]: ...` | No connection. | Check your internet. |
| `Error [RATE_LIMITED]: ... retry after Ns` | Too many requests. | Wait N seconds and try again. |

---

### backup — Backup messages

```bash
telegram-cli backup <dialog_id> [--since=TIMESTAMP] [--limit=N] [--output=FILE]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--since` | — | ISO 8601 timestamp; only messages after it are returned (incremental). |
| `--limit` | 100 | Maximum number of messages. |
| `--output` | stdout | Write JSON to this file. |

**Expected result** (full backup):

```bash
telegram-cli backup -1001234567890 --limit=500 --output=backup.json
```

```
✓ 500 messages saved to backup.json
```

**Expected result** (incremental):

```bash
telegram-cli backup -1001234567890 --since="2026-03-01T00:00:00" --output=incremental.json
```

```
✓ 12 messages saved to incremental.json
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [ENTITY_NOT_FOUND]: ...` | The dialog ID does not exist or you have no access. | Run `get-dialogs` to find the correct ID. |
| `Error [RATE_LIMITED]: ... retry after Ns` | Too many requests in a short time. | Wait N seconds and retry. |
| `Error [NETWORK_ERROR]: ...` | Connection lost during backup. | Check network, then retry. |

---

### send — Send a message

```bash
telegram-cli send <dialog_id> --text=TEXT
```

**Expected result:**

```bash
telegram-cli send -1001234567890 --text="Hello from CLI!"
```

```
✓ Message sent
  ID:    12345
  Date:  2026-03-16 14:30:00
  Text:  Hello from CLI!
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [ENTITY_NOT_FOUND]: ...` | Dialog ID does not exist. | Check the ID with `get-dialogs`. |
| `Error [PERMISSION_DENIED]: ...` | You cannot write to this channel/group. | Verify your permissions in the dialog. |
| `Error [RATE_LIMITED]: ... retry after Ns` | Sending too fast. | Wait N seconds. |

---

### edit — Edit a message

```bash
telegram-cli edit <dialog_id> <message_id> --text=TEXT
```

**Expected result:**

```bash
telegram-cli edit -1001234567890 42 --text="Corrected text"
```

```
✓ Message edited
  ID:    42
  Date:  2026-03-16 14:30:00
  Text:  Corrected text
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [ENTITY_NOT_FOUND]: ...` | Dialog or message ID does not exist. | Verify both IDs. |
| `Error [PERMISSION_DENIED]: ...` | The message was sent by another user. | You can only edit your own messages. |
| `Error [NOT_MODIFIED]: ...` | New text is identical to the current text. | Provide different text. |

---

### delete — Delete messages

```bash
telegram-cli delete <dialog_id> <message_id> [<message_id> ...]
```

**Expected result:**

```bash
telegram-cli delete -1001234567890 42 43 44
```

```
✓ 3 messages deleted
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [ENTITY_NOT_FOUND]: ...` | Dialog or message ID does not exist. | Verify the IDs. |
| `Error [PERMISSION_DENIED]: ...` | You cannot delete these messages. | You can only delete your own messages. |

---

### download-media — Download media

```bash
telegram-cli download-media <dialog_id> <message_id> [--dest=DIR]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dest` | `.` (current directory) | Target directory for the downloaded file. |

**Expected result:**

```bash
telegram-cli download-media -1001234567890 42 --dest=./downloads
```

```
✓ Downloaded: ./downloads/photo_42.jpg (2.1 MB)
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [ENTITY_NOT_FOUND]: ...` | Dialog, message, or media not found. The message may have no media attached. | Verify the IDs; check that the message contains media. |
| `Error [NETWORK_ERROR]: ...` | Download interrupted. | Check your connection and retry. |

---

### ping — Check availability

```bash
telegram-cli ping
```

**Expected result:**

```
✓ Telegram is reachable (42.3 ms)
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [NETWORK_ERROR]: ...` | No internet or Telegram is blocked. | Check your connection or try a VPN. |

---

### whoami — Validate session

```bash
telegram-cli whoami
```

**Expected result:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

**What can go wrong:**

| Output | Cause | What to do |
|--------|-------|------------|
| `Error [SESSION_INVALID]: ...` | Session expired or revoked. | Re-generate the session (Step 3). |
| `Error [AUTH_FAILED]: ...` | Account deactivated or banned. | Contact Telegram support. |

---

## Manual Tests

### Test: No network connection

This test verifies that telegram-cli reports a clear error when Telegram is unreachable.

**Setup:** Disconnect from the internet (turn off Wi-Fi, unplug the cable, or enable airplane mode).

**Steps:**

```bash
telegram-cli ping
```

**Expected result:**

```
Error [NETWORK_ERROR]: Cannot reach Telegram
```

Exit code: `2`.

```bash
telegram-cli get-dialogs
```

**Expected result:**

```
Error [NETWORK_ERROR]: ...
```

**Teardown:** Re-enable your network connection.

---

## Error Handling

When a command fails, an error message is printed to stderr and the process exits with a non-zero code.

Example:

```
Error [RATE_LIMITED]: Too many requests — retry after 30s
  retry_after: 30
```

**Error codes and what to do:**

| Code | Meaning | Action |
|------|---------|--------|
| `RATE_LIMITED` | Too many requests. | Wait the number of seconds shown in `retry_after`, then retry. |
| `AUTH_FAILED` | Account deactivated or banned. | Contact Telegram support. |
| `SESSION_INVALID` | Session expired or revoked. | Re-generate the session (Step 3). |
| `ENTITY_NOT_FOUND` | Dialog or message ID does not exist. | Verify the ID with `get-dialogs`. |
| `PERMISSION_DENIED` | No permission (e.g. read-only channel, not your message). | Check your rights in the dialog. |
| `NOT_MODIFIED` | Edit text is identical to current text. | Provide different text. |
| `NETWORK_ERROR` | Cannot reach Telegram. | Check your internet connection. |
| `INTERNAL_ERROR` | Unexpected failure. | Report the issue with the error details. |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Argument or usage error |
| 2 | Telegram API error (one of the error codes above) |

## Output Formats

- **Terminal (TTY):** human-readable tables and status messages.
- **File (`--output`):** JSON for machine-readable processing.
- **Piped stdout (non-TTY):** JSON, suitable for chaining with `jq` or other tools.
