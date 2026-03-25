# Project telegram/telegram-lib. Release notes 

## Version: 1.2.6
Fixed critical full-backup slowdown: `read_messages()` was calling Telethon with `reverse=True` when a pagination cursor (`since`) was set, causing it to walk **forward** in time (re-fetching the same newest messages on every page after page 1). Fixed by changing the direction expression to `reverse = not for_pagination and since is not None` so that pagination always walks backward (older messages per page) while incremental backup continues to walk forward. Added regression test `test_read_messages_for_pagination_uses_backward_direction` that directly asserts Telethon is called with `reverse=False` for `for_pagination=True`. All 24 tests pass.

## Version: 1.2.5
Enhanced `read_messages()` function to support dual-mode operation for pagination and incremental backup: (1) Added `for_pagination: bool = False` parameter to function signature; (2) When `for_pagination=True`, date filtering is disabled, allowing Telethon's `offset_date` parameter to properly handle message boundary dates according to Telegram API behavior; (3) When `for_pagination=False` (incremental backup mode), date filtering `msg.date <= since` is applied as before; (4) This fix resolves pagination issue where Telethon's `get_messages(offset_date=date, reverse=True)` returns messages INCLUDING the boundary date, but the filter was rejecting them, causing pagination to stall; (5) Backward compatible: existing callers not using pagination continue to work with default `for_pagination=False`; (6) Verified with backup command: --limit=200 now downloads 3 pages (100 + 99 + 1 messages) instead of stopping at first page; (7) Updated function docstring to explain dual-mode behavior and difference between pagination and incremental backup modes.

## Version: 1.2.4
Updated workspace pyproject.toml configuration: added `[tool.workspace.projects]` section to track sub-project dependencies (telegram-lib, telegram-cli), cleaned up outdated root-level dependencies (firebase-admin, pydantic, Telethon, vk_api), and updated ruff configuration. Enhanced post-task skill to use workspace configuration for dependency discovery. All 51 tests pass.

## Version: 1.2.3
Renamed Python package from `src` to `telegram_lib` to eliminate namespace collision with telegram-cli when bundled together in a shiv `.pyz` archive. Updated all internal imports, test patch paths, and pyproject.toml package discovery. Added `package-data` config to include `version.yaml` in the built wheel. No public API changes.

## Version: 1.2.2
Fixed 14 ruff lint errors and 6 black formatting issues. Changes: sorted imports (`__init__.py`, `version.py`, test files), removed unused imports (`patch` in test_client, `Path`/`PropertyMock` in test_media, `pytest` in test_version), wrapped long lines in `dialogs.py`, migrated `ErrorCode` from `(str, Enum)` to `StrEnum`. All 51 tests pass.

## Version: 1.2.1
Added F10 requirement: `count_messages()` — lightweight metadata query to count messages in a dialog without downloading content. Needed by telegram-cli `--estimate` to predict backup duration.

## Version: 1.2.0
Added version information function (F9):
- New `get_version()` function that reads `src/version.yaml` and returns a `VersionInfo` DTO.
- New `VersionInfo` model added to `models.py`.
- 4 unit tests covering happy path, missing file, malformed YAML, and missing keys.
- Added F9 requirement to telegram-lib-requirements.md and telegram-cli-requirements.md.
- Test count increased from 41 to 45.

## Version: 1.1.0
Refactored code and tests to comply with development skills:
- Fixed bug: `check_availability` was setting both payload and error simultaneously, violating TgResult contract.
- Added error documentation (possible TgError codes) to all public function docstrings.
- Added logging to `create_client()`.
- Renamed all test functions to follow `test_<subject>_<aspect>` convention.
- Split monolithic `test_telegram.py` into per-module test files.
- Added comprehensive test coverage: timeout, connection failure, permission denied, rate limit, and session validation tests.
- Test count increased from 14 to 41.

## Version: 1.0.0 
Initial development

