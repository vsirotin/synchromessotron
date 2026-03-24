#!/usr/bin/env python3
"""
Run post-build integration tests in dist/ directory.

This script:
1. Changes to the dist/ directory where the built executable and config.yaml reside
2. Runs integration tests on the built CLI
3. Collects and reports test statistics

Usage (from telegram-cli root):
    python3 tests/post_build/run_post_build_test.py
    
Usage (typically in CI/CD after build):
    cd telegram/telegram-cli/dist
    python3 ../tests/post_build/run_post_build_test.py

Pre-condition:
    - Built executable exists in dist/ (telegram-cli.pyz, telegram-cli.exe, or telegram-cli)
    - config.yaml exists in dist/ with valid Telegram credentials
"""

import io
import os
import sys
import platform
import subprocess
from pathlib import Path

# Configure stdout to handle Unicode on Windows (cp1252) and other platforms
if sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class PostBuildTestRunner:
    """Run post-build integration tests in the dist/ directory."""

    def __init__(self):
        """Initialize runner, detecting paths relative to this script."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        self.dist_dir = project_root / "dist"
        self.integration_test_module = "tests.post_build.integration_test"
    
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
        Run integration tests.
        
        Args:
            cli: CLI executable command
            project_root: Path to project root (for module imports)
        
        Returns:
            Tuple of (total_tests, total_checks, total_passed)
            
        Raises:
            RuntimeError: If subprocess fails (non-zero exit code)
        """
        cmd = [
            sys.executable,
            "-m",
            self.integration_test_module,
            cli
        ]
        
        # Prepare environment with PYTHONPATH for module imports
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(Path.cwd()),  # Run from dist/ directory where config.yaml is located
                env=env,
                capture_output=True,
                text=True,
                timeout=120
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
                    f"Command: {' '.join(cmd)}"
                )
            
            # Parse statistics from output (simple pattern matching)
            # Expected format in stdout:
            # "Tests run: N"
            # "Total checks: N"
            # "Passed: N"
            # "Failed: N"
            lines = result.stdout.split('\n')
            stats = {'tests': 0, 'checks': 0, 'passed': 0}
            
            for line in lines:
                if "Tests run:" in line:
                    try:
                        stats['tests'] = int(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                elif "Total checks:" in line:
                    try:
                        stats['checks'] = int(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                elif line.strip().startswith("Passed:"):
                    try:
                        stats['passed'] = int(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
            
            return (stats['tests'], stats['checks'], stats['passed'])
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("Tests timed out (120s)")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error running tests: {e}")


def main():
    """Main entry point."""
    try:
        runner = PostBuildTestRunner()
        project_root = runner.dist_dir.parent  # telegram-cli root directory
        
        print(f"{'='*60}")
        print("Post-Build Integration Test Runner")
        print(f"{'='*60}")
        print(f"Platform: {runner.get_platform_name()}")
        print(f"Working directory: {Path.cwd()}")
        
        # Check if config exists
        if not runner.check_config_exists():
            print("\n⚠ Warning: config.yaml not found in current directory")
            print("  Some tests may fail without valid Telegram credentials")
        
        # Get all available CLI executables
        print(f"\nLooking for built executables...")
        executables = runner.get_all_cli_executables()
        for name, cli in executables:
            print(f"  Found: {name}")
        
        # Run tests for each executable
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
            print(f"Summary for {exec_name}:")
            print(f"  Tests executed: {total_tests}")
            print(f"  Total checks: {total_checks}")
            print(f"  Passed: {total_passed}")
            print(f"  Failed: {total_failed}")
            
            if total_failed == 0 and total_checks > 0:
                print(f"  ✓ All tests passed!")
            elif total_checks == 0:
                print(f"  ⚠ No tests were executed")
            else:
                print(f"  ✗ {total_failed} check(s) failed")
        
        # Print overall summary
        print(f"\n{'='*60}")
        print("Overall Test Summary:")
        print(f"  Executables tested: {len(executables)}")
        print(f"  Total tests executed: {total_tests_all}")
        print(f"  Total checks: {total_checks_all}")
        print(f"  Passed: {total_passed_all}")
        print(f"  Failed: {total_checks_all - total_passed_all}")
        
        total_failed_all = total_checks_all - total_passed_all
        if total_failed_all == 0 and total_checks_all > 0:
            print(f"\n✓ All tests passed!")
        elif total_checks_all == 0:
            print(f"\n⚠ No tests were executed")
        else:
            print(f"\n✗ {total_failed_all} check(s) failed")
        
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
