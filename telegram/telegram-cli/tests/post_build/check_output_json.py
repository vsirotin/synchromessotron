"""
JSON output validation checks.

These functions validate that CLI output contains valid JSON
with expected structure and values.
"""

import json
from typing import Any, Callable, Dict, Optional
from .result import CheckResult


def check_json_valid() -> Callable[[str], CheckResult]:
    """Verify output is valid JSON."""
    def _check(output: str) -> CheckResult:
        try:
            json.loads(output)
            return CheckResult(True, "Output is valid JSON")
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON: {e}")
    return _check


def check_json_has_key(
    key: str, contains: Optional[Dict[str, Any]] = None
) -> Callable[[str], CheckResult]:
    """
    Verify JSON has a top-level key and optionally check nested structure.
    
    Args:
        key: Top-level key to check (e.g., "cli", "lib")
        contains: Optional dict of key-value pairs to check within the key's value
    """
    def _check(output: str) -> CheckResult:
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON: {e}")
        
        if key not in data:
            return CheckResult(False, f"Key '{key}' not found in JSON")
        
        value = data[key]
        
        # If we need to check nested structure
        if contains:
            if not isinstance(value, dict):
                return CheckResult(False, f"Value of '{key}' is not an object")
            
            for nested_key, nested_value in contains.items():
                if nested_key not in value:
                    return CheckResult(False, f"Key '{key}' missing nested key '{nested_key}'")
                # If nested_value is specified, check it matches
                if nested_value is not None and value[nested_key] != nested_value:
                    return CheckResult(
                        False, 
                        f"'{key}.{nested_key}' = {value[nested_key]}, expected {nested_value}"
                    )
        
        return CheckResult(True, f"JSON contains key '{key}' with expected structure")
    
    return _check
