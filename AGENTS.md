# Claude Pragma

Claude Pragma is a coding rules enforcement plugin. It mechanically injects rules before every task and validates compliance via deterministic linters and semantic LLM validators. Validators are authoritative -- if there is a conflict between rules guidance and a validator, the validator wins.

## Project Structure

```
plugins/pragma/
  .claude-plugin/       # Claude Code plugin manifest
  agents/               # Custom subagents (security, star-chamber)
  claude-md/            # Rule templates (universal + per-language)
    universal/          # Rules that apply to all projects
    languages/          # Language-specific rules (Go, Python, TypeScript)
  reference/            # Reference configs (golangci-lint, biome, pyproject, etc.)
  skills/               # Slash commands / skills
    implement/          # /implement - implement with auto-validation
    review/             # /review - review changes against validators
    validate/           # /validate - run all validators
    setup-project/      # /setup-project - one-time project setup
    star-chamber/       # /star-chamber - multi-LLM advisory council
    security/           # Security vulnerability checker (model-invocable)
    python-style/       # Python style validator (model-invocable)
    typescript-style/   # TypeScript style validator (model-invocable)
    go-effective/       # Effective Go validator (model-invocable)
    go-proverbs/        # Go Proverbs validator (model-invocable)
    state-machine/      # State machine correctness validator (model-invocable)
  tools/                # Deterministic Go structural linter
    go-structural/
```

## Dual-Agent Compatibility

This project supports both **Claude Code** and **OpenCode**:

- **Claude Code** uses the plugin system under `plugins/pragma/` directly (`.claude-plugin/`, skills via `SKILL.md`, agents under `agents/`).
- **OpenCode** uses equivalent configurations under `.opencode/` (skills, agents, commands) that reference the same rule content.

Both systems share the same underlying rule files in `plugins/pragma/claude-md/` and the same skill instruction bodies in `plugins/pragma/skills/`.

## Rule Files

The core rule content lives in `plugins/pragma/claude-md/`:

- `plugins/pragma/claude-md/universal/base.md` - Universal rules for all projects
- `plugins/pragma/claude-md/universal/context-aware.md` - Subdirectory rule awareness
- `plugins/pragma/claude-md/universal/validation-precedence.md` - Validation command precedence
- `plugins/pragma/claude-md/languages/go/go.md` - Go language rules
- `plugins/pragma/claude-md/languages/python/python.md` - Python language rules
- `plugins/pragma/claude-md/languages/typescript/typescript.md` - TypeScript language rules

## Skills and Commands

User-invocable commands:
- `/implement <task>` - Implement a feature/fix with 5-phase workflow and automatic validation
- `/review` - Review current changes against all applicable validators
- `/validate` - Run all validators against recent changes
- `/setup-project` - One-time project setup (detect languages, create rule files)
- `/star-chamber` - Multi-LLM advisory council for code review and design questions

Internal validators (invoked automatically by implement/review/validate):
- `security` - OWASP-based security vulnerability checker
- `python-style` - Python style and architecture validator
- `typescript-style` - TypeScript/React style validator
- `go-effective` - Effective Go conventions validator
- `go-proverbs` - Go Proverbs philosophy validator
- `state-machine` - State machine and lifecycle correctness validator

## Validation Severity Model

- **HARD** - Must fix. Blocks completion.
- **SHOULD** - Fix or explicitly justify. Blocks unless justified.
- **WARN** - Advisory only. Note but don't block.
