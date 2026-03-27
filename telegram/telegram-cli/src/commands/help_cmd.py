"""
Help command (F11) — display multilingual help text.

Loads help text from bundled JSON files (T9). Falls back to English
when the requested language is unavailable or empty.
"""

from __future__ import annotations

import importlib.resources
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger("telegram_cli")

SUPPORTED_LANGS = ("en", "ru", "fa", "tr", "ar", "de")
# Resolve the help_texts directory at import time so it works in all environments:
#   - PyInstaller one-file binary: sys._MEIPASS points to the extracted bundle
#   - Normal install / editable install: relative to this file
import sys as _sys
if hasattr(_sys, "_MEIPASS"):
    _HELP_DIR = Path(_sys._MEIPASS) / "src" / "help_texts"
else:
    _HELP_DIR = Path(__file__).resolve().parent.parent / "help_texts"


def _load_help(lang: str) -> dict:
    """Load help JSON for *lang*, falling back to English.

    Uses importlib.resources so the JSON files are accessible inside a .pyz
    zip archive or a PyInstaller binary — both of which freeze __file__.
    """
    # Try importlib.resources first (works inside .pyz / frozen binaries)
    try:
        pkg = importlib.resources.files("src.help_texts")
        text = (pkg / f"{lang}.json").read_text(encoding="utf-8")
        data = json.loads(text)
        if not data and lang != "en":
            print(f"Notice: Language '{lang}' not yet translated, showing English.", file=sys.stderr)
            return _load_help("en")
        return data
    except (FileNotFoundError, ModuleNotFoundError):
        pass

    # Fallback: filesystem path (editable installs, development)
    path = _HELP_DIR / f"{lang}.json"
    if not path.is_file():
        if lang != "en":
            print(f"Notice: Language '{lang}' not found, falling back to English.", file=sys.stderr)
            return _load_help("en")
        print("Error: Help text file missing.", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error: Cannot read help text: {exc}", file=sys.stderr)
        sys.exit(2)

    # Empty placeholder → fall back to English
    if not data and lang != "en":
        print(f"Notice: Language '{lang}' not yet translated, showing English.", file=sys.stderr)
        return _load_help("en")

    return data


def _print_general(data: dict) -> None:
    """Print the general help overview."""
    gen = data.get("general", {})
    print(gen.get("title", "telegram-cli"))
    print()
    print(gen.get("usage", "Usage: telegram-cli <command> [options]"))
    print()
    print(gen.get("commands_header", "Available commands:"))
    cmds = gen.get("commands", {})
    if cmds:
        max_name = max(len(n) for n in cmds)
        for name, desc in cmds.items():
            print(f"  {name:<{max_name + 2}}{desc}")
    print()
    print(gen.get("footer", ""))


def _print_command(data: dict, command: str) -> None:
    """Print detailed help for a specific command."""
    cmds = data.get("commands", {})
    if command not in cmds:
        print(f"Error: Unknown command '{command}'.", file=sys.stderr)
        sys.exit(1)

    info = cmds[command]
    print(info.get("title", command))
    print()
    print(f"  {info.get('usage', '')}")
    print()
    print(info.get("description", ""))

    args = info.get("arguments")
    if args:
        print()
        print("Arguments:")
        max_name = max(len(n) for n in args)
        for name, desc in args.items():
            print(f"  {name:<{max_name + 2}}{desc}")


def run_help(*, lang: str = "en", command: str | None = None) -> None:
    """Load help text and print to stdout."""
    # Validate lang
    if lang not in SUPPORTED_LANGS:
        print(f"Notice: Unsupported language '{lang}', falling back to English.", file=sys.stderr)
        lang = "en"

    data = _load_help(lang)

    if command:
        _print_command(data, command)
    else:
        _print_general(data)
