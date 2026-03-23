# Project telegram/telegram-cli. Release notes 

## Version: 1.0.12
Simplified release tagging workflow: (1) Moved `set-tag.sh` from `tools/` to workspace root at `set-tag.sh`; (2) Removed automated version file updates from script — versions now managed by post-task workflow only; (3) Script now performs simple `git tag` and `git push` operations only; (4) Updated DEVELOPMENT.md tagging documentation with new script location and manual version update instructions. Release workflow remains unchanged; users must manually update version.yaml, release-notes.md, and commit-text-proposal.txt before tagging.

## Version: 1.0.11
Post-build integration testing: (1) Refactored `test()` function to return statistics tuple `(total_checks, passed_checks)` instead of exiting, enabling CI/CD result collection; (2) Created `run_post_build_test.py` for CI/CD-specific post-build test execution in dist/ directory; (3) Integrated post-build tests into release.yml workflow (3 build jobs: pyz, windows, macos) with automatic build failure on test failure; (4) Simplified DEVELOPMENT.md documentation — removed advanced developer extension guides, focused on usage. Framework continues execution on failures, collects all statistics, exits with status code based on total failures.

## Version: 1.0.10
Enhanced release workflow: (1) Distinguished draft releases (v1.0.0 tags) and stable releases (v1.0.0-stable tags) — stable releases marked as stable on GitHub Releases page, draft releases marked as Draft; (2) Removes auto-generated source code archives (.zip, .tar.gz) from releases, keeping only the 3 executable distributions (.pyz, .exe, .zip); (3) Added set-tag.sh script in tools/ for streamlined release tagging with automatic version.yaml updates, release-notes.md entries, and commit-text-proposal.txt generation.

## Version: 1.0.9
Fixed backup tests: migrated from deprecated `--output` file parameter to `--outdir` directory parameter. Removed TestBackupStdout class (stdout backup no longer supported). Updated TestBackupToFile, TestResumable, and TestRateLimit to use directory API and `messages.json` output file. All 19 backup unit tests pass (was 19, refactored).

## Version: 1.0.8
Init command decision tree rewrite: 5-step multi-branch flow with config existence detection, config location query, credentials notes prompt, example file creation offer, and comprehensive credential validation. Graceful Ctrl+C handling throughout with friendly cancellation messages (no tracebacks). Added 7 helper functions with proper error handling. All 115 unit tests pass (94 base + 21 new init-specific tests).

## Version: 1.0.7
Added F10-a through F10-d init command UX improvements: (a) existing config detection with user choice to create example template, (b) display Ctrl+C interruption guidance before credential prompts, (c) graceful login code callback with KeyboardInterrupt support, (d) consistent error handling with friendly messages and no tracebacks. Added 20 comprehensive unit tests covering all new flows. All 115 tests pass.

## Version: 1.0.6
Updated workspace pyproject.toml configuration: added `[tool.workspace.projects]` section to track sub-project dependencies, cleaned up outdated root-level dependencies, and updated ruff configuration. Enhanced post-task skill to use workspace configuration for dependency discovery. Restored telegram-cli.exe to release workflow assets. All 95 tests pass.

## Version: 1.0.5
Fixed fragile `test_get_cli_version_happy` test that hardcoded the version string `"1.0.3"` — broke on every version bump. Replaced with `re.match(r"^\d+\.\d+\.\d+$", ...)` regex check.

## Version: 1.0.4
Fixed `telegram-cli.pyz` crashes: (1) resolved `src` namespace collision — telegram-lib package renamed from `src` to `telegram_lib`, `_lib.py` rewritten to use direct imports; (2) added `[tool.setuptools.packages.find]` and `package-data` to pyproject.toml so the `src` package and `version.yaml` are correctly included in the wheel; (3) removed obsolete `_ensure_lib_path()` from `errors.py`. Updated `test_timeout.py` to import from `telegram_lib`. All 95 tests pass.

## Version: 1.0.3
Fixed build infrastructure: updated release workflow to install telegram-lib dependency before building, refactored build scripts (build_pyz.sh, build_macos.sh, build_windows.sh) to build telegram-lib wheels first and use --find-links for local dependency resolution. Fixed pyproject.toml entry point from src.__main__:main to src.cli:main. Added post-task skill rule #3 for updating dependent project versions when libraries change.

