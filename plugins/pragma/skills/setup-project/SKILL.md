---
name: setup-project
description: Configure Claude Code for this project - detects languages and sets up rules, skills, and validators
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob
---

# Project Setup

Automatically configure Claude Code for the current project. Supports monorepos with multiple languages in subdirectories.

## Step 0: Resolve plugin root

The skill loader provides the base directory in the header: `Base directory for this skill: <path>`. Derive the plugin root from that:

```text
PLUGIN_ROOT = <base directory>/../../
```

For example, if the skill base directory is `~/.claude/plugins/cache/pragma/skills/setup-project`, then `PLUGIN_ROOT` is `~/.claude/plugins/cache/pragma`.

Verify the plugin root is valid by checking for the plugin manifest:

```bash
PLUGIN_ROOT="<base directory>/../.."
[[ -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" ]] && echo "OK" || echo "ERROR: Plugin root invalid - .claude-plugin/plugin.json not found at $PLUGIN_ROOT"
true
```

**Note:** Replace `<base directory>` with the actual path from the skill loader header above. For example, if the header says `Base directory for this skill: /home/user/.claude/plugins/cache/pragma/skills/setup-project`, then `PLUGIN_ROOT="/home/user/.claude/plugins/cache/pragma/skills/setup-project/../.."`.

**If the check fails**, stop and show:
```text
Plugin root could not be resolved. The pragma plugin may not be installed correctly.

Reinstall:
  /plugin marketplace add peteski22/agent-pragma
  /plugin install pragma@agent-pragma
```

**STOP if check fails. Do not proceed.**

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

If any exist, read them. If they have `<!-- Assembled by /setup-project` comment, safe to overwrite. Otherwise, ask before overwriting.

## Step 4: Create root .claude/CLAUDE.md

Create the directory:
```bash
mkdir -p .claude
```

Assemble root CLAUDE.md with:
1. Header comment
2. Universal rules from `$PLUGIN_ROOT/claude-md/universal/base.md`
3. **Meta-rule for subdirectory awareness** (always include this)
4. Root-level language rules (if any detected at root)

**Header:**
```markdown
<!-- Assembled by /setup-project from agent-pragma -->
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

<!-- NOTE: This section intentionally mirrors claude-md/universal/context-aware.md.
     Generated files must be standalone (users' repos can't reference agent-pragma).
     Update both files together if this guidance changes. -->
## Local Supplements

`CLAUDE.local.md` at the project root contains per-user, per-project instructions. Claude Code auto-loads it and adds it to `.gitignore`; if you create the file manually, verify it is in your `.gitignore`.

### Validation Command Overrides

Rules from `CLAUDE.local.md` are generally additive, but can override validation commands. Add a "Validation Commands" section to `CLAUDE.local.md` to specify custom lint/test scripts:

```markdown
## Validation Commands

- **Lint:** `./scripts/backend-lint.sh`
- **Test:** `./scripts/backend-test.sh`
```

These override the defaults in the language rules. Precedence (highest → lowest): CLAUDE.local.md > subdirectory rules > root rules > built-in defaults.

**Common scenarios for overriding validation commands:**

- **Wrapper scripts:** Your project has `./scripts/lint.sh` that runs multiple tools (ruff + mypy + security scans) in sequence
- **Tool versioning:** Use a specific linter version not available in the default environment
- **Integration tests:** Run integration tests as part of the validation process before commits
- **Security scanning:** Add custom vulnerability checks (e.g., `bandit`, `semgrep`) before commits
- **CI/CD parity:** Match the exact validation commands used in your CI pipeline
- **Monorepo isolation:** Different validation commands for different subdirectories

### Other Uses

- Custom environment setup notes.
- Personal workflow preferences.
- Machine-specific paths or configurations.

In git worktrees, use `@import` (a Claude Code directive that includes another CLAUDE.md file) in `CLAUDE.local.md` to reference a shared local rules file rather than duplicating it per worktree (e.g., `@import ../shared-local-rules.md`).
```

