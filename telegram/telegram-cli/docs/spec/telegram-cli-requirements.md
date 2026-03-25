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

Retrieve messages from a dialog for full or incremental backup. Saves messages to a structured directory hierarchy. By default, only messages are backed up; use content flags to include media, documents, and other data.

**Signature:**

```
telegram-cli backup <dialog_id> [--since=TIMESTAMP] [--limit=N] [--outdir=DIR] [--media] [--files] [--music] [--voice] [--links] [--gifs] [--members] [--estimate]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `dialog_id` | yes | int | Numeric ID of the dialog (use `get-dialogs` to find it). |
| `--since` | no | ISO 8601 string | If set, only messages strictly after this timestamp are returned (incremental). If omitted, the most recent messages are returned (full). |
| `--limit` | no | int | Maximum number of messages to return. Default: `100`. |
| `--outdir` | no | directory path | Root output directory where the backup directory structure is created. Default: `./synchromessotron` (created in current working directory). |
| `--media` | no | flag | Also download photos and videos. |
| `--files` | no | flag | Also download documents and file attachments. |
| `--music` | no | flag | Also download audio tracks. |
| `--voice` | no | flag | Also download voice messages. |
| `--links` | no | flag | Also save link previews and URLs. |
| `--gifs` | no | flag | Also download GIF animations. |
| `--members` | no | flag | Also save dialog participant list. |
| `--estimate` | no | flag | Instead of running the backup, print an approximate time estimate and exit. Does not write any files; independent of `--outdir`. |

**Examples:**

```bash
# Full backup — last 500 messages, to default directory
telegram-cli backup -1001234567890 --limit=500

# Incremental backup — only new messages since a date
telegram-cli backup -1001234567890 --since="2026-03-01T00:00:00"

# Backup messages and media to custom directory
telegram-cli backup -1001234567890 --limit=500 --outdir=/data/backups --media

# Backup everything (messages, media, documents, voice, etc.)
telegram-cli backup -1001234567890 --media --files --music --voice --links --gifs --members

# Estimate how long a backup would take (no files written)
telegram-cli backup -1001234567890 --limit=5000 --estimate
```

**Output:** Structured directory tree with `messages.json` and `messages.md` at leaf levels. Additional content types (media, files, etc.) saved in subdirectories.

**Estimation mechanism (`--estimate`):**

The `--estimate` flag calculates how long a backup would take **without writing any files**. The result is independent of `--outdir` and other parameters that affect file operations.

When `--estimate` is passed:

1. The CLI calls `count_messages()` (telegram-lib) to obtain the total number of messages matching the query (dialog, `--since`, `--limit`) **without downloading message content**. This is a single lightweight API call using Telethon's `client.get_messages(entity, limit=0)` → `.total`.
2. The number of API pages is calculated: `pages = ceil(min(total, limit) / page_size)`.
3. The estimated duration accounts for Telegram rate-limit pauses. Since Telegram's rate limits are not publicly documented and vary by account, this is a conservative heuristic.
4. The result is printed as a human-readable estimate and the CLI exits without performing the actual backup or creating any files.

**Example `--estimate` output:**

```
≈ 12 minutes (5000 messages, 50 pages, estimated 14.4 s/page incl. rate-limit pauses)
```

The estimate is approximate — actual duration depends on network speed, server load, and per-account rate limits. No data is written when `--estimate` is used.

**Output directory structure (when backup runs without `--estimate`):**

Data is organized hierarchically under `--outdir` (default: `./synchromessotron`):

```
<outdir>/
└── <dialog_name>_<dialog_id>/
    ├── messages.json                 (all messages in JSON format)
    ├── messages.md                   (human-readable: author, timestamp, text)
    ├── 2026/                         (year directory)
    │   ├── 01/                       (month, if > split_threshold messages)
    │   │   ├── 01/                   (day, if > split_threshold messages)
    │   │   │   ├── messages.json
    │   │   │   └── messages.md
    │   │   └── 02/
    │   │       ├── messages.json
    │   │       └── messages.md
    │   └── 02/
    │       ├── messages.json
    │       └── messages.md
    ├── media/                        (if --media flag used)
    ├── files/                        (if --files flag used)
    ├── music/                        (if --music flag used)
    ├── voice/                        (if --voice flag used)
    ├── links/                        (if --links flag used)
    ├── gifs/                         (if --gifs flag used)
    └── members/                      (if --members flag used)
