# macOS Platform Test

Standalone shell script that tests the native `telegram-cli` binary directly — no Python needed.

## Scenarios

| # | Command | Check |
|---|---------|-------|
| 1 | `version` | exit 0, non-empty output |
| 2 | `get-dialogs --limit=50 --outdir` | exit 0, `dialogs.json` created |
| 3 | `backup -4821106881 Feb 2026 --media --files --music --voice --links` | exit 0, dialog dir created |
| 4 | `help` | exit 0, non-empty output |
| 5 | `download-media -4821106881 42389` | exit 0, non-empty output |
| 6 | `send` → extract id → `edit` → `delete` | all exit 0 |

## Prerequisites

- Built binary at `dist/telegram-cli` (run `bash tools/build_macos.sh` or `build_all_platform.sh` first)
- `dist/config.yaml` with valid API credentials and Telegram session

## Run

```bash
# From dist/ (config.yaml must be present there):
cd telegram/telegram-cli/dist
bash ../tests/post_build/macos_test/macos_test.sh

# Or with an explicit CLI path:
bash ../tests/post_build/macos_test/macos_test.sh /path/to/telegram-cli
```

## Output

```
============================================================
telegram-cli macOS platform tests
CLI:  .../dist/telegram-cli
============================================================

[Test 1] version
[PASS] version  (9 lines)
...
============================================================
Results:  PASS=10   FAIL=0
============================================================
```

Exit code `0` = all passed, `1` = at least one failure.
