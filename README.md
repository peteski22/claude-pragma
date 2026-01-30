# Claude Pragma

Composable configuration for Claude Code: rules, skills, hooks, and validators.

## Quick Start

```bash
# 1. Clone this repo
git clone git@github.com:{org}/claude-pragma.git ~/src/claude-pragma

# 2. Set environment variable (add to ~/.zshrc or ~/.bashrc)
export CLAUDE_PRAGMA_PATH="$HOME/src/claude-pragma"

# 3. Create skills directory and link the setup skill
mkdir -p ~/.claude/skills
ln -s "$CLAUDE_PRAGMA_PATH/skills/universal/setup-project" ~/.claude/skills/

# 4. In any project, run:
/setup-project
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAUDE_PRAGMA_PATH` | Yes | Path to cloned claude-pragma repo |
| `STAR_CHAMBER_CONFIG` | No | Custom path to star-chamber providers.json (default: `~/.config/star-chamber/providers.json`) |
| `OPENAI_API_KEY` | For star-chamber | OpenAI API key |
| `ANTHROPIC_API_KEY` | For star-chamber | Anthropic API key |
| `GEMINI_API_KEY` | For star-chamber | Google Gemini API key |
| `ANY_LLM_KEY` | For star-chamber | Platform key from any-llm.ai (alternative to individual provider keys) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLAUDE.md                               │
│  (Assembled from composable fragments based on project)     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Primary Agent                             │
│                   (does the work)                           │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│        Hooks         │    │      Validator Agents            │
│  (deterministic      │    │  (check rules were followed)     │
│   enforcement)       │    │                                  │
└──────────────────────┘    └──────────────────────────────────┘
```

## Problem Statement

CLAUDE.md rules are **guidance** - they can be ignored or forgotten. We need:

1. **Deterministic enforcement** via hooks where possible
2. **Validator agents** that check work against specific rulesets
3. **Composable configs** - universal rules + language-specific + project-specific

## Directory Structure

```
claude-pragma/
├── claude-md/
│   ├── universal/
│   │   ├── base.md              # Universal rules for all projects
│   │   └── context-aware.md     # Meta-rule for subdirectory awareness
│   └── languages/
│       ├── go/go.md             # Go Proverbs, Effective Go, etc.
│       └── python/python.md     # PEP 8, pytest, etc.
├── hooks/                       # Hook scripts (deterministic checks)
├── skills/
│   ├── universal/
│   │   ├── setup-project/       # Configure Claude for a project
│   │   ├── implement/           # Implement with auto-validation
│   │   └── review/              # Review changes against validators
│   └── validators/
│       ├── validate/            # Orchestrator - runs all validators
│       ├── go-effective/        # Effective Go (HARD/SHOULD/WARN)
│       ├── go-proverbs/         # Go Proverbs
│       └── security/            # Security vulnerabilities
└── reference/
    └── go/golangci-lint.yml     # Reference linter config
```

## Skills

| Skill | Purpose |
|-------|---------|
| `/setup-project` | Auto-detect languages, create CLAUDE.md files, link validators |
| `/implement <task>` | Implement with validation loop built-in |
| `/review` | Review current changes against all validators |
| `/validate` | Run all validators (called by /implement and /review) |
| `/star-chamber` | Multi-LLM advisory review (OpenAI, Anthropic, Gemini consensus) |

## Workflow

```bash
# In a new project
/setup-project

# When implementing features
/implement add user authentication

# To check your work anytime
/review

# When ready to commit
/commit
```

### What `/implement` Does

1. Implements the requested feature
2. Runs linters (golangci-lint, pre-commit, etc.)
3. Spawns validator agents in parallel
4. Fixes HARD violations automatically
5. Reports SHOULD violations (fix or justify)
6. Only says "done" when validation passes

## Monorepo Support

`/setup-project` detects languages at root AND in subdirectories:

```
myproject/
├── .claude/CLAUDE.md           # Universal + meta-rule
├── backend/
│   ├── .claude/CLAUDE.md       # Python rules
│   └── pyproject.toml
├── frontend/
│   ├── .claude/CLAUDE.md       # TypeScript rules
│   └── package.json
```

The root CLAUDE.md includes a **meta-rule** that tells Claude to read subdirectory rules when working in that context.

## Validator Agent Pattern

Validators are skills with `context: fork` that:

1. Examine recent changes (git diff)
2. Check against a specific, focused ruleset
3. Report violations with file:line references
4. Can fetch current documentation (not relying on training data)

### Severity Levels

| Level | Meaning |
|-------|---------|
| **HARD** | Must fix - validation fails |
| **SHOULD** | Fix or justify - fails unless justified |
| **WARN** | Advisory only - doesn't fail |

## Gitignore

Generated CLAUDE.md files should be gitignored:

```gitignore
**/.claude/CLAUDE.md
```

Each developer runs `/setup-project` to generate their local copy. The source of truth is this config repo.

## Why This Works Better

| Approach | Enforcement | Context-Aware |
|----------|-------------|---------------|
| Single CLAUDE.md | Guidance only | No |
| Hooks | Deterministic | Limited |
| Validator Agents | Verification | Yes |
| **Combined** | **Best of all** | **Yes** |

- **Hooks** catch obvious violations deterministically (linting, formatting)
- **Validators** check nuanced rules that need LLM understanding
- **Composable configs** mean only relevant rules are loaded
- **`/implement`** bakes validation into the workflow
