"""
Error formatting for telegram-cli (T4).

Translates telegram-lib TgError objects into structured stderr output
and exit codes.
"""

from __future__ import annotations

import sys


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
