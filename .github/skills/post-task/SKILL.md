---
name: post-task
description: Post-task checklist that runs after every agent task that makes essential changes to code, documentation, scripts, or configuration. Covers version bumping, release-notes update, and commit-text proposal. Applied automatically — the agent does not need to be asked.
metadata:
  author: vsirotin
  version: "1.0"
---

# Post-Task Checklist

This skill is applied after every task that makes essential changes to code, documentation, scripts, or configuration files. The agent must execute these steps before reporting completion.

---

## Rules

### 1. Update version

Update the file `<project-root>/src/version.yaml` (if it exists). Use semantic versioning rules. Remember the new version.

### 2. Update release notes

Insert the new version entry **at the beginning** (after the header, at line 3) in `<project-root>/release-notes.md` (if it exists). Include the remembered version number and a short explanation of the version update. Latest release appears first, oldest releases appear last. Do not reorder or overwrite previous entries. Increase a value of parameter `build` in `version.yaml` by 1. Update `datetime` to the current date and time in ISO 8601 format.

### 3. Write commit text proposal

Update **only** the workspace-root file: `commit-text-proposal.txt` (in the workspace root directory where this skill file is located, not in sub-project directories).

Rewrite its content with the following format:

```
<prefix>: Project: <project>. Version: <current version>. <short label for update>.
```

**Parameters:**
- `<prefix>` (optional): See prefix table below (e.g., `feat`, `fix`, `dist`).
- `<project>`: Full sub-project path from workspace root (e.g., `telegram/telegram-lib` or `telegram/telegram-cli`).
- `<current version>`: The version from the changed sub-project's `src/version.yaml` after Rule 1.
- `<short label for update>`: Concise description of what changed (2-10 words).

**Multi-sub-project updates:** If the same commit affects multiple sub-projects, mention **only the main/primary sub-project** that drove the changes.

Prefixes:

| Prefix      | Meaning                                                        |
|-------------|----------------------------------------------------------------|
| `test`      | Update `test/*` files                                          |
| `dist`      | Changes to submodules, version bumps, updates to `package.json`|
| `minor`     | Small changes                                                  |
| `doc`       | Updates to documentation                                       |
| `fix`       | Bug fixes                                                      |
| `bin`       | Update binary scripts associated with the project              |
| `refactor`  | Refactor of existing code                                      |
| `nit`       | Small code review changes mainly around style or syntax        |
| `feat`      | New features                                                   |

**Examples:**

```
fix: Project: telegram/telegram-lib. Version 1.0.12. Closes #9, fix path issue.
nit: Project: telegram/telegram-lib. Version 1.3.12. Swap let for const.
doc: Project: telegram/telegram-lib. Version 2.3.15. Added usage section to README.md.
```

### 4. Update and test dependent projects

When a sub-project changes, discover dependent projects by:
1. **Check workspace configuration**: Look in `<project-root>/pyproject.toml` under `[tool.workspace.projects]` for the `depends-on` field.
2. **Scan all pyproject.toml files**: Across the workspace for the changed library name in their `dependencies` list.

For each dependent project found:
1. **Run tests** to ensure compatibility.
2. **Update version** in the dependent project's `src/version.yaml` and `pyproject.toml` using semantic versioning (typically a patch bump, e.g., 1.0.1 → 1.0.2).
3. **Update release notes** with an entry describing the dependency update.

This ensures that dependent projects stay synchronized with their updated dependencies.


