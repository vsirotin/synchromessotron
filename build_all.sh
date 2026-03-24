#!/bin/bash
#
# Build telegram-cli in all three formats: Python archive (.pyz), Windows binary (.exe), and macOS binary.
# This script is designed for CI/CD pipelines or developers who want to build all variants at once.
#
# Usage:
#   bash build_all.sh
#
# The script will:
#   1. Build the Python archive (.pyz) — works on any OS
#   2. Build the Windows binary (.exe) — may fail gracefully on non-Windows (requires PyInstaller + Windows tools)
#   3. Build the macOS binary — may fail gracefully on non-macOS (requires PyInstaller + code-signing tools)
#
# All artifacts are placed in telegram/telegram-cli/dist/
# Each build is independent — failure of one build does not stop the others.
#

set -e  # Exit on any error in sequence

cd telegram/telegram-cli

echo "================================"
echo "Building telegram-cli (all formats)"
echo "================================"

# Build 1: Python archive (.pyz) — works on any OS
echo ""
echo "[1/3] Building Python archive (.pyz)..."
if bash tools/build_pyz.sh; then
    echo "✓ Python archive (.pyz) built successfully"
else
    echo "✗ Python archive (.pyz) build failed"
    exit 1
fi

# Build 2: Windows binary (.exe) — may fail on non-Windows
echo ""
echo "[2/3] Building Windows binary (.exe)..."
if bash tools/build_windows.sh 2>/dev/null; then
    echo "✓ Windows binary (.exe) built successfully"
else
    echo "⚠ Windows binary (.exe) build skipped or failed (expected on non-Windows platforms)"
fi

# Build 3: macOS binary — may fail on non-macOS
echo ""
echo "[3/3] Building macOS binary..."
if bash tools/build_macos.sh 2>/dev/null; then
    echo "✓ macOS binary built successfully"
else
    echo "⚠ macOS binary build skipped or failed (expected on non-macOS platforms)"
fi

echo ""
echo "================================"
echo "Build Summary"
echo "================================"
echo ""
echo "All available artifacts in dist/:"
ls -lh dist/telegram-cli* 2>/dev/null || echo "(no artifacts found)"
echo ""
echo "Smoke test commands:"
echo "  python3 dist/telegram-cli.pyz version       # Python archive"
echo "  dist/telegram-cli version                    # macOS"
echo "  dist\\telegram-cli.exe version                # Windows"
