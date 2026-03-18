# telegram-cli — Developer Guide

This document is for developers who contribute to or build telegram-cli. For end-user documentation see [README.md](README.md).

---

## 1. Building Executables

telegram-cli is distributed in three variants. Each has its own build process.

### 1.1 Python variant (.pyz) — shiv

The `.pyz` archive bundles all Python dependencies into a single file. Users need Python ≥ 3.11 to run it.

**Prerequisites:** `pip install shiv`

```bash
cd telegram/telegram-cli

shiv -c telegram-cli -o dist/telegram-cli.pyz .
```

The entry point is `src.__main__:main` (via `__main__.py`). shiv reads the project's `pyproject.toml` to resolve dependencies.

### 1.2 Windows variant (.exe) — PyInstaller

**Prerequisites:** A Windows machine (or the GitHub Actions `windows-latest` runner) with Python ≥ 3.11 and `pip install pyinstaller`.

```powershell
cd telegram\telegram-cli

pyinstaller --onefile --name telegram-cli src\__main__.py
```

This produces `dist\telegram-cli.exe`. The binary is self-contained — no Python installation is needed on the target machine.

> **Note:** The `.exe` is not code-signed. On first run, Windows SmartScreen will show a warning. See README.md Step 1 for the user-facing instructions.

### 1.3 macOS variant — PyInstaller

**Prerequisites:** A macOS machine (or the GitHub Actions `macos-latest` runner) with Python ≥ 3.11 and `pip install pyinstaller`.

```bash
cd telegram/telegram-cli

pyinstaller --onefile --name telegram-cli src/__main__.py
```

This produces `dist/telegram-cli` (extensionless binary). Package it for distribution:

```bash
cd dist
zip telegram-cli-macos.zip telegram-cli
```

> **Note:** The binary is not notarized. On first run, macOS Gatekeeper blocks it. See README.md Step 1 for `chmod +x` / `xattr` instructions.

### 1.4 CI release workflow (release.yml)

All three variants are built automatically by the GitHub Actions workflow `.github/workflows/release.yml`. The workflow is triggered by pushing a version tag:

```bash
git tag v0.5.2
git push origin v0.5.2
```

**The same via VS Code UI:**

1. Open the **Source Control** panel (⌃⇧G / Ctrl+Shift+G).
2. Commit and push all changes.
3. Open the **Command Palette** (⌘⇧P / Ctrl+Shift+P) → type **Git: Create Tag** → enter the tag name (e.g. `v0.5.2`).
4. Open the **Command Palette** again → **Git: Push Tags**.

The workflow:

1. **ubuntu-latest** — builds `telegram-cli.pyz` with shiv.
2. **windows-latest** — builds `telegram-cli.exe` with PyInstaller.
3. **macos-latest** — builds `telegram-cli`, zips it to `telegram-cli-macos.zip`.

All three artifacts are uploaded as assets to the GitHub Release created for the tag.

### 1.5 Local builds

For local testing, build artifacts go into `dist/`. This directory is in `.gitignore` and must never be committed.

```bash
# Quick smoke test after a local build:
dist/telegram-cli version       # macOS
dist\telegram-cli.exe version   # Windows
python3 dist/telegram-cli.pyz version  # Python
```

---

## 2. Local Development Setup

```bash
# Clone and enter the sub-project
cd telegram/telegram-cli

# Create a virtual environment (one level up from the monorepo root is also fine)
python3 -m venv ../../.venv
source ../../.venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Also install telegram-lib (sibling dependency, editable)
pip install -e ../telegram-lib
```

After this, you can run the CLI directly:

```bash
python3 -m src ping
```

---

## 3. Project Structure

