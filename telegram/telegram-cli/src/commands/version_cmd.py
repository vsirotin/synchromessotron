"""
Version command (F9) — show CLI and library version info.
"""

from __future__ import annotations

import json

from src.version import get_cli_version
from src._lib import get_lib_version


def run_version() -> None:
    """Print CLI and library version as JSON."""
    cli_ver = get_cli_version()

    lib_result = get_lib_version()
    if lib_result.ok:
        lib_ver = {
            "version": lib_result.payload.version,
            "build": lib_result.payload.build,
            "datetime": lib_result.payload.datetime,
        }
    else:
        lib_ver = {"version": "unknown", "build": 0, "datetime": "unknown"}

    output = {"cli": cli_ver, "lib": lib_ver}
    print(json.dumps(output, indent=2))
