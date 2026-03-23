"""
Standard output validation checks.

These functions validate the content and format of CLI stdout.
"""

from typing import Callable, Optional
from .result import CheckResult


def check_stdout_contains(text: str) -> Callable[[str], CheckResult]:
    """Verify output contains a substring."""
    def _check(output: str) -> CheckResult:
        if text in output:
            return CheckResult(True, f"Output contains '{text}'")
        return CheckResult(False, f"Output does not contain '{text}'")
    return _check


def check_stdout_line_count(
    min_lines: int = 0, max_lines: Optional[int] = None
) -> Callable[[str], CheckResult]:
    """Verify output has a certain number of lines."""
    def _check(output: str) -> CheckResult:
        lines = [line for line in output.split("\n") if line.strip()]
        count = len(lines)
        
        if count < min_lines:
            return CheckResult(False, f"Output has {count} lines, expected >= {min_lines}")
        if max_lines is not None and count > max_lines:
            return CheckResult(False, f"Output has {count} lines, expected <= {max_lines}")
        
        expected_str = f"{min_lines}-{max_lines or 'inf'}" if max_lines else f">={min_lines}"
        return CheckResult(True, f"Output has {count} lines (expected {expected_str})")
    return _check
