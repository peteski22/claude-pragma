---
name: setup-project
description: Configure Claude Code for this project - detects languages and sets up rules, skills, and validators
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob
---

# Project Setup

Automatically configure Claude Code for the current project.

## Config repo location

Use: `~/src/peteski/claude-config`

## Step 1: Detect project languages

Run these checks and collect which languages are present:

```bash
# Check for each language
[[ -f go.mod ]] || ls *.go 2>/dev/null | head -1 && echo "go"
[[ -f pyproject.toml ]] || [[ -f setup.py ]] || ls *.py 2>/dev/null | head -1 && echo "python"
[[ -f package.json ]] && echo "javascript"
[[ -f tsconfig.json ]] || ls *.ts 2>/dev/null | head -1 && echo "typescript"
[[ -f Cargo.toml ]] && echo "rust"
```

## Step 2: Check for existing config

```bash
[[ -f .claude/CLAUDE.md ]] && echo "exists"
```

If exists, read it and check if it was assembled by us (has the "Assembled from claude-config" comment). If user-created, ASK before overwriting.

## Step 3: Assemble and write CLAUDE.md

Create the directory:
```bash
mkdir -p .claude
```

Use the Write tool to create `.claude/CLAUDE.md` with contents assembled from:
1. Always: `~/src/peteski/claude-config/claude-md/universal/base.md`
2. For each detected language: `~/src/peteski/claude-config/claude-md/languages/{lang}/{lang}.md`

Add a header comment:
```markdown
<!-- Assembled by /setup-project from claude-config -->
<!-- Languages: go, python -->
<!-- Re-run /setup-project to regenerate -->
```

## Step 4: Link validator skills

Check what's already linked:
```bash
ls -la ~/.claude/skills/ 2>/dev/null | grep validate
```

Create symlinks for validators that aren't already linked:
```bash
mkdir -p ~/.claude/skills
ln -sf ~/src/peteski/claude-config/skills/validators/validate ~/.claude/skills/
ln -sf ~/src/peteski/claude-config/skills/validators/security ~/.claude/skills/
```

For Go projects, also link:
```bash
ln -sf ~/src/peteski/claude-config/skills/validators/go-proverbs ~/.claude/skills/
```

## Step 5: Output summary

```
## Setup Complete

**Project:** {current directory name}
**Languages detected:** Go, Python

**Created:** .claude/CLAUDE.md
  - Universal rules
  - Go rules (Go Proverbs, error handling, testing)
  - Python rules (PEP 8, pytest)

**Validators linked:**
  - /validate (orchestrator)
  - /validate-security
  - /validate-go-proverbs

**Usage:**
  - Rules are now active for this project
  - Run `/validate` after making changes to verify compliance
```

Keep it brief. The user should be able to run `/setup-project` and immediately start working.
