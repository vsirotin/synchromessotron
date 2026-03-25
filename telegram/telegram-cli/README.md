# telegram-cli

Telegram is one of the most widely used messengers in the world, with over 900 million monthly active users across dozens of languages and countries.

| Language | ISO 639‑1 | Top Countries | Estimated Telegram Users |
|----------|-----------|---------------|--------------------------|
| Russian | ru | Russia, Ukraine, Belarus | ≈ 120–150 million |
| English | en | India, USA, UK | ≈ 110–130 million |
| Persian (Farsi) | fa | Iran, Afghanistan, Tajikistan | ≈ 40–50 million |
| Turkish | tr | Turkey, Cyprus, Germany (diaspora) | ≈ 25–35 million |
| Arabic | ar | Egypt, Iraq, Saudi Arabia | ≈ 20–30 million |
| German | de | Germany, Austria, Switzerland | ≈ 8–12 million |

Telegram can sometimes be unavailable or blocked in certain countries or geographical regions. In these cases, telegram-cli can help — it allows you to work with your Telegram data from the command line, independently of the official apps.

It is especially useful for **offline processing** of Telegram content — for example, backing up conversations, groups, and channels for later analysis with AI tools or other automation.

You do not need to be a programmer to use this tool. Just follow the steps below.

## Overview

| Command | What it does |
|---------|-------------|
| `init` | Set up credentials and session |
| `whoami` | Validate session and show user info |
| `ping` | Check Telegram availability |
| `get-dialogs` | List the user's dialogs |
| `backup` | Full or incremental message backup |
| `send` | Send a message to a dialog |
| `edit` | Edit a previously sent message |
| `delete` | Delete own messages |
| `download-media` | Download a media file from a message |
| `help` | Show help in your language |
| `version` | Show version information |

> **What is a "dialog"?** In Telegram, a "dialog" means any conversation — a private chat with a person, a group, or a channel.

---

## How to Install

### Step 1 — Choose your variant and download

