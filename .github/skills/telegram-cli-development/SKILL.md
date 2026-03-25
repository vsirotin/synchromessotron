---
name: telegram-cli-development
description: Full development lifecycle skill for telegram/telegram-cli. Covers bug-fix workflow (TDD), running unit tests, running integration tests in dist/, building platform artifacts, and pre-release verification before version bump and release notes.
metadata:
  author: vsirotin
  version: "1.1"
  applyTo: telegram/telegram-cli
---

# Telegram-CLI Development Skill

This skill governs **all development work** on `telegram/telegram-cli`: writing code, fixing bugs, running tests, building artifacts, and preparing releases. Apply it for any agent task that touches `telegram/telegram-cli/` source, tests, tools, or configuration.

---

## 1. Bug-Fix Workflow (TDD)

Follow this order for every bug fix:

1. Write a **unit test that fails** because of the bug (in `tests/unit/`).
2. Run unit tests to confirm it fails.
3. Fix the production code.
4. Run unit tests to confirm all pass.
5. Proceed to pre-release verification (section 3).

---

## 2. Run Unit Tests

Execute all unit tests in `telegram/telegram-cli/tests/unit/` via pytest.

**Steps:**
1. Navigate to `telegram/telegram-cli/`
2. Run: `python3 -m pytest tests/unit/ -v`
3. Collect test results (number of tests, passes, failures)
4. Print summary

**Behavior:**
- **On success:** Continue to section 3
- **On failure:** Print collected test results, continue anyway to section 3 (do not stop)

---

## 3. Run Integration Tests (Post-Build Verification)

Integration tests run against the **real built artifact** using real Telegram credentials.

**Location of config and artifact:** `telegram/telegram-cli/dist/`  
— `config.yaml` with real API credentials lives here.  
— The built `.pyz` (or binary) lives here.

**Steps:**
1. Navigate to `telegram/telegram-cli/dist/`
2. Run: `python3 ../tests/post_build/run_post_build_test.py`
3. Collect results

**Behavior:**
- **On success:** Proceed to section 4
- **On failure:** Print verification results, continue anyway (do not stop this skill)

**Rationale:** Integration tests hit the live Telegram API. `config.yaml` must be present in `dist/` before running them. These tests are also executed in CI/CD during `release.yml`.

---

## 4. Building Platform Artifacts

Build scripts are located in `telegram/telegram-cli/tools/`.

| Artifact | Script | Platform |
|----------|--------|----------|
| `.pyz` Python archive | `tools/build_pyz.sh` | Any OS |
| macOS binary | `tools/build_macos.sh` | macOS only |
| Windows `.exe` | `tools/build_windows.sh` | Windows only |
| All variants | `tools/build_all_platform.sh` | macOS (skips unsupported) |

**To build the Python archive (most common for local testing):**
```bash
cd telegram/telegram-cli
bash tools/build_pyz.sh
```

**To build all variants at once:**
```bash
cd telegram/telegram-cli
bash tools/build_all_platform.sh
```

All artifacts land in `telegram/telegram-cli/dist/`.

---

## 5. Pre-Release Verification Summary (BLOCKING GATE)

Before version bump and release notes, collect and report results of sections 2 and 3.

**Output format:**

```
============================================================
Telegram-CLI Pre-Release Verification Summary
============================================================
Unit Tests:         PASSED / FAILED (N passed, M failed)
Integration Tests:  PASSED / FAILED (details from run_post_build_test.py)

Executables Verified: [.pyz, .exe, .bin]
Ready for post-task (version bump, release notes)?  YES/NO
============================================================
```

**Decision Gate (BLOCKING):**
- **YES** — Both unit tests AND integration tests PASSED → proceed to workspace post-task skill (version bump, release notes, commit text).
- **NO** — Any failures detected → STOP. Do NOT run workspace post-task skill. Resolve failures first.

---

## Notes

- This skill targets changes **within** `telegram/telegram-cli/` (code, tests, configs)
- Does **not** run for documentation-only changes (README.md, DEVELOPMENT.md, etc.)
- **Failures BLOCK the workspace post-task skill** — This ensures no version bumps or release notes are created when tests fail
- The workflow guarantees code quality: testing → verification → version management
- Developer must fix all errors before attempting to commit changes
