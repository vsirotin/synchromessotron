# Windows Platform Test

Standalone batch script that tests the native `telegram-cli.exe` binary directly — no Python needed.

## Scenarios

| # | Command | Check |
|---|---------|-------|
| 1 | `version` | exit 0, non-empty output |
| 2 | `get-dialogs --limit=50 --outdir` | exit 0, `dialogs.json` created |
| 3 | `backup -4821106881 Feb 2026 --media --files --music --voice --links` | exit 0, dialog dir created |
| 4 | `help` | exit 0, non-empty output |
| 5 | `download-media -4821106881 42389` | exit 0, non-empty output |
| 6 | `send` → extract id → `edit` → `delete` | all exit 0 |

Message ID extraction in Test 6 uses PowerShell's `ConvertFrom-Json` — PowerShell 5+ is included in Windows 10/11.

## Prerequisites

- Built binary at `dist\telegram-cli.exe` (run `tools\build_windows.sh` or `build_all_platform.sh` first)
- `dist\config.yaml` with valid API credentials and Telegram session

## Run

```bat
:: From dist\ (config.yaml must be present there):
cd telegram\telegram-cli\dist
..\tests\post_build\windows_test\windows_test.bat

:: Or with an explicit CLI path:
..\tests\post_build\windows_test\windows_test.bat C:\path\to\telegram-cli.exe
```

## Output

```
==============================================================
telegram-cli Windows platform tests
CLI: ...\dist\telegram-cli.exe
==============================================================

[Test 1] version
[PASS] version  (9 lines)
...
==============================================================
Results:  PASS=10  FAIL=0
==============================================================
```

Exit code `0` = all passed, `1` = at least one failure.
