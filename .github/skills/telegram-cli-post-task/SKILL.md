---
name: telegram-cli-post-task
description: Pre-release verification for telegram-cli that runs BEFORE the workspace post-task skill. Executes unit tests and post-build verification to ensure code quality before version bumping and release notes updates.
metadata:
  author: vsirotin
  version: "1.0"
  applyTo: telegram/telegram-cli
---

# Telegram-CLI Post-Task Verification

This skill is applied **after code changes** to `telegram/telegram-cli` (both production and test code) but **before the workspace post-task skill** runs. It ensures code quality through testing before version management.

---

## Rules

### 1. Run Unit Tests

Execute all unit tests in `telegram/telegram-cli/tests/unit/` via pytest.

**Steps:**
1. Navigate to `telegram/telegram-cli/`
2. Run: `python3 -m pytest tests/unit/ -v`
3. Collect test results (number of tests, passes, failures)
4. Print summary

**Behavior:**
- **On success:** Continue to Rule 2
- **On failure:** Print collected test results, continue anyway to Rule 2 (do not stop)

**Rationale:** Tests must run before version bump, but failures don't block post-task skill from running. This ensures release notes can be generated even if tests fail.

---

### 2. Run Post-Build Verification

Execute `telegram/telegram-cli/tests/post_build/run_post_build_test.py` to verify built executables.

**Steps:**
1. Navigate to `telegram/telegram-cli/dist/`
2. Run: `python3 ../tests/post_build/run_post_build_test.py`
3. Collect results

**Behavior:**
- **On success:** Return success status
- **On failure:** Print verification results, continue anyway (do not stop this skill)

**Rationale:** Post-build verification runs in CI/CD pipeline during `release.yml` workflow. Running locally ensures executables work before creating a GitHub release.

---

### 3. Collect and Report Results (BLOCKING GATE)

Summarize both unit tests and post-build verification results.

**Output format:**

```
============================================================
Telegram-CLI Pre-Release Verification Summary
============================================================
Unit Tests:         PASSED / FAILED (N passed, M failed)
Post-Build Tests:   PASSED / FAILED (details from run_post_build_test.py)

Executables Verified: [.pyz, .exe, .bin]
Ready for post-task (version bump, release notes)?  YES/NO
============================================================
```

**Decision Gate (BLOCKING):**
- **YES, proceed to post-task skill** — Only if **BOTH** unit tests AND post-build verification PASSED
- **NO, STOP here** — If **ANY** failures detected in either tests or verification. Do NOT allow workspace post-task skill to run. Errors must be resolved first.

**Rationale:** Best practice — all tests must pass before committing version changes and release notes. Failures indicate broken code that should not be released.

---

## Notes

- This skill targets changes **within** `telegram/telegram-cli/` (code, tests, configs)
- Does **not** run for documentation-only changes (README.md, DEVELOPMENT.md, etc.)
- **Failures BLOCK the workspace post-task skill** — This ensures no version bumps or release notes are created when tests fail
- The workflow guarantees code quality: testing → verification → version management
- Developer must fix all errors before attempting to commit changes
