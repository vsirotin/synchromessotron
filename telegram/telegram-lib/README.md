# telegram-lib

Python library providing Telegram integration functions for reading and writing messages via the Telegram user account API.

## Overview

This library implements the core Telegram functionality used by other subprojects (`telegram-cli`, `telegram-web`, etc.). It authenticates as a **user account** (not a bot) using the [Telethon](https://github.com/LorenzoTheWorker/Telethon) library and provides:

- **Reading** messages from channels and groups where the user is a member, and from conversations with other users.
- **Writing** messages to channels and groups where the user is a member, and to conversations with other users.

---

## Getting Started

### Step 1 — Install the project from Git

```bash
git clone https://github.com/vsirotin/synchromessotron.git
cd synchromessotron/telegram/telegram-lib
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Step 2 — Run unit tests

Unit tests verify the core logic — the sync algorithm, error handling, and the Telegram read/write logic — using mocked API calls. **No real credentials, no internet connection needed.**

```bash
pytest tests/unit/
```

You should see all tests pass. If any fail, check that dependencies installed correctly and that you are running Python 3.11 or later.

---

### Step 3 — Create a Telegram application

1. Open <https://my.telegram.org/apps> in a browser and sign in with your phone number.
2. Click **API development tools**.
3. Fill in the **Create new application** form. The App title and Short name can be anything, e.g. `synchromessotron` / `syncbot`. Platform can be left as `Other`.

   ![Create new application dialog](../../docs/images/telegram1.png)

4. Click **Create application**.
5. You will see your **App api_id** (a number) and **App api_hash** (a long hex string). Note both values — you will need them in the next step.

   ![api_id and api_hash](../../docs/images/telegram2.png)

### Step 4 — Create the secure environment file

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

Replace `12345` with your real api_id, `your_api_hash_here` with your real api_hash, and `+1234567890` with your Telegram phone number (with country code). Leave `TG_SESSION` empty for now — it will be filled in the next step.

> **Security:** The `.env.telegram` file is matched by the `.env.*` pattern in `.gitignore` and will never be committed. Never share this file.

### Step 5 — Generate a session string

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

### Step 6 — List your dialogs

Run the dialog listing tool to confirm your credentials work and see all your Telegram dialogs with their numeric IDs:

```bash
python3 tools/tg_check.py list
```

Example output:

```
✓ Logged in as: Your Name (@yourhandle, id=123456789)

  TYPE         ID                 NAME
  ------------ ------------------ ---------------------------------------------
  User         123456789          Your Name  @yourhandle
  Channel      -1001234567890     Family Group  @familygroup
  Chat         -987654321         Old Project
```

| Type      | What it is                                          |
|-----------|-----------------------------------------------------|
| `Channel` | A Telegram channel or supergroup (large/public)     |
| `Chat`    | A regular group chat                                |
| `User`    | A direct message conversation with a person         |

Note the **ID** of the dialog you want to test — including the minus sign for groups and channels.

### Step 7 — Verify read and write access

```bash
python3 tools/tg_check.py test <dialog_id>
```

Replace `<dialog_id>` with the actual ID from Step 6, for example:

```bash
python3 tools/tg_check.py test -1001234567890
```

The tool will:
1. Print the last 3 messages from the dialog so you can confirm it is the right one.
2. Ask if you want to send a test message.

> **⚠️ WARNING:** If you type a message and press Enter, it will be sent as a **real message** visible to all members of the dialog. Press Enter without typing to skip.

---

## Architecture

```
telegram-lib/
├── .env.telegram.example    # Credentials template (copy to .env.telegram)
├── pyproject.toml           # Package configuration
├── src/
│   ├── core/
│   │   ├── interfaces.py    # IReader, IWriter, ISyncStateStorage, Message, Attachment
│   │   ├── orchestrator.py  # Sync algorithm (read → write → update state)
│   │   └── retry.py         # Async retry with exponential backoff
│   ├── config/
│   │   ├── schema.py        # Pydantic config models
│   │   └── loader.py        # YAML config loader
│   ├── messengers/
│   │   └── telegram/
│   │       ├── reader.py    # TelegramReader — reads messages via Telethon
│   │       └── writer.py    # TelegramWriter — writes/forwards messages
│   └── storage/
│       └── firestore.py     # Firestore-based sync state persistence
├── tools/
│   ├── generate_session.py  # One-time session string generator
│   └── tg_check.py          # CLI helper: list dialogs, test read/write
└── tests/
    ├── unit/
    │   ├── test_orchestrator.py
    │   └── test_telegram.py
    └── integration/
        └── test_firestore.py
```

## Prerequisites

| Tool       | Version | Purpose                     |
|------------|---------|-----------------------------|
| Python     | 3.11+   | Runtime                     |
| Telethon   | 1.36+   | Telegram client library     |
| pydantic   | 2.6+    | Config validation           |
| PyYAML     | 6.0+    | Config file parsing         |

## Running Tests

```bash
# Unit tests (no credentials needed)
pytest tests/unit/

# Integration tests (requires Firebase emulator)
FIRESTORE_EMULATOR_HOST=localhost:8080 pytest tests/integration/
```

## Current Status

**Version:** 0.1.0 (initial working implementation)

The Telegram read/write functionality is fully operational and tested.

## License

MIT
