---
name: libs-development
description: Development of libraries (collections of stateless functions). Use this skill when creating a new library, adding functions to an existing library, improving library-wide design, or fixing bugs in library code. Covers signatures, error handling, TDD, and statelessness. Common rules (requirements, bug-fix workflow, logging, coding style, versioning) are in the common-development skill.
metadata:
  author: vsirotin
  version: "1.1"
---

# Library Development Skill

> **Prerequisite:** Always apply the [common-development](../common-development/SKILL.md) rules in addition to the rules below.
> The common-development skill is located at `.github/skills/common-development/SKILL.md`.

## When to apply which rules

- **Green-field development or improving a whole library / adding a new function** — follow rules 1–7.
- **Refactoring or error correction** — analyse how rules 1–5 apply to your task, but focus on rule 6 (TDD workflow).

---

## Rules

### 1. Functions never raise exceptions

By default, library functions never raise exceptions. When a problem occurs, the function returns an **error object** (e.g. `TgError`, `Result.error`) instead of propagating an exception to the caller.

### 2. Signatures and error objects must be fully described

Every function signature — including input parameters, return type, and the structure of returned error objects — must be clearly and completely documented.

### 3. Analyse possible error situations

Possible error situations must be analysed according to:
- The specification of internally used components.
- The source code of called functions (when available).

### 4. Document errors and their mapping

In each function's documentation, list all possible errors (e.g. network failures, timeouts, permission issues, invalid input) and show how each maps to the returned error object.

### 5. Document the happy-path payload

The returned payload object (success / happy path) must also be described in the function's documentation.

### 6. Test-Driven Development (TDD)

Develop library functions in the following order:

1. **Signature + documentation + empty body** — define the function's interface and docstring first.
2. **Unit tests** — write tests covering both the happy path and error situations (network errors, timeouts, invalid input, permission failures, etc.).
3. **Implementation** — fill in the function body.
4. **Run unit tests** — all tests must pass.

### 7. Stateless by default

All functions must be stateless unless the specification explicitly requires state. A function receives all necessary context through its parameters and produces output solely through its return value.

### 8. Lint check after every code change

After every change to library source files, run `ruff check` before committing:

```bash
cd <library-root>
.venv/bin/python3 -m ruff check .
```

All errors must be resolved before proceeding to post-task (version bump, release notes). Auto-fixable errors (`[*]` in ruff output) can be applied with `--fix`; non-auto-fixable errors must be corrected manually. A clean ruff run is a hard gate — do not skip it even for cosmetic or style-only changes.