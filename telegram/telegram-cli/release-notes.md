# Project telegram/telegram-cli. Release notes 

## Version: 1.0.30
Implemented media/file downloading for the backup command: (1) Enabled `ENABLE_MEDIA_DOWNLOADS = True` in `backup.py`; downloads are now active for all flag-selected categories (--media, --files, --music, --voice, --gifs); (2) Updated `_get_media_category()` to use semantic type strings ("photo", "video", "audio", "voice", "gif", "document", "webpage") from telegram-lib 1.2.8, replacing the previous Telethon class-name heuristic that failed to distinguish videos/audio/voice from plain documents; (3) Fixed root cause in telegram-lib 1.2.8: `_to_message_info()` now sets `media_type` to a semantic string by inspecting Telethon `DocumentAttribute*` objects; (4) Fixed download bug in telegram-lib 1.2.8: `download_media()` passed `ids=int` to `get_messages`, causing `'Message' object is not subscriptable` — fixed to `ids=[int]`; (5) Added 2 new check functions to integration test framework: `check_json_all_elements_have_key` and `check_files_referenced_in_json_exist`; (6) Added integration tests 21–25 (TDD): --files downloads 3 documents, --media downloads 94 photos+videos, --music downloads 1 audio file, --voice downloads 2 voice messages, --links creates 24-entry category dir with no file downloads; all 47 checks across 17 tests pass. All 115 unit tests pass.

## Version: 1.0.29
Dependency update: telegram-lib bumped to 1.2.7 (ruff lint fixes in media.py and members.py — no functional change). All 115 unit tests pass.

## Version: 1.0.28
Fixed full-backup slowdown bug where messages after ~100–200 were processed progressively slower: (1) Root cause confirmed: `read_messages()` in telegram-lib used `reverse=True` when a pagination cursor was present, telling Telethon to walk forward (re-fetching the same newest messages). After the dialog had no more "forward" messages, Telegram returned 0–1 boundary messages per API call, draining `remaining` one tick at a time and incurring a rate-limit pause each round; (2) Fixed in telegram-lib 1.2.6: `reverse` is now `False` for pagination so Telethon walks backward (older messages per page); (3) Defensive fix in backup.py pagination loop: `existing_ids` is now updated with each page's collected IDs so boundary-message overlap is deduplicated within a single run; (4) Added regression test `TestPaginationDirection.test_full_backup_paginates_backward_to_older_messages` in test_backup.py; (5) Moved workspace-root `build_all.sh` into `telegram/telegram-cli/tools/build_all_platform.sh` and updated it to resolve its own path so it works when called from any directory; (6) Renamed `telegram-cli-post-task` skill to `telegram-cli-development` and extended it to cover the full development lifecycle (TDD, unit tests, integration tests in `dist/`, build scripts, pre-release gate). All 115 unit tests pass.

## Version: 1.0.27

Fixed critical pagination bug in message backup that prevented downloading more than ~100 messages: (1) Root cause analysis identified dual-mode usage of `read_messages()` function — pagination mode using Telethon's `offset_date` parameter and incremental backup mode using date-based filtering; (2) Telethon's `get_messages(offset_date=date)` includes boundary-date messages in results, but date filter `msg.date <= since` was rejecting them, causing pagination to stall at first page; (3) Solution implemented: Added `for_pagination: bool = False` parameter to `read_messages()` function signature in telegram_lib/messages.py; when True, disables date filtering and lets Telethon handle pagination boundaries correctly; (4) Updated backup.py pagination loop (line 476) to pass `for_pagination=True` when calling `read_messages()` in pagination context; (5) Verified fix: backup with --limit=200 now correctly downloads 3 pages (100 + 99 + 1 = 200 messages) instead of stopping at first page; (6) Issue 1 resolved: pagination continues past 100 messages; (7) Issue 2 status: all downloaded messages properly collected in memory, may require additional investigation of JSON file writing if persistence issue observed; (8) Updated test timeouts (60s → 90s for per-command, 120s → 180s for individual tests) to accommodate actual Telegram API response times; (9) Enhanced integration tests 19-20 to verify pagination works correctly with limit > 199.

## Version: 1.0.26

