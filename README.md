# Claude Pragma

Pragma directives for Claude Code - rules that stick.

## Quick Start

```bash
# Clone and install
git clone git@github.com:peteski22/claude-pragma.git
cd claude-pragma
make install

# Add to your shell profile (~/.zshrc or ~/.bashrc)
export CLAUDE_PRAGMA_PATH="/path/to/claude-pragma"  # use actual path from make install output

# In any project, run:
/setup-project
```

## Skills

### Universal Skills

| Skill | Description |
|-------|-------------|
| `/setup-project` | Auto-detect languages, create CLAUDE.md files, link validators |
| `/implement <task>` | Implement with validation loop - runs linters and validators automatically |
| `/review` | Review current changes against all validators |

### Validators

| Skill | Language | Description |
|-------|----------|-------------|
| `/validate` | All | Orchestrator - runs all applicable validators |
| `/security` | All | Check for secrets, injection, path traversal, auth gaps |
| `/python-style` | Python | Google docstrings, type hints, error handling, architecture |
| `/typescript-style` | TypeScript | Strict mode, React patterns, hooks usage, state management |
| `/go-effective` | Go | Effective Go rules - naming, error handling, interfaces |
| `/go-proverbs` | Go | Go Proverbs - idiomatic patterns, concurrency, abstraction |

### Advisory Skills

| Skill | Description |
|-------|-------------|
| `/star-chamber` | Multi-LLM review council (OpenAI, Anthropic, Gemini) with consensus feedback |

## Usage

```bash
# Set up a new project
/setup-project

# Implement a feature (includes validation)
/implement add user authentication

# Review your changes
/review

# Get multi-LLM feedback (optional)
/star-chamber
/star-chamber --debate --rounds 2
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAUDE_PRAGMA_PATH` | Yes | Path to cloned claude-pragma repo |
| `STAR_CHAMBER_CONFIG` | No | Custom path to star-chamber config (default: `~/.config/star-chamber/providers.json`) |
| `OPENAI_API_KEY` | For star-chamber | OpenAI API key (direct mode) |
| `ANTHROPIC_API_KEY` | For star-chamber | Anthropic API key (direct mode) |
| `GEMINI_API_KEY` | For star-chamber | Google Gemini API key (direct mode) |
| `ANY_LLM_KEY` | For star-chamber | Platform key from any-llm.ai (alternative to individual keys) |

## Directory Structure

```
claude-pragma/
├── claude-md/
│   ├── universal/          # Universal rules for all projects
│   └── languages/          # Language-specific rules (go, python, typescript)
├── skills/
│   ├── universal/          # setup-project, implement, review
│   ├── validators/         # validate, security, python-style, etc.
│   └── advisory/           # star-chamber
└── reference/              # Template configs (golangci-lint, providers.json)
```

## Monorepo Support

`/setup-project` detects languages at root AND in subdirectories:

```
myproject/
├── .claude/CLAUDE.md           # Universal rules
├── backend/
│   ├── .claude/CLAUDE.md       # Python rules
│   └── pyproject.toml
└── frontend/
    ├── .claude/CLAUDE.md       # TypeScript rules
    └── package.json
```

## Validator Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **HARD** | Must fix | Blocks completion |
| **SHOULD** | Fix or justify | Requires justification to proceed |
| **WARN** | Advisory | Noted but doesn't block |

## Gitignore

Generated CLAUDE.md files should be gitignored:

```gitignore
**/.claude/CLAUDE.md
```

Each developer runs `/setup-project` to generate their local copy.

## More Information

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design decisions, validator contracts, and system flow diagrams.