```

**Content in media subdirectories:**

Each media subdirectory (`media/`, `files/`, `music/`, `voice/`, `links/`, `gifs/`) contains:
- **messages.json:** List of messages with media, with each entry containing message metadata and a `file_path` field pointing to the downloaded media file (named by message ID, e.g., `43853.jpg`, `44280.mp4`).
- **messages.md:** Human-readable markdown representation of media messages (author, timestamp, text, [MEDIA] indicator).
- **Downloaded files:** Actual media files organized by message ID.

**Members subdirectory:**

The `members/` subdirectory (when `--members` flag used) contains:
- **members.json:** Single file with list of dialog participants. Each entry contains basic member info (id, name, username, and optional photo_file_path).

**Chronological ordering:**

All entries in `*.json` and `*.md` files are stored in chronological order (oldest first).

Splitting decisions (controlled by `split_threshold` in `config.yaml`, default: 50):
- **Year** directory always created.
- If year > threshold → create **month** subdirectories.
- If month > threshold → create **day** subdirectories.
- If day > threshold → create **hour** subdirectories.
- If hour > threshold → create **minute** subdirectories.
- Messages stored only at the leaf level.

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
telegram-cli get-dialogs [--limit=N] [--outdir=DIR]
```

**Arguments:**

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `--limit` | no | int | Maximum number of dialogs to return. Default: all (no limit). |
| `--outdir` | no | directory path | Save `dialogs.json` to this directory (if omitted, only print to stdout). |

**Examples:**

```bash
# Print all dialogs as a table to stdout
telegram-cli get-dialogs

# Save first 50 dialogs to a JSON file in specified directory
telegram-cli get-dialogs --limit=50 --outdir=/data/backups
```

**Output (stdout):** Human-readable table with columns: TYPE, ID, NAME.

**Output (file):** JSON array of dialog objects (id, name, type, username, unread_count), written to `dialogs.json` in the specified `--outdir`.

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

**Decision Tree Flow:**

