"""
CLI argument parser and command dispatch for telegram-cli (T2).

Defines the argparse subcommands and dispatches to the appropriate
command handler.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse parser with all subcommands."""
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

    # send (F2)
    sp = subparsers.add_parser("send", help="Send a text message")
    sp.add_argument("dialog_id", type=int, help="Target dialog ID")
    sp.add_argument("--text", type=str, required=True, help="Message text to send")

    # edit (F3)
    ep = subparsers.add_parser("edit", help="Edit a previously sent message")
    ep.add_argument("dialog_id", type=int, help="Dialog containing the message")
    ep.add_argument("message_id", type=int, help="ID of the message to edit")
    ep.add_argument("--text", type=str, required=True, help="Replacement text")

    # delete (F4)
    dp = subparsers.add_parser("delete", help="Delete own messages")
    dp.add_argument("dialog_id", type=int, help="Dialog containing the messages")
    dp.add_argument("message_ids", type=int, nargs="+", help="IDs of messages to delete")

    # backup (F1)
    bp = subparsers.add_parser("backup", help="Backup message history from a dialog")
    bp.add_argument("dialog_id", type=int, help="Numeric dialog ID")
    bp.add_argument("--since", type=str, default=None, help="ISO 8601 timestamp for incremental backup")
    bp.add_argument("--limit", type=int, default=100, help="Maximum messages to retrieve (default: 100)")
    bp.add_argument("--outdir", type=str, default=None, help="Root output directory (default: ./synchromessotron)")
    bp.add_argument("--media", action="store_true", help="Also download photos and videos")
    bp.add_argument("--files", action="store_true", help="Also download documents and file attachments")
    bp.add_argument("--music", action="store_true", help="Also download audio tracks")
    bp.add_argument("--voice", action="store_true", help="Also download voice messages")
    bp.add_argument("--links", action="store_true", help="Also save link previews and URLs")
    bp.add_argument("--gifs", action="store_true", help="Also download GIF animations")
    bp.add_argument("--members", action="store_true", help="Also save dialog participant list")
    bp.add_argument("--estimate", action="store_true", help="Print time estimate and exit")

    # download-media (F6)
    dm = subparsers.add_parser("download-media", help="Download media from a message")
    dm.add_argument("dialog_id", type=int, help="Dialog containing the message")
    dm.add_argument("message_id", type=int, help="ID of the message with media")
    dm.add_argument("--dest", type=str, default=".", help="Target directory (default: current)")

    # help (F11)
    hp = subparsers.add_parser("help", help="Show help text")
    hp.add_argument("help_args", nargs="*", help="[LANG] [COMMAND]")

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
    elif args.command == "send":
        from src.commands.send import run_send
        run_send(dialog_id=args.dialog_id, text=args.text)
    elif args.command == "edit":
        from src.commands.edit import run_edit
        run_edit(dialog_id=args.dialog_id, message_id=args.message_id, text=args.text)
    elif args.command == "delete":
        from src.commands.delete import run_delete
        run_delete(dialog_id=args.dialog_id, message_ids=args.message_ids)
    elif args.command == "backup":
        from src.commands.backup import run_backup
        run_backup(
            dialog_id=args.dialog_id,
            since=args.since,
            limit=args.limit,
            outdir=args.outdir,
            media=args.media,
            files=args.files,
            music=args.music,
            voice=args.voice,
            links=args.links,
            gifs=args.gifs,
            members=args.members,
            estimate=args.estimate,
        )
    elif args.command == "download-media":
        from src.commands.download_media import run_download_media
        run_download_media(dialog_id=args.dialog_id, message_id=args.message_id, dest=args.dest)
    elif args.command == "help":
        from src.commands.help_cmd import run_help, SUPPORTED_LANGS
        lang = "en"
        command = None
        for arg in (args.help_args or []):
            if arg in SUPPORTED_LANGS:
                lang = arg
            else:
                command = arg
        run_help(lang=lang, command=command)
    elif args.command == "version":
        from src.commands.version_cmd import run_version
        run_version()
    else:
        parser.print_help()
        sys.exit(1)
