---
name: review
description: Review recent changes - run all validators and report status
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep, Task
---

# Review Changes

Run all applicable validators against recent changes and report findings.

**Step 2 (rule injection) is mandatory and must complete before validation.**

## Step 1: Identify what changed

Get changed files. Try in order until one succeeds:

```bash
# 1. Committed changes (most common)
git diff HEAD~1 --name-only --diff-filter=ACMRT

# 2. Staged changes (pre-commit)
git diff --cached --name-only --diff-filter=ACMRT

# 3. Unstaged changes (working directory)
git diff --name-only --diff-filter=ACMRT
```

The `--diff-filter=ACMRT` includes Added, Copied, Modified, Renamed, Type-changed (excludes Deleted).

Collect the list of changed files and their directories.

## Step 2: Inject applicable rules

Collect rules from `.claude/rules/*.md` at the project root:

```
Check: .claude/rules/*.md (all files, auto-loaded by Claude Code)
```

Use the Glob tool to discover `.claude/rules/*.md` files, then the Read tool to load them. Collect and read those that exist.
De-duplicate (a rule file only needs to be read once even if multiple files share it).

**Precedence:** Most specific rules override more general rules.

If two rules conflict and precedence is unclear, prefer the more specific rule and note the conflict in the report.

Record which rule files were loaded.

## Step 2a: Check for local supplements

Check for `CLAUDE.local.md` at the project root and read it if present:

```bash
[[ -f CLAUDE.local.md ]] && echo "local-supplements:exists"
```

If it exists, read it. Pay particular attention to any "Validation Commands" section, which overrides defaults. Claude Code may also auto-load this file into context; the explicit read here ensures local supplements are always applied regardless of execution environment.

## Step 3: Run deterministic checks

**Check rules for custom validation commands first:**
Look for a "Validation Commands" section in these sources, in precedence order:
1. `CLAUDE.local.md` (from Step 2a — highest priority)
2. Path-scoped `.claude/rules/*.md` files (from Step 2)
3. Universal `.claude/rules/universal.md` (from Step 2)

Use the highest-precedence match. See `claude-md/universal/validation-precedence.md` for the canonical precedence rules.

If no custom commands found, use these defaults based on file types:

**Go:**
```bash
golangci-lint run -v 2>&1 | tail -50
```

**Python:**
```bash
uv run pre-commit run --all-files 2>&1 | tail -50
```

**TypeScript:**
```bash
pnpm run lint 2>&1 | tail -50
# or: npx biome check . 2>&1 | tail -50
```

Report linter results. If linters fail, report and stop - fix these first.

## Step 4: Run semantic validators

Use the Task tool to spawn validators in parallel based on what changed:

**Always run:**
- `security`

**If Go files changed (.go):**
- `go-effective`
- `go-proverbs`

**If Python files changed (.py):**
- `python-style`

**If TypeScript files changed (.ts, .tsx):**
- `typescript-style`

Collect all results.

## Step 5: Aggregate and report

```
## Review Results

### Rules Applied
- .claude/rules/python.md (scoped to backend/**)
- .claude/rules/universal.md

### Files Changed
- cmd/main.go
- internal/service/handler.go
- internal/service/handler_test.go

### Linting
✓ golangci-lint passed

### Security Validation
✓ passed (no HARD, no unexplained SHOULD)

### Go Effective Validation
✗ FAILED (1 HARD, 1 SHOULD unexplained)

**HARD violations (must fix):**
1. handler.go:45 - Exported function `ProcessRequest` missing doc comment

**SHOULD violations (fix or justify):**
1. handler.go:78 - Function has 6 parameters (>5 requires justification)

**Warnings:**
1. handler.go:120 - Complex function, consider breaking up

### Summary
- Rules applied: 2
- Hard violations: 1
- Should violations: 1 (0 justified)
- Warnings: 1

### Recommended Actions
1. Add doc comment to ProcessRequest
2. Consider using options pattern for ProcessRequest parameters
```

## Rules

- Step 2 (rule injection) is mandatory. Do NOT skip it.
- Report ALL findings, don't summarize away details.
- Be specific with file:line locations.
- Clearly separate HARD/SHOULD/WARN severity.
- Note any rule conflicts encountered.
- If everything passes, say so clearly.
