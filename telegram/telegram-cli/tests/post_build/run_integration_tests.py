#!/usr/bin/env python3
"""
Run integration tests for telegram-cli across platforms.

This script:
1. Verifies the built CLI executable exists
2. Detects the current platform
3. Runs integration tests using the appropriate executable

Note: No installation is required. The script runs the built executable directly
from the dist/ directory.

Usage:
    python3 run_integration_tests.py
    python3 run_integration_tests.py --rebuild

Options:
    --rebuild    Rebuild the executable before testing (optional)
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


class IntegrationTestRunner:
    """Manages platform detection and test execution."""

    def __init__(self, project_root: Path = None):
        """
        Initialize the runner.
        
        Args:
            project_root: Path to telegram-cli project root (auto-detect if None)
        """
        if project_root is None:
            # Auto-detect: assume script is in tests/post-build/
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = project_root
        self.dist_dir = project_root / "dist"
        self.integration_test_script = Path(__file__).parent / "integration_test.py"
    
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
        Get the appropriate CLI executable path for the current platform.
        
        Returns:
            CLI path (e.g., "python3 dist/telegram-cli.pyz", "dist/telegram-cli", etc.)
        
        Raises:
            FileNotFoundError: If no executable found for current platform
        """
        platform_name = self.get_platform_name()
        
        # For all platforms, try .pyz first (most portable)
        pyz_path = self.dist_dir / "telegram-cli.pyz"
        if pyz_path.exists():
            return f"python3 {pyz_path}"
        
        # Platform-specific binaries as fallback
        if platform_name == "macos":
            macos_bin = self.dist_dir / "telegram-cli"
            if macos_bin.exists():
                return str(macos_bin)
        
        elif platform_name == "windows":
            windows_bin = self.dist_dir / "telegram-cli.exe"
            if windows_bin.exists():
                return str(windows_bin)
        
        # No executable found
        raise FileNotFoundError(
            f"No CLI executable found in {self.dist_dir}\n"
            f"Expected one of: telegram-cli.pyz, telegram-cli (macOS), telegram-cli.exe (Windows)\n"
            f"Build first with: bash tools/build_pyz.sh (or tools/build_macos.sh / tools/build_windows.sh)"
        )
    
    def rebuild_if_requested(self, rebuild: bool) -> None:
        """
        Optionally rebuild the executable.
        
        Args:
            rebuild: If True, rebuild before testing
        """
        if not rebuild:
            return
        
        print(f"Rebuilding executable...")
        
        platform_name = self.get_platform_name()
        
        # Select build script
        if platform_name == "macos":
            script = self.project_root / "tools" / "build_macos.sh"
        elif platform_name == "windows":
            script = self.project_root / "tools" / "build_windows.sh"
        else:
            script = self.project_root / "tools" / "build_pyz.sh"
        
        if not script.exists():
            print(f"  ✗ Build script not found: {script}")
            sys.exit(1)
        
        try:
            result = subprocess.run(
                ["bash", str(script)],
                cwd=str(self.project_root),
                capture_output=False,
                timeout=300,
            )
            if result.returncode != 0:
                print(f"  ✗ Build failed")
                sys.exit(1)
            print(f"  ✓ Build succeeded")
        except Exception as e:
            print(f"  ✗ Build error: {e}")
            sys.exit(1)
    
    def run_tests(self, cli: str) -> None:
        """
        Run integration tests with the specified CLI executable.
        
        Args:
            cli: CLI executable path
        """
        # Run as a module to support relative imports
        # This ensures integration_test.py can import from check_*.py files
        # IMPORTANT: Run from dist/ directory so CLI can find config.yaml there
        cmd = [
            sys.executable,
            "-m",
            "tests.post_build.integration_test",
            cli
        ]
        
        # Set PYTHONPATH to include project root so modules can be imported
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)
        
        try:
            # Run tests from dist/ directory where config.yaml is expected
            # Tests 19-20 require 180s each for backup operations + overhead
            result = subprocess.run(cmd, cwd=str(self.dist_dir), env=env, timeout=600)
            sys.exit(result.returncode)
        except subprocess.TimeoutExpired:
            print(f"\n✗ Tests timed out (600s)")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error running tests: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    rebuild = "--rebuild" in sys.argv
    
    try:
        runner = IntegrationTestRunner()
        
        print(f"Platform detected: {runner.get_platform_name()}")
        print(f"Project root: {runner.project_root}")
        
        # Rebuild if requested
        runner.rebuild_if_requested(rebuild)
        
        # Get CLI executable
        print(f"\nLooking for built executable in {runner.dist_dir}...")
        cli = runner.get_cli_executable()
        print(f"  Found: {cli}")
        
        # Run tests
        print(f"\nStarting integration tests...\n")
        runner.run_tests(cli)
    
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
