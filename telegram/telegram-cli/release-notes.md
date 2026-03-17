# Project telegram/telegram-cli. Release notes 

## Version: 1.0.0 
Initial development

## Version: 0.5.0
First functional release. Implements the core CLI framework and five commands:
- `init` — interactive session setup (F10)
- `whoami` — validate session and display user info (F8)
- `ping` — check Telegram availability with latency (F7)
- `get-dialogs` — list dialogs with optional `--limit` and `--outdir` (F5)
- `version` — display CLI and library version as JSON (F9)

Includes config.yaml loader (T1), argparse-based argument parsing (T2), structured error output to stderr (T4), and output directory conflict detection (T14). 46 unit tests.

