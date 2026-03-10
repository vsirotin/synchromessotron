# Development Guide

## Architecture Overview

```
Firebase Cloud Function (scheduled cron)
  └─ functions/main.py
       ├─ load_config()                    ← src/config/loader.py
       ├─ FirestoreStateStorage            ← src/storage/firestore.py
       └─ SyncOrchestrator.run()           ← src/core/orchestrator.py
            ├─ IReader.read_since()  ──►  src/messengers/{telegram,vk}/reader.py
            ├─ IWriter.write()       ──►  src/messengers/{telegram,vk}/writer.py
            └─ ISyncStateStorage.set_last_sync()
```

### Key files

| File | Purpose |
|---|---|
| `src/core/interfaces.py` | `IReader`, `IWriter`, `ISyncStateStorage`, `Message`, `MessengerAccount` |
| `src/core/orchestrator.py` | 5-step sync algorithm |
| `src/core/retry.py` | Async retry with exponential backoff |
| `src/storage/firestore.py` | Firestore implementation of `ISyncStateStorage` |
| `src/config/schema.py` | Pydantic config models |
| `src/config/loader.py` | YAML config loader |
| `src/messengers/telegram/` | Telegram `IReader` and `IWriter` (Telethon) |
| `src/messengers/vk/` | VK `IReader` and `IWriter` (vk_api) |
| `functions/main.py` | Firebase Cloud Function entry point |

### Sync algorithm

```
last_sync ← Firestore
for each sync pair:
    messages ← IReader.read_since(source_account, last_sync)   # retried on network errors
for each sync pair + messages:
    IWriter.write(target_account, messages)                    # retried on network errors
now ← datetime.now(UTC)
Firestore ← now   ← only if ALL reads and writes succeeded
```

### Write strategies

| Strategy | Same-platform | Cross-platform |
|---|---|---|
| `forward` | Native platform forward | Falls back to repost |
| `repost` | New message (no attribution) | New message with `[From X]` prefix |

---

## Local Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Lint and test:

```bash
ruff check .
black --check .
pytest tests/unit/
```

---

## Adding a New Messenger

### 1. Create the module structure

```
src/messengers/<messenger_name>/
    __init__.py
    reader.py     # implements IReader
    writer.py     # implements IWriter
```

### 2. Define the credentials format

Pick a JSON schema for credentials and document it in README.md under "Credentials".

Example:

```json
{"api_key": "...", "api_secret": "..."}
```

### 3. Implement IReader

```python
# src/messengers/my_platform/reader.py
from __future__ import annotations

import json
import os
from datetime import datetime

from src.core.interfaces import IReader, Message, MessengerAccount


def _load_credentials(credentials_ref: str) -> dict:
    raw = os.environ.get(credentials_ref)
    if not raw:
        raise EnvironmentError(f"Environment variable {credentials_ref!r} is not set.")
    return json.loads(raw)


class MyPlatformReader(IReader):
    async def read_since(
        self, account: MessengerAccount, since: datetime
    ) -> list[Message]:
        creds = _load_credentials(account.credentials_ref)
        # 1. Connect to the platform API using creds.
        # 2. Fetch messages from account.account_id (the peer/dialog) since `since`.
        # 3. Map each platform message to Message(
        #        id=str(...),
        #        text=...,
        #        timestamp=...,        # must be timezone-aware UTC
        #        source_messenger="my_platform",
        #        metadata={...}        # store peer_id + message_id for potential forwarding
        #    )
        # 4. Return sorted oldest-first.
        ...
```

### 4. Implement IWriter

```python
# src/messengers/my_platform/writer.py
from src.core.interfaces import IWriter, Message, MessengerAccount


class MyPlatformWriter(IWriter):
    def __init__(self, strategy: str = "repost") -> None:
        self._strategy = strategy

    async def write(
        self, account: MessengerAccount, messages: list[Message]
    ) -> None:
        # 1. Connect to the platform API.
        # 2. For each message:
        #    - If strategy == "forward" and msg.source_messenger == "my_platform":
        #        use native forwarding with msg.metadata["message_id"] etc.
        #    - Else: send new message.
        #      Add attribution prefix if msg.source_messenger != "my_platform":
        #        f"[From {msg.source_messenger.capitalize()}]\n" + msg.text
        ...
```

### 5. Register in the function entry point

Add a branch in `_build_messenger()` in `functions/main.py`:

```python
if messenger_id == "my_platform":
    from src.messengers.my_platform.reader import MyPlatformReader
    from src.messengers.my_platform.writer import MyPlatformWriter

    account = MessengerAccount(
        messenger_id=messenger_id,
        account_id=account_id,
        credentials_ref=credentials_ref,
    )
    return MyPlatformReader(), MyPlatformWriter(strategy=write_strategy), account
```

### 6. Write unit tests

Create `tests/unit/test_my_platform.py` following the patterns in
`tests/unit/test_telegram.py` and `tests/unit/test_vk.py`.

---

## Credential Format Reference

Each credentials env var must contain a JSON string.

| Messenger | Required JSON keys |
|---|---|
| Telegram | `api_id` (int), `api_hash` (str), `session` (Telethon StringSession str) |
| VK | `token` (str — user access token with `messages` scope) |

---

## Error Handling Notes

- **Transient network errors** (`OSError`, `TimeoutError`, `ConnectionError`) are retried
  up to 3 times with exponential backoff. See `src/core/retry.py`.
- **Telegram FloodWaitError** (rate limit) is caught in the Telegram reader/writer;
  the service sleeps for the required duration and then raises `OSError` to trigger
  the generic retry mechanism.
- **Sync state is updated only after all writes succeed.** On failure, the next run
  re-reads all messages since the last successful sync. Messenger implementations
  should be idempotent where possible (e.g. the VK writer uses a deterministic
  `random_id` to prevent duplicate messages on retry).
