"""
Configuration loader for telegram-cli (T1).

Loads credentials and settings from ``config.yaml`` located next to the
executable.  The file has a ``telegram`` section with api_id, api_hash,
phone, session, and optional output_dir / split_threshold.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("telegram_cli")


def _find_config_file() -> Path:
    """Return the path to config.yaml next to the running script/pyz."""
    return Path.cwd() / "config.yaml"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and return the ``telegram`` section from config.yaml.

    Args:
        config_path: Explicit path to config.yaml. If None, searches
            in the current working directory.

    Returns:
        Dict with keys: api_id, api_hash, phone, session, and optionally
        output_dir and split_threshold.

    Raises:
        SystemExit: If the file is missing, unreadable, or malformed.
    """
    path = config_path or _find_config_file()
    logger.debug("[load_config] loading %s", path)

    if not path.exists():
        _config_error(f"Config file not found: {path}\nRun 'telegram-cli init' to create one.")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _config_error(f"Cannot read config file: {exc}")

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        _config_error(f"Invalid YAML in config file: {exc}")

    if not isinstance(data, dict) or "telegram" not in data:
        _config_error("Config file must contain a 'telegram' section.")

    tg = data["telegram"]
    if not isinstance(tg, dict):
        _config_error("The 'telegram' section must be a mapping.")

    for key in ("api_id", "api_hash", "phone", "session"):
        if key not in tg:
            _config_error(f"Missing required field: telegram.{key}")

    tg["api_id"] = int(tg["api_id"])
    return tg


def save_config(config: dict[str, Any], config_path: Path | None = None) -> None:
    """Write a config dict to config.yaml.

    Args:
        config: The telegram section content.
        config_path: Explicit path. Defaults to cwd/config.yaml.
    """
    path = config_path or _find_config_file()
    data = {"telegram": config}
    try:
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    except OSError as exc:
        import sys
        print(f"Error: Cannot write config file: {exc}", file=sys.stderr)
        sys.exit(1)
    logger.debug("[save_config] saved to %s", path)


def resolve_outdir(cli_outdir: str | None, config: dict[str, Any]) -> Path | None:
    """Resolve the output directory from CLI flag and config (T14).

    Args:
        cli_outdir: Value of --outdir from command line, or None.
        config: Loaded config dict.

    Returns:
        Resolved Path, or None if neither is set.

    Raises:
        SystemExit: If both are set and differ (T14 conflict rule).
    """
    config_dir = config.get("output_dir")

    if cli_outdir and config_dir:
        cli_path = Path(cli_outdir).resolve()
        cfg_path = Path(config_dir).resolve()
        if cli_path != cfg_path:
            import sys
            print(
                f"Error: --outdir ({cli_outdir}) conflicts with output_dir "
                f"in config.yaml ({config_dir}). Remove one to resolve.",
                file=sys.stderr,
            )
            sys.exit(1)
        return cli_path

    if cli_outdir:
        return Path(cli_outdir).resolve()
    if config_dir:
        return Path(config_dir).resolve()
    return None


def _config_error(message: str) -> None:
    """Print a config error to stderr and exit with code 1."""
    import sys
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)
