#!/usr/bin/env bash
# Build telegram-cli.exe (Windows, PyInstaller).
# Run on a Windows machine via Git Bash, WSL, or the GitHub Actions runner.
# Requires: Python >= 3.11, pip, PyInstaller.
#
# Usage (from telegram/telegram-cli):
#   bash tools/build_windows.sh
#
# Output: dist/telegram-cli.exe

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB_DIR="$(cd "$PROJECT_DIR/../telegram-lib" && pwd)"

cd "$PROJECT_DIR"

echo "==> Installing PyInstaller..."
pip install --quiet pyinstaller

echo "==> Installing telegram-lib from $LIB_DIR..."
pip install --quiet "$LIB_DIR"

echo "==> Installing telegram-cli..."
pip install --quiet .

echo "==> Building telegram-cli.exe..."
pyinstaller --onefile --name telegram-cli src/__main__.py

echo "==> Done: dist/telegram-cli.exe"
echo "    Smoke test:  dist\\telegram-cli.exe version"
