---
name: post-task
description: Post-task checklist that runs after every agent task that makes essential changes to code, documentation, scripts, or configuration. Covers version bumping, release-notes update, and commit-text proposal. Applied automatically — the agent does not need to be asked.
metadata:
  author: vsirotin
  version: "1.0"
---

# Post-Task Checklist

This skill is applied **automatically** after every agent task that makes essential changes to code, documentation, scripts, or configuration files. The agent must execute these steps before reporting completion.

---

## Rules

### 1. Update version

Update the file `<project-root>/src/version.yaml` (if it exists). Use semantic versioning rules. Remember the new version.

### 2. Update release notes

Insert the new version entry **at the beginning** (after the header, at line 3) in `<project-root>/release-notes.md` (if it exists). Include the remembered version number and a short explanation of the version update. Latest release appears first, oldest releases appear last. Do not reorder or overwrite previous entries.

### 3. Write commit text proposal

Rewrite the content of `<project-root>/commit-text-proposal.txt` with the following format:

```
<prefix>: Project: <project>. Version: <current version>. <short label for update>.
```

`<prefix>` is optional. `<project>` is the sub-project path (e.g. `telegram/telegram-lib`). If one commit updates many sub-projects, write only about the main updated sub-project.

Prefixes:

| Prefix       | Meaning                                                        |
|--------------|----------------------------------------------------------------|
| `[test]`     | Update `test/*` files                                          |
| `[dist]`     | Changes to submodules, version bumps, updates to `package.json`|
| `[minor]`    | Small changes                                                  |
| `[doc]`      | Updates to documentation                                       |
| `[fix]`      | Bug fixes                                                      |
| `[bin]`      | Update binary scripts associated with the project              |
| `[refactor]` | Refactor of existing code                                      |
| `[nit]`      | Small code review changes mainly around style or syntax        |
| `[feat]`     | New features                                                   |

**Examples:**

```
fix: Project: telegram/telegram-lib. Version 1.0.12. Closes #9, fix path issue.
nit: Project: telegram/telegram-lib. Version 1.3.12. Swap let for const.
doc: Project: telegram/telegram-lib. Version 2.3.15. Added usage section to README.md.
```
