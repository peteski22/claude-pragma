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

## Step 1: Detect project metadata

Get org and repo name:
```bash
# From git remote
git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/([^/]+)(\.git)?$|\1/\2|' | tr -d '\n'

# Or from go.mod
grep -m1 "^module" go.mod 2>/dev/null | awk '{print $2}' | sed 's|.*/||'
```

Store these for templating configs later.

## Step 2: Detect project languages

Run these checks and collect which languages are present:

```bash
# Check for each language
[[ -f go.mod ]] && echo "go"
[[ -f pyproject.toml ]] || [[ -f setup.py ]] && echo "python"
[[ -f package.json ]] && echo "javascript"
[[ -f tsconfig.json ]] && echo "typescript"
[[ -f Cargo.toml ]] && echo "rust"
```

## Step 3: Check for existing config

```bash
[[ -f .claude/CLAUDE.md ]] && echo "exists"
```

If exists, read it and check if it was assembled by us (has the "Assembled from claude-config" comment). If user-created, ASK before overwriting.

## Step 4: Assemble and write CLAUDE.md

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
<!-- Org/Repo: {org}/{repo} -->
<!-- Re-run /setup-project to regenerate -->
```

## Step 5: Link skills

Create symlinks for skills that aren't already linked:

```bash
mkdir -p ~/.claude/skills
```

**Universal skills (always):**
```bash
ln -sf ~/src/peteski/claude-config/skills/universal/implement ~/.claude/skills/
ln -sf ~/src/peteski/claude-config/skills/universal/review ~/.claude/skills/
ln -sf ~/src/peteski/claude-config/skills/validators/validate ~/.claude/skills/
ln -sf ~/src/peteski/claude-config/skills/validators/security ~/.claude/skills/
```

**Go projects:**
```bash
ln -sf ~/src/peteski/claude-config/skills/validators/go-proverbs ~/.claude/skills/
ln -sf ~/src/peteski/claude-config/skills/validators/go-effective ~/.claude/skills/
```

## Step 6: Copy reference configs (if missing)

For Go projects, if no golangci-lint config exists:
```bash
[[ ! -f .golangci.yml ]] && [[ ! -f .golangci.yaml ]] && echo "no-lint-config"
```

If missing, offer to copy the reference config:
- Source: `~/src/peteski/claude-config/reference/go/golangci-lint.yml`
- Destination: `.golangci.yml`
- Replace `{org}` and `{repo}` with detected values.

## Step 7: Output summary

```
## Setup Complete

**Project:** {repo}
**Org:** {org}
**Languages detected:** Go

**Created:** .claude/CLAUDE.md
  - Universal rules
  - Go rules (Effective Go, Go Proverbs)

**Skills linked:**
  - /implement - implement with auto-validation
  - /review - review changes against all validators
  - /validate - run all validators
  - /validate-go-effective
  - /validate-go-proverbs
  - /validate-security

**Usage:**
  /implement <task>    - implement with validation loop
  /review              - validate current changes
```

Keep it brief. The user should be able to run `/setup-project` and immediately start working.
