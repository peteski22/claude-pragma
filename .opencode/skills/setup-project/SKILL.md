---
name: setup-project
description: Configure this project for pragma rules enforcement - detects languages and sets up rules and validators
---

# Project Setup

Automatically configure the current project for pragma rules enforcement. Supports monorepos with multiple languages in subdirectories. Works for both Claude Code and OpenCode.

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
[[ -f .claude/CLAUDE.md ]] && echo "root:claude-exists"
[[ -f AGENTS.md ]] && echo "root:agents-exists"
for dir in */; do
  [[ -f "${dir}.claude/CLAUDE.md" ]] && echo "${dir%/}:claude-exists"
  [[ -f "${dir}AGENTS.md" ]] && echo "${dir%/}:agents-exists"
done
true
```

If any exist, read them. If they have `<!-- Assembled by /setup-project` comment, safe to overwrite. Otherwise, ask before overwriting.

## Step 4: Create root .claude/CLAUDE.md

Create the directory:
```bash
mkdir -p .claude
```

Assemble root CLAUDE.md by reading and combining:
1. Header comment
2. Universal rules from `plugins/pragma/claude-md/universal/base.md`
3. Context-aware rules section (always include)
4. Root-level language rules (if any detected at root)

**Header:**
```markdown
<!-- Assembled by /setup-project from claude-pragma -->
<!-- Org/Repo: {org}/{repo} -->
<!-- Re-run /setup-project to regenerate -->
```

Read the universal rules from `plugins/pragma/claude-md/universal/base.md` and include them. Then add the context-aware rules section and any language-specific rules for languages detected at root from `plugins/pragma/claude-md/languages/{lang}/{lang}.md`.

## Step 5: Create subdirectory .claude/CLAUDE.md files

For each subdirectory with detected languages, create `{subdir}/.claude/CLAUDE.md`:

```bash
mkdir -p {subdir}/.claude
```

Assemble with:
1. Header comment (noting it's for that subdirectory)
2. Language-specific rules from `plugins/pragma/claude-md/languages/{lang}/{lang}.md`

## Step 6: Create local supplements file

```bash
! [[ -f CLAUDE.local.md ]] && touch CLAUDE.local.md
grep -qxF 'CLAUDE.local.md' .gitignore 2>/dev/null || echo 'CLAUDE.local.md' >> .gitignore
```

## Step 7: Verify tooling prerequisites

**Check star-chamber prerequisites:**
```bash
command -v uv >/dev/null 2>&1 && echo "uv:ok" || echo "uv:missing"
```

**Build go-structural (ONLY if Go was detected in Step 2):**

If Go was detected:

```bash
PLUGIN_ROOT="plugins/pragma"
cd "$PLUGIN_ROOT/tools/go-structural" && go build -o go-structural . && echo "go-structural:ok" || echo "go-structural:build-failed"
```

## Step 8: Offer reference configs

### Go linter config

For Go projects, if no golangci-lint config exists:
```bash
{ ! [[ -f .golangci.yml ]] && ! [[ -f .golangci.yaml ]]; } && echo "no-lint-config"
true
```

If missing, offer to copy from `plugins/pragma/reference/go/golangci-lint.yml`.

## Step 9: Output summary

```
## Setup Complete

**Project:** {org}/{repo}

**Structure detected:**
  - Root: [languages or "none"]
  - backend/: Python
  - frontend/: TypeScript

**Created:**
  - .claude/CLAUDE.md (universal + context-aware rules)
  - backend/.claude/CLAUDE.md (Python rules)
  - frontend/.claude/CLAUDE.md (TypeScript rules)

**Skills available:**
  - /implement (or load implement skill) - implement with auto-validation
  - /review (or load review skill) - review changes against all validators
  - /validate (or load validate skill) - run all validators
  - /star-chamber (or load star-chamber skill) - multi-LLM advisory council

**Agents available:**
  - security - auto-invokes on trust boundary changes
  - star-chamber - auto-invokes on architectural decisions

**Usage (Claude Code):**
  /implement <task>    - implement with validation loop
  /review              - validate current changes

**Usage (OpenCode):**
  /implement <task>    - implement with validation loop (via command)
  /review              - validate current changes (via command)
  Or load skills directly via the skill tool.

**Recommended:**
  - Commit the generated `.claude/CLAUDE.md` files so other developers get the same rules.
  - `CLAUDE.local.md` has been created for personal/machine-specific rules. It is gitignored.
```
