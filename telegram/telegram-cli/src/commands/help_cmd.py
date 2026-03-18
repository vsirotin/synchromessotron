"""
Help command (F11) — display multilingual help text.

Loads help text from bundled JSON files (T9). Falls back to English
when the requested language is unavailable or empty.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger("telegram_cli")

SUPPORTED_LANGS = ("en", "ru", "fa", "tr", "ar", "de")
_HELP_DIR = Path(__file__).resolve().parent.parent / "help_texts"


def _load_help(lang: str) -> dict:
    """Load help JSON for *lang*, falling back to English."""
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