```
telegram/telegram-cli/
├── pyproject.toml            # Package metadata, dependencies, pytest config
├── README.md                 # End-user documentation
├── DEVELOPMENT.md            # This file
├── release-notes.md          # Changelog (appended per version)
├── commit-text-proposal.txt  # Last proposed commit message
├── docs/
│   ├── images/               # Screenshots for README
│   └── spec/
│       └── telegram-cli-requirements.md   # Functional & technical requirements
├── src/
│   ├── __init__.py           # Package docstring
│   ├── __main__.py           # Entry point: python3 -m src / .pyz
│   ├── cli.py                # argparse parser + command dispatch (T2)
│   ├── config.py             # config.yaml loader (T1)
│   ├── errors.py             # TgError → stderr formatting (T4)
│   ├── version.py            # Reads version.yaml (F9)
│   ├── version.yaml          # Current version, build, datetime
│   ├── _lib.py               # Adapter for importing telegram-lib (see §6)
│   └── commands/
│       ├── __init__.py
│       ├── init_cmd.py       # init command (F10)
│       ├── whoami.py         # whoami command (F8)
│       ├── ping.py           # ping command (F7)
│       ├── get_dialogs.py    # get-dialogs command (F5)
│       └── version_cmd.py    # version command (F9)
└── tests/
    └── unit/
        ├── __init__.py
        └── test_timeout.py   # (+ other test files)
```

---

## 4. Testing

### Running tests

```bash
cd telegram/telegram-cli
pytest --tb=short
```

All tests are in `tests/unit/`. pytest configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Test conventions

- Each command has a corresponding test module (e.g. `test_whoami.py`, `test_ping.py`).
- Tests mock telegram-lib calls via `_lib.py` — never make real network calls.
- Cover all code paths: success, every error code, missing config, timeouts.
- Use `pytest-mock` for patching, `pytest-asyncio` for async commands.

### Adding a test for a new command

1. Create `tests/unit/test_<command>.py`.
2. Mock `_lib.py` functions to return `TgResult.ok(...)` or `TgResult.err(...)`.
3. Call the command handler and assert stdout/stderr/exit code.

---

## 5. Quality Gate CI

The repository has a monorepo CI workflow at `.github/workflows/quality-gate.yml`. It detects which sub-projects have changed files and runs their test suites.

telegram-cli is registered (commented out) in that workflow. To activate it, uncomment the `telegram-cli` sections in the `detect-changes` job outputs and filters, and add the `telegram-cli` job block.

The telegram-cli CI job should:

1. Check out the repository.
2. Set up Python 3.11.
3. `pip install -e ".[dev]"` and `pip install -e ../telegram-lib`.
4. Run `pytest --tb=short`.

---

## 6. Architecture Notes

### _lib.py adapter

Both telegram-cli (`src/`) and telegram-lib (`src/`) use the package name `src`. Python cannot import two different packages with the same name via normal `import`. The `_lib.py` module solves this by loading telegram-lib modules via `importlib.util.spec_from_file_location()`, using absolute file paths relative to the monorepo layout.

All telegram-lib calls go through `_lib.py`. Command modules never import from telegram-lib directly.

### TgResult error model

telegram-lib functions return `TgResult[T]` — a result type that is either `TgResult.ok(value)` or `TgResult.err(TgError(...))`. Command handlers check `result.is_ok()` and either use `result.value` or pass `result.error` to `errors.format_error_and_exit()`.

### Config loader

`config.py` reads `config.yaml` from the current working directory. It returns the `telegram` section as a plain dict. Missing or malformed files cause an immediate `SystemExit` with a user-friendly message.

### Command dispatch

`cli.py` builds an `argparse.ArgumentParser` with subcommands. The `main()` function parses arguments and dispatches to the appropriate `run_*` handler in `src/commands/`. New commands are added by:

1. Adding a subparser in `cli.py → build_parser()`.
2. Creating `src/commands/<name>.py` with a `run_<name>()` function.
3. Adding the dispatch branch in `cli.py → main()`.

---

## 7. Version Management

Version information lives in `src/version.yaml`:

```yaml
version: 0.5.1
build: 1
datetime: 2026-03-18T00:00:00Z
```

The post-task workflow (see `.github/skills/post-task/SKILL.md`) updates three files after every task:

| File | Updated how |
|------|-------------|
| `src/version.yaml` | Semantic version bump + new datetime |
| `release-notes.md` | New version entry appended |
| `commit-text-proposal.txt` | Rewritten with prefixed commit message |

`pyproject.toml` also has a `version` field — keep it in sync manually when cutting a release tag.