The initialization process follows a 5-step decision tree optimized to minimize user input and provide graceful recovery options. The flow diagram below illustrates all decision points and paths:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Display Interruption Notice                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ "ℹ  To interrupt at any time, press Ctrl+C"                                │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────────────┐
│ STEP 2: Check for Existing config.yaml                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Does config.yaml exist in the current directory?                            │
└──────────────────────┬───────────────────────────┬──────────────────────────┘
                       │ YES                       │ NO
                       │                           │
          ┌────────────▼──────────────┐   ┌───────▼──────────────────┐
          │ INFORM: Config found      │   │ Continue (go to STEP 4a) │
          │ Exit(0) gracefully        │   │                          │
          │ Return session immediately│   └───────┬──────────────────┘
          └──────────────────────────┘           │
                                                  │
                ┌─────────────────────────────────▼────────────────────────┐
                │ STEP 4a: Ask Config Location                             │
                ├──────────────────────────────────────────────────────────┤
                │ "Do you have config.yaml in another location? [y/N]: "  │
                └──┬──────────────────────────────────────────┬────────────┘
         YES    │                                             │    NO / Ctrl+C
       ┌────────▼──────────┐                        ┌────────▼──────────┐
       │ GUIDE TO COPY      │                        │ Continue (STEP 4b)│
       │ Show copy cmd      │                        │                   │
       │ Exit(0) on success │                        └────────┬──────────┘
       └───────────────────┘                                  │
                                                               │
                ┌──────────────────────────────────────────────▼────────────┐
                │ STEP 4b: Ask About Credentials                            │
                ├───────────────────────────────────────────────────────────┤
                │ "Do you have api_id, api_hash, phone noted? [y/N]: "    │
                └──┬────────────────────────────────────────┬──────────────┘
         YES    │                                           │    NO / Ctrl+C
       ┌────────▼──────────────────┐          ┌────────────▼──────────┐
       │ STEP 4c: Offer Example     │          │ STEP 5: Prompt All    │
       │ "Create example config? [y/N]: "     │ Credentials           │
       └──┬───────────────────────┬───┘       │ api_id, api_hash,     │
  YES  │               │ NO / Ctrl+C   │     │ phone (with validation)
  ┌────▼──────┐   ┌────▼────────┐    │      │                        │
  │ CREATE     │   │ CONTINUE    │    │      │ (Falls through to STEP 6)
  │ EXAMPLE    │   │ TO STEP 5   │    │      └────────┬──────────────┘
  │ Exit(0)    │   └────┬────────┘    │               │
  └───────────┘        │              │               │
                        │              │               │
              ┌─────────▴──────────────┴───────────────▴───────────────┐
              │ STEP 6: Telegram Authentication                        │
              ├────────────────────────────────────────────────────────┤
              │ - Connect to Telegram                                  │
              │ - If login code needed: Prompt for code (Ctrl+C safe) │
              │ - If 2FA enabled: Prompt for password (Ctrl+C safe)   │
              │ - Save session string to config.yaml                  │
              │ - Exit(0) on success                                  │
              └────────────────────────────────────────────────────────┘
```

**Detailed Behavior:**

1. **STEP 1 — Interruption Guidance:** Display `"ℹ  To interrupt at any time, press Ctrl+C"` to inform users they can cancel safely at any point.

2. **STEP 2 — Existing Config Detection:** Check if `config.yaml` exists in the current directory.
   - **If found:** Display informational message and exit with code 0 (session already initialized; no action needed).
   - **If not found:** Proceed to STEP 4a.

3. **STEP 4a — Config Location Query:** Ask: `"Do you have config.yaml in another location? [y/N]: "`
   - **If Yes:** Guide the user to copy the existing config, display the command, and exit with code 0.
   - **If No or Ctrl+C:** Proceed to STEP 4b.

4. **STEP 4b — Credentials Notes Query:** Ask: `"Do you have api_id, api_hash, and phone noted somewhere? [y/N]: "`
   - **If Yes:** Offer to create an example file (proceed to STEP 4c).
   - **If No or Ctrl+C:** Skip to STEP 5 (direct credential prompt).

5. **STEP 4c — Example File Offer:** Ask: `"Should I create an example config.yaml.example for you? [y/N]: "`
   - **If Yes:** Create a template file with placeholders and exit with code 0 (user will fill it manually later).
   - **If No or Ctrl+C:** Proceed to STEP 5.

6. **STEP 5 — Prompt for Credentials:** Ask for `api_id`, `api_hash`, and `phone` with:
   - Input validation (e.g. `api_id` must be numeric).
   - Graceful Ctrl+C handling (show cancellation message, exit with code 1).
   - Helpful error messages for invalid input.

7. **STEP 6 — Telegram Authentication:** 
   - Connect to Telegram and initiate authentication.
   - If a login code is sent: Prompt: `"Enter the login code sent to your Telegram app: "` (Ctrl+C safe).
   - If Two-Step Verification (2FA) is enabled: Prompt: `"Enter your 2FA password: "` (Ctrl+C safe).
   - Save the generated session string to `config.yaml` (field `session` under the `telegram` section).
   - Exit with code 0 on success.

**Graceful Error Handling:**

- **Ctrl+C (KeyboardInterrupt) at any prompt:** Display `"✗ Setup cancelled by user. Run 'telegram-cli init' again when ready."` and exit with code 1. No Python tracebacks.
- **Invalid input (validation failure):** Display a friendly message explaining the error and re-prompt the user.
- **File write failure:** Display `"✗ Cannot write config.yaml: [reason]"` and exit with code 1.
- **Telegram API error:** Display error details with code 2.

**Examples:**

```bash
# Typical flow for new user (no config)
telegram-cli init
ℹ  To interrupt at any time, press Ctrl+C
Do you have config.yaml in another location? [y/N]: n
Do you have api_id, api_hash, and phone noted somewhere? [y/N]: n
Enter api_id: 1234567
Enter api_hash: abc123def456...
Enter phone (with country code, e.g. +1234567890): +1234567890
[Telegram sends code]
Enter the login code sent to your Telegram app: 12345
✓ Session created and saved to config.yaml
  Run 'telegram-cli whoami' to verify.
