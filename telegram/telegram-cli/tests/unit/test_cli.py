"""
Unit tests for src/cli.py — argument parsing and dispatch.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_cli_root = Path(__file__).resolve().parents[3]
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))

from src.cli import build_parser, main


class TestBuildParser:
    """Tests for build_parser()."""

    def test_parser_init(self):
        """Parser recognises 'init' subcommand."""
        parser = build_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"

    def test_parser_whoami(self):
        """Parser recognises 'whoami' subcommand."""
        parser = build_parser()
        args = parser.parse_args(["whoami"])
        assert args.command == "whoami"

    def test_parser_ping(self):
        """Parser recognises 'ping' subcommand."""
        parser = build_parser()
        args = parser.parse_args(["ping"])
        assert args.command == "ping"

    def test_parser_version(self):
        """Parser recognises 'version' subcommand."""
        parser = build_parser()
        args = parser.parse_args(["version"])
        assert args.command == "version"

    def test_parser_get_dialogs(self):
        """Parser recognises 'get-dialogs' with flags."""
        parser = build_parser()
        args = parser.parse_args(["get-dialogs", "--limit=50", "--outdir=/tmp/out"])
        assert args.command == "get-dialogs"
        assert args.limit == 50
        assert args.outdir == "/tmp/out"

    def test_parser_get_dialogs_defaults(self):
        """get-dialogs defaults: limit=None, outdir=None."""
        parser = build_parser()
        args = parser.parse_args(["get-dialogs"])
        assert args.limit is None
        assert args.outdir is None

    def test_parser_send(self):
        """Parser recognises 'send' with dialog_id and --text."""
        parser = build_parser()
        args = parser.parse_args(["send", "123", "--text=Hello"])
        assert args.command == "send"
        assert args.dialog_id == 123
        assert args.text == "Hello"

    def test_parser_edit(self):
        """Parser recognises 'edit' with dialog_id, message_id, --text."""
        parser = build_parser()
        args = parser.parse_args(["edit", "100", "55", "--text=Updated"])
        assert args.command == "edit"
        assert args.dialog_id == 100
        assert args.message_id == 55
        assert args.text == "Updated"

    def test_parser_delete(self):
        """Parser recognises 'delete' with dialog_id and message_ids."""
        parser = build_parser()
        args = parser.parse_args(["delete", "100", "10", "11", "12"])
        assert args.command == "delete"
        assert args.dialog_id == 100
        assert args.message_ids == [10, 11, 12]

    def test_parser_backup(self):
        """Parser recognises 'backup' with all flags."""
        parser = build_parser()
        args = parser.parse_args([
            "backup", "100", "--since=2026-03-01T00:00:00",
            "--limit=500", "--output=out.json", "--estimate",
        ])
        assert args.command == "backup"
        assert args.dialog_id == 100
        assert args.since == "2026-03-01T00:00:00"
        assert args.limit == 500
        assert args.output == "out.json"
        assert args.estimate is True

    def test_parser_backup_defaults(self):
        """Backup defaults: limit=100, rest None/False."""
        parser = build_parser()
        args = parser.parse_args(["backup", "100"])
        assert args.limit == 100
        assert args.since is None
        assert args.output is None
        assert args.estimate is False

    def test_parser_download_media(self):
        """Parser recognises 'download-media' with args."""
        parser = build_parser()
        args = parser.parse_args(["download-media", "100", "42", "--dest=./dl"])
        assert args.command == "download-media"
        assert args.dialog_id == 100
        assert args.message_id == 42
        assert args.dest == "./dl"

    def test_parser_download_media_defaults(self):
        """download-media defaults: dest='.'."""
        parser = build_parser()
        args = parser.parse_args(["download-media", "100", "42"])
        assert args.dest == "."

    def test_parser_help(self):
        """Parser recognises 'help' with optional args."""
        parser = build_parser()
        args = parser.parse_args(["help", "de", "backup"])
        assert args.command == "help"
        assert args.help_args == ["de", "backup"]

    def test_parser_help_no_args(self):
        """Help with no args gives empty list."""
        parser = build_parser()
        args = parser.parse_args(["help"])
        assert args.help_args == []


class TestMain:
    """Tests for main() dispatch."""

    def test_main_no_cmd(self):
        """No command prints help and exits 1."""
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1

    def test_main_version(self):
        """'version' dispatches to run_version."""
        with patch("src.commands.version_cmd.run_version") as mock_ver:
            main(["version"])
            mock_ver.assert_called_once()

    def test_main_init(self):
        """'init' dispatches to run_init."""
        with patch("src.commands.init_cmd.run_init") as mock_init:
            main(["init"])
            mock_init.assert_called_once()

    def test_main_whoami(self):
        """'whoami' dispatches to run_whoami."""
        with patch("src.commands.whoami.run_whoami") as mock_wh:
            main(["whoami"])
            mock_wh.assert_called_once()

    def test_main_ping(self):
        """'ping' dispatches to run_ping."""
        with patch("src.commands.ping.run_ping") as mock_p:
            main(["ping"])
            mock_p.assert_called_once()

    def test_main_get_dialogs(self):
        """'get-dialogs' dispatches to run_get_dialogs with parsed flags."""
        with patch("src.commands.get_dialogs.run_get_dialogs") as mock_gd:
            main(["get-dialogs", "--limit=20", "--outdir=/tmp/x"])
            mock_gd.assert_called_once_with(limit=20, outdir="/tmp/x")

    def test_main_send(self):
        """'send' dispatches to run_send with parsed args."""
        with patch("src.commands.send.run_send") as mock_s:
            main(["send", "123", "--text=Hello"])
            mock_s.assert_called_once_with(dialog_id=123, text="Hello")

    def test_main_edit(self):
        """'edit' dispatches to run_edit with parsed args."""
        with patch("src.commands.edit.run_edit") as mock_e:
            main(["edit", "100", "55", "--text=Updated"])
            mock_e.assert_called_once_with(dialog_id=100, message_id=55, text="Updated")

    def test_main_delete(self):
        """'delete' dispatches to run_delete with parsed args."""
        with patch("src.commands.delete.run_delete") as mock_d:
            main(["delete", "100", "10", "11", "12"])
            mock_d.assert_called_once_with(dialog_id=100, message_ids=[10, 11, 12])

    def test_main_backup(self):
        """'backup' dispatches to run_backup with parsed args."""
        with patch("src.commands.backup.run_backup") as mock_b:
            main(["backup", "100", "--limit=500", "--output=out.json", "--estimate"])
            mock_b.assert_called_once_with(
                dialog_id=100,
                since=None,
                limit=500,
                output="out.json",
                estimate=True,
            )

    def test_main_download_media(self):
        """'download-media' dispatches to run_download_media."""
        with patch("src.commands.download_media.run_download_media") as mock_dm:
            main(["download-media", "100", "42", "--dest=./dl"])
            mock_dm.assert_called_once_with(dialog_id=100, message_id=42, dest="./dl")

    def test_main_help(self):
        """'help' dispatches to run_help with lang and command."""
        with patch("src.commands.help_cmd.run_help") as mock_h:
            main(["help", "de", "backup"])
            mock_h.assert_called_once_with(lang="de", command="backup")

    def test_main_help_default(self):
        """'help' with no args dispatches with lang=en, command=None."""
        with patch("src.commands.help_cmd.run_help") as mock_h:
            main(["help"])
            mock_h.assert_called_once_with(lang="en", command=None)
