"""
Version information function (F9).

Returns the library's version, build number, and build timestamp
by reading ``src/version.yaml``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from telegram_lib.models import ErrorCode, TgError, TgResult, VersionInfo

logger = logging.getLogger("telegram_lib")

_VERSION_FILE = Path(__file__).parent / "version.yaml"


def get_version() -> TgResult[VersionInfo]:
    """Return the library version information (F9).

    Reads ``src/version.yaml`` and returns its content as a
    ``VersionInfo`` object.

    This is a **synchronous** function — no network call is needed.

    Returns:
        ``TgResult`` whose payload is a ``VersionInfo``.

    Possible errors (``TgResult.error``):
        - ``INTERNAL_ERROR`` — the version file is missing or malformed.
    """
    logger.debug("[get_version] reading %s", _VERSION_FILE)
    try:
        text = _VERSION_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("[get_version] cannot read version file: %s", exc)
        return TgResult(error=TgError(ErrorCode.INTERNAL_ERROR, f"Cannot read version file: {exc}"))

    try:
        data: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition(":")
            if not _:
                raise ValueError(f"Malformed line: {line!r}")
            data[key.strip()] = value.strip()

        version = data["version"]
        build = int(data["build"])
        dt = data["datetime"]
    except (KeyError, ValueError) as exc:
        logger.error("[get_version] malformed version file: %s", exc)
        return TgResult(error=TgError(ErrorCode.INTERNAL_ERROR, f"Malformed version file: {exc}"))

    info = VersionInfo(version=version, build=build, datetime=dt)
    logger.debug("[get_version] %s", info)
    return TgResult(payload=info)
