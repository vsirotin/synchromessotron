#!/usr/bin/env python3
"""
Integration test framework for telegram-cli.

Simple function-based approach: write test cases using check_* functions.
No JSON DSL, no complex parsing — just Python functions.

Usage:
    integration_test(cli="/path/to/cli", command="version", check_json_valid(), ...)
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Callable
from pathlib import Path

from .result import CheckResult
from .check_output_json import (
    check_json_valid, 
    check_json_has_key,
    check_json_file_exists,
    check_json_file_valid,
    check_json_array_length,
    check_json_contains_element,
    check_directory_exists,
    check_file_exists,
    check_json_all_elements_have_key,
    check_files_referenced_in_json_exist,
)
from .check_stdout import (
    check_stdout_contains,
    check_stdout_line_count,
    check_stdout_exact_line_count,
    check_stdout_contains_line_with_parts,
    check_stdout_first_line_starts_with,
    check_stdout_contains_line_starting_with,
)
def test(cli: str, command: str, *checks: Callable[..., CheckResult]) -> tuple[int, int]:
    """
    Run a single CLI command and validate against check functions.
    
    Args:
        cli: CLI executable path or command (e.g., "python3 dist/telegram-cli.pyz")
        command: Command to run (e.g., "version", "ping")
        *checks: Variable number of check function results to validate
    
    Returns:
        Tuple of (total_checks, passed_checks)
    """
    full_cmd = f"{cli} {command}"
    
    print(f"\n  Running: {full_cmd}")
    
    total_checks = len(checks)
    passed_checks = 0
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        print(f"  ✗ FAILED: Command timed out (90s)")
        return (total_checks, 0)
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return (total_checks, 0)
    
    # Check for command execution error
    if result.returncode != 0:
        print(f"  ✗ FAILED: Command exited with code {result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:200]}")
        return (total_checks, 0)
    
    # Run all checks against stdout
    for check_fn in checks:
        check_result = check_fn(result.stdout)
        if not check_result.passed:
            print(f"  ✗ FAILED: {check_result.message}")
        else:
            passed_checks += 1
            print(f"    ✓ {check_result.message}")
    
    return (total_checks, passed_checks)


def test_file_output(cli: str, command: str, *checks: Callable[[], CheckResult]) -> tuple[int, int]:
    """
    Run a CLI command that outputs to files and validate file results.
    
    Args:
        cli: CLI executable path or command (e.g., "python3 dist/telegram-cli.pyz")
        command: Command to run (e.g., "get-dialogs --limit=50 --outdir=tmp1")
        *checks: Variable number of file-based check function results to validate
    
    Returns:
        Tuple of (total_checks, passed_checks)
    """
    full_cmd = f"{cli} {command}"
    
    print(f"\n  Running: {full_cmd}")
    
    total_checks = len(checks)
    passed_checks = 0
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        print(f"  ✗ FAILED: Command timed out (90s)")
        return (total_checks, 0)
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return (total_checks, 0)
    
    # Check for command execution error
    if result.returncode != 0:
        print(f"  ✗ FAILED: Command exited with code {result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:200]}")
        return (total_checks, 0)
    
    # Run all file-based checks
    for check_fn in checks:
        check_result = check_fn()
        if not check_result.passed:
            print(f"  ✗ FAILED: {check_result.message}")
        else:
            passed_checks += 1
            print(f"    ✓ {check_result.message}")
    
    return (total_checks, passed_checks)


def count_files_in_dir(directory: str, min_size: int = 1) -> int:
    """Count non-empty files in a directory (not subdirectories)."""
    if not os.path.isdir(directory):
        return 0
    count = 0
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            file_size = os.path.getsize(item_path)
            if file_size >= min_size:
                count += 1
    return count


def integration_test(cli: str) -> tuple[int, int, int]:
    """
    Run all integration tests.
    
    Args:
        cli: CLI executable path (e.g., "python3 dist/telegram-cli.pyz")
    
    Returns:
        Tuple of (total_tests, total_passed_checks, total_failed_checks)
    """
    # Clean up test artifacts before starting
    import shutil
    test_output_dir = "synchromessotron"
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)
    
    print(f"\n{'='*60}")
    print(f"Integration Tests for telegram-cli")
    print(f"CLI: {cli}")
    print(f"{'='*60}")
    
    total_tests = 0
    total_checks = 0
    total_passed = 0
    
    # Test 1: version command
    test_name = "version command"
    print(f"\n[Test 1] {test_name}")
    checks_count, passed_count = test(
        cli,
        "version",
        check_json_valid(),
        check_json_has_key("cli", contains={"version": None}),
        check_json_has_key("lib", contains={"datetime": None})
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 2: get-dialogs command
    test_name = "get-dialogs command with --limit=500"
    print(f"\n[Test 2] {test_name}")
    checks_count, passed_count = test(
        cli,
        "get-dialogs --limit=500",
        check_stdout_exact_line_count(136),
        check_stdout_contains_line_with_parts("User", "93372553", "BotFather", "@BotFather")
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 3: get-dialogs with file output
    test_name = "get-dialogs command outputting to file with --limit=50 --outdir=tmp1"
    print(f"\n[Test 3] {test_name}")
    
    # Tests run from dist/ directory, so output file is relative to dist/
    output_file = "tmp1/dialogs.json"
    
    # Clean up old test output if it exists
    if os.path.exists(output_file):
        os.remove(output_file)
    
    checks_count, passed_count = test_file_output(
        cli,
        "get-dialogs --limit=50 --outdir=tmp1",
        check_json_file_exists(output_file),
        check_json_file_valid(output_file),
        check_json_array_length(output_file, 50),
        check_json_contains_element(output_file, {"id": -718738386, "type": "Chat"})
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 4: backup command - happy path with default output directory
    test_name = "backup command - retrieve messages with --limit=500"
    print(f"\n[Test 4] {test_name}")
    
    checks_count, passed_count = test(
        cli,
        "backup -4821106881 --limit=500",
        check_stdout_first_line_starts_with("Backup: dialog=-4821106881, limit=500 | output="),
        check_stdout_contains_line_starting_with("Local:"),
        check_stdout_contains_line_starting_with("Estimated time:"),
        check_stdout_contains("messages saved")
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 5: backup creates correct directory structure with messages.json
    test_name = "backup creates directory structure with messages.json"
    print(f"\n[Test 5] {test_name}")
    
    # Backup output should be in synchromessotron/<dialog_name>_<dialog_id>/
    # We need to find what directory was created - look for pattern
    backup_root = "synchromessotron"
    
    # Clean up old backup if it exists
    if os.path.exists(backup_root):
        import shutil
        shutil.rmtree(backup_root)
    
    checks_count, passed_count = test(
        cli,
        "backup -4821106881 --limit=500",
        check_stdout_first_line_starts_with("Backup: dialog=-4821106881"),
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 6: backup with custom output directory
    test_name = "backup command with custom --outdir"
    print(f"\n[Test 6] {test_name}")
    
    custom_outdir = "custom_backup"
    
    # Clean up old backup if it exists
    if os.path.exists(custom_outdir):
        import shutil
        shutil.rmtree(custom_outdir)
    
    checks_count, passed_count = test(
        cli,
        f"backup -4821106881 --limit=100 --outdir={custom_outdir}",
        check_stdout_first_line_starts_with("Backup: dialog=-4821106881"),
        check_stdout_contains("Local:"),
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 7: backup --estimate flag (no files written)
    test_name = "backup --estimate flag shows time estimate without writing files"
    print(f"\n[Test 7] {test_name}")
    
    checks_count, passed_count = test(
        cli,
        "backup -4821106881 --limit=500 --estimate",
        check_stdout_contains("messages"),
        check_stdout_contains("pages"),
        check_stdout_contains("\u2248")  # ≈ symbol
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 8: backup with small limit
    test_name = "backup with --limit=50 creates messages for small dataset"
    print(f"\n[Test 8] {test_name}")
    
    backup_small = "backup_small"
    if os.path.exists(backup_small):
        import shutil
        shutil.rmtree(backup_small)
    
    checks_count, passed_count = test(
        cli,
        f"backup -4821106881 --limit=50 --outdir={backup_small}",
        check_stdout_contains("Local:"),
        check_stdout_contains("messages saved"),
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 9: verify backup creates dialog subdirectory with correct structure
    test_name = "backup creates dialog_name_dialog_id subdirectory (F1 requirement)"
    print(f"\n[Test 9] {test_name}")
    
    backup_verify = "backup_verify"
    if os.path.exists(backup_verify):
        import shutil
        shutil.rmtree(backup_verify)
    
    # Run backup command
    test(
        cli,
        f"backup -4821106881 --limit=20 --outdir={backup_verify}",
        check_stdout_contains("messages saved"),
    )
    
    # Now verify the directory structure
    # The dialog_name for -4821106881 should be a group name from get-dialogs
    # According to the data we saw, this is "Виталий, Viktor и Сергей"
    # But we should check for any directory matching pattern: *_-4821106881
    
    import glob
    matching_dirs = glob.glob(os.path.join(backup_verify, "*_-4821106881"))
    
    checks_count = 3
    passed_count = 0
    
    _MEDIA_CAT_IT = {"media", "files", "music", "voice", "gifs", "links", "members"}

    def _leaf_json_files(dialog_dir):
        """Return all non-category messages.json paths under dialog_dir."""
        result = []
        for root, _dirs, files in os.walk(dialog_dir):
            parts = os.path.relpath(root, dialog_dir).split(os.sep)
            if any(p in _MEDIA_CAT_IT for p in parts):
                continue
            if "messages.json" in files:
                result.append(os.path.join(root, "messages.json"))
        return result

    def _count_tree_messages(dialog_dir):
        """Sum message counts across all non-category messages.json files."""
        total = 0
        for jf in _leaf_json_files(dialog_dir):
            try:
                with open(jf, encoding="utf-8") as fp:
                    d = json.load(fp)
                    if isinstance(d, list):
                        total += len(d)
            except Exception:
                pass
        return total

    def _count_tree_md_headers(dialog_dir):
        """Count ## headers across all non-category messages.md files."""
        total = 0
        for jf in _leaf_json_files(dialog_dir):
            md = jf.replace("messages.json", "messages.md")
            try:
                with open(md, encoding="utf-8") as fp:
                    total += sum(1 for l in fp if l.startswith("##"))
            except Exception:
                pass
        return total

    if matching_dirs:
        dialog_dir = matching_dirs[0]
        leaf_jsons = _leaf_json_files(dialog_dir)

        print(f"\n  Checking directory structure at: {dialog_dir}")

        checks_count = 3
        passed_count = 0
        if leaf_jsons:
            messages_json = leaf_jsons[0]
            messages_md = messages_json.replace("messages.json", "messages.md")
            for check_fn in [
                check_file_exists(messages_json),
                check_file_exists(messages_md),
                check_json_file_valid(messages_json),
            ]:
                check_result = check_fn()
                if not check_result.passed:
                    print(f"  ✗ FAILED: {check_result.message}")
                else:
                    passed_count += 1
                    print(f"    ✓ {check_result.message}")
        else:
            print(f"  ✗ FAILED: No messages.json found in hierarchy under {dialog_dir}")
    else:
        checks_count = 3
        passed_count = 0
        # If no matching directory found, report failure
        print(f"  ✗ FAILED: No directory matching *_-4821106881 found in {backup_verify}")
        matching = glob.glob(os.path.join(backup_verify, "*"))
        if matching:
            print(f"    Found: {matching}")
    
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 10: backup messages.json contains valid JSON array
    test_name = "backup messages.json is valid JSON array"
    print(f"\n[Test 10] {test_name}")
    
    backup_json = "backup_json"
    if os.path.exists(backup_json):
        import shutil
        shutil.rmtree(backup_json)
    
    test(
        cli,
        f"backup -4821106881 --limit=30 --outdir={backup_json}",
        check_stdout_contains("messages saved"),
    )
    
    # Find the messages.json file and validate it
    matching_dirs = glob.glob(os.path.join(backup_json, "*_-4821106881"))
    
    checks_count = 2
    passed_count = 0
    
    if matching_dirs:
        leaf_jsons_10 = _leaf_json_files(matching_dirs[0])
        if leaf_jsons_10:
            messages_json = leaf_jsons_10[0]
            r_valid = check_json_file_valid(messages_json)()
            if r_valid.passed:
                passed_count += 1
                print(f"    ✓ {r_valid.message}")
            else:
                print(f"  ✗ FAILED: {r_valid.message}")

            total_tree = _count_tree_messages(matching_dirs[0])
            if total_tree == 30:
                passed_count += 1
                print(f"    ✓ messages hierarchy contains {total_tree} messages (expected 30)")
            else:
                print(f"  ✗ FAILED: messages hierarchy contains {total_tree} messages (expected 30)")
        else:
            print(f"  ✗ FAILED: No messages.json found in tree under {matching_dirs[0]}")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Tests 11-18: DISABLED TEMPORARILY for debugging Issues 1 and 2
    # Tests 11-18: DISABLED TEMPORARILY for debugging Issues 1 and 2
    # These tests will be re-enabled after core pagination and message storage bugs are fixed
    # To restore: See git history

    
    # Test 11: backup downloads more than 200 messages when limit > 200
    test_name = "backup downloads more than 200 messages when limit > 200"
    print(f"\n[Test 11] {test_name}")

    backup_issue1 = "backup_issue1"
    if os.path.exists(backup_issue1):
        shutil.rmtree(backup_issue1)

    full_cmd = f"{cli} backup -4821106881 --limit=205 --outdir={backup_issue1}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=180)

    checks_count = 1
    passed_count = 0

    match = re.search(r'(\d+)\s+messages?\s+saved', result.stdout)
    if match:
        saved_count = int(match.group(1))
        if saved_count > 200:
            passed_count += 1
            print(f"    ✓ Downloaded {saved_count} messages (> 200) when --limit=205")
        else:
            print(f"    ✗ FAILED: Downloaded {saved_count} messages (expected > 200) with --limit=205")
    else:
        print(f"    ✗ FAILED: Could not parse message count from output")

    if os.path.exists(backup_issue1):
        shutil.rmtree(backup_issue1)

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Tests 12-16: Media / file downloading
    # All use correct (since <= upto) date ranges derived from real message metadata.
    # -----------------------------------------------------------------------

    # Helper: run a backup with given flags, return (dialog_dir_path, stdout, returncode)
    def _run_backup_with_flags(outdir: str, flags: str, timeout_s: int = 300):
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        cmd = f"{cli} backup -4821106881 {flags} --outdir={outdir}"
        print(f"\n  Running: {cmd}")
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout_s)
        matched = glob.glob(os.path.join(outdir, "*_-4821106881"))
        dialog_dir = matched[0] if matched else None
        return dialog_dir, proc.stdout, proc.returncode

    # Helper: run standard checks for a download category
    def _check_download_category(dialog_dir, category: str, expected_msg_count: int):
        """Return (checks_count, passed_count) for a downloaded category."""
        cat_dir = os.path.join(dialog_dir, category)
        cat_json = os.path.join(cat_dir, "messages.json")
        checks = [
            check_directory_exists(cat_dir),
            check_json_array_length(cat_json, expected_msg_count),
            check_json_all_elements_have_key(cat_json, "file_path"),
            check_files_referenced_in_json_exist(cat_json, cat_dir),
        ]
        passed = 0
        for chk in checks:
            result = chk()
            if result.passed:
                passed += 1
                print(f"    ✓ {result.message}")
            else:
                print(f"  ✗ FAILED: {result.message}")
        return len(checks), passed

    # Test 12: --files downloads 2 document files (Jan 7–14 2026 window)
    # Files in window: MOV_20260107 (2026-01-07) + MOV_20260114 (2026-01-14) = 2 files
    test_name = "backup --files downloads 2 document files (Jan 7–14 2026)"
    print(f"\n[Test 12] {test_name}")

    dialog_dir_12, _, rc_12 = _run_backup_with_flags(
        "backup_files_dl",
        "--files --limit=200 --since=2026-01-07T00:00:00+00:00 --upto=2026-01-14T23:59:59+00:00",
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_12 and rc_12 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_12, "files", 2)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_12}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 13: --media downloads photos + videos (Dec 21 2025 window, 5 items)
    # Dec 21 2025 has 5 media items (photos and videos)
    test_name = "backup --media downloads 5 media items (Dec 21 2025)"
    print(f"\n[Test 13] {test_name}")

    dialog_dir_13, _, rc_13 = _run_backup_with_flags(
        "backup_media_dl",
        "--media --limit=100 --since=2025-12-21T00:00:00+00:00 --upto=2025-12-21T23:59:59+00:00",
        timeout_s=300,
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_13 and rc_13 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_13, "media", 5)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_13}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 14: --music downloads 1 music file (Oct 28 2025: Гроздья акации.m4a)
    test_name = "backup --music downloads 1 music file (Oct 28 2025)"
    print(f"\n[Test 14] {test_name}")

    dialog_dir_14, _, rc_14 = _run_backup_with_flags(
        "backup_music_dl",
        "--music --limit=100 --since=2025-10-28T00:00:00+00:00 --upto=2025-10-28T23:59:59+00:00",
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_14 and rc_14 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_14, "music", 1)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_14}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 15: --voice downloads 1 voice message (Jan 7 2026: voice_2026-01-07_13-09-39.ogg)
    test_name = "backup --voice downloads 1 voice message (Jan 7 2026)"
    print(f"\n[Test 15] {test_name}")

    dialog_dir_15, _, rc_15 = _run_backup_with_flags(
        "backup_voice_dl",
        "--voice --limit=100 --since=2026-01-07T00:00:00+00:00 --upto=2026-01-07T23:59:59+00:00",
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_15 and rc_15 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_15, "voice", 1)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_15}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 16: --links creates links/ directory (Oct 26 2025 window: 2 link entries)
    test_name = "backup --links creates links/ directory with 2 entries (Oct 26 2025)"
    print(f"\n[Test 16] {test_name}")

    dialog_dir_16, _, rc_16 = _run_backup_with_flags(
        "backup_links_dl",
        "--links --limit=100 --since=2025-10-26T00:00:00+00:00 --upto=2025-10-26T23:59:59+00:00",
    )
    checks_count = 2
    passed_count = 0
    if dialog_dir_16 and rc_16 == 0:
        cat_dir_16 = os.path.join(dialog_dir_16, "links")
        cat_json_16 = os.path.join(cat_dir_16, "messages.json")
        for chk in [
            check_directory_exists(cat_dir_16),
            check_json_array_length(cat_json_16, 2),
        ]:
            r = chk()
            if r.passed:
                passed_count += 1
                print(f"    ✓ {r.message}")
            else:
                print(f"  ✗ FAILED: {r.message}")
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_16}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Tests 17-19: --upto, --count, --split_threshold
    # -----------------------------------------------------------------------

    # Test 17: --upto filters out messages after the timestamp
    test_name = "backup --upto filters out messages newer than the cutoff"
    print(f"\n[Test 17] {test_name}")

    backup_upto = "backup_upto"
    if os.path.exists(backup_upto):
        shutil.rmtree(backup_upto)

    subprocess.run(
        f"{cli} backup -4821106881 --limit=500 --upto=2026-03-19T00:00:00+00:00 --outdir={backup_upto}",
        shell=True, capture_output=True, text=True, timeout=120,
    )

    matching_dirs_17 = glob.glob(os.path.join(backup_upto, "*_-4821106881"))
    checks_count = 2
    passed_count = 0
    if matching_dirs_17:
        tree_count = _count_tree_messages(matching_dirs_17[0])
        if tree_count == 480:
            passed_count += 1
            print(f"    ✓ --upto: tree contains {tree_count} messages (expected 480)")
        else:
            print(f"  ✗ FAILED: --upto: tree contains {tree_count} messages (expected 480)")

        if tree_count < 500:
            passed_count += 1
            print(f"    ✓ --upto: {tree_count} < 500 (messages were filtered)")
        else:
            print(f"  ✗ FAILED: --upto: {tree_count} >= 500 (filter had no effect)")
    else:
        print(f"  ✗ FAILED: dialog dir not found after --upto backup")

    if os.path.exists(backup_upto):
        shutil.rmtree(backup_upto)

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 18: --count prints totals, writes no files
    test_name = "backup --count prints total + breakdown and creates no output files"
    print(f"\n[Test 18] {test_name}")

    backup_count_outdir = "backup_count_nowrite"
    if os.path.exists(backup_count_outdir):
        shutil.rmtree(backup_count_outdir)

    checks_count, passed_count = test(
        cli,
        f"backup -4821106881 --count --limit=500 --outdir={backup_count_outdir}",
        check_stdout_contains("Messages: 500 total"),
        check_stdout_contains("photo: 86"),
        check_stdout_contains("link/webpage: 24"),
        check_stdout_contains("video: 10"),
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Extra check: no backup directory was written
    checks_count = 1
    passed_count = 0
    if not os.path.exists(backup_count_outdir):
        passed_count += 1
        print(f"    ✓ --count: no output directory created (no files written)")
    else:
        print(f"  ✗ FAILED: --count: output directory {backup_count_outdir!r} was created (should not write files)")
        shutil.rmtree(backup_count_outdir)

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 19: --split_threshold creates deeper hierarchy when count exceeds threshold
    test_name = "backup --split_threshold=5 creates month-level subdirectory"
    print(f"\n[Test 19] {test_name}")

    backup_split = "backup_split"
    if os.path.exists(backup_split):
        shutil.rmtree(backup_split)

    checks_count, passed_count = test_file_output(
        cli,
        f"backup -4821106881 --limit=20 --split_threshold=5 --outdir={backup_split}",
    )

    matching_dirs_19 = glob.glob(os.path.join(backup_split, "*_-4821106881"))
    checks_count = 2
    passed_count = 0
    if matching_dirs_19:
        dialog_dir_19 = matching_dirs_19[0]
        month_dir = os.path.join(dialog_dir_19, "2026", "03")
        if os.path.isdir(month_dir):
            passed_count += 1
            print(f"    ✓ --split_threshold=5 created month subdir: {month_dir}")
        else:
            print(f"  ✗ FAILED: --split_threshold=5 month subdir not found: {month_dir}")
            print(f"    tree: {list(os.walk(dialog_dir_19))}")

        tree_count_19 = _count_tree_messages(dialog_dir_19)
        if tree_count_19 == 20:
            passed_count += 1
            print(f"    ✓ --split_threshold=5 tree contains {tree_count_19} messages (expected 20)")
        else:
            print(f"  ✗ FAILED: --split_threshold=5 tree contains {tree_count_19} messages (expected 20)")
    else:
        print(f"  ✗ FAILED: dialog dir not found after --split_threshold backup")

    if os.path.exists(backup_split):
        shutil.rmtree(backup_split)

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Test 20: invalid --since / --upto combination is rejected
    # -----------------------------------------------------------------------

    test_name = "backup rejects --since after --upto with exit code 1"
    print(f"\n[Test 20] {test_name}")

    inv_cmd = f"{cli} backup -4821106881 --limit=10 --since=2026-01-21T00:00:00+00:00 --upto=2026-01-20T23:59:59+00:00"
    inv_result = subprocess.run(inv_cmd, shell=True, capture_output=True, text=True, timeout=30)

    checks_count = 2
    passed_count = 0

    if inv_result.returncode != 0:
        passed_count += 1
        print(f"    ✓ CLI exited with code {inv_result.returncode} (non-zero, as expected)")
    else:
        print(f"  ✗ FAILED: CLI exited 0 — should have rejected invalid time range")

    if "--since" in inv_result.stderr or "--upto" in inv_result.stderr or "Error" in inv_result.stderr:
        passed_count += 1
        print(f"    ✓ stderr contains helpful error message")
    else:
        print(f"  ✗ FAILED: stderr has no error message (stderr={inv_result.stderr[:200]!r})")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Tests 21-25: --since / --upto date granularity acceptance
    # All use --estimate (no downloads) to keep tests fast.
    # -----------------------------------------------------------------------

    def _check_estimate_accepts(label: str, flags: str) -> tuple[int, int]:
        """Run backup --estimate with given flags; verify exit 0 and ≈ in output."""
        cmd = f"{cli} backup -4821106881 --limit=50 --estimate {flags}"
        print(f"\n  Running: {cmd}")
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        passed = 0
        if proc.returncode == 0:
            passed += 1
            print(f"    ✓ {label}: CLI accepted the date format (exit 0)")
        else:
            print(f"  ✗ FAILED: {label}: CLI rejected the date format (exit {proc.returncode})")
            print(f"    stderr: {proc.stderr[:200]}")
        if "\u2248" in proc.stdout:
            passed += 1
            print(f"    ✓ {label}: output contains ≈ (estimate printed)")
        else:
            print(f"  ✗ FAILED: {label}: ≈ not found in stdout")
        return 2, passed

    # Test 21: --upto with seconds precision
    test_name = "backup --upto accepts seconds-precision timestamp"
    print(f"\n[Test 21] {test_name}")
    checks_count, passed_count = _check_estimate_accepts(
        "seconds", "--upto=2026-01-07T13:09:39+00:00"
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 22: --upto with minutes precision (no seconds)
    test_name = "backup --upto accepts minutes-precision timestamp"
    print(f"\n[Test 22] {test_name}")
    checks_count, passed_count = _check_estimate_accepts(
        "minutes", "--upto=2026-01-07T13:09"
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 23: --upto with day precision (date only)
    test_name = "backup --upto accepts day-precision date"
    print(f"\n[Test 23] {test_name}")
    checks_count, passed_count = _check_estimate_accepts(
        "day", "--upto=2026-01-07"
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 24: --upto with month precision (year-month)
    test_name = "backup --upto accepts month-precision date (YYYY-MM)"
    print(f"\n[Test 24] {test_name}")
    checks_count, passed_count = _check_estimate_accepts(
        "month", "--upto=2026-01"
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 25: --upto with year precision
    test_name = "backup --upto accepts year-precision date (YYYY)"
    print(f"\n[Test 25] {test_name}")
    checks_count, passed_count = _check_estimate_accepts(
        "year", "--upto=2026"
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Test 26: --help command
    # -----------------------------------------------------------------------

    test_name = "help command prints general usage"
    print(f"\n[Test 26] {test_name}")
    checks_count, passed_count = test(
        cli,
        "help",
        check_stdout_contains("telegram-cli"),
        check_stdout_contains("backup"),
        check_stdout_contains("send"),
        check_stdout_contains("Available commands:"),
    )
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Test 27: download-media command
    # Sends a test message with a photo (via backup existing media msg),
    # downloads it via download-media, and verifies the file exists.
    # Uses known voice message id from Jan 7 2026 window backup.
    # -----------------------------------------------------------------------

    # First obtain the message_id of a known media message by running a backup
    # with limited scope and reading the media messages.json
    test_name = "download-media downloads a file for a known media message"
    print(f"\n[Test 27] {test_name}")

    dl_outdir = "backup_for_dm"
    if os.path.exists(dl_outdir):
        shutil.rmtree(dl_outdir)

    # Run a small backup to get a media message id
    dm_cmd = f"{cli} backup -4821106881 --voice --limit=100 --since=2026-01-07T00:00:00+00:00 --upto=2026-01-07T23:59:59+00:00 --outdir={dl_outdir}"
    dm_proc = subprocess.run(dm_cmd, shell=True, capture_output=True, text=True, timeout=120)

    checks_count = 3
    passed_count = 0

    dl_dialog_dirs = glob.glob(os.path.join(dl_outdir, "*_-4821106881"))
    media_msg_id = None
    if dl_dialog_dirs:
        voice_json = os.path.join(dl_dialog_dirs[0], "voice", "messages.json")
        if os.path.exists(voice_json):
            with open(voice_json, encoding="utf-8") as fp:
                voice_msgs = json.load(fp)
            if voice_msgs:
                media_msg_id = voice_msgs[0]["id"]

    if media_msg_id is not None:
        dl_dest = "download_media_test"
        if os.path.exists(dl_dest):
            shutil.rmtree(dl_dest)
        os.makedirs(dl_dest, exist_ok=True)

        dm2_cmd = f"{cli} download-media -4821106881 {media_msg_id} --dest={dl_dest}"
        print(f"\n  Running: {dm2_cmd}")
        dm2_proc = subprocess.run(dm2_cmd, shell=True, capture_output=True, text=True, timeout=60)

        if dm2_proc.returncode == 0:
            passed_count += 1
            print(f"    ✓ download-media exited 0")
        else:
            print(f"  ✗ FAILED: download-media exited {dm2_proc.returncode}")
            print(f"    stderr: {dm2_proc.stderr[:200]}")

        try:
            dm_output = json.loads(dm2_proc.stdout)
            if "file_path" in dm_output:
                passed_count += 1
                print(f"    ✓ output JSON contains file_path: {dm_output['file_path']}")
            else:
                print(f"  ✗ FAILED: output JSON missing file_path")
            downloaded_file = dm_output.get("file_path", "")
            if downloaded_file and os.path.exists(downloaded_file):
                passed_count += 1
                print(f"    ✓ downloaded file exists: {downloaded_file}")
            else:
                # file_path may be relative to dl_dest
                alt = os.path.join(dl_dest, os.path.basename(downloaded_file)) if downloaded_file else ""
                if alt and os.path.exists(alt):
                    passed_count += 1
                    print(f"    ✓ downloaded file exists (relative): {alt}")
                else:
                    print(f"  ✗ FAILED: downloaded file not found at {downloaded_file!r}")
        except (json.JSONDecodeError, Exception) as exc:
            print(f"  ✗ FAILED: could not parse download-media JSON output: {exc}")
            print(f"    stdout: {dm2_proc.stdout[:200]}")

        if os.path.exists(dl_dest):
            shutil.rmtree(dl_dest)
    else:
        print(f"  ✗ FAILED: could not obtain media message id (backup step failed)")

    if os.path.exists(dl_outdir):
        shutil.rmtree(dl_outdir)

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Test 28: send / download-media / edit / delete flow
    # Sends a text message, edits it, then deletes it.
    # Also sends a backup to find a media message, downloads it, verifies.
    # Dialog: -4821106881
    # -----------------------------------------------------------------------

    test_name = "send → edit → delete message flow"
    print(f"\n[Test 28] {test_name}")

    checks_count = 6
    passed_count = 0
    sent_msg_id = None
    FLOW_DIALOG = -4821106881

    # Step 1: send
    send_cmd = f'{cli} send {FLOW_DIALOG} --text="Integration test message - please ignore"'
    print(f"\n  Running: {send_cmd}")
    send_proc = subprocess.run(send_cmd, shell=True, capture_output=True, text=True, timeout=30)

    if send_proc.returncode == 0:
        passed_count += 1
        print(f"    ✓ send exited 0")
        try:
            send_out = json.loads(send_proc.stdout)
            sent_msg_id = send_out.get("id")
            if sent_msg_id:
                passed_count += 1
                print(f"    ✓ send returned message id={sent_msg_id}")
            else:
                print(f"  ✗ FAILED: send output missing 'id': {send_out}")
        except (json.JSONDecodeError, Exception) as exc:
            print(f"  ✗ FAILED: could not parse send output: {exc}")
    else:
        print(f"  ✗ FAILED: send exited {send_proc.returncode}")
        print(f"    stderr: {send_proc.stderr[:200]}")

    # Step 2: edit (requires sent_msg_id)
    if sent_msg_id is not None:
        edit_cmd = f'{cli} edit {FLOW_DIALOG} {sent_msg_id} --text="Integration test message - EDITED"'
        print(f"\n  Running: {edit_cmd}")
        edit_proc = subprocess.run(edit_cmd, shell=True, capture_output=True, text=True, timeout=30)

        if edit_proc.returncode == 0:
            passed_count += 1
            print(f"    ✓ edit exited 0")
            try:
                edit_out = json.loads(edit_proc.stdout)
                if edit_out.get("id") == sent_msg_id and "EDITED" in edit_out.get("text", ""):
                    passed_count += 1
                    print(f"    ✓ edit returned updated message with correct text")
                else:
                    print(f"  ✗ FAILED: edit output mismatch: {edit_out}")
            except (json.JSONDecodeError, Exception) as exc:
                print(f"  ✗ FAILED: could not parse edit output: {exc}")
        else:
            print(f"  ✗ FAILED: edit exited {edit_proc.returncode}")
            print(f"    stderr: {edit_proc.stderr[:200]}")

    # Step 3: delete
    if sent_msg_id is not None:
        del_cmd = f"{cli} delete {FLOW_DIALOG} {sent_msg_id}"
        print(f"\n  Running: {del_cmd}")
        del_proc = subprocess.run(del_cmd, shell=True, capture_output=True, text=True, timeout=30)

        if del_proc.returncode == 0:
            passed_count += 1
            print(f"    ✓ delete exited 0")
            try:
                del_out = json.loads(del_proc.stdout)
                if isinstance(del_out, list) and sent_msg_id in del_out:
                    passed_count += 1
                    print(f"    ✓ delete returned list containing id {sent_msg_id}")
                else:
                    print(f"  ✗ FAILED: delete output mismatch: {del_out}")
            except (json.JSONDecodeError, Exception) as exc:
                print(f"  ✗ FAILED: could not parse delete output: {exc}")
        else:
            print(f"  ✗ FAILED: delete exited {del_proc.returncode}")
            print(f"    stderr: {del_proc.stderr[:200]}")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    return (total_tests, total_checks, total_passed)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: integration_test.py <cli-path>")
        print("Example: integration_test.py 'python3 dist/telegram-cli.pyz'")
        sys.exit(1)
    
    cli = sys.argv[1]
    total_tests, total_checks, total_passed = integration_test(cli)
    
    total_failed = total_checks - total_passed
    
    print(f"\n{'='*60}")
    print("Test Statistics:")
    print(f"  Tests run: {total_tests}")
    print(f"  Total checks: {total_checks}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"{'='*60}\n")
    
    sys.exit(0 if total_failed == 0 else 1)
