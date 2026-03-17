# Requirements for Sub-Project telegram-cli

This document describes the functional and technical requirements for telegram-cli — a command-line interface for performing Telegram operations (backup, messaging, media download, connectivity checks) from the terminal.

## Structural Requirements

Telegram-cli is a standalone command-line application. It loads credentials from the `.env.telegram` file, communicates with the Telegram API, and formats output for the terminal or file. The user interacts only with CLI commands and does not need to know about internal implementation details.

## Error Handling

Every command can fail. When it does, the tool prints a structured error to stderr and exits with a non-zero code. The error contains:

| Field | Description |
|-------|-------------|
| `code` | Machine-readable error code (see table below). |
| `message` | Human-readable explanation of what went wrong. |
| `retry_after` | Seconds to wait before retrying (only for `RATE_LIMITED`). |

**Error codes and recommended user actions:**

| Code | Meaning | What to do |
|------|---------|------------|
| `RATE_LIMITED` | Too many requests in a short time. | Wait the number of seconds shown in `retry_after`, then retry. |
| `AUTH_FAILED` | Account is deactivated or banned. | Contact Telegram support. |
| `SESSION_INVALID` | Session string is expired or revoked. | Re-generate the session (see Getting Started). |
| `ENTITY_NOT_FOUND` | The dialog or message ID does not exist. | Verify the ID with `get-dialogs`. |
| `PERMISSION_DENIED` | No permission for this action (e.g. writing to a read-only channel, editing someone else's message). | Check that you have the required rights in this dialog. |
| `NOT_MODIFIED` | The edit did not change anything (new text is identical to old). | Provide different text. |
| `NETWORK_ERROR` | Cannot connect to Telegram servers. | Check your internet connection and retry. |
| `INTERNAL_ERROR` | Unexpected failure. | Report the issue with the error details. |

**Example error output (stderr):**

```
Error [RATE_LIMITED]: Too many requests — retry after 30s
  retry_after: 30
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success. |
| 1 | Argument or usage error (wrong flags, missing required values). |
| 2 | Telegram API error (one of the error codes above). |

---

## Functional Requirements

> **Terminology:** In the Telegram API the term **"dialog"** denotes any conversation the user participates in — a one-to-one chat with another user, a group, or a channel.

---

### F1 — Backup message history

Retrieve messages from a dialog for full or incremental backup.

**Signature:**

```
telegram-cli backup <dialog_id> [--since=TIMESTAMP] [--limit=N] [--output=FILE]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `dialog_id` | yes | int | Numeric ID of the dialog (use `get-dialogs` to find it). |
| `--since` | no | ISO 8601 string | If set, only messages strictly after this timestamp are returned (incremental). If omitted, the most recent messages are returned (full). |
| `--limit` | no | int | Maximum number of messages to return. Default: `100`. |
| `--output` | no | file path | Write JSON output to this file instead of stdout. |

**Examples:**

```bash
# Full backup — last 500 messages, save to file
telegram-cli backup -1001234567890 --limit=500 --output=backup.json

# Incremental backup — only new messages since a date
telegram-cli backup -1001234567890 --since="2026-03-01T00:00:00" --output=incremental.json

# Quick preview — last 10 messages to stdout
telegram-cli backup -1001234567890 --limit=10
```

**Output:** JSON array of message objects (id, dialog_id, text, date, sender_name, has_media).

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `ENTITY_NOT_FOUND` | The `dialog_id` does not exist or is not accessible. |
| `RATE_LIMITED` | Too many requests. Wait `retry_after` seconds. |
| `SESSION_INVALID` | Session has expired. Re-generate it. |
| `NETWORK_ERROR` | No connection to Telegram. |

---

### F2 — Send a message

Send a text message to a dialog on behalf of the authenticated user.

**Signature:**

```
telegram-cli send <dialog_id> --text=TEXT
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `dialog_id` | yes | int | Target dialog. |
| `--text` | yes | string | The message text to send. |

**Examples:**

```bash
telegram-cli send -1001234567890 --text="Hello, world!"
telegram-cli send 123456789 --text="Direct message to a user"
```

**Output:** JSON object of the sent message (id, date, text).

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `ENTITY_NOT_FOUND` | The `dialog_id` does not exist. |
| `PERMISSION_DENIED` | You do not have write access to this dialog (e.g. read-only channel). |
| `RATE_LIMITED` | Too many messages sent. Wait `retry_after` seconds. |
| `SESSION_INVALID` | Session has expired. |
| `NETWORK_ERROR` | No connection to Telegram. |

---

### F3 — Edit a message

Edit a previously sent message. Only the user's own messages can be edited.

**Signature:**

```
telegram-cli edit <dialog_id> <message_id> --text=TEXT
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `dialog_id` | yes | int | The dialog containing the message. |
| `message_id` | yes | int | ID of the message to edit. |
| `--text` | yes | string | The replacement text. |

**Examples:**

```bash
telegram-cli edit -1001234567890 42 --text="Corrected text"
```

**Output:** JSON object of the updated message (id, date, text).

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `ENTITY_NOT_FOUND` | The dialog or message does not exist. |
| `PERMISSION_DENIED` | The message was sent by someone else — you can only edit your own. |
| `NOT_MODIFIED` | The new text is identical to the current text. Nothing was changed. |
| `RATE_LIMITED` | Too many requests. Wait `retry_after` seconds. |
| `SESSION_INVALID` | Session has expired. |

---

### F4 — Delete messages

Delete one or more of the user's own messages.

**Signature:**

```
telegram-cli delete <dialog_id> <message_id> [<message_id> ...]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `dialog_id` | yes | int | The dialog containing the messages. |
| `message_id` | yes | int (one or more) | IDs of the messages to delete. |

**Examples:**

```bash
# Delete a single message
telegram-cli delete -1001234567890 42

# Delete multiple messages
telegram-cli delete -1001234567890 42 43 44
```

**Output:** List of deleted message IDs.

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `ENTITY_NOT_FOUND` | The dialog or a message ID does not exist. |
| `PERMISSION_DENIED` | You do not have permission to delete messages in this dialog, or the message is not yours. |
| `RATE_LIMITED` | Too many requests. Wait `retry_after` seconds. |
| `SESSION_INVALID` | Session has expired. |

---

### F5 — List dialogs

Retrieve the user's Telegram dialogs (all conversations: users, groups, channels).

**Signature:**

```
telegram-cli get-dialogs [--limit=N] [--output=FILE]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `--limit` | no | int | Maximum number of dialogs to return. Default: all (no limit). |
| `--output` | no | file path | Write JSON output to this file instead of stdout. |

**Examples:**

```bash
# Print all dialogs as a table
telegram-cli get-dialogs

# Save first 50 dialogs to a file
telegram-cli get-dialogs --limit=50 --output=dialogs.json
```

**Output (stdout):** Human-readable table with columns: TYPE, ID, NAME.

**Output (file):** JSON array of dialog objects (id, name, type, username, unread_count).

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `RATE_LIMITED` | Too many requests. Wait `retry_after` seconds. |
| `SESSION_INVALID` | Session has expired. |
| `NETWORK_ERROR` | No connection to Telegram. |

---

### F6 — Download media

Download the media file (photo, video, document) attached to a specific message.

**Signature:**

```
telegram-cli download-media <dialog_id> <message_id> [--dest=DIR]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `dialog_id` | yes | int | The dialog containing the message. |
| `message_id` | yes | int | ID of the message whose media to download. |
| `--dest` | no | directory path | Target directory. Default: current directory (`.`). |

**Examples:**

```bash
telegram-cli download-media -1001234567890 42 --dest=./downloads
telegram-cli download-media -1001234567890 42
```

**Output:** File path, MIME type, and size in bytes of the downloaded file.

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `ENTITY_NOT_FOUND` | The dialog, message, or media does not exist (e.g. the message has no attachment). |
| `RATE_LIMITED` | Too many requests. Wait `retry_after` seconds. |
| `SESSION_INVALID` | Session has expired. |
| `NETWORK_ERROR` | No connection to Telegram. |

---

### F7 — Check availability

Check whether the Telegram service is reachable and measure round-trip latency.

**Signature:**

```
telegram-cli ping
```

**Arguments:** None.

**Examples:**

```bash
telegram-cli ping
```

**Output (success):** `✓ Telegram is reachable (42.3 ms)`

**Output (failure):** `✗ Telegram is not reachable` (exit code 2).

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `NETWORK_ERROR` | Cannot connect to Telegram servers. Check your internet connection. |
| `SESSION_INVALID` | Session has expired. |

---

### F8 — Validate session

Validate the current session and display the authenticated user's information.

**Signature:**

```
telegram-cli whoami
```

**Arguments:** None.

**Examples:**

```bash
telegram-cli whoami
```

**Output (success):**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `SESSION_INVALID` | Session string is expired, revoked, or empty. Re-generate it. |
| `AUTH_FAILED` | Account is deactivated or banned. |
| `NETWORK_ERROR` | Cannot connect to Telegram. |

---

### F9 — Show version information

Display version information as a JSON object containing both the library version and the CLI's own version.

**Signature:**

```
telegram-cli version
```

**Arguments:** None.

**Examples:**

```bash
telegram-cli version
```

**Output (success):**

```json
{
  "cli": {
    "version": "1.0.0",
    "build": 1,
    "datetime": "2026-03-17T00:00:00Z"
  },
  "lib": {
    "version": "1.2.0",
    "build": 3,
    "datetime": "2026-03-18T00:00:00Z"
  }
}
```

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `INTERNAL_ERROR` | Version file is missing or malformed. |

---

## Technical Requirements

- T1. Credentials are loaded from the `.env.telegram` file using `python-dotenv`.
- T2. The CLI uses Python's `argparse` module for argument parsing.
- T3. All output uses two formats: human-readable tables/text to stdout (when connected to a TTY), and JSON when `--output` is specified or when stdout is piped (not a TTY).
- T4. When an error occurs, the tool prints a structured error message to stderr and exits with the appropriate exit code.
- T5. The CLI is a single-file script (`telegram-cli.py`) for simplicity. It may be split into modules if complexity grows.
- T6. Unit tests mock internal API calls and verify argument parsing, output formatting, and error handling.
