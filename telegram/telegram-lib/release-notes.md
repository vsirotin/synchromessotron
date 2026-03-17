# Project telegram/telegram-lib. Release notes 

## Version: 1.0.0 
Initial development

## Version: 1.1.0
Refactored code and tests to comply with development skills:
- Fixed bug: `check_availability` was setting both payload and error simultaneously, violating TgResult contract.
- Added error documentation (possible TgError codes) to all public function docstrings.
- Added logging to `create_client()`.
- Renamed all test functions to follow `test_<subject>_<aspect>` convention.
- Split monolithic `test_telegram.py` into per-module test files.
- Added comprehensive test coverage: timeout, connection failure, permission denied, rate limit, and session validation tests.
- Test count increased from 14 to 41.

