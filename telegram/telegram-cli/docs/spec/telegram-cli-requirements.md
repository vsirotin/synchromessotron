# Requirements for Sub-Project telegram-cli

This document describes the functional and technical requirements for telegram-cli — a command-line interface for performing Telegram operations (backup, messaging, media download, connectivity checks) from the terminal.

## Structural Requirements

Telegram-cli is a standalone command-line application distributed in three variants:

| Variant | File | Requires | Built with |
|---------|------|----------|------------|
| **Windows** | `telegram-cli.exe` | Nothing | PyInstaller (GitHub Actions, `windows-latest`) |
| **macOS** | `telegram-cli-macos.zip` (contains `telegram-cli`) | Nothing | PyInstaller (GitHub Actions, `macos-latest`) |
| **Python (cross-platform)** | `telegram-cli.pyz` | Python ≥ 3.11 | shiv |

The Python variant (`telegram-cli.pyz`) is packaged with [shiv](https://github.com/linkedin/shiv) so that all Python dependencies (including telegram-lib) are bundled inside. Users who choose this variant need a compatible Python installation — no `pip install`, no virtual environments. The Python variant is also intended for users who want full code transparency: `.pyz` is a standard zip archive that can be inspected.

The Windows and macOS variants are self-contained executables built with [PyInstaller](https://pyinstaller.org). They do not require Python to be installed. These are built automatically by a GitHub Actions workflow (`release.yml`) and uploaded as release assets.

All three variants are distributed via [GitHub Releases](../../releases). Each release contains all three files as downloadable assets. There is no need for a separate directory of old versions — GitHub Releases provides version history.

The tool reads credentials from a `config.yaml` file located next to the executable. The user interacts only with CLI commands and does not need to know about internal implementation details.

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

### F10 — Initialize configuration (session setup)

Interactively create or update the `config.yaml` file by generating a Telegram session string.

**Signature:**

```
telegram-cli init
```

**Arguments:** None.

**Behaviour:**

1. If `config.yaml` does not exist, the command asks the user for `api_id`, `api_hash`, and `phone`, then writes a new `config.yaml`.
2. If `config.yaml` already exists, the command reads `api_id`, `api_hash`, and `phone` from it.
3. Connects to Telegram and sends a login code to the user's Telegram app.
4. Prompts the user to enter the code.
5. If Two-Step Verification (2FA) is enabled, prompts for the 2FA password.
6. Writes the generated session string into `config.yaml` (field `telegram.session`).

**Examples:**

```bash
python3 telegram-cli.pyz init
```

**Output (success):**

```
✓ Session created and saved to config.yaml
  Run 'python3 telegram-cli.pyz whoami' to verify.
```

**Possible errors:**

| Error code | When it happens |
|------------|-----------------|
| `AUTH_FAILED` | Account is deactivated or banned. |
| `NETWORK_ERROR` | Cannot connect to Telegram. |
| `INTERNAL_ERROR` | Cannot write config.yaml (permissions, disk full, etc.). |

---

### F11 — Multilingual help

Display help text in one of the supported languages.

**Signature:**

```
telegram-cli help [LANG] [COMMAND]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `LANG` | no | ISO 639-1 code | Language for the help text. Supported: `en` (default), `ru`, `fa`, `tr`, `ar`, `de`. |
| `COMMAND` | no | string | If given, show detailed help for that specific command only. |

**Supported languages:**

| Language | Code |
|----------|------|
| English | `en` |
| Russian | `ru` |
| Persian (Farsi) | `fa` |
| Turkish | `tr` |
| Arabic | `ar` |
| German | `de` |

**Examples:**

```bash
# General help in English (default)
telegram-cli help

# General help in German
telegram-cli help de

# Detailed help for the backup command in Russian
telegram-cli help ru backup
```

**Output:** Human-readable help text in the requested language. Contains a list of all commands with short descriptions (general mode) or detailed usage for a single command (command mode).

**Possible errors:**

| Error code | When it happens |
|------------|------------------|
| `INTERNAL_ERROR` | Requested language file is missing or corrupted. |

> If an unsupported language code is given, the command falls back to English and prints a notice.

---

### F12 — Estimate duration of long-running commands

Provide an approximate time estimate for potentially long-running commands before the user commits to running them.

**Signature:**

```
telegram-cli howlong <command> [ARGS...]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `command` | yes | string | The command to estimate. Supported: `backup`, `download-media`, `get-dialogs`. |
| `ARGS` | no | mixed | The same arguments that would be passed to the actual command (e.g. `<dialog_id> --limit=5000`). Used to refine the estimate. |

**Examples:**

```bash
telegram-cli howlong backup -1001234567890 --limit=5000
telegram-cli howlong download-media -1001234567890 42
telegram-cli howlong get-dialogs
```

**Output (success):** A human-readable estimate, e.g.:

```
≈ 12 minutes (5000 messages, estimated 2.4 ms per message)
```

**Estimation method:** The command may connect to Telegram briefly to determine the data volume (e.g. total number of messages in a dialog) and then calculate the estimate based on known per-item processing time and Telegram rate limits.

**Possible errors:**

| Error code | When it happens |
|------------|------------------|
| `INTERNAL_ERROR` | The specified command does not support time estimation (e.g. `send`, `edit`). |
| `ENTITY_NOT_FOUND` | The dialog ID does not exist. |
| `NETWORK_ERROR` | Cannot connect to determine data volume. |
| `SESSION_INVALID` | Session has expired. |

---

## Technical Requirements

- T1. Credentials (api_id, api_hash, phone, session) are loaded from a `config.yaml` file located in the same directory as the executable. The file uses YAML format with a flat `telegram` section.
- T2. The CLI uses Python's `argparse` module for argument parsing.
- T3. All output uses two formats: human-readable tables/text to stdout (when connected to a TTY), and structured files in the output directory when `--outdir` is specified. When stdout is piped (not a TTY), output is JSON.
- T4. When an error occurs, the tool prints a structured error message to stderr and exits with the appropriate exit code.
- T5. The Python variant of the CLI is packaged as a single `.pyz` file using [shiv](https://github.com/linkedin/shiv). All Python dependencies (telegram-lib, Telethon, python-dotenv, PyYAML, etc.) are bundled inside. The user invokes it via `python3 telegram-cli.pyz <command>`.
- T6. Unit tests mock internal API calls and verify argument parsing, output formatting, and error handling.
- T7. The CLI includes a built-in `init` command that interactively generates a session string and writes it to `config.yaml`, so users do not need separate tooling.
- T8. The CLI requires Python ≥ 3.11 for the `.pyz` variant. The Windows (`.exe`) and macOS variants do not require Python. The `init` command and README provide platform-specific guidance.
- T9. Help texts are bundled for six languages: English (`en`), Russian (`ru`), Persian (`fa`), Turkish (`tr`), Arabic (`ar`), German (`de`). Texts are stored as resource files inside the package and shipped within all distribution variants. English is the default fallback.
- T10. The `howlong` command connects to Telegram only when necessary (e.g. to count messages in a dialog). It must not modify any data.
- T11. Before writing to the output directory, the CLI checks that the directory can be created and is writable. If the check fails, the command exits with `PERMISSION_DENIED` (exit code 2).
- T12. Dialog sub-directory names follow the pattern `<name_prefix>_<abs_id>`: first 10 characters of the dialog name (spaces → `_`, shorter names used in full), underscore, absolute value of the dialog ID.
- T13. Time-based directory splitting uses the `split_threshold` setting from `config.yaml` (default: `50`). The hierarchy levels are: year → month → day → hour → minute. Splitting is applied recursively; messages are stored only at the leaf level in `messages.json` (full data) and `messages.md` (author, timestamp, text).
- T14. If both `--outdir` and `config.yaml` `output_dir` are set and point to different paths, the CLI exits with an error (exit code 1). If they match, the value is accepted.
- T15. By default, only messages are backed up. Additional content types (media, files, music, voice, links, GIFs, members) require explicit flags (`--media`, `--files`, etc.). This may require extending telegram-lib to support content-type filtering during backup.
- T16. A GitHub Actions workflow (`release.yml`) builds the Windows `.exe` and macOS binary using PyInstaller on the respective runner OS (`windows-latest`, `macos-latest`). The `.pyz` is built with shiv on `ubuntu-latest`. All three artifacts are uploaded as release assets when a version tag (e.g. `v0.5.0`) is pushed.
- T17. The Windows `.exe` is not code-signed. On first run, Windows SmartScreen may warn the user. The README documents how to proceed ("More info" → "Run anyway").
- T18. The macOS binary is not notarized. On first run, macOS Gatekeeper may block execution. The README documents the one-time setup: `chmod +x telegram-cli` and `xattr -d com.apple.quarantine telegram-cli`.

## Configuration File

The `config.yaml` file has the following structure:

```yaml
telegram:
  api_id: 12345
  api_hash: "your_api_hash_here"
  phone: "+1234567890"
  session: "your_session_string_here"
  output_dir: "./synchromessotron"
  split_threshold: 50
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `api_id` | yes | — | Telegram application ID. |
| `api_hash` | yes | — | Telegram application hash. |
| `phone` | yes | — | Phone number in international format. |
| `session` | yes | — | Session string (generated by `init`). |
| `output_dir` | no | `./synchromessotron` | Root output directory for data-producing commands. |
| `split_threshold` | no | `50` | Maximum messages per time-period directory before splitting into sub-directories. |

A template file `config.yaml.example` is distributed alongside the executable.

## Output Directory Structure

All data-producing commands (`backup`, `download-media`, etc.) write output into a structured **output directory**.

### Location

Default: `<working directory>/synchromessotron/`.

Override per invocation with `--outdir=DIR`, or permanently via `output_dir` in `config.yaml`:

```yaml
telegram:
  output_dir: "/path/to/my/data"
```

Precedence: `--outdir` flag > `config.yaml` `output_dir` > default.

> **Conflict rule:** If both `--outdir` and `config.yaml` `output_dir` are present and point to different paths, the command exits with an error (exit code 1). This prevents accidental writes to an unexpected location.

### Write-permission check

Before writing, the CLI verifies that the output directory can be created and is writable. If the check fails, the command exits with `PERMISSION_DENIED` (exit code 2).

### Dialog sub-directory naming

Each dialog produces a sub-directory named:

```
<name_prefix>_<abs_id>
```

where:

| Component | Rule |
|-----------|------|
| `name_prefix` | First 10 characters of the dialog name. Spaces are replaced with `_`. If the name is shorter than 10 characters, the full name is used. |
| `abs_id` | Absolute value of the dialog ID (no minus sign). |

**Examples:**

| Dialog (type, ID, name) | Sub-directory |
|-------------------------|---------------|
| `Chat  -718738386  Мемуары кочевого программиста. Байки, были, думы` | `Мемуары_ко_718738386` |
| `User  777000  Telegram` | `Telegram_777000` |

### Time-based hierarchy

Inside each dialog directory, data is split into time-period sub-directories. The depth is determined by the number of messages in each period and the `split_threshold` setting in `config.yaml` (default: `50`).

The rule is applied **recursively** from coarse to fine:

1. A **year** directory is always created (`2025/`, `2026/`, …).
2. If a year contains more than `split_threshold` messages → **month** sub-directories (`01/` … `12/`).
3. If a month exceeds the threshold → **day** sub-directories (`01/` … `31/`).
4. If a day exceeds the threshold → **hour** sub-directories (`00/` … `23/`).
5. If an hour exceeds the threshold → **minute** sub-directories (`00/` … `59/`).

Messages are stored only at the deepest (leaf) level.

### Message files

At each leaf level, two files are written:

| File | Format | Content |
|------|--------|---------|
| `messages.json` | JSON | All known message attributes (full data). |
| `messages.md` | Markdown | Author, timestamp, and message text only. |

### Media sub-directories

When messages at a given level contain attachments, the following sub-directories are created alongside the message files:

| Sub-directory | Content |
|---------------|---------|
| `media/` | Photos and videos. |
| `files/` | Documents and other file attachments. |
| `music/` | Audio tracks. |
| `voice/` | Voice messages. |
| `links/` | Link previews and URLs. |
| `gifs/` | GIF animations. |

Content sub-directories are created **only** when the corresponding content flag is passed to `backup` (e.g. `--media`, `--files`). They follow the same time-based splitting rule.

### Members

A `members/` sub-directory is created in the dialog's root directory when `--members` is passed to `backup`.

### Example tree

```
synchromessotron/
├── Мемуары_ко_718738386/
│   ├── members/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── messages.json
│   │   │   ├── messages.md
│   │   │   └── media/
│   │   └── 02/
│   │       ├── messages.json
│   │       └── messages.md
│   └── 2026/
│       ├── messages.json
│       └── messages.md
└── Telegram_777000/
    └── 2026/
        ├── messages.json
        └── messages.md
```
