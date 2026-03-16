---
name: libs-development
description: Development of libraries (collections of stateless functions). Use this skill when creating a new library, adding functions to an existing library, improving library-wide design, or fixing bugs in library code. Covers requirements, signatures, error handling, TDD, logging, and coding style.
metadata:
  author: vsirotin
  version: "1.0"
---

# Library Development Skill

## When to apply which rules

- **Green-field development or improving a whole library / adding a new function** — follow rules 1–10.
- **Refactoring or error correction** — analyse how rules 1–6 apply to your task, but focus on rule 7 (TDD workflow).

---

## Rules

### 1. Requirements must be clear and feasible

Functional and technical requirements must be provided in an understandable and feasible form before implementation begins. If requirements are ambiguous, ask the user for clarification.

### 2. Functions never raise exceptions

By default, library functions never raise exceptions. When a problem occurs, the function returns an **error object** (e.g. `TgError`, `Result.error`) instead of propagating an exception to the caller.

### 3. Signatures and error objects must be fully described

Every function signature — including input parameters, return type, and the structure of returned error objects — must be clearly and completely documented.

### 4. Analyse possible error situations

Possible error situations must be analysed according to:
- The specification of internally used components.
- The source code of called functions (when available).

### 5. Document errors and their mapping

In each function's documentation, list all possible errors (e.g. network failures, timeouts, permission issues, invalid input) and show how each maps to the returned error object.

### 6. Document the happy-path payload

The returned payload object (success / happy path) must also be described in the function's documentation.

### 7. Test-Driven Development (TDD)

Develop library functions in the following order:

1. **Signature + documentation + empty body** — define the function's interface and docstring first.
2. **Unit tests** — write tests covering both the happy path and error situations (network errors, timeouts, invalid input, permission failures, etc.).
3. **Implementation** — fill in the function body.
4. **Run unit tests** — all tests must pass.

When fixing a bug, follow the bug-fix variant of TDD:

1. Write a unit test that **fails** because of the bug.
2. Run the test to **confirm it fails**.
3. Fix the code.
4. Run the test to **confirm it passes**.
5. Report the result.

### 8. Logging by default

All functions must include logging. If the specification does not describe logging, use best practices for the language (e.g. a `@logged` decorator for entry/exit, structured log fields for errors).

### 9. Stateless by default

All functions must be stateless unless the specification explicitly requires state. A function receives all necessary context through its parameters and produces output solely through its return value.

### 10. Consistent coding style

Use best practices of the programming language, but maintain a common, consistent style across the entire library. Do not mix conventions within one codebase.