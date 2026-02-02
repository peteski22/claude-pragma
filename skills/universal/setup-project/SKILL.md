---
name: setup-project
description: Configure Claude Code for this project - detects languages and sets up rules, skills, and validators
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob
---

# Project Setup

Automatically configure Claude Code for the current project. Supports monorepos with multiple languages in subdirectories.

## Step 0: Verify config repo

Requires `$CLAUDE_PRAGMA_PATH` environment variable to be set.

```bash
echo "$CLAUDE_PRAGMA_PATH"
[[ -z "$CLAUDE_PRAGMA_PATH" ]] && echo "ERROR: CLAUDE_PRAGMA_PATH not set"
[[ ! -d "$CLAUDE_PRAGMA_PATH" ]] && echo "ERROR: CLAUDE_PRAGMA_PATH does not exist"
[[ ! -f "$CLAUDE_PRAGMA_PATH/claude-md/universal/base.md" ]] && echo "ERROR: Invalid claude-pragma repo"
```

If not set, tell the user:

```
CLAUDE_PRAGMA_PATH is not set.

1. Clone the config repo:
   git clone git@github.com:{org}/claude-pragma.git ~/src/claude-pragma

2. Set the environment variable (add to ~/.zshrc or ~/.bashrc):
   export CLAUDE_PRAGMA_PATH="$HOME/src/claude-pragma"

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

Create the directories:
```bash
mkdir -p .claude
mkdir -p .claude/local
```

Assemble root CLAUDE.md with:
1. Header comment
2. Universal rules from `$CLAUDE_PRAGMA_PATH/claude-md/universal/base.md`
3. **Meta-rule for subdirectory awareness** (always include this)
4. Root-level language rules (if any detected at root)

**Header:**
```markdown
<!-- Assembled by /setup-project from claude-pragma -->
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

## Local Supplements

If `.claude/local/CLAUDE.md` exists, read it and apply those rules in addition to the generated rules. Use this for project-specific additions like custom test commands or local environment notes.

Local supplements are additive only. If a local rule conflicts with a generated rule, the generated rule takes precedence. Use local supplements for additions, not for overriding core behavior.

Add `.claude/local/` to your `.gitignore` to keep personal rules out of version control.
```

**Create empty local CLAUDE.md (only if it doesn't exist):**
```bash
[[ ! -f .claude/local/CLAUDE.md ]] && touch .claude/local/CLAUDE.md
```

## Step 5: Create subdirectory .claude/CLAUDE.md files

For each subdirectory with detected languages, create `{subdir}/.claude/CLAUDE.md`:

```bash
mkdir -p {subdir}/.claude
```

Assemble with:
1. Header comment (noting it's for that subdirectory)
2. Language-specific rules from `$CLAUDE_PRAGMA_PATH/claude-md/languages/{lang}/{lang}.md`

**Header:**
```markdown
<!-- Assembled by /setup-project from claude-pragma -->
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
ln -sf "$CLAUDE_PRAGMA_PATH/skills/universal/implement" ~/.claude/skills/
ln -sf "$CLAUDE_PRAGMA_PATH/skills/universal/review" ~/.claude/skills/
ln -sf "$CLAUDE_PRAGMA_PATH/skills/validators/validate" ~/.claude/skills/
ln -sf "$CLAUDE_PRAGMA_PATH/skills/validators/security" ~/.claude/skills/
```

**Advisory skills (always):**
```bash
ln -sf "$CLAUDE_PRAGMA_PATH/skills/advisory/star-chamber" ~/.claude/skills/
```

**Check star-chamber prerequisites:**
```bash
command -v uvx >/dev/null 2>&1 && echo "uvx:ok" || echo "uvx:missing"
```

Store the result - if `uvx:missing`, include a warning in Step 8 output.

**Go (if detected anywhere):**
```bash
ln -sf "$CLAUDE_PRAGMA_PATH/skills/validators/go-proverbs" ~/.claude/skills/
ln -sf "$CLAUDE_PRAGMA_PATH/skills/validators/go-effective" ~/.claude/skills/
```

**Python (if detected anywhere):**
```bash
ln -sf "$CLAUDE_PRAGMA_PATH/skills/validators/python-style" ~/.claude/skills/
```

**TypeScript (if detected anywhere):**
```bash
ln -sf "$CLAUDE_PRAGMA_PATH/skills/validators/typescript-style" ~/.claude/skills/
```

## Step 7: Offer reference configs

### Go linter config

For Go projects, if no golangci-lint config exists:
```bash
{ [[ ! -f .golangci.yml ]] && [[ ! -f .golangci.yaml ]]; } && echo "no-lint-config"
true
```

If missing, offer to copy from `$CLAUDE_PRAGMA_PATH/reference/go/golangci-lint.yml`, replacing `{org}` and `{repo}`.

### Star-Chamber provider config

Check if star-chamber config exists:
```bash
[[ ! -f ~/.config/star-chamber/providers.json ]] && echo "no-star-chamber-config"
```

If missing, offer to set it up:

```
/star-chamber requires provider configuration for multi-LLM reviews.

Would you like to set up the configuration?

[Yes, set it up] / [No, skip for now]
```

**If user accepts**, ask about API key management:

```
How would you like to manage API keys?

[any-llm.ai platform] - Single ANY_LLM_KEY, centralized key vault, usage tracking
[Direct provider keys] - Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY individually
```

**If user chooses "any-llm.ai platform":**
```bash
mkdir -p ~/.config/star-chamber
cat > ~/.config/star-chamber/providers.json << 'EOF'
{
  "platform": "any-llm",
  "providers": [
    {"provider": "openai", "model": "gpt-4o"},
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
    {"provider": "gemini", "model": "gemini-2.0-flash"}
  ],
  "consensus_threshold": 2,
  "timeout_seconds": 60
}
EOF
```

Then include in the summary:
```
**Star-Chamber configured (any-llm.ai platform mode):**
  Config: ~/.config/star-chamber/providers.json

  Setup:
    1. Create account at https://any-llm.ai
    2. Create a project and add your provider API keys
    3. Copy your project key and set:
       export ANY_LLM_KEY="ANY.v1...."
```

**If user chooses "Direct provider keys":**
```bash
mkdir -p ~/.config/star-chamber
cp "$CLAUDE_PRAGMA_PATH/reference/star-chamber/providers.json" ~/.config/star-chamber/providers.json
```

Then include in the summary:
```
**Star-Chamber configured (direct keys mode):**
  Config: ~/.config/star-chamber/providers.json

  Set these environment variables:
    export OPENAI_API_KEY="sk-..."
    export ANTHROPIC_API_KEY="sk-ant-..."
    export GEMINI_API_KEY="..."

  Edit the config to remove providers you don't have keys for.
```

**If user declines setup**, note in summary:
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
  /star-chamber --file <file> --provider openai --provider gemini  - target specific files and providers
  /star-chamber --debate                                        - enable debate mode (2 rounds, each sees others' responses)
  /star-chamber --debate --rounds 3                             - debate mode with 3 rounds of deliberation
```

**If uvx is missing**, include this warning:
```
⚠️  **Warning:** uvx is not installed. /star-chamber requires uvx to run.

Install uvx:
  curl -LsSf https://astral.sh/uv/install.sh | sh

Or see: https://docs.astral.sh/uv/getting-started/installation/
```

Then continue with:
```
**Important:** Start a new Claude Code session for newly linked skills to be available.

**Recommended:**
  - Commit the generated `.claude/CLAUDE.md` files so other developers get the same rules.
  - Add `.claude/local/` to `.gitignore` for personal supplements.
```