```

```bash
# User has config elsewhere
telegram-cli init
ℹ  To interrupt at any time, press Ctrl+C
Do you have config.yaml in another location? [y/N]: y
ℹ  To use your existing config here, run:
  cp /path/to/existing/config.yaml ./config.yaml
Then run 'telegram-cli init' again to validate the session.
```

```bash
# User has credentials noted, wants example file
telegram-cli init
ℹ  To interrupt at any time, press Ctrl+C
Do you have config.yaml in another location? [y/N]: n
Do you have api_id, api_hash, and phone noted somewhere? [y/N]: y
Should I create an example config.yaml.example for you? [y/N]: y
✓ Example config created as config.yaml.example
  Edit it with your credentials (api_id, api_hash, phone) and rename to config.yaml.
Then run 'telegram-cli init' again.
```

```bash
# User interrupts with Ctrl+C
telegram-cli init
ℹ  To interrupt at any time, press Ctrl+C
Do you have config.yaml in another location? [y/N]: ^C
✗ Setup cancelled by user. Run 'telegram-cli init' again when ready.
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Session created and saved successfully, or informational exit (config found, user guided elsewhere). |
| 1 | User cancelled with Ctrl+C, invalid input, file write failure, or other local error. |
| 2 | Telegram API error (authentication failed, network error, account banned). |

**Possible errors:**

