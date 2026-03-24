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
    
    def get_all_cli_executables(self) -> tuple[list[tuple[str, str]], bool]:
        """
        Get all available CLI executables in current directory.
        
        Returns:
            Tuple of (executables_list, has_platform_binary)
            - executables_list: List of tuples (name, command) for each available executable
            - has_platform_binary: True if platform-specific binary exists (.exe, .bin, or .pyz on Linux)
        
        Raises:
            FileNotFoundError: If no executables found at all
        """
        platform_name = self.get_platform_name()
        executables = []
        has_platform_binary = False
        
        # Check for .pyz (portable, works on all platforms)
        if Path("telegram-cli.pyz").exists():
            executables.append(("Python archive (.pyz)", f"python3 {Path('telegram-cli.pyz').resolve()}"))
        
        # Platform-specific binaries
        if platform_name == "macos":
            if Path("telegram-cli").exists():
                executables.append(("macOS native binary", str(Path("telegram-cli").resolve())))
                has_platform_binary = True
        
        elif platform_name == "windows":
            if Path("telegram-cli.exe").exists():
                executables.append(("Windows executable (.exe)", str(Path("telegram-cli.exe").resolve())))
                has_platform_binary = True
        
        elif platform_name == "linux":
            if Path("telegram-cli").exists():
                executables.append(("Linux binary", str(Path("telegram-cli").resolve())))
                has_platform_binary = True
        
        # No executables found at all
        if not executables:
            raise FileNotFoundError(
                f"No CLI executables found in {Path.cwd()}\n"
                f"Expected: telegram-cli.pyz, telegram-cli (macOS/Linux), or telegram-cli.exe (Windows)"
            )
        
        return executables, has_platform_binary
    
    def rebuild_platform_binary(self) -> bool:
        """
        Rebuild the platform-specific executable for this machine.
        
        Returns:
            True if rebuild succeeded, False otherwise
        """
        platform_name = self.get_platform_name()
        
        if platform_name == "macos":
            build_script = "tools/build_macos.sh"
        elif platform_name == "windows":
            build_script = "tools/build_windows.sh"
        else:
            print(f"⚠ Linux platform builds not yet supported")
            return False
        
        print(f"\n{'='*60}")
        print(f"Rebuilding {platform_name} binary...")
        print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(
                f"bash {build_script}",
                cwd=str(self.dist_dir.parent),  # Run from telegram-cli root
                capture_output=True,
                text=True,
                timeout=300,
                shell=True
            )
            
            if result.returncode == 0:
                print(f"✓ {platform_name} binary rebuilt successfully")
                return True
            else:
                print(f"✗ Build failed:")
                print(result.stderr if result.stderr else result.stdout)
                return False
        except subprocess.TimeoutExpired:
            print(f"✗ Build timed out (300s)")
            return False
        except Exception as e:
            print(f"✗ Build error: {e}")
            return False
    
    
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
        platform_name = runner.get_platform_name()
        print(f"Platform: {platform_name}")
        print(f"Working directory: {Path.cwd()}")
        
        # Get all available CLI executables
        print(f"\nLooking for built executables...")
        executables, has_platform_binary = runner.get_all_cli_executables()
        for name, cli in executables:
            print(f"  Found: {name}")
        
        # Check if development platform binary exists
        if not has_platform_binary:
            # In CI/CD mode with only .pyz, allow it (cross-platform)
            # In developer mode, attempt rebuild
            is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
            
            if is_ci and len(executables) > 0:
                # CI/CD mode: .pyz alone is sufficient (cross-platform)
                print(f"\n✓ CI/CD mode: Using {len(executables)} executable(s) for verification")
            else:
                # Developer mode: attempt to rebuild platform binary
                print(f"\n⚠ Warning: No {platform_name} native binary found!")
                print(f"  Attempting to rebuild...")
                
                if runner.rebuild_platform_binary():
                    # Re-scan for executables after rebuild
                    print(f"\n  Re-scanning for executables...")
                    executables, has_platform_binary = runner.get_all_cli_executables()
                    print(f"  Found: {len(executables)} executable(s)")
                    for name, cli in executables:
                        print(f"    - {name}")
                else:
                    print(f"  Build failed. Cannot continue without platform binary.")
                    sys.exit(1)
        
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
