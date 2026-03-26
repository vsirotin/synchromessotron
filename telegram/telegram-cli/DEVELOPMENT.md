# telegram-cli — Developer Guide

This document is for developers who contribute to or build telegram-cli. For end-user documentation see [README.md](README.md).

---

## 1. Building Executables

telegram-cli is distributed in three variants. Build scripts live in `tools/` and are used by both the CI workflow and local builds.

| Variant | Script | Output | Platform |
|---------|--------|--------|----------|
| Python archive | `tools/build_pyz.sh` | `dist/telegram-cli.pyz` | Any (needs Python ≥ 3.11) |
| Windows binary | `tools/build_windows.sh` | `dist/telegram-cli.exe` | Windows |
| macOS binary | `tools/build_macos.sh` | `dist/telegram-cli-macos.zip` | macOS |

### 1.0 Build all variants

To build all three variants at once (useful for CI/CD or release preparation), use the workspace-level script:

```bash
cd <workspace-root>
bash build_all.sh
```

This script:
1. Builds the Python archive (.pyz) — always succeeds (Python + pip required)
2. Attempts Windows binary (.exe) — may skip on non-Windows platforms
3. Attempts macOS binary — may skip on non-macOS platforms

Each build is independent. Failures in one build do not stop the others. All artifacts appear in `telegram/telegram-cli/dist/`.

### 1.1 Local build

Run the script that matches your platform from the `telegram/telegram-cli` directory:

```bash
cd telegram/telegram-cli

# Python archive (works on any OS):
bash tools/build_pyz.sh

# macOS native binary (macOS only):
bash tools/build_macos.sh

# Windows native binary (Windows only — use Git Bash or WSL):
bash tools/build_windows.sh
```

Each script installs its own build tools (shiv or PyInstaller), installs `telegram-lib` from the sibling directory, builds the artifact into `dist/`, and prints a smoke-test command.

Smoke-test examples:

```bash
python3 dist/telegram-cli.pyz version       # Python archive
dist/telegram-cli version                    # macOS
dist\telegram-cli.exe version                # Windows
```

`dist/` is in `.gitignore` and must never be committed.

### 1.2 What each script does (step by step)

All three scripts follow the same pattern:

1. **Install build tool** — `pip install shiv` (for `.pyz`) or `pip install pyinstaller` (for native binaries).
2. **Install telegram-lib** — `pip install ../telegram-lib` so the dependency is available.
3. **Install telegram-cli itself** — `pip install .` (reads `pyproject.toml` for metadata and dependencies).
4. **Build the artifact**:
   - *shiv* bundles all Python packages into a single `.pyz` file. The entry point `src.__main__:main` is declared in `pyproject.toml → [project.scripts]`. Users need Python ≥ 3.11 to run the `.pyz`.
   - *PyInstaller* freezes the Python interpreter + all packages into a single native executable. No Python installation is needed on the target machine.
5. **Package** (macOS only) — zips the binary for easier distribution.

> **Windows note:** The `.exe` is not code-signed. On first run, Windows SmartScreen shows a warning. See README.md for user instructions.
>
> **macOS note:** The binary is not notarized. On first run, macOS Gatekeeper blocks it. See README.md for `chmod +x` / `xattr` instructions.

### 1.3 CI release workflow

The GitHub Actions workflow `.github/workflows/release.yml` calls the same `tools/build_*.sh` scripts on three runners (ubuntu, windows, macos). It is triggered when you push a version tag.

#### How to trigger a release

Release tags control whether a release appears as **Draft** or **Stable** on the GitHub Releases page:

- **`v1.0.0`** (without `-stable` suffix) → Release marked as **Draft** with auto-generated release notes.
- **`v1.0.0-stable`** (with `-stable` suffix) → Release marked as **Stable** and promoted on the Releases page.

**Use the set-tag.sh script:**

```bash
bash ../../set-tag.sh v1.0.0
```

The script:
1. Creates the Git tag locally.
2. Pushes the tag to GitHub to trigger the CI release workflow.

> **Note:** Version files (`src/version.yaml`, `release-notes.md`, `commit-text-proposal.txt`) must be updated manually before tagging. Typically done via the post-task workflow when completing development tasks.

**To mark an existing release as stable:**

After the v1.0.0 release is published, create a secondary stable tag:

```bash
bash ../../set-tag.sh v1.0.0-stable
```

This only creates the stable tag to promote the release on GitHub.

**Manual alternative:**

You can also create and push tags manually:

```bash
# Create and push tag
git tag v1.0.0
git push origin v1.0.0
```

The `set-tag.sh` script automates these two commands.

**VS Code UI:**

1. Open the **Source Control** panel (⌃⇧G / Ctrl+Shift+G).
2. Commit and push all changes.
3. Open the **Command Palette** (⌘⇧P / Ctrl+Shift+P) → type **Git: Create Tag** → enter the tag name (e.g. `v1.0.0` or `v1.0.0-stable`).
4. Open the **Command Palette** again → **Git: Push Tags**.

#### How to monitor the build

After pushing the tag:

1. Go to the repository on GitHub: **https://github.com/vsirotin/synchromessotron**.
2. Click the **Actions** tab.
3. You will see a workflow run named **Release** with the tag name. Click it.
4. Inside you see four jobs: **build-pyz**, **build-windows**, **build-macos**, **release**.
5. Click any job to see its real-time log. Each step (Set up Python, Build, Upload) shows its output. If a step fails, it turns red and the log shows the error.

> **Tip:** You can also click the **Actions** tab directly from VS Code if you have the [GitHub Actions extension](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-github-actions) installed.

#### How to download the release artifacts

When all four jobs finish green:

1. Go to the repository → **Releases** (right sidebar, or direct link: `https://github.com/vsirotin/synchromessotron/releases`).
2. The latest release shows the tag name and three downloadable assets:
   - `telegram-cli.pyz`
   - `telegram-cli.exe`
   - `telegram-cli-macos.zip`
3. Click on an asset to download it.

You can also download intermediate build artifacts (before the release job runs) from the workflow run page → **Artifacts** section at the bottom.

#### How to delete a bad release

If a release contains broken artifacts or was created by mistake:

1. Go to **Releases** → click the release you want to remove.
2. Click the **Delete** button (top-right, next to "Edit").
3. Confirm the deletion. This removes the release page and its assets but does **not** delete the Git tag.
4. To also delete the tag (so you can re-use the same version number):

   **Terminal:**
   ```bash
   git tag -d v1.0.0                  # delete local tag
   git push origin --delete v1.0.0    # delete remote tag
   ```

   **VS Code:** There is no built-in UI for deleting tags — use the terminal.

5. After fixing the issue, create the tag again and push it to re-trigger the workflow.

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

## 3. Testing

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

## 4. Quality Gate CI

The repository has a monorepo CI workflow at `.github/workflows/quality-gate.yml`. It detects which sub-projects have changed files and runs their test suites.

telegram-cli is registered in that workflow. On every push that touches files under `telegram/telegram-cli/`, the CI job:

1. Checks out the repository.
2. Sets up Python 3.11.
3. `pip install -e ../telegram-lib` and `pip install -e ".[dev]"`.
4. Runs `pytest --tb=short`.

---

## 5. Architecture Notes

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

## 6. Post-Build Integration Testing

Simple, function-based integration test framework. No JSON DSL—just Python.

### 6.1 Quick Start

After building the CLI executable:

```bash
cd telegram/telegram-cli/dist

# Automatic: detects platform, finds executable, runs tests
python3 ../tests/post_build/run_integration_tests.py

# With rebuild (if you want to rebuild first)
python3 ../tests/post_build/run_integration_tests.py --rebuild
```

### 6.2 How It Works

#### Test Framework: `integration_test.py`

Write tests using simple Python functions:

```python
from integration_test import test, check_json_valid, check_json_has_key

# Example: test the version command
test(
    cli="python3 dist/telegram-cli.pyz",    # Platform-agnostic: works on any OS
    command="version",
    check_json_valid(),                      # Verify output is valid JSON
    check_json_has_key("cli", contains={"version": None}),  # Check structure
    check_json_has_key("lib", contains={"datetime": None})
)
```

**Key point:** The `cli` parameter is passed to `test()`, making it **platform-independent**. The same test code runs on all platforms.

#### Runner Script: `run_integration_tests.py`

Automates test execution:

```bash
python3 run_integration_tests.py
```

The runner:
1. Detects your platform (macOS, Windows, Linux)
2. Looks for the built executable in `dist/`
3. Runs `integration_test.py` with the correct CLI path
4. Reports results

**Note:** Tests assume `config.yaml` exists in the `dist/` directory with valid Telegram credentials. If config is missing or invalid, tests requiring network access will fail.

### 6.3 Test Execution Flow

**For developers (manual testing):**

Always run from the `dist/` directory where `config.yaml` and the executable are located:

```bash
cd telegram/telegram-cli/dist
python3 ../tests/post_build/run_integration_tests.py
```

The runner:
- Detects your platform (macOS, Windows, Linux)
- Finds the built executable in the current directory
- Runs integration tests using that executable (from dist/)
- Reports test statistics (total checks, passed, failed)

**Config file location:**

Tests and the CLI expect `config.yaml` in the `dist/` directory (where the executable runs):

```bash
telegram/telegram-cli/dist/
├── telegram-cli.pyz           # Executable
├── config.yaml                # Required: Telegram credentials
└── tmp1/                       # Test output directory
    └── dialogs.json
```

Create `config.yaml` once and keep it in `dist/` for all test runs.

### 6.4 Available Check Functions

Check functions are organized into modular files:

**check_output_json.py:**
- `check_json_valid()` — Verify output is valid JSON
- `check_json_has_key(key, contains={...})` — Check JSON structure

**check_stdout.py:**
- `check_stdout_contains(text)` — Check for substring in output
- `check_stdout_line_count(min=0, max=None)` — Verify line count

### 6.5 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more checks failed |
| 2 | Executable not found or other error |

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
