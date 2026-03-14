# Project Plan — Synchromessotron

Development roadmap organized by subproject. Each section lists draft issues intended to be developed as pull requests with AI agents.

---

## telegram-lib

Issues for extracting and stabilizing the Telegram core library from the existing monolith.

- **TL-1**: Extract Telegram-specific code into `telegram/telegram-lib/src/` — move `src/messengers/telegram/`, `src/core/`, `src/config/`, `src/storage/` and adapt imports
- **TL-2**: Create `telegram/telegram-lib/pyproject.toml` with its own package metadata and dependencies (Telethon, pydantic, PyYAML, firebase-admin)
- **TL-3**: Move `tools/tg_check.py` into `telegram/telegram-lib/tools/` and update relative imports
- **TL-4**: Move Telegram-related unit tests (`tests/unit/test_telegram.py`, `tests/unit/test_orchestrator.py`) into `telegram/telegram-lib/tests/`
- **TL-5**: Move integration tests (`tests/integration/test_firestore.py`) into `telegram/telegram-lib/tests/integration/`
- **TL-6**: Set up CI workflow (GitHub Actions) for telegram-lib: lint (ruff, black) + unit tests on push/PR
- **TL-7**: Add `py.typed` marker and type annotations to all public interfaces
- **TL-8**: Write API documentation (docstrings) for `IReader`, `IWriter`, `ISyncStateStorage`, `Message`, `Attachment`
- **TL-9**: Add support for reading message attachments (photos, documents, audio, video) and representing them in the `Attachment` model
- **TL-10**: Tag and release `telegram-lib` v0.1.0

---

## telegram-cli

Issues for building the command-line tool on top of telegram-lib.

- **TC-1**: Initialize `telegram/telegram-cli/` project structure — `pyproject.toml`, `src/`, dependency on telegram-lib
- **TC-2**: Implement `read` command — read messages from a specified Telegram dialog and print to stdout
- **TC-3**: Implement `export` command — export messages to local files (JSON format) with configurable output path
- **TC-4**: Implement `export --format markdown` — export messages as human-readable Markdown files
- **TC-5**: Implement `post` command — send a message (from argument or stdin) to a specified Telegram dialog
- **TC-6**: Implement `post --file` — publish content from a local file to a Telegram dialog
- **TC-7**: Implement `sync` command — two-way sync between Telegram dialog and local file directory
- **TC-8**: Add `--since` and `--until` date filters for read/export commands
- **TC-9**: Add `--author` filter for read/export commands
- **TC-10**: Implement `list` command — list available dialogs (wrap tg_check.py functionality)
- **TC-11**: Add interactive mode with prompt-based dialog selection
- **TC-12**: Set up CI workflow for telegram-cli: lint + unit tests
- **TC-13**: Write user documentation (README with usage examples)
- **TC-14**: Tag and release `telegram-cli` v0.1.0

---

## telegram-web

Issues for building the web application (Angular frontend + Python backend).

### Backend

- **TW-B1**: Initialize `telegram/telegram-web/backend/` — FastAPI project structure, dependency on telegram-cli
- **TW-B2**: Implement REST endpoint `GET /api/dialogs` — list available Telegram dialogs
- **TW-B3**: Implement REST endpoint `GET /api/messages?dialog_id=&since=&until=` — read messages from a dialog
- **TW-B4**: Implement REST endpoint `POST /api/messages` — send a message to a dialog
- **TW-B5**: Implement REST endpoint `GET /api/export?dialog_id=&format=` — export messages to file and return download link
- **TW-B6**: Add authentication middleware (token-based or session-based)
- **TW-B7**: Add WebSocket support for real-time message updates
- **TW-B8**: Write backend API tests
- **TW-B9**: Set up CI workflow for telegram-web backend

### Frontend

