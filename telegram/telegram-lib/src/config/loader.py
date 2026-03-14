"""
Configuration loader for Synchromessotron.

Loads and validates the YAML configuration file.
The config file path can be supplied explicitly or via the
``SYNCHROMESSOTRON_CONFIG`` environment variable.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.config.schema import AppConfig

logger = logging.getLogger(__name__)

_ENV_VAR = "SYNCHROMESSOTRON_CONFIG"
_DEFAULT_PATH = Path(__file__).parent.parent.parent / "config.yaml"


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load and validate the application configuration from a YAML file.

    Priority for the config file path:
    1. The *path* argument (if provided).
    2. The ``SYNCHROMESSOTRON_CONFIG`` environment variable.
    3. ``config.yaml`` in the project root.
    """
    if path is None:
        env_path = os.getenv(_ENV_VAR)
        path = Path(env_path) if env_path else _DEFAULT_PATH

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a YAML mapping, got {type(raw).__name__}")

    try:
        config = AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration:\n{exc}") from exc

    logger.info("Loaded config from %s (%d sync pair(s))", path, len(config.sync_pairs))
    return config
