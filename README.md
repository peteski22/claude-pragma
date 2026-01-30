# Claude Config

Composable configuration for Claude Code: rules, skills, hooks, and validators.

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
claude-config/
├── claude-md/
│   ├── universal/           # Rules for all projects
│   │   └── base.md
│   └── languages/
│       ├── go/
│       │   └── go.md        # Go Proverbs, Effective Go, etc.
│       └── python/
│           └── python.md
├── hooks/
│   └── *.sh                 # Hook scripts for deterministic checks
├── skills/
│   ├── universal/           # Skills for all projects
│   ├── languages/
│   │   └── go/              # Go-specific skills
│   └── validators/          # Validator agent skills
│       ├── go-proverbs/
│       ├── effective-go/
│       └── security/
└── scripts/
    └── assemble.sh          # Assemble CLAUDE.md for a project
```

## Usage

### Assembling a CLAUDE.md

For a Go project, concatenate the relevant fragments:

```bash
cat claude-md/universal/base.md \
    claude-md/languages/go/go.md \
    > /path/to/project/.claude/CLAUDE.md
```

Or use the assembly script:

```bash
./scripts/assemble.sh --lang go --output /path/to/project/.claude/CLAUDE.md
```

### Installing Skills

Symlink relevant skills to your Claude config:

```bash
# Universal skills
ln -s /path/to/claude-config/skills/universal/* ~/.claude/skills/

# Language-specific skills (Go project)
ln -s /path/to/claude-config/skills/languages/go/* ~/.claude/skills/

# Validators
ln -s /path/to/claude-config/skills/validators/* ~/.claude/skills/
```

### Running Validators

After making changes, run validators:

```
/validate           # Run all validators
/validate-go        # Run Go-specific validators
```

Validators examine git diff and check against their rulesets, reporting violations.

## Validator Agent Pattern

Validators are skills with `context: fork` that:

1. Examine recent changes (git diff, staged files)
2. Check against a specific, focused ruleset
3. Report violations with file:line references
4. Can fetch current documentation (not relying on training data)

Example validator structure:

```yaml
---
name: validate-go-proverbs
description: Check Go code against Go Proverbs
context: fork
agent: general-purpose
user-invocable: false
---

[Focused instructions for checking Go Proverbs]
```

The orchestrator (`/validate`) spawns these in parallel and aggregates results.

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
