"""
CLI argument parser and command dispatch for telegram-cli (T2).

Defines the argparse subcommands and dispatches to the appropriate
command handler.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse parser with all v0.5.0 subcommands."""
    parser = argparse.ArgumentParser(
        prog="telegram-cli",
        description="Command-line interface for Telegram.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    subparsers.add_parser("init", help="Set up credentials and session")

    # whoami
    subparsers.add_parser("whoami", help="Validate session and show user info")

    # ping
    subparsers.add_parser("ping", help="Check Telegram availability")

    # get-dialogs
    gd = subparsers.add_parser("get-dialogs", help="List the user's dialogs")
    gd.add_argument("--limit", type=int, default=None, help="Maximum number of dialogs to return")
    gd.add_argument("--outdir", type=str, default=None, help="Save dialogs.json to this directory")

    # version
    subparsers.add_parser("version", help="Show version information")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate command handler."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        from src.commands.init_cmd import run_init
        run_init()
    elif args.command == "whoami":
        from src.commands.whoami import run_whoami
        run_whoami()
    elif args.command == "ping":
        from src.commands.ping import run_ping
        run_ping()
    elif args.command == "get-dialogs":
        from src.commands.get_dialogs import run_get_dialogs
        run_get_dialogs(limit=args.limit, outdir=args.outdir)
    elif args.command == "version":
        from src.commands.version_cmd import run_version
        run_version()
    else:
        parser.print_help()
        sys.exit(1)
