# Synchromessotron — Project Plan

> AI-agent-driven development plan with explicit human-in-the-loop checkpoints.

## Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Runtime / hosting | Firebase Cloud Functions v2 (scheduled, cron via Cloud Scheduler) |
| Sync-state storage | Firestore |
| Telegram library | TBD at Checkpoint 1 (Telethon recommended) |
| VK library | TBD at Checkpoint 1 (`vk_api` or `vkbottle` recommended) |
| Credentials | Environment variables / Firebase Secret Manager |
| Tests | `pytest` + `pytest-asyncio` |
| Linting / formatting | `ruff`, `black` |
| CI | GitHub Actions |

---

## Human-in-the-Loop Checkpoints Summary

| # | Phase | Who | What | Blocks |
|---|-------|-----|------|--------|
| 1 | After Phase 0 | Human | Confirm library / tech choices | Phases 1–5 |
| 2 | After Phase 9 | Human | Local emulator review & testing | Phase 10 |
| 3 | After Phase 10 | Human | Production deployment & smoke test | Done |

---

## Phase 0 — Project Setup *(AI agents)*

**Goal:** Create a working skeleton that CI can lint and test.

Tasks:
- Initialize GitHub repository with MIT license and `.gitignore` (Python + Firebase).
- Scaffold the directory structure (see "Target File Structure" section below).
- Set up Python environment: `pyproject.toml` with dev dependencies (`pytest`, `pytest-asyncio`, `ruff`, `black`, `firebase-admin`).
- Add `firebase.json` and `.firebaserc` stubs.
- Configure GitHub Actions workflow: lint with `ruff`, format-check with `black`, run `pytest` on every push.

---

## 🛑 Human Checkpoint 1 — Technology Stack Decision

**Who:** Human owner  
**Trigger:** Phase 0 complete.

**Context for the human:**

Telegram options:
- **Telethon** *(recommended)* — async MTProto client, can act as a user account (required for reading and forwarding personal messages).
- `python-telegram-bot` — bot-only; cannot read user account messages → unsuitable for this use case.

VK options:
- **`vk_api`** *(recommended)* — stable, widely used, supports user tokens.
- **`vkbottle`** — async, modern, supports user accounts.

Storage: **Firestore** is the native Firebase choice and fits the serverless model well.

**Decisions required:**
1. Confirm or replace the Telegram library.
2. Confirm or replace the VK library.
3. Confirm Firestore as the sync-state storage backend.

**Output:** Human records decisions in `docs/tech-decisions.md`.

---

## Phase 1 — Core Abstractions *(AI agents, after Checkpoint 1)*

**Goal:** Define the stable contracts that all other code depends on.

Tasks:
- `src/core/interfaces.py`:
  - `Message` dataclass: `id`, `text`, `timestamp`, `attachments` (optional), `source_messenger`.
  - `MessengerAccount` dataclass: `messenger_id`, `credentials_ref`.
  - `IReader` abstract class: `read_since(account: MessengerAccount, since: datetime) -> list[Message]`.
  - `IWriter` abstract class: `write(account: MessengerAccount, messages: list[Message]) -> None`.
  - `ISyncStateStorage` abstract class: `get_last_sync() -> datetime`, `set_last_sync(dt: datetime) -> None`.
- Write unit tests for interface contracts using mock implementations.

---

## Phase 2 — Sync Orchestrator *(AI agents, depends on Phase 1)*

**Goal:** Implement the 5-step algorithm from the requirements.

Tasks:
- `src/core/orchestrator.py`:
  - `SyncOrchestrator.__init__(pairs: list[SyncPair])` where `SyncPair = (reader, writer_account, writer, reader_account)`.
  - `SyncOrchestrator.run(storage: ISyncStateStorage) -> None` — implements steps 1–5.
  - Sync state is updated **only after** all writes succeed.
  - Handle empty message lists gracefully (no-op).
- Unit tests with mocked readers, writers, and storage.

---

## Phase 3 — Firestore State Storage *(AI agents, parallel with Phase 2)*

**Goal:** Persist sync state between cron invocations.

Tasks:
- `src/storage/firestore.py`:
  - `FirestoreStateStorage(ISyncStateStorage)` using `firebase-admin` SDK.
  - Store last-sync timestamp in a dedicated Firestore collection (configurable collection name).
- Integration tests using the Firestore emulator.

---

## Phase 4 — Telegram Integration *(AI agents, depends on Phase 1 + Checkpoint 1)*

**Goal:** Concrete Reader and Writer for Telegram.

Tasks:
- `src/messengers/telegram/reader.py`:
  - `TelegramReader(IReader)` — authenticate with a user account session, fetch messages from configured dialogs since the given timestamp, map to `Message`.
- `src/messengers/telegram/writer.py`:
  - `TelegramWriter(IWriter)` — forward or re-post messages to configured dialogs.
  - Write strategy (forward / re-post with attribution) is configurable per account pair.
- Unit tests with a mocked Telegram client.

---

## Phase 5 — VK Integration *(AI agents, parallel with Phase 4)*

**Goal:** Concrete Reader and Writer for VK.com.

Tasks:
- `src/messengers/vk/reader.py`:
  - `VKReader(IReader)` — authenticate with a user token, fetch messages from configured conversations since the given timestamp, map to `Message`.
