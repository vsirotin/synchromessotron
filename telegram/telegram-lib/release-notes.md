# Project telegram/telegram-lib. Release notes 

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

