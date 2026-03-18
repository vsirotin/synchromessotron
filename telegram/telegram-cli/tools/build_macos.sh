#!/usr/bin/env bash
# Build telegram-cli-macos.zip (macOS, PyInstaller).
# Run on a macOS machine. Requires: Python >= 3.11, pip, PyInstaller.
#
# Usage (from telegram/telegram-cli):
#   bash tools/build_macos.sh
#
# Output: dist/telegram-cli-macos.zip (contains the extensionless binary)

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

echo "==> Building telegram-cli binary..."
pyinstaller --onefile --name telegram-cli src/__main__.py

echo "==> Packaging as zip..."
cd dist
zip telegram-cli-macos.zip telegram-cli

echo "==> Done: dist/telegram-cli-macos.zip"
echo "    Smoke test:  dist/telegram-cli version"