**Create local supplements file and ensure it is gitignored:**
```bash
test -f CLAUDE.local.md || touch CLAUDE.local.md
grep -qxF 'CLAUDE.local.md' .gitignore 2>/dev/null || echo 'CLAUDE.local.md' >> .gitignore
```

## Step 5: Create subdirectory .claude/CLAUDE.md files

For each subdirectory with detected languages, create `{subdir}/.claude/CLAUDE.md`:

```bash
mkdir -p {subdir}/.claude
```

Assemble with:
1. Header comment (noting it's for that subdirectory)
2. Language-specific rules from `$PLUGIN_ROOT/claude-md/languages/{lang}/{lang}.md`

**Header:**
```markdown
<!-- Assembled by /setup-project from agent-pragma -->
<!-- Subdirectory: {subdir} -->
<!-- Languages: {lang} -->
<!-- Re-run /setup-project to regenerate -->
```

## Step 6: Verify plugin skills and agents

All skills and agents are provided by the pragma plugin — no symlinks needed.

**Check star-chamber prerequisites:**
```bash
command -v uv >/dev/null 2>&1 && echo "uv:ok" || echo "uv:missing"
```

Store the result - if `uv:missing`, include a warning in Step 8 output.

**Build go-structural (ONLY if Go was detected in Step 2):**

Skip this entirely if no `go` language was detected in Step 2 output (e.g. if the only output was `root:python`, there is no Go — do not build go-structural).

If and only if Go was detected (any line matching `*:go` in Step 2 output):

```bash
cd "$PLUGIN_ROOT/tools/go-structural" && go build -o go-structural . && echo "go-structural:ok" || echo "go-structural:build-failed"
```

If `go` is not available or the build fails, note in Step 8 output that go-structural is unavailable.

## Step 7: Offer reference configs

### Go linter config

For Go projects, if no golangci-lint config exists:
```bash
test -f .golangci.yml || test -f .golangci.yaml || echo "no-lint-config"
true
```

If missing, offer to copy from `$PLUGIN_ROOT/reference/go/golangci-lint.yml`, replacing `{org}` and `{repo}`.

### Star-Chamber provider config

Check if star-chamber config exists:
```bash
test -f "$HOME/.config/star-chamber/providers.json" || echo "no-star-chamber-config"
```

If missing **and `uv` is available** (from the Step 6 check), offer to set it up. If `uv` is missing, skip this offer and tell the user: "Skipping star-chamber config — `uv` is not installed." The Step 8 output includes install instructions.

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
uv run --no-project --isolated python "$PLUGIN_ROOT/reference/star-chamber/generate_config.py" --platform
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
uv run --no-project --isolated python "$PLUGIN_ROOT/reference/star-chamber/generate_config.py" --direct
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

**Skills available (via pragma plugin):**
  - /implement - implement with auto-validation
  - /review - review changes against all validators
  - /validate - run all validators
  - /star-chamber - multi-LLM advisory council

**Agents available (via pragma plugin):**
  - security - auto-invokes on trust boundary changes
  - star-chamber - auto-invokes on architectural decisions

**Usage:**
  /implement <task>    - implement with validation loop
  /review              - validate current changes

Run `/star-chamber` for usage details and options.
```

**If uv is missing**, include this warning:
```text
⚠️  **Warning:** uv is not installed. /star-chamber requires uv to run.

Install uv:
  curl -LsSf https://astral.sh/uv/install.sh | sh

Or see: https://docs.astral.sh/uv/getting-started/installation/
```

Then continue with:
```
**Recommended:**
  - Commit the generated `.claude/CLAUDE.md` files so other developers get the same rules.
  - `CLAUDE.local.md` has been created for personal/machine-specific rules (custom validation commands, local environment notes, personal workflow preferences). It is auto-loaded by Claude Code and gitignored.
```
