"""
Version information for telegram-cli (F9).

Returns the CLI's version, build number, and build timestamp
by reading ``src/version.yaml``.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("telegram_cli")

_VERSION_FILE = Path(__file__).parent / "version.yaml"


def get_cli_version() -> dict[str, str | int]:
    """Return the CLI version information as a dict.

    Reads ``src/version.yaml`` and returns its content.

    Returns:
        Dict with keys: version, build, datetime.

    Raises:
        No exceptions — returns a fallback dict on read errors.
    """
    logger.debug("[get_cli_version] reading %s", _VERSION_FILE)
    try:
        text = _VERSION_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("[get_cli_version] cannot read version file: %s", exc)
        return {"version": "unknown", "build": 0, "datetime": "unknown"}

    data: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        data[key.strip()] = value.strip()

    return {
        "version": data.get("version", "unknown"),
        "build": int(data.get("build", "0")),
        "datetime": data.get("datetime", "unknown"),
    }
