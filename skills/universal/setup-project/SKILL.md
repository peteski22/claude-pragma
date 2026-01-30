---
name: setup-project
description: Configure Claude Code for this project - detects languages and sets up rules, skills, and validators
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob
---

# Project Setup

Automatically configure Claude Code for the current project. Supports monorepos with multiple languages in subdirectories.

## Step 0: Verify config repo

Requires `$CLAUDE_CONFIG_PATH` environment variable to be set.

```bash
echo "$CLAUDE_CONFIG_PATH"
[[ -z "$CLAUDE_CONFIG_PATH" ]] && echo "ERROR: CLAUDE_CONFIG_PATH not set"
[[ ! -d "$CLAUDE_CONFIG_PATH" ]] && echo "ERROR: CLAUDE_CONFIG_PATH does not exist"
[[ ! -f "$CLAUDE_CONFIG_PATH/claude-md/universal/base.md" ]] && echo "ERROR: Invalid claude-config repo"
```

If not set, tell the user:

```
CLAUDE_CONFIG_PATH is not set.

1. Clone the config repo:
   git clone git@github.com:{org}/claude-config.git ~/src/claude-config

2. Set the environment variable (add to ~/.zshrc or ~/.bashrc):
   export CLAUDE_CONFIG_PATH="$HOME/src/claude-config"

3. Re-run /setup-project
```

**STOP if not set. Do not proceed.**

## Step 1: Detect project metadata

Get org and repo name from git remote:

```bash
git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/([^/]+)(\.git)?$|\1 \2|'
```

Store `{org}` and `{repo}` for templating.

## Step 2: Scan for languages (root and subdirectories)

Check root directory AND immediate subdirectories for language markers.

```bash
# Root level
[[ -f go.mod ]] && echo "root:go"
{ [[ -f pyproject.toml ]] || [[ -f setup.py ]]; } && echo "root:python"
[[ -f package.json ]] && echo "root:javascript"
[[ -f tsconfig.json ]] && echo "root:typescript"
[[ -f Cargo.toml ]] && echo "root:rust"

# Subdirectories (one level deep)
for dir in */; do
  [[ -f "${dir}go.mod" ]] && echo "${dir%/}:go"
  { [[ -f "${dir}pyproject.toml" ]] || [[ -f "${dir}setup.py" ]]; } && echo "${dir%/}:python"
  [[ -f "${dir}package.json" ]] && echo "${dir%/}:javascript"
  [[ -f "${dir}tsconfig.json" ]] && echo "${dir%/}:typescript"
  [[ -f "${dir}Cargo.toml" ]] && echo "${dir%/}:rust"
done
true
```

This produces output like:
- `root:go` (single-language project)
- `backend:python`, `frontend:typescript` (monorepo)

## Step 3: Check for existing configs

```bash
[[ -f .claude/CLAUDE.md ]] && echo "root:exists"
for dir in */; do
  [[ -f "${dir}.claude/CLAUDE.md" ]] && echo "${dir%/}:exists"
done
true
```

If any exist, read them. If they have `<!-- Assembled by /setup-project -->` comment, safe to overwrite. Otherwise ASK before overwriting.

## Step 4: Create root .claude/CLAUDE.md

Create the directory:
```bash
mkdir -p .claude
```

Assemble root CLAUDE.md with:
1. Header comment
2. Universal rules from `$CLAUDE_CONFIG_PATH/claude-md/universal/base.md`
3. **Meta-rule for subdirectory awareness** (always include this)
4. Root-level language rules (if any detected at root)

**Header:**
```markdown
<!-- Assembled by /setup-project from claude-config -->
<!-- Org/Repo: {org}/{repo} -->
<!-- Re-run /setup-project to regenerate -->
```

**Meta-rule to include after universal rules:**
```markdown
## Context-Aware Rules

When working on files in a subdirectory, check if that subdirectory contains a `.claude/CLAUDE.md` file. If so, read it and apply those rules in addition to these universal rules.

For example:
- Editing `backend/app/main.py` → also read `backend/.claude/CLAUDE.md`
- Editing `frontend/src/App.tsx` → also read `frontend/.claude/CLAUDE.md`

Always apply the most specific rules available for the code you're working on.
```

## Step 5: Create subdirectory .claude/CLAUDE.md files

For each subdirectory with detected languages, create `{subdir}/.claude/CLAUDE.md`:

```bash
mkdir -p {subdir}/.claude
```

Assemble with:
1. Header comment (noting it's for that subdirectory)
2. Language-specific rules from `$CLAUDE_CONFIG_PATH/claude-md/languages/{lang}/{lang}.md`

**Header:**
```markdown
<!-- Assembled by /setup-project from claude-config -->
<!-- Subdirectory: {subdir} -->
<!-- Languages: {lang} -->
<!-- Re-run /setup-project to regenerate -->
```

## Step 6: Link skills

```bash
mkdir -p ~/.claude/skills
```

**Universal skills (always):**
```bash
ln -sf "$CLAUDE_CONFIG_PATH/skills/universal/implement" ~/.claude/skills/
ln -sf "$CLAUDE_CONFIG_PATH/skills/universal/review" ~/.claude/skills/
ln -sf "$CLAUDE_CONFIG_PATH/skills/validators/validate" ~/.claude/skills/
ln -sf "$CLAUDE_CONFIG_PATH/skills/validators/security" ~/.claude/skills/
```

**Advisory skills (always):**
```bash
ln -sf "$CLAUDE_CONFIG_PATH/skills/advisory/star-chamber" ~/.claude/skills/
```

**Go (if detected anywhere):**
```bash
ln -sf "$CLAUDE_CONFIG_PATH/skills/validators/go-proverbs" ~/.claude/skills/
ln -sf "$CLAUDE_CONFIG_PATH/skills/validators/go-effective" ~/.claude/skills/
```

**Python (if detected anywhere):**
```bash
ln -sf "$CLAUDE_CONFIG_PATH/skills/validators/python-style" ~/.claude/skills/
```

**TypeScript (if detected anywhere):**
```bash
ln -sf "$CLAUDE_CONFIG_PATH/skills/validators/typescript-style" ~/.claude/skills/
```

## Step 7: Offer reference configs

### Go linter config

For Go projects, if no golangci-lint config exists:
```bash
{ [[ ! -f .golangci.yml ]] && [[ ! -f .golangci.yaml ]]; } && echo "no-lint-config"
true
```

If missing, offer to copy from `$CLAUDE_CONFIG_PATH/reference/go/golangci-lint.yml`, replacing `{org}` and `{repo}`.

### Star-Chamber provider config

Check if star-chamber config exists:
```bash
[[ ! -f ~/.config/star-chamber/providers.json ]] && echo "no-star-chamber-config"
```

If missing, offer to set it up:

```
/star-chamber requires provider configuration for multi-LLM reviews.

Would you like to set up the default configuration?

This will configure OpenAI, Anthropic, and Gemini providers.
API keys are read from environment variables.

[Yes, set it up] / [No, skip for now]
```

**If user accepts:**
```bash
mkdir -p ~/.config/star-chamber
cp "$CLAUDE_CONFIG_PATH/reference/star-chamber/providers.json" ~/.config/star-chamber/providers.json
```

Then include in the summary:
```
**Star-Chamber configured:**
  Config: ~/.config/star-chamber/providers.json

  Required environment variables:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - GEMINI_API_KEY

  Edit the config to remove providers you don't have keys for.
```

**If user declines**, note in summary:
```
**Star-Chamber:** Not configured (run /star-chamber to set up later)
```

## Step 8: Output summary

```
## Setup Complete

**Project:** {org}/{repo}

**Structure detected:**
  - Root: [languages or "none"]
  - backend/: Python
  - frontend/: TypeScript

**Created:**
  - .claude/CLAUDE.md (universal + meta-rule)
  - backend/.claude/CLAUDE.md (Python rules)
  - frontend/.claude/CLAUDE.md (TypeScript rules)

**Skills linked:**
  - /implement - implement with auto-validation
  - /review - review changes against all validators
  - /validate - run all validators
  - /star-chamber - multi-LLM advisory council

**Usage:**
  /implement <task>    - implement with validation loop
  /review              - validate current changes

**Star-Chamber Usage:**
  /star-chamber                                                 - review recent changes using configured providers
  /star-chamber --file <file> --provider <provider1,provider2>  - target specific files and providers
  /star-chamber --deliberate N                                  - sequential council deliberation (feed responses around)
  /star-chamber --interject N                                   - parallel interjections from all providers (rubber-ducking)

**Note:** Add `**/.claude/CLAUDE.md` to .gitignore
```
