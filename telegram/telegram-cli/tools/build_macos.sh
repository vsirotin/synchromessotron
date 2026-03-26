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

# Create an isolated build venv so we never touch the global Python.
BUILD_VENV="$PROJECT_DIR/dist/.build-venv"
if [[ ! -d "$BUILD_VENV" ]]; then
    echo "==> Creating build venv at dist/.build-venv ..."
    python3 -m venv "$BUILD_VENV"
fi

# Detect Windows vs Unix venv structure
if [[ -d "$BUILD_VENV/Scripts" ]]; then
    # Windows
    PY="$BUILD_VENV/Scripts/python.exe"
else
    # Unix/Linux/macOS
    PY="$BUILD_VENV/bin/python"
fi

echo "==> Installing PyInstaller, build, and wheel..."
"$PY" -m pip install --quiet pyinstaller build wheel

echo "==> Building telegram-lib wheel..."
mkdir -p dist/wheels
cd "$LIB_DIR"
"$PY" -m build --wheel --outdir "$PROJECT_DIR/dist/wheels" .
cd "$PROJECT_DIR"

echo "==> Installing telegram-lib from wheel..."
"$PY" -m pip install --quiet --force-reinstall --find-links dist/wheels telegram-lib

echo "==> Installing telegram-cli..."
"$PY" -m pip install --quiet .

echo "==> Building telegram-cli binary..."
"$PY" -m PyInstaller ./telegram-cli.spec

echo "==> Packaging as zip..."
cd dist
zip telegram-cli-macos.zip telegram-cli

echo "==> Done: dist/telegram-cli-macos.zip"
echo "    Smoke test:  dist/telegram-cli version"