- `src/messengers/vk/writer.py`:
  - `VKWriter(IWriter)` — post or forward messages to VK conversations.
  - Write strategy is configurable per account pair.
- Unit tests with a mocked VK client.

---

## Phase 6 — Configuration Layer *(AI agents, depends on Phase 4 + Phase 5)*

**Goal:** Make all runtime details configurable without code changes.

Tasks:
- `src/config/schema.py` — define configuration dataclasses / Pydantic models:
  - List of sync pairs: source messenger + account, target messenger + account.
  - Per-messenger write strategy settings.
  - Credentials references (env var names or Secret Manager paths).
  - Firestore collection name for sync state.
- `src/config/loader.py` — load and validate config from a YAML file or environment variables.
- Document all configuration options in README.

---

## Phase 7 — Firebase Cloud Function Entry Point *(AI agents, depends on Phase 2, 3, 6)*

**Goal:** Wire everything together as a deployable scheduled function.

Tasks:
- `functions/main.py`:
  - Scheduled Cloud Function (cron expression configurable in `firebase.json`).
  - On invocation: load config → instantiate readers/writers → instantiate `FirestoreStateStorage` → call `SyncOrchestrator.run()`.
- Update `firebase.json` with function definition and schedule.
- Add Firebase emulator configuration (`firebase.json` + `.firebaserc`) for local testing.

---

## Phase 8 — Error Handling & Logging *(AI agents, depends on Phase 7)*

**Goal:** Make the service production-safe and debuggable.

Tasks:
- Retry transient network errors with exponential backoff (configurable max retries).
- Respect API rate limits per messenger (back off on rate-limit responses).
- Structured JSON logging using Python `logging` with a JSON formatter compatible with Google Cloud Logging.
- Log: function start/end, messages read/written counts, errors with stack traces.
- Ensure sync state is only updated after **all** writes complete successfully.

---

## Phase 9 — Documentation *(AI agents, depends on Phase 6, 7, 8)*

**Goal:** Project is understandable and ready for external contributors.

Tasks:
- **`README.md`**: project description, prerequisites, setup guide, configuration reference, local testing instructions, deployment steps.
- **`DEVELOPMENT.md`**: architecture overview, step-by-step guide for adding a new messenger (with code template), local dev setup, testing guide.
- Inline docstrings on all public interfaces and key classes.

---

## 🛑 Human Checkpoint 2 — Local Review & Testing

**Who:** Human owner  
**Trigger:** Phase 9 complete.

Tasks:
1. Run `firebase emulators:start` and trigger the function manually.
2. Verify messages are correctly synchronized between test Telegram and VK accounts.
3. Review code with focus on: credentials handling (no secrets in code/logs), extensibility of abstractions, error recovery behavior.
4. Review README and DEVELOPMENT.md for clarity and completeness.

**Exit criteria:** Human approves, or files issues. AI agents address all issues before Phase 10.

---

## Phase 10 — Bug Fixes from Review *(AI agents, depends on Checkpoint 2)*

**Goal:** All issues from human review are resolved.

Tasks:
- Fix all issues raised during Checkpoint 2.
- Re-run full test suite; all tests must pass.
- Update documentation if behavior changed.

---

## 🛑 Human Checkpoint 3 — Production Deployment

**Who:** Human owner  
**Trigger:** Phase 10 complete (all tests pass, human review sign-off).

Tasks:
1. Create / configure the Firebase production project.
2. Store messenger credentials in Firebase Secret Manager.
3. Run `firebase deploy --only functions`.
4. Validate the first scheduled execution in Google Cloud Logging.
5. Smoke test: verify messages are synchronized correctly in production accounts.

---

## Target File Structure

```
synchromessotron/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── interfaces.py        # IReader, IWriter, ISyncStateStorage, Message, MessengerAccount
│   │   └── orchestrator.py      # SyncOrchestrator
│   ├── messengers/
│   │   ├── __init__.py
│   │   ├── telegram/
│   │   │   ├── __init__.py
│   │   │   ├── reader.py        # TelegramReader
│   │   │   └── writer.py        # TelegramWriter
│   │   └── vk/
│   │       ├── __init__.py
│   │       ├── reader.py        # VKReader
│   │       └── writer.py        # VKWriter
│   ├── storage/
│   │   ├── __init__.py
│   │   └── firestore.py         # FirestoreStateStorage
│   └── config/
│       ├── __init__.py
│       ├── schema.py            # Config dataclasses / Pydantic models
│       └── loader.py            # Config loader + validator
├── functions/
│   ├── __init__.py
│   └── main.py                  # Firebase Cloud Function entry point
├── tests/
│   ├── unit/
│   │   ├── test_orchestrator.py
│   │   ├── test_telegram.py
│   │   └── test_vk.py
│   └── integration/
│       └── test_firestore.py
├── docs/
│   └── tech-decisions.md        # Filled in at Checkpoint 1
├── .github/
│   └── workflows/
│       └── ci.yml               # Lint + test on push
├── README.md
├── DEVELOPMENT.md
├── firebase.json
├── .firebaserc
├── pyproject.toml
└── .gitignore
```