- **TW-F1**: Initialize `telegram/telegram-web/frontend/` — Angular 17+ project with routing and basic layout
- **TW-F2**: Create dialog list page — display available Telegram dialogs
- **TW-F3**: Create message view page — display messages for a selected dialog with pagination
- **TW-F4**: Create message compose component — input field with send button
- **TW-F5**: Create export dialog — select format (JSON/Markdown), date range, download
- **TW-F6**: Add search/filter functionality — filter messages by text, date, author
- **TW-F7**: Add responsive layout for mobile browsers
- **TW-F8**: Write frontend unit tests (Jasmine/Karma)
- **TW-F9**: Set up CI workflow for telegram-web frontend: lint + test + build

---

## telegram-web-server

Issues for deploying telegram-web to Firebase.

- **TWS-1**: Create `telegram/telegram-web-server/firebase.json` — configure Hosting (frontend) and Cloud Functions (backend)
- **TWS-2**: Create deployment script — build frontend, package backend, deploy to Firebase
- **TWS-3**: Configure Firebase Authentication for user access control
- **TWS-4**: Migrate Firestore sync-state storage from monolith to telegram-web-server
- **TWS-5**: Set up CI/CD workflow — deploy to Firebase on push to main
- **TWS-6**: Add staging environment configuration (separate Firebase project)
- **TWS-7**: Write deployment documentation in README
- **TWS-8**: Tag and release `telegram-web-server` v0.1.0

---

## telegram-windows

Issues for creating the Windows desktop app via GitHub Action.

- **TWIN-1**: Evaluate desktop wrapper options (Electron, Tauri, PyInstaller) and document decision
- **TWIN-2**: Create desktop wrapper configuration for Windows builds
- **TWIN-3**: Create GitHub Action `create-telegram-windows` — build pipeline that produces `.exe` installer
- **TWIN-4**: Add code signing configuration (optional, for trusted installer)
- **TWIN-5**: Configure GitHub Action to upload `.exe` as release asset on tag push
- **TWIN-6**: Write end-user README with download link, system requirements, installation instructions
- **TWIN-7**: Test the built `.exe` on Windows 10 and Windows 11
- **TWIN-8**: Tag and release `telegram-windows` v0.1.0

---

## telegram-macos

Issues for creating the macOS desktop app via GitHub Action.

- **TMAC-1**: Create desktop wrapper configuration for macOS builds (.app bundle)
- **TMAC-2**: Create GitHub Action `create-telegram-macos` — build pipeline that produces `.dmg` or `.app.zip`
- **TMAC-3**: Add code signing and notarization configuration (Apple Developer certificates)
- **TMAC-4**: Configure GitHub Action to upload macOS app as release asset on tag push
- **TMAC-5**: Write end-user README with download link, system requirements, installation instructions
- **TMAC-6**: Test the built app on macOS 12+ (Intel and Apple Silicon)
- **TMAC-7**: Tag and release `telegram-macos` v0.1.0

---

## vkontakte

Issues for VK.com integration — to be detailed after the Telegram subprojects are established.

- **VK-1**: Define subproject structure (vk-lib, vk-cli, etc.) — mirror Telegram pattern
- **VK-2**: Extract existing VK code (`src/messengers/vk/`, `tools/vk_auth.py`, `tests/unit/test_vk.py`) into `vkontakte/vk-lib/`
- **VK-3**: Create `vkontakte/vk-lib/pyproject.toml` and README
- **VK-4**: Set up CI workflow for vk-lib
- **VK-5**: Plan remaining VK subprojects (vk-cli, vk-web, etc.)

---

## Cross-cutting / Infrastructure

- **INFRA-1**: Set up monorepo tooling — workspace-level CI, shared linting config, dependency management
- **INFRA-2**: Create root-level `Makefile` or `justfile` with commands for all subprojects (lint, test, build)
- **INFRA-3**: Configure dependabot or renovate for automated dependency updates
- **INFRA-4**: Add LICENSE file to each subproject
- **INFRA-5**: Set up branch protection rules and PR templates