Implemented media subdirectory organization for backup command media flags: (1) Added `_get_media_category()` function to map Telethon media types (PhotoMedia, DocumentMedia, AudioMedia, etc.) to backup subdirectory categories (media/, files/, music/, voice/, links/, gifs/); (2) Modified `run_backup()` to accept media flags (--media, --files, --music, --voice, --links, --gifs, --members) and build set of enabled_categories; (3) Updated `_async_backup()` function signature to accept enabled_categories parameter and return output_dir instead of output_file; (4) Implemented media organization logic: when media flags are enabled, messages with media are filtered by type and saved to category-specific subdirectories with separate messages.json and messages.md files; (5) Added media_type field to message JSON output and markdown generation to show [MEDIA] indicator for messages with attachments; (6) Updated unit tests to include media_type field in _FakeMessageInfo; (7) Tested with real Telegram data: verified media/ subdirectory created with 10 photo/video messages and links/ subdirectory with 7 web page preview messages. Post-build verification passed for both Python archive and macOS binary.

## Version: 1.0.25

Improved test cleanup and backup command progress output: (1) Added automatic cleanup of test artifacts — integration tests now delete `synchromessotron/` directory before starting, preventing stale data from interfering with results; (2) Fixed progress bar to show 100% completion at end of backup instead of intermediate percentage; (3) Updated final progress message to explicitly mention both `messages.json` and `messages.md` files that are created; (4) Created workspace-level `build_all.sh` script to build all three variants (Python archive, Windows binary, macOS binary) at once; (5) Added documentation in DEVELOPMENT.md section 1.0 describing the build_all.sh workflow for CI/CD and release preparation.

Fixed unit tests for backup command directory structure changes: (1) Added `_FakeDialogInfo` class to mock DialogInfo for testing; (2) Updated `test_backup_to_file`, `test_backup_error`, `test_resumable_skips_existing`, and `test_rate_limit_retry` to mock `get_dialogs` function calls; (3) Updated test assertions to expect files in new `<dialog_name>_<dialog_id>/` directory structure instead of flat backup directory; (4) All unit tests now pass with the new hierarchical directory structure for message backups.

## Version: 1.0.23

Fixed backup command directory structure and file generation per F1 requirements: (1) Created hierarchical directory structure `<dialog_name>_<dialog_id>/` instead of flat structure for message backups; (2) Fetch dialog name asynchronously from Telegram API using `get_dialogs()` to create user-readable directory names; (3) Added `messages.md` markdown file generation alongside `messages.json` for human-readable message backup; (4) Updated `_progress_start()` to include dialog name in progress output; (5) Refactored `_async_backup()` to handle dialog info fetching within async context before pagination; (6) All 10 integration tests now pass (26/26 checks): Tests 1-8 validate command functionality, Tests 9-10 validate F1-compliant directory structure and file generation.

## Version: 1.0.22

Fixed Windows build script venv path issues: (1) Windows venv creates `Scripts/python.exe` (not `bin/python`) and `Scripts/pip`; bash script was hardcoding Unix paths; (2) Added platform detection to both Windows and macOS build scripts: check if `BUILD_VENV/Scripts/` exists to determine Windows vs Unix; (3) Set `PY` variable to correct path based on detection; (4) Changed PyInstaller invocation from `$PYINSTALLER` variable to `$PY -m PyInstaller` which is more portable; (5) Changed venv check from `[[ ! -f "$BUILD_VENV/bin/python" ]]` to `[[ ! -d "$BUILD_VENV" ]]` (simpler and platform-agnostic); (6) GitHub Actions Windows runner with bash now correctly finds Python in venv.

## Version: 1.0.21
Fixed CI/CD pipeline builds for GitHub Actions: (1) Fixed Windows build script using non-existent `.build-venv/bin/pip` path on Windows; changed to `$PY -m pip` which works on all platforms (Windows, macOS, Linux); (2) Added CI/CD mode detection to post-build verification: detect `CI` or `GITHUB_ACTIONS` environment variables; (3) In CI/CD mode, allow `.pyz` (cross-platform) to pass without requiring platform-specific binary; in developer mode, require platform binary to catch environment issues early; (4) Updated build scripts (Windows, macOS) to use `$PY -m pip` consistently instead of separate `$PIP` variable; (5) Fixed venv path issues in WSL/bash by using Python module invocation rather than direct pip executable lookup. All three GitHub Actions jobs (.pyz on Linux, .exe on Windows, native binary on macOS) now succeed.

