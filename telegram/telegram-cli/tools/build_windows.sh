#!/usr/bin/env bash
# Build telegram-cli.exe (Windows, PyInstaller).
# Run on a Windows machine via Git Bash, WSL, or the GitHub Actions runner.
# Requires: Python >= 3.11, pip, PyInstaller, build.
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

# Create an isolated build venv so we never touch the global Python.
BUILD_VENV="$PROJECT_DIR/dist/.build-venv"
if [[ ! -f "$BUILD_VENV/bin/python" ]]; then
    echo "==> Creating build venv at dist/.build-venv ..."
    python3 -m venv "$BUILD_VENV"
fi
PY="$BUILD_VENV/bin/python"
PYINSTALLER="$BUILD_VENV/bin/pyinstaller"

echo "==> Installing PyInstaller, build, and wheel..."
"$PY" -m pip install --quiet pyinstaller build wheel

echo "==> Building telegram-lib wheel..."
mkdir -p dist/wheels
cd "$LIB_DIR"
"$PY" -m build --wheel --outdir "$PROJECT_DIR/dist/wheels" .
cd "$PROJECT_DIR"

echo "==> Installing telegram-lib from wheel..."
"$PY" -m pip install --quiet --find-links dist/wheels telegram-lib

echo "==> Installing telegram-cli..."
"$PY" -m pip install --quiet .

echo "==> Building telegram-cli.exe..."
"$PYINSTALLER" ./telegram-cli.spec

echo "==> Done: dist/telegram-cli.exe"
echo "    Smoke test:  dist\\telegram-cli.exe version"
