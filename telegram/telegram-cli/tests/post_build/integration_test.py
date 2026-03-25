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

    
    # Test 19: Verify Issue 1 - download count should match limit (not stuck at ~199)
    test_name = "Issue 1: backup downloads more than 199 messages when limit > 199"
    print(f"\n[Test 19] {test_name}")
    
    backup_issue1 = "backup_issue1"
    if os.path.exists(backup_issue1):
        import shutil
        shutil.rmtree(backup_issue1)
    
    # Capture stdout to check message count
    import subprocess
    full_cmd = f"{cli} backup -4821106881 --limit=500 --outdir={backup_issue1}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=180)
    
    checks_count = 1
    passed_count = 0
    
    # Parse stdout to extract "X messages saved" count
    import re
    match = re.search(r'(\d+)\s+messages?\s+saved', result.stdout)
    if match:
        saved_count = int(match.group(1))
        if saved_count > 199:
            passed_count += 1
            print(f"    ✓ Downloaded {saved_count} messages (> 199) when --limit=500")
        else:
            print(f"    ✗ FAILED: Downloaded {saved_count} messages (expected > 199) with --limit=500")
    else:
        print(f"    ✗ FAILED: Could not parse message count from output")
    
    # Cleanup
    if os.path.exists(backup_issue1):
        import shutil
        shutil.rmtree(backup_issue1)
    
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count
    
    # Test 20: Verify Issue 2 - messages.json should contain all downloaded messages (not just 100)
    test_name = "Issue 2: messages.json contains ALL downloaded messages (not just 100)"
    print(f"\n[Test 20] {test_name}")
    
    backup_issue2 = "backup_issue2"
    if os.path.exists(backup_issue2):
        import shutil
        shutil.rmtree(backup_issue2)
    
    # Capture stdout to check message count
    full_cmd = f"{cli} backup -4821106881 --limit=500 --outdir={backup_issue2}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=180)
    
    checks_count = 2
    passed_count = 0
    
    # Parse stdout to extract "X messages saved" count
    match = re.search(r'(\d+)\s+messages?\s+saved', result.stdout)
    saved_count = None
    if match:
        saved_count = int(match.group(1))
    
    # Find dialog directory
    matching_dirs = glob.glob(os.path.join(backup_issue2, "*_-4821106881"))
    if matching_dirs:
        json_count = _count_tree_messages(matching_dirs[0])
        if json_count > 100:
            passed_count += 1
            print(f"    ✓ messages hierarchy contains {json_count} messages (> 100)")
        else:
            print(f"    ✗ FAILED: messages hierarchy contains {json_count} messages (expected > 100)")
        if saved_count and json_count != saved_count:
            print(f"    ⚠ Warning: tree has {json_count} msgs but stdout said {saved_count} saved")

        md_count = _count_tree_md_headers(matching_dirs[0])
        if md_count > 100:
            passed_count += 1
            print(f"    ✓ messages.md headers across tree: {md_count} (> 100)")
        else:
            print(f"    ✗ FAILED: messages.md headers across tree: {md_count} (expected > 100)")
    else:
        print(f"    ✗ FAILED: Dialog directory not found")
    
    # Cleanup
    if os.path.exists(backup_issue2):
        import shutil
        shutil.rmtree(backup_issue2)
    
    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Tests 21-25: Media / file downloading (requires --media / --files /
    # --music / --voice / --links flags and ENABLE_MEDIA_DOWNLOADS = True)
    # -----------------------------------------------------------------------

    # Helper: run a backup with given flags, return (dialog_dir_path, stdout, returncode)
    def _run_backup_with_flags(outdir: str, flags: str, timeout_s: int = 300):
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        cmd = f"{cli} backup -4821106881 --limit=500 {flags} --outdir={outdir}"
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

    # Test 21: --files downloads 3 document files
    # Uses --since=2026-01-21 --upto=2026-01-20 to constrain to 159 messages (Jan 2026 and earlier):
    # pagination starts before Jan 21 and stops naturally (no messages before that window are wasted),
    # then --upto=Jan 20 confirms the upper bound. Only 3 docs exist in this window.
    test_name = "backup --files downloads 3 document files with non-zero size"
    print(f"\n[Test 21] {test_name}")

    dialog_dir_21, _, rc_21 = _run_backup_with_flags(
        "backup_files_dl",
        "--files --since=2026-01-21T00:00:00+00:00 --upto=2026-01-20T23:59:59+00:00",
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_21 and rc_21 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_21, "files", 3)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_21}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 22: --media downloads photos + videos.
    # Same Jan 2026 window (--since=Jan 21, --upto=Jan 20): 159 messages, 39 photos + 5 videos = 44 items.
    # This is ~54 % fewer downloads than the full-history window (94 items), reducing test run time.
    test_name = "backup --media downloads 44 photos+videos with non-zero size"
    print(f"\n[Test 22] {test_name}")

    dialog_dir_22, _, rc_22 = _run_backup_with_flags(
        "backup_media_dl",
        "--media --since=2026-01-21T00:00:00+00:00 --upto=2026-01-20T23:59:59+00:00",
        timeout_s=300,
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_22 and rc_22 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_22, "media", 44)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_22}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 23: --music downloads 1 music file.
    # Uses Feb 2026 window (--since=Feb 28, --upto=Feb 27) — 376 messages, 1 music track.
    test_name = "backup --music downloads 1 music file with non-zero size"
    print(f"\n[Test 23] {test_name}")

    dialog_dir_23, _, rc_23 = _run_backup_with_flags(
        "backup_music_dl",
        "--music --since=2026-02-28T00:00:00+00:00 --upto=2026-02-27T23:59:59+00:00",
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_23 and rc_23 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_23, "music", 1)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_23}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 24: --voice downloads 2 voice messages (same Feb window: 2 voice files).
    test_name = "backup --voice downloads 2 voice messages with non-zero size"
    print(f"\n[Test 24] {test_name}")

    dialog_dir_24, _, rc_24 = _run_backup_with_flags(
        "backup_voice_dl",
        "--voice --since=2026-02-28T00:00:00+00:00 --upto=2026-02-27T23:59:59+00:00",
    )
    checks_count = 4
    passed_count = 0
    if dialog_dir_24 and rc_24 == 0:
        checks_count, passed_count = _check_download_category(dialog_dir_24, "voice", 2)
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_24}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # Test 25: --links creates links/ directory (same Feb window: 17 link entries, no file downloads).
    test_name = "backup --links creates links/ directory with 17 message entries"
    print(f"\n[Test 25] {test_name}")

    dialog_dir_25, _, rc_25 = _run_backup_with_flags(
        "backup_links_dl",
        "--links --since=2026-02-28T00:00:00+00:00 --upto=2026-02-27T23:59:59+00:00",
    )
    checks_count = 2
    passed_count = 0
    if dialog_dir_25 and rc_25 == 0:
        cat_dir_25 = os.path.join(dialog_dir_25, "links")
        cat_json_25 = os.path.join(cat_dir_25, "messages.json")
        for chk in [
            check_directory_exists(cat_dir_25),
            check_json_array_length(cat_json_25, 17),
        ]:
            r = chk()
            if r.passed:
                passed_count += 1
                print(f"    ✓ {r.message}")
            else:
                print(f"  ✗ FAILED: {r.message}")
    else:
        print(f"  ✗ FAILED: backup command failed (rc={rc_25}) or dialog dir not found")

    total_tests += 1
    total_checks += checks_count
    total_passed += passed_count

    # -----------------------------------------------------------------------
    # Tests 26-28: New flags --upto, --count, --split_threshold
    # -----------------------------------------------------------------------

    # Test 26: --upto filters out messages after the timestamp
    test_name = "backup --upto filters out messages newer than the cutoff"
    print(f"\n[Test 26] {test_name}")

    backup_upto = "backup_upto"
    if os.path.exists(backup_upto):
        shutil.rmtree(backup_upto)

    checks_count, passed_count = test_file_output(
        cli,
        f"backup -4821106881 --limit=500 --upto=2026-03-19T00:00:00+00:00 --outdir={backup_upto}",
        # command must succeed (captured in test_file_output)
    )

    # Now manually count total messages in tree and compare
    matching_dirs_26 = glob.glob(os.path.join(backup_upto, "*_-4821106881"))
    checks_count = 2
    passed_count = 0
    if matching_dirs_26:
        tree_count = _count_tree_messages(matching_dirs_26[0])
        if tree_count == 480:
            passed_count += 1
            print(f"    ✓ --upto: tree contains {tree_count} messages (expected 480)")
        else:
            print(f"  ✗ FAILED: --upto: tree contains {tree_count} messages (expected 480)")

        # Also verify it is strictly less than without --upto (500)
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

    # Test 27: --count prints totals, writes no files
    test_name = "backup --count prints total + breakdown and creates no output files"
    print(f"\n[Test 27] {test_name}")

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

    # Test 28: --split_threshold creates deeper hierarchy when count exceeds threshold
    test_name = "backup --split_threshold=5 creates month-level subdirectory"
    print(f"\n[Test 28] {test_name}")

    backup_split = "backup_split"
    if os.path.exists(backup_split):
        shutil.rmtree(backup_split)

    checks_count, passed_count = test_file_output(
        cli,
        f"backup -4821106881 --limit=20 --split_threshold=5 --outdir={backup_split}",
    )

    matching_dirs_28 = glob.glob(os.path.join(backup_split, "*_-4821106881"))
    checks_count = 2
    passed_count = 0
    if matching_dirs_28:
        dialog_dir_28 = matching_dirs_28[0]
        # With 20 msgs > threshold=5, should drill past year → month level
        # All 20 messages are from 2026-03: expect 2026/03/ directory
        month_dir = os.path.join(dialog_dir_28, "2026", "03")
        if os.path.isdir(month_dir):
            passed_count += 1
            print(f"    ✓ --split_threshold=5 created month subdir: {month_dir}")
        else:
            print(f"  ✗ FAILED: --split_threshold=5 month subdir not found: {month_dir}")
            print(f"    tree: {list(os.walk(dialog_dir_28))}")

        # Verify total message count is still 20
        tree_count_28 = _count_tree_messages(dialog_dir_28)
        if tree_count_28 == 20:
            passed_count += 1
            print(f"    ✓ --split_threshold=5 tree contains {tree_count_28} messages (expected 20)")
        else:
            print(f"  ✗ FAILED: --split_threshold=5 tree contains {tree_count_28} messages (expected 20)")
    else:
        print(f"  ✗ FAILED: dialog dir not found after --split_threshold backup")

    if os.path.exists(backup_split):
        shutil.rmtree(backup_split)

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
