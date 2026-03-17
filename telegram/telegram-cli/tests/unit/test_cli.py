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
