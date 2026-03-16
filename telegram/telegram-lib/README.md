# telegram-lib

A library of stateless Python functions that wraps the Telegram user-account API via [Telethon](https://github.com/LorenzoTheWorker/Telethon).

## Overview

This library provides the core Telegram functionality used by other subprojects (`telegram-cli`, `telegram-web`, etc.). It authenticates as a **user account** (not a bot) and exposes stateless wrapper functions for the user's dialogs, groups, and channels:

- **F1 — Backup:** full and incremental backup of message history.
- **F2 — Send:** send messages on behalf of the user's account.
- **F3 — Edit:** edit and resend the user's own messages.
- **F4 — Delete:** delete the user's own messages.
- **F5 — Dialogs:** retrieve the complete list of the user's dialogs, groups, and channels.
- **F6 — Media:** download individual messages, photos, and media files.
- **F7 — Availability:** check whether the Telegram service is reachable.
- **F8 — Session:** validate the current user session.

> **Terminology:** In the Telegram API the term **"dialog"** denotes any conversation the user participates in — a one-to-one chat with another user, a group, or a channel. This is the official term used by the MTProto protocol and the Telethon library, and it is preserved throughout this project.

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

Unit tests verify every library function (F1–F8) — including error handling and the Result/Error contract — using mocked API calls. **No real credentials, no internet connection needed.**

```bash
pytest tests/unit/
```

You should see all tests pass. If any fail, check that dependencies installed correctly and that you are running Python 3.11 or later.

---

### Step 3 — Create a Telegram application

1. Open <https://my.telegram.org/apps> in a browser and sign in with your phone number.
2. Click **API development tools**.
3. Fill in the **Create new application** form. The App title and Short name can be anything, e.g. `synchromessotron` / `syncbot`. Platform can be left as `Other`.

   ![Create new application dialog](docs/images/telegram1.png)

4. Click **Create application**.
5. You will see your **App api_id** (a number) and **App api_hash** (a long hex string). Note both values — you will need them in the next step.

   ![api_id and api_hash](docs/images/telegram2.png)

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
| `Chat`    | A regular group (legacy, non-supergroup)             |
| `User`    | A direct message dialog with another person         |

All three types are "dialogs" in the Telegram API sense.

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
