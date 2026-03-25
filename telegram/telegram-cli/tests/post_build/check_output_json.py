"""
JSON output validation checks.

These functions validate that CLI output contains valid JSON
with expected structure and values.
"""

import json
import os
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


def check_json_file_exists(filepath: str) -> Callable[[], CheckResult]:
    """
    Verify a JSON file exists at the specified path.
    
    Args:
        filepath: Path to the JSON file to check
    
    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        if not os.path.exists(filepath):
            return CheckResult(False, f"File not found: {filepath}")
        return CheckResult(True, f"File exists: {filepath}")
    return _check


def check_json_file_valid(filepath: str) -> Callable[[], CheckResult]:
    """
    Verify a file contains valid JSON.
    
    Args:
        filepath: Path to the JSON file to check
    
    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            return CheckResult(True, f"File contains valid JSON: {filepath}")
        except FileNotFoundError:
            return CheckResult(False, f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            return CheckResult(False, f"Error reading {filepath}: {e}")
    return _check


def check_json_array_length(filepath: str, expected_length: int) -> Callable[[], CheckResult]:
    """
    Verify a JSON file contains an array with the expected number of elements.
    
    Args:
        filepath: Path to the JSON file to check
        expected_length: Expected number of array elements
    
    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return CheckResult(False, f"File content is not a JSON array: {filepath}")
            
            actual_length = len(data)
            if actual_length != expected_length:
                return CheckResult(
                    False, 
                    f"Array length {actual_length} != expected {expected_length}"
                )
            
            return CheckResult(True, f"Array contains {expected_length} elements")
        except FileNotFoundError:
            return CheckResult(False, f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            return CheckResult(False, f"Error reading {filepath}: {e}")
    return _check


def check_json_contains_element(
    filepath: str, 
    match_fields: Dict[str, Any]
) -> Callable[[], CheckResult]:
    """
    Verify a JSON array contains an element with specific field values.
    
    Args:
        filepath: Path to the JSON file to check
        match_fields: Dictionary of field names and values to match
                     (e.g., {"id": -718738386, "type": "Chat"})
    
    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return CheckResult(False, f"File content is not a JSON array: {filepath}")
            
            # Search for element matching all fields
            for element in data:
                if not isinstance(element, dict):
                    continue
                
                # Check if all match_fields are present with correct values
                if all(element.get(field) == value for field, value in match_fields.items()):
                    field_str = ", ".join(f'"{k}": {v}' for k, v in match_fields.items())
                    return CheckResult(True, f"Found element with {{{field_str}}}")
            
            # No match found
            field_str = ", ".join(f'"{k}": {v}' for k, v in match_fields.items())
            return CheckResult(False, f"No element found with {{{field_str}}}")
        except FileNotFoundError:
            return CheckResult(False, f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            return CheckResult(False, f"Error reading {filepath}: {e}")
    return _check


def check_directory_exists(dirpath: str) -> Callable[[], CheckResult]:
    """
    Verify a directory exists at the specified path.
    
    Args:
        dirpath: Path to the directory to check
    
    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        if not os.path.isdir(dirpath):
            return CheckResult(False, f"Directory not found: {dirpath}")
        return CheckResult(True, f"Directory exists: {dirpath}")
    return _check


def check_file_exists(filepath: str) -> Callable[[], CheckResult]:
    """
    Verify a file exists at the specified path.
    
    Args:
        filepath: Path to the file to check
    
    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        if not os.path.isfile(filepath):
            return CheckResult(False, f"File not found: {filepath}")
        return CheckResult(True, f"File exists: {filepath}")
    return _check


def check_json_all_elements_have_key(filepath: str, key: str) -> Callable[[], CheckResult]:
    """
    Verify all elements in a JSON array have the specified key with a non-None value.

    Args:
        filepath: Path to the JSON file to check
        key: The key that every element must have

    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                return CheckResult(False, f"File content is not a JSON array: {filepath}")

            if not data:
                return CheckResult(False, f"Array is empty: {filepath}")

            missing_indices = [
                i for i, el in enumerate(data)
                if not (isinstance(el, dict) and key in el and el[key] is not None)
            ]
            if missing_indices:
                return CheckResult(
                    False,
                    f"{len(missing_indices)}/{len(data)} elements missing key '{key}' in {filepath}"
                )
            return CheckResult(True, f"All {len(data)} elements have key '{key}'")
        except FileNotFoundError:
            return CheckResult(False, f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            return CheckResult(False, f"Error reading {filepath}: {e}")
    return _check


def check_files_referenced_in_json_exist(
    json_filepath: str,
    files_dir: str,
    key: str = "file_path",
) -> Callable[[], CheckResult]:
    """
    Verify that all files referenced by a key in a JSON array exist with non-zero size.

    Args:
        json_filepath: Path to the JSON array file whose elements have a file reference
        files_dir: Directory against which file_path values are resolved
        key: The key holding the relative filename (default: "file_path")

    Returns:
        A function that returns CheckResult
    """
    def _check() -> CheckResult:
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                return CheckResult(False, f"Not a JSON array: {json_filepath}")

            referenced = [el[key] for el in data if isinstance(el, dict) and key in el and el[key]]
            if not referenced:
                return CheckResult(False, f"No elements with key '{key}' found in {json_filepath}")

            missing = []
            empty = []
            for filename in referenced:
                fp = os.path.join(files_dir, filename)
                if not os.path.isfile(fp):
                    missing.append(filename)
                elif os.path.getsize(fp) == 0:
                    empty.append(filename)

            if missing:
                return CheckResult(
                    False,
                    f"{len(missing)} referenced file(s) not found in {files_dir}: {missing[:3]}"
                )
            if empty:
                return CheckResult(
                    False,
                    f"{len(empty)} referenced file(s) are empty (0 bytes): {empty[:3]}"
                )
            return CheckResult(
                True, f"All {len(referenced)} referenced files exist with non-zero size"
            )
        except FileNotFoundError:
            return CheckResult(False, f"File not found: {json_filepath}")
        except json.JSONDecodeError as e:
            return CheckResult(False, f"Invalid JSON in {json_filepath}: {e}")
        except Exception as e:
            return CheckResult(False, f"Error: {e}")
    return _check

