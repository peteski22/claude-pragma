---
name: review
description: Review recent changes - run all validators and report status
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep, Task
---

# Review Changes

Run all applicable validators against recent changes and report findings.

## Step 1: Identify what changed

```bash
# Get list of changed files
git diff HEAD~1 --name-only 2>/dev/null || git diff --cached --name-only 2>/dev/null || git status --porcelain | awk '{print $2}'
```

Categorize by type:
- Go files (*.go)
- Python files (*.py)
- Config files
- Other

## Step 2: Run deterministic checks

Based on detected languages, run linters:

**Go:**
```bash
golangci-lint run -v 2>&1 | tail -50
```

**Python:**
```bash
uv run pre-commit run --all-files 2>&1 | tail -50
```

Report linter results. If linters fail, report and stop - fix these first.

## Step 3: Run semantic validators

Use the Task tool to spawn validators in parallel based on what changed:

**Always run:**
- `validate-security`

**If Go files changed:**
- `validate-go-effective`
- `validate-go-proverbs`

**If Python files changed:**
- (future: validate-python-style)

Collect all results.

## Step 4: Aggregate and report

```
## Review Results

### Files Changed
- cmd/main.go
- internal/service/handler.go
- internal/service/handler_test.go

### Linting
✓ golangci-lint passed

### Security Validation
✓ No issues found

### Go Effective Validation
✗ FAILED

**HARD violations (must fix):**
1. handler.go:45 - Exported function `ProcessRequest` missing doc comment

**SHOULD violations (fix or justify):**
1. handler.go:78 - Function has 6 parameters (>5 requires justification)

**Warnings:**
1. handler.go:120 - Complex function, consider breaking up

### Summary
- Hard violations: 1
- Should violations: 1
- Warnings: 1

### Recommended Actions
1. Add doc comment to ProcessRequest
2. Consider using options pattern for ProcessRequest parameters
```

## Rules

- Report ALL findings, don't summarize away details.
- Be specific with file:line locations.
- Clearly separate HARD/SHOULD/WARN severity.
- If everything passes, say so clearly.