## Version: 1.0.20
Enhanced post-build verification and created telegram-cli-post-task skill: (1) Refactored `run_post_build_test.py` to distinguish between CI/CD (any executable OK) and developer machine (platform binary required); (2) Added `get_all_cli_executables()` return value to track whether platform-specific binary exists; (3) Implemented `rebuild_platform_binary()` method that automatically rebuilds missing developer platform executable (macOS/Windows) via corresponding build script; (4) Main test runner now attempts auto-rebuild when platform binary missing, supporting rapid local development iteration; (5) Created `telegram-cli-post-task` skill with `.instructions.md` activation file for pre-release verification (unit tests + post-build checks) before workspace post-task; (6) Skill runs automatically when changes affect `telegram/telegram-cli/` code or tests, collecting results and proceeding regardless of test status.

## Version: 1.0.19
Fixed PyInstaller data files bundling: (1) Added `datas` parameter to `telegram-cli.spec` to explicitly include version.yaml files from both `src` and `telegram_lib` packages; (2) Previous fix only added `telegram_lib` to `hiddenimports`, which includes Python modules but NOT data files; (3) Used `Path(__file__).parent` and relative paths to dynamically construct paths to version.yaml files; (4) PyInstaller now correctly bundles version.yaml files into the macOS and Windows executables at runtime. Version output now returns correct semantic version (e.g., 1.0.19) instead of "unknown".

## Version: 1.0.18
Fixed PyInstaller spec file path in build scripts: Changed relative path from `../telegram-cli.spec` to `./telegram-cli.spec` in both `build_macos.sh` and `build_windows.sh`. The incorrect path caused build failures with "Spec file not found" when scripts ran from the project root directory. This was not caught locally because build scripts were not executed during development.

## Version: 1.0.17
Fixed PyInstaller bundling of telegram_lib: (1) Added `'telegram_lib'` to `hiddenimports` in `telegram-cli.spec`; (2) Updated `build_macos.sh` and `build_windows.sh` to use `telegram-cli.spec` instead of command-line PyInstaller invocation; (3) PyInstaller now includes the telegram_lib package when building .exe and macOS binaries, fixing "ModuleNotFoundError: No module named 'telegram_lib'" runtime errors; (4) Version output now works correctly in all distributed formats (.pyz, .exe, .bin). Created `telegram-cli-post-task` skill for pre-release verification (unit tests + post-build checks). Updated `release.yml` workflow labels from "Post-build integration tests" to "Post-build tests".

## Version: 1.0.16
Fixed post-build build verification: (1) Refactored `run_post_build_test.py` from attempting to run integration tests to quick build verification via `version` subcommand; (2) Added semantic version pattern regex to validate version output; (3) Now correctly tests each executable (.pyz, .exe, .bin) by running `<executable> version` and checking for valid version output (X.Y.Z format); (4) Full integration tests with config.yaml remain separate in `integration_test.py` and run via `run_integration_tests.py`; (5) Removed unused `integration_test_module` reference and PYTHONPATH configuration; (6) Simplified main() output to focus on executable build verification status rather than parsing test statistics.

## Version: 1.0.15
Fixed post-build error detection: (1) Added `result.returncode` check in `run_tests()` method to catch subprocess failures; (2) When subprocess fails (including module import errors), RuntimeError is raised and propagates to main(), exiting with code 2; (3) Previously, subprocess failures were silently swallowed and treat as "no tests executed", causing GitHub Actions to show green instead of red. Now CI/CD workflow correctly fails when executable build verification encounters errors. Also upgraded `dorny/paths-filter@v3` to `@v4` to fix Node.js 20 deprecation warning.

## Version: 1.0.14
Fixed post-build test Unicode encoding error on Windows CI/CD: Wrapped stdout with UTF-8 encoding to handle Unicode characters (⚠, ✓, ✗) on systems using cp1252 default encoding. Windows platform no longer fails with "UnicodeEncodeError: 'charmap' codec can't encode character" when running post-build integration tests.

## Version: 1.0.13
Fixed pytest test discovery error: (1) Updated `pyproject.toml` to restrict pytest `testpaths` from `tests/` to `tests/unit/` only; (2) Added explicit `python_files` and `python_functions` patterns to prevent pytest from discovering integration test module functions as test fixtures; (3) CI/CD no longer fails with "fixture 'cli' not found" error when running quality-gate workflow. Integration tests remain in `tests/post_build/` and are executed via custom runners (`run_integration_tests.py`, `run_post_build_test.py`), not pytest.

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

