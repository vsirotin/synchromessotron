#!/usr/bin/env bash
# Build telegram-cli.pyz (cross-platform Python archive).
# Requires: Python >= 3.11, pip, shiv.
#
# Usage (from telegram/telegram-cli):
#   bash tools/build_pyz.sh
#
# Output: dist/telegram-cli.pyz

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB_DIR="$(cd "$PROJECT_DIR/../telegram-lib" && pwd)"

cd "$PROJECT_DIR"

echo "==> Installing shiv..."
pip install --quiet shiv

echo "==> Installing telegram-lib from $LIB_DIR..."
pip install --quiet "$LIB_DIR"

echo "==> Building telegram-cli.pyz..."
mkdir -p dist
shiv -c telegram-cli -o dist/telegram-cli.pyz .

echo "==> Done: dist/telegram-cli.pyz"
echo "    Smoke test:  python3 dist/telegram-cli.pyz version"
