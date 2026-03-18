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

## Version: 0.5.1
Documentation update: README and requirements updated for three distribution variants (Windows .exe, macOS binary, Python .pyz). Command Reference section restructured with uniform pattern — bare syntax, parameters table, and platform-specific call examples for every command. Requirements extended with T16–T18 (CI builds, SmartScreen, Gatekeeper).

## Version: 0.5.2
Added DEVELOPMENT.md — developer guide covering executable builds (shiv, PyInstaller, release.yml CI), local dev setup, project structure, testing, quality gate CI, architecture notes (_lib.py adapter, TgResult, config loader, command dispatch), and version management. README.md links to it.

## Version: 0.5.3
Eliminated standalone `howlong` command. Its functionality is now the `--estimate` flag on `backup`. Updated README (removed howlong section, added --estimate to backup) and requirements (removed F12, updated F1 signature/arguments/examples, reworded T10).

## Version: 0.5.4
Expanded `--estimate` requirements with full estimation mechanism: rate-limit-aware duration calculation using `count_messages()` from telegram-lib (F10). Added T19 (cooldown-aware pagination loop for backup), T20 (dependency on telegram-lib `count_messages`). Updated T10 with implementation detail.

