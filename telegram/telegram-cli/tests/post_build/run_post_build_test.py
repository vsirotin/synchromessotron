#!/usr/bin/env python3
"""
Run post-build verification tests in dist/ directory.

This script performs quick build verification by running `version` subcommand on each built
executable to confirm the binary was compiled correctly and is executable.

This script:
1. Changes to the dist/ directory where the built executable resides
2. Runs `executable version` on each built CLI executable
3. Verifies version output matches semantic version format (e.g., "1.0.15")
4. Collects and reports test statistics

Usage (from telegram-cli root):
    python3 tests/post_build/run_post_build_test.py
    
Usage (typically in CI/CD after build):
    cd telegram/telegram-cli/dist
    python3 ../tests/post_build/run_post_build_test.py

Pre-condition:
    - Built executable exists in dist/ (telegram-cli.pyz, telegram-cli.exe, or telegram-cli)

Note:
    - This is quick build verification, NOT full integration testing.
    - Full integration tests with config.yaml are in `tests/post_build/integration_test.py`
      and run separately via `tests/post_build/run_integration_tests.py`.
"""

import io
import os
import sys
import re
import platform
import subprocess
from pathlib import Path

# Configure stdout to handle Unicode on Windows (cp1252) and other platforms
if sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class PostBuildTestRunner:
    """Run post-build verification tests in the dist/ directory."""

    def __init__(self):
        """Initialize runner, detecting paths relative to this script."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        self.dist_dir = project_root / "dist"
    
    def get_platform_name(self) -> str:
        """Detect current platform: 'macos', 'windows', or 'linux'."""
        system = platform.system()
        if system == "Darwin":
            return "macos"
        elif system == "Windows":
            return "windows"
        else:
            return "linux"
    
    def get_all_cli_executables(self) -> list[tuple[str, str]]:
        """
        Get all available CLI executables in current directory.
        
        Returns:
            List of tuples (name, command) for each available executable.
            name: descriptive name (e.g., "Python archive", "macOS native")
            command: executable command (e.g., "python3 telegram-cli.pyz", etc.)
        
        Raises:
            FileNotFoundError: If no executables found
        """
        platform_name = self.get_platform_name()
        executables = []
        
        # Check for .pyz (portable, works on all platforms)
        if Path("telegram-cli.pyz").exists():
            executables.append(("Python archive (.pyz)", f"python3 {Path('telegram-cli.pyz').resolve()}"))
        
        # Platform-specific binaries
        if platform_name == "macos":
            if Path("telegram-cli").exists():
                executables.append(("macOS native binary", str(Path("telegram-cli").resolve())))
        
        elif platform_name == "windows":
            if Path("telegram-cli.exe").exists():
                executables.append(("Windows executable (.exe)", str(Path("telegram-cli.exe").resolve())))
        
        # No executables found
        if not executables:
            raise FileNotFoundError(
                f"No CLI executables found in {Path.cwd()}\n"
                f"Expected: telegram-cli.pyz, telegram-cli (macOS), or telegram-cli.exe (Windows)"
            )
        
        return executables
    
    
    def check_config_exists(self) -> bool:
        """Check if config.yaml exists in current directory."""
        return Path("config.yaml").exists()
    
    def run_tests(self, cli: str, project_root: Path) -> tuple[int, int, int]:
        """
        Run post-build verification: execute `version` subcommand to verify executable works.
        
        Args:
            cli: CLI executable command (e.g., "python3 telegram-cli.pyz" or "./telegram-cli")
            project_root: Path to project root (unused for version check)
        
        Returns:
            Tuple of (total_tests, total_checks, total_passed)
            - total_tests: 1 (the version check)
            - total_checks: 1
            - total_passed: 1 if version output is valid, 0 if failed
            
        Raises:
            RuntimeError: If subprocess fails (non-zero exit code)
        """
        # Build command using shell format
        cmd = f"{cli} version"
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(Path.cwd()),  # Run from dist/ directory
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )
            
            # Print captured output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            # Check if subprocess failed
            if result.returncode != 0:
                raise RuntimeError(
                    f"Subprocess failed with exit code {result.returncode}.\n"
                    f"Command: {cmd}"
                )
            
            # Verify version output matches semantic version format (e.g., "1.0.15")
            version_match = re.search(r'\d+\.\d+\.\d+', result.stdout + result.stderr)
            if not version_match:
                raise RuntimeError(
                    f"Version output does not match semantic version format.\n"
                    f"Expected format: X.Y.Z (e.g., 1.0.15)\n"
                    f"Got: {result.stdout.strip() if result.stdout else result.stderr.strip()}"
                )
            
            # Version check passed: 1 test, 1 check, 1 passed
            return (1, 1, 1)
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("Version check timed out (30s)")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error running version check: {e}")


def main():
    """Main entry point."""
    try:
        runner = PostBuildTestRunner()
        project_root = runner.dist_dir.parent  # telegram-cli root directory
        
        print(f"{'='*60}")
        print("Post-Build Verification Test Runner")
        print(f"{'='*60}")
        print(f"Platform: {runner.get_platform_name()}")
        print(f"Working directory: {Path.cwd()}")
        
        # Get all available CLI executables
        print(f"\nLooking for built executables...")
        executables = runner.get_all_cli_executables()
        for name, cli in executables:
            print(f"  Found: {name}")
        
        # Run version check for each executable
        total_tests_all = 0
        total_checks_all = 0
        total_passed_all = 0
        
        for exec_name, cli in executables:
            print(f"\n{'='*60}")
            print(f"Testing: {exec_name}")
            print(f"{'='*60}\n")
            
            total_tests, total_checks, total_passed = runner.run_tests(cli, project_root)
            total_failed = total_checks - total_passed
            
            total_tests_all += total_tests
            total_checks_all += total_checks
            total_passed_all += total_passed
            
            # Print per-executable summary
            print(f"\n{'-'*60}")
            print(f"Result for {exec_name}:")
            print(f"  Version check: {'✓ Passed' if total_passed > 0 else '✗ Failed'}")
            
            if total_passed > 0:
                print(f"  ✓ Executable is valid!")
            else:
                print(f"  ✗ Executable verification failed")
        
        # Print overall summary
        print(f"\n{'='*60}")
        print("Overall Verification Summary:")
        print(f"  Executables tested: {len(executables)}")
        print(f"  Total checks: {total_checks_all}")
        print(f"  Passed: {total_passed_all}")
        print(f"  Failed: {total_checks_all - total_passed_all}")
        
        total_failed_all = total_checks_all - total_passed_all
        if total_failed_all == 0 and total_checks_all > 0:
            print(f"\n✓ All executables are valid and ready for release!")
        elif total_checks_all == 0:
            print(f"\n⚠ No executables were tested")
        else:
            print(f"\n✗ {total_failed_all} executable(s) failed verification")
        
        print(f"{'='*60}\n")
        
        sys.exit(0 if total_failed_all == 0 else 1)
    
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
