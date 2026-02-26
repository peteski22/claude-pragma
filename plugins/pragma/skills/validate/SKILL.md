---
name: validate
description: Run all validators against recent code changes
disable-model-invocation: true
allowed-tools: Task, Bash
---

# Validation Orchestrator

Run all applicable validators against recent code changes.

## Step 1: Determine which validators to run

Check what files have changed:
```bash
git diff HEAD~1 --name-only --diff-filter=ACMRT 2>/dev/null || git diff --cached --name-only --diff-filter=ACMRT 2>/dev/null || git diff --name-only --diff-filter=ACMRT
```

Based on file extensions, select validators:
- `.go` files → run `go-effective`, `go-proverbs`
- `.py` files → run `python-style`
- `.ts` or `.tsx` files → run `typescript-style`
- All files → run `security`
- All files → run `state-machine`

## Step 2: Run validators in parallel

Use the Task tool to spawn validators in parallel. For each applicable validator, create a Task with:
- subagent_type: "general-purpose"
- prompt: Use the Skill tool to invoke the validator. The prompt must explicitly require skill invocation and verbatim JSON output.

**Example Task prompt for each validator:**
```text
Invoke the `go-effective` skill using the Skill tool (skill: "go-effective"). Return its JSON output verbatim — do not summarize, reformat, or re-implement the validation logic.
```

**Go files changed:**
1. Task: Invoke `go-effective` skill and return JSON output verbatim.
2. Task: Invoke `go-proverbs` skill and return JSON output verbatim.
3. Task: Invoke `security` skill and return JSON output verbatim.
4. Task: Invoke `state-machine` skill and return JSON output verbatim.

**Python files changed:**
1. Task: Invoke `python-style` skill and return JSON output verbatim.
2. Task: Invoke `security` skill and return JSON output verbatim.
3. Task: Invoke `state-machine` skill and return JSON output verbatim.

**TypeScript files changed:**
1. Task: Invoke `typescript-style` skill and return JSON output verbatim.
2. Task: Invoke `security` skill and return JSON output verbatim.
3. Task: Invoke `state-machine` skill and return JSON output verbatim.

**Mixed languages:** Combine all applicable validators. Security and state-machine always run exactly once regardless of how many languages are detected.

Run all applicable Tasks in parallel (multiple Task calls in one response).

## Step 3: Aggregate results

Collect all validator outputs and present a unified report:

```markdown
# Validation Results

## Security
[JSON output from security]

## State Machine
[JSON output from state-machine]

## Go Effective (if applicable)
[JSON output from go-effective]

## Go Proverbs (if applicable)
[JSON output from go-proverbs]

## Python Style (if applicable)
[JSON output from python-style]

## TypeScript Style (if applicable)
[JSON output from typescript-style]

## Summary
- Total validators run: N
- HARD violations: N (must fix)
- SHOULD violations: N (fix or justify)
- Warnings: N (advisory)
- Pass: YES/NO
```

## Step 4: Verdict

If any HARD violations or unjustified SHOULD violations:
- **FAIL** - list what must be fixed

If only warnings:
- **PASS with warnings** - note them but don't block

If clean:
- **PASS** - ready for commit
