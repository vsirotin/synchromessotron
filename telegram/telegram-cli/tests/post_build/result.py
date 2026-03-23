"""Check result data structure."""


class CheckResult:
    """Result of a single check."""
    
    def __init__(self, passed: bool, message: str):
        self.passed = passed
        self.message = message
