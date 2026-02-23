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
git diff HEAD~1 --name-only 2>/dev/null || git diff --cached --name-only 2>/dev/null || git status --porcelain | awk '{print $2}'
```

Based on file extensions, select validators:
- `.go` files → run validate-go-effective, validate-go-proverbs
- All files → run validate-security

## Step 2: Run validators in parallel

Use the Task tool to spawn validator agents in parallel.

For each applicable validator, create a Task with:
- subagent_type: "general-purpose"
- prompt: "Run the [validator-name] skill against recent changes and report results"

**Go files changed - spawn these in parallel:**
1. Task: "Run validate-go-effective skill"
2. Task: "Run validate-go-proverbs skill"
3. Task: "Run validate-security skill"

**No Go files - spawn:**
1. Task: "Run validate-security skill"

Run these in parallel (multiple Task calls in one response).

## Step 3: Aggregate results

Collect all validator outputs and present a unified report:

```
# Validation Results

## Go Effective
[JSON output from validate-go-effective]

## Go Proverbs
[results from validate-go-proverbs]

## Security
[results from validate-security]

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
