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
git diff HEAD~1 --name-only
```

Based on file extensions, select validators:
- `.go` files → run validate-go-proverbs
- All files → run validate-security

## Step 2: Run validators in parallel

Use the Task tool to spawn validator agents in parallel:

For each applicable validator, create a Task with:
- subagent_type: "general-purpose"
- prompt: "Run the /validate-X skill and report results"

Run these in parallel (multiple Task calls in one response).

## Step 3: Aggregate results

Collect all validator outputs and present a unified report:

```
# Validation Results

## Go Proverbs
[results from validate-go-proverbs]

## Security
[results from validate-security]

## Summary
- Total validators run: 2
- Total issues found: X
- Critical: X
- Warnings: X
```

## Step 4: Provide actionable next steps

If violations found, suggest:
1. Which files need attention
2. Priority order (security critical first)
3. Specific fixes to apply
