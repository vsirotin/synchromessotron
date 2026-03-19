#!/usr/bin/env bash
# Build telegram-cli.pyz (cross-platform Python archive).
# Requires: Python >= 3.11, pip, shiv, build.
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

echo "==> Installing shiv and build..."
pip install --quiet shiv build

echo "==> Building telegram-lib wheel..."
mkdir -p dist/wheels
cd "$LIB_DIR"
python -m build --wheel --outdir "$PROJECT_DIR/dist/wheels" .
cd "$PROJECT_DIR"

echo "==> Creating console script wrapper..."
cat > src/_pyz_entry.py << 'EOF'
"""Wrapper to run telegram-cli from pyz."""
from src.cli import main
if __name__ == "__main__":
    main()
EOF

echo "==> Building telegram-cli.pyz..."
mkdir -p dist
shiv -o dist/telegram-cli.pyz --find-links dist/wheels -e src._pyz_entry:main .

echo "==> Done: dist/telegram-cli.pyz"
echo "    Smoke test:  python3 dist/telegram-cli.pyz version"
