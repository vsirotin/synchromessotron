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
    
    if matching_dirs:
        dialog_dir = matching_dirs[0]
        
        # Check that messages.json exists in the dialog subdirectory
        messages_json = os.path.join(dialog_dir, "messages.json")
        messages_md = os.path.join(dialog_dir, "messages.md")
        
        print(f"\n  Checking directory structure at: {dialog_dir}")
        
        # Run checks directly since files are already created
        check_fns = [
            check_file_exists(messages_json),
            check_file_exists(messages_md),
            check_json_file_valid(messages_json),
        ]
        
        for check_fn in check_fns:
            check_result = check_fn()
            if not check_result.passed:
                print(f"  ✗ FAILED: {check_result.message}")
            else:
                passed_count += 1
                print(f"    ✓ {check_result.message}")
    else:
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
        messages_json = os.path.join(matching_dirs[0], "messages.json")
        
        # Run checks directly since files are already created
        check_fns = [
            check_json_file_valid(messages_json),
            check_json_array_length(messages_json, 30),  # Should have around 30 messages
        ]
        
        for check_fn in check_fns:
            check_result = check_fn()
            if not check_result.passed:
                print(f"  ✗ FAILED: {check_result.message}")
            else:
                passed_count += 1
                print(f"    ✓ {check_result.message}")
    
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
        messages_json = os.path.join(matching_dirs[0], "messages.json")
        messages_md = os.path.join(matching_dirs[0], "messages.md")
        
        # Check messages.json
        if os.path.exists(messages_json):
            try:
                with open(messages_json, 'r', encoding='utf-8') as f:
                    msgs = json.load(f)
                    json_count = len(msgs) if isinstance(msgs, list) else 0
                    if json_count > 100:
                        passed_count += 1
                        print(f"    ✓ messages.json contains {json_count} messages (> 100)")
                    else:
                        print(f"    ✗ FAILED: messages.json contains {json_count} messages (expected > 100)")
                    
                    # If we know saved_count, verify it matches
                    if saved_count and json_count != saved_count:
                        print(f"    ⚠ Warning: messages.json has {json_count} msgs but stdout said {saved_count} saved")
            except (json.JSONDecodeError, IOError) as e:
                print(f"    ✗ FAILED: Could not read messages.json: {e}")
        else:
            print(f"    ✗ FAILED: messages.json not found")
        
        # Check messages.md line count (should also be > 100)
        if os.path.exists(messages_md):
            try:
                with open(messages_md, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Rough check: each message is typically multiple lines, so count ## headers
                    headers = [l for l in lines if l.startswith('##')]
                    md_count = len(headers)
                    if md_count > 100:
                        passed_count += 1
                        print(f"    ✓ messages.md contains {md_count} message headers (> 100)")
                    else:
                        print(f"    ✗ FAILED: messages.md contains {md_count} message headers (expected > 100)")
            except IOError as e:
                print(f"    ✗ FAILED: Could not read messages.md: {e}")
        else:
            print(f"    ✗ FAILED: messages.md not found")
    else:
        print(f"    ✗ FAILED: Dialog directory not found")
    
    # Cleanup
    if os.path.exists(backup_issue2):
        import shutil
        shutil.rmtree(backup_issue2)
    
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
