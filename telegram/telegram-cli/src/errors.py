"""
Error formatting for telegram-cli (T4).

Translates telegram-lib TgError objects into structured stderr output
and exit codes.
"""

from __future__ import annotations

import sys

# Importing from telegram-lib
_LIB_PATH_SETUP_DONE = False


def _ensure_lib_path() -> None:
    """Ensure telegram-lib's src package is importable."""
    global _LIB_PATH_SETUP_DONE
    if _LIB_PATH_SETUP_DONE:
        return
    from pathlib import Path
    lib_root = Path(__file__).resolve().parents[2] / "telegram-lib"
    if lib_root.exists() and str(lib_root) not in sys.path:
        sys.path.insert(0, str(lib_root))
    _LIB_PATH_SETUP_DONE = True


def format_error_and_exit(error) -> None:
    """Print a TgError to stderr and exit with code 2.

    Format::

        Error [CODE]: message
          retry_after: N   (only for RATE_LIMITED)

    Args:
        error: A TgError instance from telegram-lib.
    """
    line = f"Error [{error.code.value}]: {error.message}"
    print(line, file=sys.stderr)
    if error.retry_after is not None:
        print(f"  retry_after: {int(error.retry_after)}", file=sys.stderr)
    sys.exit(2)
