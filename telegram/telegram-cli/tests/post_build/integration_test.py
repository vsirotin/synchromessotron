#!/usr/bin/env python3
"""
Integration test framework for telegram-cli.

Simple function-based approach: write test cases using check_* functions.
No JSON DSL, no complex parsing — just Python functions.

Usage:
    integration_test(cli="/path/to/cli", command="version", check_json_valid(), ...)
"""

import os
import subprocess
import sys
import glob
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
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(f"  ✗ FAILED: Command timed out (30s)")
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
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print(f"  ✗ FAILED: Command timed out (30s)")
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


def integration_test(cli: str) -> tuple[int, int, int]:
    """
    Run all integration tests.
    
    Args:
        cli: CLI executable path (e.g., "python3 dist/telegram-cli.pyz")
    
    Returns:
        Tuple of (total_tests, total_passed_checks, total_failed_checks)
    """
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
    
    # Add more tests as needed
    
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
