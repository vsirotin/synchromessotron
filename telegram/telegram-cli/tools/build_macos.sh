#!/usr/bin/env bash
# Build telegram-cli-macos.zip (macOS, PyInstaller).
# Run on a macOS machine. Requires: Python >= 3.11, pip, PyInstaller, build.
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

echo "==> Installing PyInstaller, build, and wheel..."
pip install --quiet pyinstaller build wheel

echo "==> Building telegram-lib wheel..."
mkdir -p dist/wheels
cd "$LIB_DIR"
python -m build --wheel --outdir "$PROJECT_DIR/dist/wheels" .
cd "$PROJECT_DIR"

echo "==> Installing telegram-lib from wheel..."
pip install --quiet --no-index --find-links dist/wheels telegram-lib

echo "==> Installing telegram-cli..."
pip install --quiet .

echo "==> Building telegram-cli binary..."
pyinstaller ./telegram-cli.spec

echo "==> Packaging as zip..."
cd dist
zip telegram-cli-macos.zip telegram-cli

echo "==> Done: dist/telegram-cli-macos.zip"
echo "    Smoke test:  dist/telegram-cli version"
