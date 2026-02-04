# Validation Command Precedence

This document defines the priority order for validation commands used by `/implement` and `/review` skills.

## Priority Order (Highest to Lowest)

1. **`.claude/local/CLAUDE.md`** - Personal/machine-specific overrides
2. **`{subdir}/.claude/CLAUDE.md`** - Project component rules
3. **`.claude/CLAUDE.md`** - Repository root rules
4. **Built-in defaults** - Language-specific fallbacks

## Rationale

Local supplements have the highest priority because they allow per-machine customization without modifying version-controlled project rules. This supports scenarios like:

- Different paths to tools on different developer machines
- Local wrapper scripts that add extra checks (mypy, security scans)
- CI/CD environments with different validation requirements
- Temporary overrides during development

Subdirectory rules override root rules because more specific contexts (e.g., `backend/` vs repo root) have more specific requirements.

## How to Override

Validation commands are configured at the repository root by the setup-project skill. Override them at two levels:

**Subdirectory overrides** (`backend/.claude/CLAUDE.md`) - component-specific rules:
```markdown
## Validation Commands
- **Lint:** `uv run ruff check . && uv run mypy --strict .`
- **Test:** `uv run pytest -x`
```

**Local overrides** (`.claude/local/CLAUDE.md`) - machine-specific, not committed:
```markdown
## Validation Commands
- **Lint:** `./scripts/my-lint.sh`
- **Test:** `./scripts/my-test.sh`
```

> **Note:** Root-level commands are set automatically by the setup-project skill based on detected language and tooling.

## Common Override Scenarios

- **Wrapper scripts:** Project has `./scripts/lint.sh` that runs multiple tools (ruff + mypy + custom checks)
- **CI/CD integration:** Different commands for local dev vs CI environment
- **Monorepo isolation:** Different validation per subdirectory
- **Tool versioning:** Use a specific linter version not in default environment
- **Security scanning:** Add custom vulnerability checks before commits

## Personal CLAUDE.md (`~/.claude/CLAUDE.md`)

Your personal global CLAUDE.md (`~/.claude/CLAUDE.md`) is **separate from this precedence order**. It applies to all Claude Code conversations but has these characteristics:

- **It is NOT merged into generated project rules.** When `/setup-project` creates `.claude/CLAUDE.md` files, it uses only the claude-pragma templates.
- **It IS visible to validators** because they use `context: fork` and inherit the conversation context.
- **It MAY cause confusion** if it contains language-specific rules (e.g., Go rules appearing in Python context).

**Recommendations:**
- Keep personal CLAUDE.md language-agnostic (workflow preferences, communication style)
- Put language-specific personal preferences in `.claude/local/CLAUDE.md` within each project
- Validators have explicit Language Scope sections to prevent cross-language contamination