| Error code | When it happens | User-Facing Message |
|------------|-----------------|-----|
| `RATE_LIMITED` | Too many auth attempts. | "Too many login attempts — wait a moment and try again." |
| `AUTH_FAILED` | Account is deactivated or banned. | "Account deactivated or banned. Contact Telegram support." |
| `SESSION_INVALID` | Session generation failed. | "Session generation failed. Try again or contact support." |
| `NETWORK_ERROR` | Cannot connect to Telegram. | "Cannot connect to Telegram. Check your internet and try again." |
| `INTERNAL_ERROR` | Cannot write config.yaml (permissions, disk full, etc.). | "Cannot write config.yaml: [specific reason]." |

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
- T10. The `--estimate` flag connects to Telegram only when necessary (a single API call to count messages). It must not modify any data. The estimation uses `count_messages()` from telegram-lib — a lightweight call that returns the total message count without downloading content.
- T11. Before writing to the output directory, the CLI checks that the directory can be created and is writable. If the check fails, the command exits with `PERMISSION_DENIED` (exit code 2).
- T12. Dialog sub-directory names follow the pattern `<name_prefix>_<abs_id>`: first 10 characters of the dialog name (spaces → `_`, shorter names used in full), underscore, absolute value of the dialog ID.
- T13. Time-based directory splitting uses the `split_threshold` setting from `config.yaml` (default: `50`). The hierarchy levels are: year → month → day → hour → minute. Splitting is applied recursively; messages are stored only at the leaf level in `messages.json` (full data) and `messages.md` (author, timestamp, text).
- T14. If both `--outdir` and `config.yaml` `output_dir` are set and point to different paths, the CLI exits with an error (exit code 1). If they match, the value is accepted.
- T15. By default, only messages are backed up. Additional content types (media, files, music, voice, links, GIFs, members) require explicit flags (`--media`, `--files`, etc.). This may require extending telegram-lib to support content-type filtering during backup.
- T16. A GitHub Actions workflow (`release.yml`) builds the Windows `.exe` and macOS binary using PyInstaller on the respective runner OS (`windows-latest`, `macos-latest`). The `.pyz` is built with shiv on `ubuntu-latest`. All three artifacts are uploaded as release assets when a version tag (e.g. `v0.5.0`) is pushed.
- T17. The Windows `.exe` is not code-signed. On first run, Windows SmartScreen may warn the user. The README documents how to proceed ("More info" → "Run anyway").
- T18. The macOS binary is not notarized. On first run, macOS Gatekeeper may block execution. The README documents the one-time setup: `chmod +x telegram-cli` and `xattr -d com.apple.quarantine telegram-cli`.
- T19. The `backup` command implements a cooldown-aware pagination loop. It fetches messages in pages (using telegram-lib `read_messages`). When a page request returns `RATE_LIMITED` with `retry_after`, the CLI waits the specified number of seconds and retries automatically. Progress is reported to stdout (e.g. `Page 3/50 — fetched 300 messages`). This loop is required both for actual backup and for accurate `--estimate` calibration.
- T20. The `--estimate` implementation depends on a `count_messages()` function in telegram-lib (not yet implemented). This function must be added to telegram-lib before `--estimate` can be coded. See telegram-lib requirements for the corresponding update.
- T21. All file writes in data-producing commands (`backup`, `download-media`, etc.) use **atomic writes**: data is written to a temporary file in the same directory, then renamed to the target path. On POSIX systems `os.rename()` is atomic; on Windows `os.replace()` is used. This guarantees that if the process is interrupted (user abort, crash, power loss), the target file is either the previous complete version or the new complete version — never a half-written file.
- T22. **Resumable backup.** Before downloading, the `backup` command scans the output directory for already-downloaded content (messages, media files, etc.). It compares local state against the requested scope (dialog, `--since`, `--limit`) and downloads **only the difference** — items that are missing or newer than what is stored locally. This makes backup idempotent: re-running the same command after an interruption (user abort, crash, network failure) skips already-completed work and continues from where it left off. The scan uses message IDs and timestamps from existing `messages.json` files in the output directory tree (T13). No `--since` flag is required for resumption — the CLI determines the resume point automatically.
- T23. **Structured progress output.** During `backup` (and other long-running commands), the CLI reports progress to stdout in five stages:
  1. **Start** — command name, dialog ID, requested scope (limit, since), output directory.
  2. **Local scan result** — number of already-downloaded elements found, latest local timestamp, number of new items to fetch. Example: `Local: 3200 messages (latest: 2026-03-15T14:22:00Z). To download: 1800 new messages.`
  3. **Time estimate** — estimated duration for the remaining download (same formula as `--estimate`, but applied only to the diff). Example: `Estimated time: ≈ 4 minutes (1800 messages, 18 pages).`
  4. **Progress bar** — a continuously updated progress indicator showing: current page / total pages, messages fetched so far / total, elapsed time, and estimated time remaining. When stdout is a TTY, the line is overwritten in place (carriage return). When piped, each update is a new line. Example: `[████████░░░░░░░░] 44% | 800/1800 messages | 1m 48s elapsed | ≈ 2m 12s left`
  5. **Final report** — total messages downloaded, total time, output directory path, any warnings (e.g. rate-limit pauses encountered). Example: `Done. 1800 messages saved to ./synchromessotron/MyChat_1234567890/. Total time: 3m 54s (2 rate-limit pauses, 45s total wait).`

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