## Version: 1.0.2
Updated telegram-lib dependency to version 1.2.2. Fixed 14 ruff lint errors and 6 black formatting issues in telegram-lib (import sorting, unused imports, line length, StrEnum).

## Version: 1.0.1
Added build scripts `tools/build_pyz.sh`, `tools/build_windows.sh`, `tools/build_macos.sh` for local builds. Refactored `release.yml` to call the same scripts. Expanded DEVELOPMENT.md §1 with step-by-step build explanations, CI monitoring instructions, artifact download guide, and release deletion procedure. Updated project structure tree and §5 (quality-gate now active for telegram-cli).

## Version: 1.0.0
Phase E complete. Added GitHub Actions release workflow (`release.yml`) for three distribution variants: `.pyz` (shiv, cross-platform), `.exe` (PyInstaller, Windows), macOS binary (PyInstaller + zip). Workflow triggers on `v*` tag push and creates a GitHub Release with all three artefacts. Synced `pyproject.toml` version and added `[project.scripts]` entry point. 95 unit tests.

## Version: 0.9.0
Phase D complete. Added `help` command (F11) with i18n infrastructure (T9). English help texts in `en.json`; empty placeholder files for ru, fa, tr, ar, de. Unsupported/empty languages fall back to English with a notice. 95 unit tests (was 86).

## Version: 0.8.0
Phase C complete. Added `download-media` command (F6). Downloads photo/video/document from a message with `--dest` option. Uses existing telegram-lib `download_media()`. 86 unit tests (was 81).

## Version: 0.7.0
Phase B complete. Added `backup` command (F1) with: cooldown-aware pagination loop (T19), `--estimate` mode using `count_messages` (T10/T20), resumable backup scanning existing output (T22), atomic file writes via temp+rename (T21), structured five-stage progress output (T23), output directory write-permission check (T11), message deduplication and merge. 81 unit tests (was 58).

## Version: 0.6.0
Phase A complete. Added three message commands: `send` (F2), `edit` (F3), `delete` (F4). New subparsers and dispatch in cli.py. 58 unit tests (was 46).

## Version: 0.5.6
Added T22 (resumable backup — scan existing output, download only the diff) and T23 (structured five-stage progress output: start, local scan result, time estimate, progress bar, final report).

## Version: 0.5.5
Added T21 — atomic file writes for crash safety. All data-producing commands write to a temp file first, then rename, so interrupted backups never leave corrupt output files.

## Version: 0.5.4
Expanded `--estimate` requirements with full estimation mechanism: rate-limit-aware duration calculation using `count_messages()` from telegram-lib (F10). Added T19 (cooldown-aware pagination loop for backup), T20 (dependency on telegram-lib `count_messages`). Updated T10 with implementation detail.

## Version: 0.5.3
Eliminated standalone `howlong` command. Its functionality is now the `--estimate` flag on `backup`. Updated README (removed howlong section, added --estimate to backup) and requirements (removed F12, updated F1 signature/arguments/examples, reworded T10).

## Version: 0.5.2
Added DEVELOPMENT.md — developer guide covering executable builds (shiv, PyInstaller, release.yml CI), local dev setup, project structure, testing, quality gate CI, architecture notes (_lib.py adapter, TgResult, config loader, command dispatch), and version management. README.md links to it.

## Version: 0.5.1
Documentation update: README and requirements updated for three distribution variants (Windows .exe, macOS binary, Python .pyz). Command Reference section restructured with uniform pattern — bare syntax, parameters table, and platform-specific call examples for every command. Requirements extended with T16–T18 (CI builds, SmartScreen, Gatekeeper).

## Version: 0.5.0
First functional release. Implements the core CLI framework and five commands:
- `init` — interactive session setup (F10)
- `whoami` — validate session and display user info (F8)
- `ping` — check Telegram availability with latency (F7)
- `get-dialogs` — list dialogs with optional `--limit` and `--outdir` (F5)
- `version` — display CLI and library version as JSON (F9)

Includes config.yaml loader (T1), argparse-based argument parsing (T2), structured error output to stderr (T4), and output directory conflict detection (T14). 46 unit tests.

