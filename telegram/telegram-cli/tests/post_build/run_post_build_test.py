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
    
    def get_cli_executable(self) -> str:
        """
        Get the appropriate CLI executable path in current directory.
        
        Returns:
            CLI command (e.g., "python3 telegram-cli.pyz", "telegram-cli.exe", etc.)
        
        Raises:
            FileNotFoundError: If no executable found
        """
        platform_name = self.get_platform_name()
        
        # Check for .pyz first (most portable, works everywhere)
        if Path("telegram-cli.pyz").exists():
            return "python3 telegram-cli.pyz"
        
        # Platform-specific binaries
        if platform_name == "macos":
            if Path("telegram-cli").exists():
                return "./telegram-cli"
        
        elif platform_name == "windows":
            if Path("telegram-cli.exe").exists():
                return "telegram-cli.exe"
        
        # No executable found
        raise FileNotFoundError(
            f"No CLI executable found in {Path.cwd()}\n"
            f"Expected: telegram-cli.pyz, telegram-cli (macOS), or telegram-cli.exe (Windows)"
        )
    
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
        """
        cmd = [
            sys.executable,
            "-m",
            self.integration_test_module,
            cli
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Print captured output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
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
            print("✗ Tests timed out (120s)")
            return (0, 0, 0)
        except Exception as e:
            print(f"✗ Error running tests: {e}")
            return (0, 0, 0)


def main():
    """Main entry point."""
    try:
        runner = PostBuildTestRunner()
        project_root = runner.dist_dir.parent.parent
        
        print(f"{'='*60}")
        print("Post-Build Integration Test Runner")
        print(f"{'='*60}")
        print(f"Platform: {runner.get_platform_name()}")
        print(f"Working directory: {Path.cwd()}")
        
        # Check if config exists
        if not runner.check_config_exists():
            print("\n⚠ Warning: config.yaml not found in current directory")
            print("  Some tests may fail without valid Telegram credentials")
        
        # Get CLI executable
        print(f"\nLooking for built executable...")
        cli = runner.get_cli_executable()
        print(f"  Found: {cli}")
        
        # Run tests
        print(f"\n{'='*60}")
        print("Running integration tests...\n")
        
        total_tests, total_checks, total_passed = runner.run_tests(cli, project_root)
        total_failed = total_checks - total_passed
        
        # Print summary
        print(f"\n{'='*60}")
        print("Post-Build Test Summary:")
        print(f"  Tests executed: {total_tests}")
        print(f"  Total checks: {total_checks}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        
        if total_failed == 0 and total_checks > 0:
            print(f"\n✓ All tests passed!")
        elif total_checks == 0:
            print(f"\n⚠ No tests were executed")
        else:
            print(f"\n✗ {total_failed} check(s) failed")
        
        print(f"{'='*60}\n")
        
        sys.exit(0 if total_failed == 0 else 1)
    
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
