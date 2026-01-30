---
name: implement
description: Implement a feature or fix with automatic validation
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, WebFetch, WebSearch
---

# Implement with Validation

Implement the requested feature/fix, then validate before completing.

## Task

$ARGUMENTS

## Workflow

### Phase 1: Understand
1. Clarify requirements if ambiguous.
2. Identify files that need changes.
3. Understand existing patterns in the codebase.

### Phase 2: Implement
1. Make the necessary code changes.
2. Follow the project's CLAUDE.md rules.
3. Keep changes focused - don't over-engineer.

### Phase 3: Validate
After implementation is complete, run validation:

1. **Run linters first** (deterministic checks):
   - Go: `golangci-lint run --fix -v`
   - Python: `uv run pre-commit run --all-files`
   - Fix any issues before proceeding.

2. **Run semantic validators** (LLM checks):
   - Use the Task tool to spawn validators in parallel:
     - `validate-security` (always)
     - `validate-go-effective` (if Go files changed)
     - `validate-go-proverbs` (if Go files changed)

3. **Fix violations**:
   - HARD violations: must fix.
   - SHOULD violations: fix or justify.
   - WARN: note but don't block.

4. **Re-validate** if fixes were made.

### Phase 4: Complete
Only after validation passes:

1. Summarize what was implemented.
2. List files changed.
3. Note any warnings or justified SHOULD violations.

## Output Format

```
## Implementation Complete

**Task:** [what was requested]

**Changes:**
- file.go: [what changed]
- file_test.go: [what changed]

**Validation:**
- Linting: ✓ passed
- Security: ✓ passed
- Go Effective: ✓ passed (1 warning noted)

**Warnings:**
- [any WARN items to be aware of]

Ready for review or commit.
```

## Rules

- Do NOT skip validation.
- Do NOT say "done" until validation passes.
- Do NOT ignore HARD or SHOULD violations.
- If stuck in a validation loop (3+ attempts), report the issue and ask for guidance.
