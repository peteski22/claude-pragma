---
name: implement
description: Implement a feature or fix with automatic validation
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, WebFetch, WebSearch
---

# Implement with Validation

Implement the requested feature/fix, then validate before completing.

**Phase 0 is mandatory and must complete successfully before any other phase.**

## Task

$ARGUMENTS

## Phase 0: Inject Applicable Rules

Before starting work, collect and read all applicable CLAUDE.md rules.

### Step 1: Identify target directories

Based on the task, identify which directories will contain files to be created or modified.

If uncertain, err on the side of including more directories rather than fewer. Extra rules being applied is safe; missing rules is not.

### Step 2: Walk up and collect rules

For each directory, walk upward to repo root collecting `.claude/CLAUDE.md` files:

```
For a file in backend/app/handlers/:
  Check: backend/app/handlers/.claude/CLAUDE.md
  Check: backend/app/.claude/CLAUDE.md
  Check: backend/.claude/CLAUDE.md
  Check: .claude/CLAUDE.md (root)
```

Use the Read tool to check each path. Collect those that exist.

### Step 3: Read and apply rules

Read each discovered CLAUDE.md file.
Apply rules in order of precedence (most specific first):

```
1. backend/app/.claude/CLAUDE.md (if exists) - highest precedence
2. backend/.claude/CLAUDE.md (if exists)
3. .claude/CLAUDE.md (root) - lowest precedence
```

Earlier rules override later rules where they conflict.

If two rules conflict and precedence is unclear, prefer the more specific rule and note the conflict in the final report.

### Step 4: Record applied rules

Track which rule files were loaded for the final report.

---

## Phase 1: Understand

1. Clarify requirements if ambiguous.
2. Identify files that need changes.
3. Understand existing patterns in the codebase.

---

## Phase 2: Implement

1. Make the necessary code changes.
2. Follow the rules loaded in Phase 0.
3. Keep changes focused - don't over-engineer.

---

## Phase 3: Validate

After implementation is complete, run validation.

**Before running validators:** Re-check whether any new directories were introduced during implementation. If so, repeat Phase 0 for those directories and include any newly discovered rules.

1. **Run linters first** (deterministic checks):
   - Go: `golangci-lint run --fix -v`
   - Python: `uv run pre-commit run --all-files`
   - TypeScript: `pnpm run lint` or `npx biome check .`
   - Fix any issues before proceeding.

2. **Run semantic validators** (LLM checks):
   - Use the Task tool to spawn validators in parallel:
     - `validate-security` (always)
     - `validate-go-effective` (if Go files changed)
     - `validate-go-proverbs` (if Go files changed)
     - `validate-python-style` (if Python files changed)
     - `validate-typescript-style` (if TypeScript files changed)

3. **Fix violations**:
   - HARD violations: must fix.
   - SHOULD violations: fix or justify.
   - WARN: note but don't block.

4. **Re-validate** if fixes were made.

---

## Phase 4: Complete

Only after validation passes:

1. Summarize what was implemented.
2. List files changed.
3. List rules that were applied (from Phase 0).
4. Note any warnings or justified SHOULD violations.
5. Note any rule conflicts encountered.

## Output Format

```
## Implementation Complete

**Task:** [what was requested]

**Rules Applied:**
- backend/.claude/CLAUDE.md
- .claude/CLAUDE.md

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

- Phase 0 is mandatory. Do NOT skip rule injection.
- Do NOT skip validation.
- Do NOT say "done" until validation passes.
- Do NOT ignore HARD or SHOULD violations.
- If stuck in a validation loop (3+ attempts), report the issue and ask for guidance.
