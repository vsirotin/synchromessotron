#!/usr/bin/env bash
# Build telegram-cli.pyz (cross-platform Python archive).
# Requires: Python >= 3.11.
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

# Create an isolated build venv so we never touch the global Python.
BUILD_VENV="$PROJECT_DIR/dist/.build-venv"
if [[ ! -f "$BUILD_VENV/bin/python" ]]; then
    echo "==> Creating build venv at dist/.build-venv ..."
    python3 -m venv "$BUILD_VENV"
fi
PY="$BUILD_VENV/bin/python"
PIP="$BUILD_VENV/bin/pip"
SHIV="$BUILD_VENV/bin/shiv"

echo "==> Installing shiv and build into build venv..."
"$PIP" install --quiet shiv build

echo "==> Building telegram-lib wheel..."
mkdir -p dist/wheels
cd "$LIB_DIR"
"$PY" -m build --wheel --outdir "$PROJECT_DIR/dist/wheels" .
cd "$PROJECT_DIR"

echo "==> Installing telegram-lib from wheel into build venv..."
"$PIP" install --quiet --force-reinstall --find-links dist/wheels telegram-lib

echo "==> Building telegram-cli.pyz..."
mkdir -p dist
"$SHIV" -o dist/telegram-cli.pyz --find-links dist/wheels -e src.cli:main .

echo "==> Done: dist/telegram-cli.pyz"
echo "    Smoke test:  python3 dist/telegram-cli.pyz version"