Go to the [Release](https://github.com/vsirotin/synchromessotron/releases/) page, find last stable version, open "Assets" and download the variant for your platform:

| Platform | File | Python needed? |
|----------|------|----------------|
| **Windows** | `telegram-cli.exe` | No |
| **macOS** | `telegram-cli-macos.zip` | No |
| **Any (Python)** | `telegram-cli.pyz` | Yes (≥ 3.11) |

Put the downloaded file in a folder of your choice — for example, a `telegram-cli` folder on your Desktop or in your home directory.

> **Which variant should I choose?**
>
> - **Windows or macOS** — use the platform-specific variant. No extra software needed.
> - **Python variant** — choose this if you want to be absolutely sure about the code running on your computer: `.pyz` is a standard Python zip archive that you can inspect. It also works on Linux and any other OS with Python ≥ 3.11.

**Platform-specific first-run notes:**

- **Windows:** On the first run, SmartScreen may show _"Windows protected your PC"_. Click **More info** → **Run anyway**. This happens once.
- **macOS:** After unzipping, open Terminal in the folder and run once:
  ```
  chmod +x telegram-cli
  xattr -d com.apple.quarantine telegram-cli
  ```
  This removes the download quarantine and makes the file executable.
- **Python variant:** Requires Python 3.11 or newer. Check with `python3 --version`. Install from <https://www.python.org/downloads/> if needed.

### Step 2 — Create a Telegram application

To use telegram-cli you need your own Telegram API credentials. This is a one-time setup.

1. Open <https://my.telegram.org/apps> in a browser and sign in with your phone number.
2. Click **API development tools**.
3. Fill in the **Create new application** form. The App title and Short name can be anything, e.g. `synchromessotron` / `syncbot`. Platform can be left as `Other`.

   ![Create new application dialog](docs/images/telegram1.png)

4. Click **Create application**.
5. You will see your **App api_id** (a number) and **App api_hash** (a long hex string). Keep this page open — you will need both values in the next step.

   ![api_id and api_hash](docs/images/telegram2.png)

### Step 3 — Set up your session

Open a terminal, navigate to the folder where you placed the downloaded file, and run:

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli init` |
| **macOS** | `./telegram-cli init` |
| **Python** | `python3 telegram-cli.pyz init` |

The command will:
1. Ask for your **api_id**, **api_hash**, and **phone number** (from Step 2).
2. Send a login code to your Telegram app — type it when prompted.
3. If you have Two-Step Verification enabled, ask for your **2FA password**.
4. Create a `config.yaml` file with your credentials and session.

> **What is the 2FA password?** It is a password *you chose yourself* when you enabled Two-Step Verification in Telegram. To check or change it: open Telegram → **Settings → Privacy and Security → Two-Step Verification**.

**Expected result:**

```
✓ Session created and saved to config.yaml
  Run 'telegram-cli whoami' to verify.
```

### Step 4 — Verify the setup

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli whoami` |
| **macOS** | `./telegram-cli whoami` |
| **Python** | `python3 telegram-cli.pyz whoami` |

**Expected result:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

Possible errors: `AUTH_FAILED`, `NETWORK_ERROR`, `SESSION_INVALID`. See [Error Handling](#error-handling) below.

Also verify that Telegram is reachable:

```
telegram-cli ping
```

Or `python3 telegram-cli.pyz ping` (Python variant) / `./telegram-cli ping` (macOS).

**Expected result:**

```
✓ Telegram is reachable (42.3 ms)
```

---

## Security — Protecting Your Credentials

The `config.yaml` file contains sensitive data: your Telegram API credentials and session string. **Anyone who has this file can access your Telegram account.**

**Rules:**

1. **Never share `config.yaml` with anyone.** It is like a password.
2. **Never upload it to the internet** — do not put it on GitHub, Google Drive, Dropbox, email, or any public/shared location.
3. **Keep it only in the same folder as the telegram-cli executable** on your own computer.
4. **If you suspect compromise** — if someone may have seen or copied your `config.yaml` — immediately revoke the session in Telegram: go to **Settings → Devices** (or **Settings → Privacy and Security → Active Sessions**) and terminate the suspect session. Then re-run `telegram-cli init` to create a new one.

> The file `config.yaml.example` is a template with no real credentials — it is safe to share or commit.

---

## Output Directory

All data produced by telegram-cli (backups, downloaded media) is stored in a structured **output directory**.

### Location

By default, the output directory is created in the folder where you run `telegram-cli.pyz`:

```
<current folder>/synchromessotron/
```

You can override it with `--outdir`:

```
python3 telegram-cli.pyz backup -1001234567890 --outdir=/path/to/my/data
```

> **Conflict rule:** If both `--outdir` and `output_dir` in `config.yaml` are set and they point to different paths, the command exits with an error. Remove one of them to resolve the conflict.

### Write permissions

Before writing any data, telegram-cli checks that the output directory can be created and written to. If the check fails, the command prints an error and exits.

**macOS / Linux:**

The user running `telegram-cli.pyz` must have write permission to the parent folder. To check:

```
ls -ld /path/to/parent/folder
```

If you see `drwx------` or similar with `w` in the owner permissions, you are fine. To grant write permission:

```
chmod u+w /path/to/parent/folder
```

Most home-directory locations (Desktop, Documents, home folder) already have write permission.

**Windows:**

Right-click the target folder → **Properties** → **Security** tab → check that your user has **Write** permission. If not, click **Edit**, select your user, and check the **Write** box.

Alternatively, in Command Prompt:

```
icacls "C:\path\to\folder"
```

Look for `(W)` or `(F)` next to your username. If write permission is missing:

```
icacls "C:\path\to\folder" /grant %USERNAME%:W
```

### Dialog sub-directories

For each dialog, a sub-directory is created using this naming convention:

```
<first 10 characters of name>_<absolute value of ID>
```

- Spaces in the name are replaced with underscores (`_`).
- If the name is shorter than 10 characters, the full name is used.

| Dialog | Sub-directory |
|--------|---------------|
| `Chat  -718738386  Мемуары кочевого программиста. Байки, были, думы` | `Мемуары_ко_718738386` |
| `User  777000  Telegram` | `Telegram_777000` |

### Time-based hierarchy

Inside each dialog directory, messages are organized by time. The depth of the hierarchy depends on the volume of messages.

The rule is controlled by `split_threshold` in `config.yaml` (default: `50`):

- A **year** directory is always created (e.g. `2025/`, `2026/`).
- If a year contains more than `split_threshold` messages → sub-directories for **months** (`01/` … `12/`).
- If a month exceeds the threshold → sub-directories for **days** (`01/` … `31/`).
- If a day exceeds the threshold → sub-directories for **hours** (`00/` … `23/`).
- If an hour exceeds the threshold → sub-directories for **minutes** (`00/` … `59/`).

This rule is applied recursively. Messages are always stored at the deepest (leaf) level.

### Message files

At each leaf level, two files are created:

| File | Format | Content |
|------|--------|---------|
| `messages.json` | JSON | All known message attributes (full data for machine processing). |
| `messages.md` | Markdown | Message author, timestamp, and text only (human-readable). |

### Content flags

By default, only **messages** are backed up (`messages.json` + `messages.md`). To include additional content, add the corresponding flags:

| Flag | Content saved |
|------|---------------|
| `--media` | Photos and videos (saved to `media/` sub-directories) |
| `--files` | Documents and other file attachments (saved to `files/`) |
| `--music` | Audio tracks (saved to `music/`) |
| `--voice` | Voice messages (saved to `voice/`) |
| `--links` | Link previews and URLs (saved to `links/`) |
| `--gifs` | GIF animations (saved to `gifs/`) |
| `--members` | Dialog participants (saved to `members/` in the dialog root) |

Each content sub-directory follows the same time-based splitting rule as messages.

Example — estimate time before starting a large backup:

```
python3 telegram-cli.pyz backup -1001234567890 --limit=5000 --estimate
```

Example — preview message and file counts without downloading anything:

```
python3 telegram-cli.pyz backup -1001234567890 --count
```

Expected output:

```
Messages: 350 total
  photo: 42
  link/webpage: 8
  video: 5
  file/document: 2
```

Example — incremental backup using `--since` (only messages after a date):

```
python3 telegram-cli.pyz backup -1001234567890 --since=2026-01-01T00:00:00+00:00
```

Example — archive a historical snapshot using `--upto` (messages on or before a date):

```
python3 telegram-cli.pyz backup -1001234567890 --upto=2025-12-31T23:59:59+00:00 --limit=1000
```

Example — backup a specific time window with `--since` and `--upto` (**correct combination** — `since` before `upto`):

```
python3 telegram-cli.pyz backup -1001234567890 \
    --since=2026-01-01T00:00:00+00:00 \
    --upto=2026-01-31T23:59:59+00:00 \
    --limit=1000
```

> **Wrong combination** — `--since` after `--upto` (inverted window, saves 0 messages):
>
> ```
> python3 telegram-cli.pyz backup -1001234567890 \
>     --since=2026-02-01T00:00:00+00:00 \
>     --upto=2026-01-01T00:00:00+00:00
> ```
>
> There are no messages that are both **after** Feb 1 and **on or before** Jan 1. The backup saves 0 messages. Always verify that `--since` is an earlier date than `--upto`.

Example — custom hierarchy depth with `--split_threshold` (split into monthly directories when a bucket exceeds 20 messages):

```
python3 telegram-cli.pyz backup -1001234567890 --split_threshold=20
```

Example — backup messages and photos:

```
python3 telegram-cli.pyz backup -1001234567890 --media
```

Example — backup everything:

```
python3 telegram-cli.pyz backup -1001234567890 --media --files --music --voice --links --gifs --members
```

### Example

Assuming `backup` was run with `--media --members`:

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

In this example:
- The dialog "Мемуары кочевого…" had more than 50 messages in 2025, so it was split into months. In 2026 there were 50 or fewer, so they stay directly in the year directory.
- "Telegram" had few messages overall — no monthly split needed.

---

## Command Reference

### get-dialogs — List dialogs

```
get-dialogs [--limit=N] [--outdir=DIR]
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--limit` | 100 | Maximum number of dialogs to return. Omit to get the default 100. Use `--limit=500` or higher for more dialogs. |
| `--outdir` | — | Save `dialogs.json` to this directory (see [Output Directory](#output-directory)). |

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli get-dialogs --limit=50` |
| **macOS** | `./telegram-cli get-dialogs --limit=50` |
| **Python** | `python3 telegram-cli.pyz get-dialogs --limit=50` |

**Expected result:**

```
  TYPE         ID                 NAME
  ------------ ------------------ ------------------------------------------
  User         123456789          Your Name  @yourhandle
  Channel      -1001234567890     Family Group  @familygroup
  Chat         -987654321         Old Project

3 dialogs found.
```

With `--outdir`, the table is still printed and `dialogs.json` is saved to the output directory root.

Possible errors: `NETWORK_ERROR`, `PERMISSION_DENIED`, `RATE_LIMITED`, `SESSION_INVALID`. See [Error Handling](#error-handling) below.

---

### backup — Backup messages

```
backup <dialog_id> [--since=TIMESTAMP] [--upto=TIMESTAMP] [--limit=N] [--outdir=DIR] [--media] [--files] [--music] [--voice] [--links] [--gifs] [--members] [--estimate] [--count] [--split_threshold=N]
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `<dialog_id>` | — | Dialog ID (required). Use `get-dialogs` to find it. |
| `--since` | — | ISO 8601 timestamp; only messages after it are returned (incremental). |
| `--upto` | — | ISO 8601 timestamp; only messages on or before it are returned. Combine with `--since` for a time window. |
| `--limit` | 100 | Maximum number of messages. |
| `--outdir` | `./synchromessotron` | Root output directory (see [Output Directory](#output-directory)). |
| `--media` | off | Also download photos and videos. |
| `--files` | off | Also download documents and file attachments. |
| `--music` | off | Also download audio tracks. |
| `--voice` | off | Also download voice messages. |
| `--links` | off | Also save link previews and URLs. |
| `--gifs` | off | Also download GIF animations. |
| `--members` | off | Also save dialog participant list. |
| `--estimate` | off | Print a time estimate instead of running the backup. No data is written. |
| `--count` | off | Print counts of messages and files by type, then exit. No data is written. |
| `--split_threshold` | 100 | Messages per time bucket before a deeper subdirectory is created (year → month → day → hour → minute). |

By default, only messages are saved (`messages.json` + `messages.md`). Add content flags to include additional data.

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli backup -1001234567890 --limit=500` |
| **macOS** | `./telegram-cli backup -1001234567890 --limit=500` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --limit=500` |

**Expected result** (messages only):

```
✓ 500 messages saved to synchromessotron/Telegram_777000/2026/
```

**Expected result** (with `--media --files`):

```
✓ 500 messages saved to synchromessotron/Telegram_777000/2026/
✓ 23 media files downloaded
✓ 7 documents downloaded
```

**Expected result** (incremental, `--since="2026-03-01T00:00:00"`):

```
✓ 12 messages saved to synchromessotron/Telegram_777000/2026/03/
```

**Expected result** (with `--estimate`):

```
≈ 12 minutes (5000 messages, estimated 2.4 ms per message)
```

The estimate is approximate — actual time depends on network speed and Telegram rate limits. No data is written when `--estimate` is used.

Possible errors: `ENTITY_NOT_FOUND`, `NETWORK_ERROR`, `PERMISSION_DENIED`, `RATE_LIMITED`. See [Error Handling](#error-handling) below.

---

### send — Send a message

```
send <dialog_id> --text=TEXT
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `<dialog_id>` | Dialog ID (required). |
| `--text` | Message text (required). |

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli send -1001234567890 --text="Hello from CLI!"` |
| **macOS** | `./telegram-cli send -1001234567890 --text="Hello from CLI!"` |
| **Python** | `python3 telegram-cli.pyz send -1001234567890 --text="Hello from CLI!"` |

**Expected result:**

```
✓ Message sent
  ID:    12345
  Date:  2026-03-16 14:30:00
  Text:  Hello from CLI!
```

Possible errors: `ENTITY_NOT_FOUND`, `PERMISSION_DENIED`, `RATE_LIMITED`. See [Error Handling](#error-handling) below.

---

### edit — Edit a message

```
edit <dialog_id> <message_id> --text=TEXT
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `<dialog_id>` | Dialog ID (required). |
| `<message_id>` | Message ID (required). |
| `--text` | New message text (required). |

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli edit -1001234567890 42 --text="Corrected text"` |
| **macOS** | `./telegram-cli edit -1001234567890 42 --text="Corrected text"` |
| **Python** | `python3 telegram-cli.pyz edit -1001234567890 42 --text="Corrected text"` |

**Expected result:**

```
✓ Message edited
  ID:    42
  Date:  2026-03-16 14:30:00
  Text:  Corrected text
```

Possible errors: `ENTITY_NOT_FOUND`, `NOT_MODIFIED`, `PERMISSION_DENIED`. See [Error Handling](#error-handling) below.

---

### delete — Delete messages

```
delete <dialog_id> <message_id> [<message_id> ...]
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `<dialog_id>` | Dialog ID (required). |
| `<message_id>` | One or more message IDs (required). |

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli delete -1001234567890 42 43 44` |
| **macOS** | `./telegram-cli delete -1001234567890 42 43 44` |
| **Python** | `python3 telegram-cli.pyz delete -1001234567890 42 43 44` |

**Expected result:**

```
✓ 3 messages deleted
```

Possible errors: `ENTITY_NOT_FOUND`, `PERMISSION_DENIED`. See [Error Handling](#error-handling) below.

---

### download-media — Download media

```
download-media <dialog_id> <message_id> [--outdir=DIR]
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `<dialog_id>` | — | Dialog ID (required). |
| `<message_id>` | — | Message ID (required). |
| `--outdir` | `./synchromessotron` | Root output directory (see [Output Directory](#output-directory)). |

The file is saved into the appropriate content sub-directory (`media/`, `files/`, `music/`, `voice/`, `gifs/`) inside the dialog's time-based hierarchy.

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli download-media -1001234567890 42` |
| **macOS** | `./telegram-cli download-media -1001234567890 42` |
| **Python** | `python3 telegram-cli.pyz download-media -1001234567890 42` |

**Expected result:**

```
✓ Downloaded: synchromessotron/Telegram_777000/2026/03/media/photo_42.jpg (2.1 MB)
```

Possible errors: `ENTITY_NOT_FOUND`, `NETWORK_ERROR`, `PERMISSION_DENIED`. See [Error Handling](#error-handling) below.

---

### ping — Check availability

```
ping
```

No parameters.

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli ping` |
| **macOS** | `./telegram-cli ping` |
| **Python** | `python3 telegram-cli.pyz ping` |

**Expected result:**

```
✓ Telegram is reachable (42.3 ms)
```

Possible errors: `NETWORK_ERROR`. See [Error Handling](#error-handling) below.

---

### whoami — Validate session

```
whoami
```

No parameters.

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli whoami` |
| **macOS** | `./telegram-cli whoami` |
| **Python** | `python3 telegram-cli.pyz whoami` |

**Expected result:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

Possible errors: `AUTH_FAILED`, `SESSION_INVALID`. See [Error Handling](#error-handling) below.

---

### help — Show help in your language

```
help [LANG] [COMMAND]
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LANG` | `en` | ISO 639-1 language code. Supported: `en`, `ru`, `fa`, `tr`, `ar`, `de`. |
| `COMMAND` | — | If given, show detailed help for that specific command. |

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli help de backup` |
| **macOS** | `./telegram-cli help de backup` |
| **Python** | `python3 telegram-cli.pyz help de backup` |

**Expected result** (general, English):

```
telegram-cli — command-line tool for Telegram

Commands:
  init            Set up credentials and session
  whoami          Validate session and show user info
  ping            Check Telegram availability
  get-dialogs     List your dialogs
  backup          Full or incremental message backup
  send            Send a message
  edit            Edit a previously sent message
  delete          Delete own messages
  download-media  Download media from a message
  help            Show this help
  version         Show version information

Run 'telegram-cli help <lang> <command>' for details.
```

---

### version — Show version information

```
version
```

No parameters.

**Call examples:**

| Variant | Command |
|---------|---------|
| **Windows** | `telegram-cli version` |
| **macOS** | `./telegram-cli version` |
| **Python** | `python3 telegram-cli.pyz version` |

**Expected result - something like:**

```json
{
  "cli": { "version": "1.0.0", "build": 1, "datetime": "2026-03-17T00:00:00Z" },
  "lib": { "version": "1.2.0", "build": 3, "datetime": "2026-03-18T00:00:00Z" }
}
```

---

## Manual Tests

### Test: No network connection

This test verifies that telegram-cli reports a clear error when Telegram is unreachable.

**Setup:** Disconnect from the internet (turn off Wi-Fi, unplug the cable, or enable airplane mode).

**Steps:**

```
python3 telegram-cli.pyz ping
```

**Expected result:**

```
Error [NETWORK_ERROR]: Cannot reach Telegram
```

Exit code: `2`.

```
python3 telegram-cli.pyz get-dialogs
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
| `AUTH_FAILED` | Account deactivated or banned. | Contact Telegram support. |
| `ENTITY_NOT_FOUND` | Dialog or message ID does not exist. | Verify the ID with `get-dialogs`. |
| `INTERNAL_ERROR` | Unexpected failure. | Report the issue with the error details. |
| `NETWORK_ERROR` | Cannot reach Telegram. | Check your internet connection. |
| `NOT_MODIFIED` | Edit text is identical to current text. | Provide different text. |
| `PERMISSION_DENIED` | No permission (e.g. read-only channel, not your message). | Check your rights in the dialog. |
| `RATE_LIMITED` | Too many requests. | Wait the number of seconds shown in `retry_after`, then retry. |
| `SESSION_INVALID` | Session expired or revoked. | Re-run `telegram-cli init`. |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Argument or usage error |
| 2 | Telegram API error (one of the error codes above) |

## Output Formats

- **Terminal (TTY):** human-readable tables and status messages.
- **Output directory (`--outdir`):** structured directory tree with `messages.json` (full data) and `messages.md` (human-readable) at each level. See [Output Directory](#output-directory).
- **Piped stdout (non-TTY):** JSON, suitable for chaining with `jq` or other tools.

---

## For Developers

If you are a developer contributing to telegram-cli — building executables, running tests, or working on the codebase — see [DEVELOPMENT.md](DEVELOPMENT.md).

---

## Release notes:

See [release-notes.md](release-notes.md).
