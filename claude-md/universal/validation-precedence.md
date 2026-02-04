# Validation Command Precedence

This document defines the priority order for validation commands used by `/implement` and `/review` skills.

## Priority Order (Highest to Lowest)

1. **`.claude/local/CLAUDE.md`** - Personal/machine-specific overrides
2. **`{subdir}/.claude/CLAUDE.md`** - Project component rules
3. **`.claude/CLAUDE.md`** - Repository root rules
4. **Built-in defaults** - Language-specific fallbacks

## Rationale

Local supplements have highest priority because they allow per-machine customization without modifying version-controlled project rules. This supports scenarios like:

- Different paths to tools on different developer machines
- Local wrapper scripts that add extra checks (mypy, security scans)
- CI/CD environments with different validation requirements
- Temporary overrides during development

Subdirectory rules override root rules because more specific contexts (e.g., `backend/` vs repo root) have more specific requirements.

## How to Override

Add a "Validation Commands" section to your local supplements (`.claude/local/CLAUDE.md`):

```markdown
## Validation Commands

- **Lint:** `./scripts/backend-lint.sh`
- **Test:** `./scripts/backend-test.sh`
```

## Common Override Scenarios

- **Wrapper scripts:** Project has `./scripts/lint.sh` that runs multiple tools (ruff + mypy + custom checks)
- **CI/CD integration:** Different commands for local dev vs CI environment
- **Monorepo isolation:** Different validation per subdirectory
- **Tool versioning:** Use a specific linter version not in default environment
- **Security scanning:** Add custom vulnerability checks before commits
