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


def check_stdout_exact_line_count(expected_lines: int) -> Callable[[str], CheckResult]:
    """Verify output has exactly the expected number of lines (excluding header/separator lines)."""
    def _check(output: str) -> CheckResult:
        lines = [line for line in output.split("\n") if line.strip() and not line.strip().startswith("-")]
        count = len(lines)
        
        if count == expected_lines:
            return CheckResult(True, f"Output has exactly {count} lines")
        return CheckResult(False, f"Output has {count} lines, expected {expected_lines}")
    return _check


def check_stdout_contains_line_with_parts(*parts: str) -> Callable[[str], CheckResult]:
    """Verify output contains a line with all specified parts."""
    def _check(output: str) -> CheckResult:
        lines = [line for line in output.split("\n") if line.strip()]
        for line in lines:
            if all(part in line for part in parts):
                return CheckResult(True, f"Found line containing {parts}")
        parts_str = ", ".join([f"'{p}'" for p in parts])
        return CheckResult(False, f"No line found containing all parts: {parts_str}")
    return _check


def check_stdout_first_line_starts_with(prefix: str) -> Callable[[str], CheckResult]:
    """Verify the first non-empty line starts with the given prefix."""
    def _check(output: str) -> CheckResult:
        lines = [line for line in output.split("\n") if line.strip()]
        if not lines:
            return CheckResult(False, "No output found")
        first_line = lines[0]
        if first_line.startswith(prefix):
            return CheckResult(True, f"First line starts with '{prefix}'")
        return CheckResult(False, f"First line doesn't start with '{prefix}'. Got: {first_line[:50]}...")
    return _check


def check_stdout_contains_line_starting_with(prefix: str) -> Callable[[str], CheckResult]:
    """Verify output contains a line that starts with the given prefix."""
    def _check(output: str) -> CheckResult:
        lines = [line for line in output.split("\n") if line.strip()]
        for line in lines:
            if line.startswith(prefix):
                return CheckResult(True, f"Found line starting with '{prefix}'")
        return CheckResult(False, f"No line found starting with '{prefix}'")
    return _check

