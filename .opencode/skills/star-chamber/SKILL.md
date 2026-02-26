---
name: star-chamber
description: Multi-LLM craftsmanship council for code review and design questions - fans out to multiple LLM providers
---

# Star-Chamber: Multi-LLM Craftsmanship Council

Advisory skill that fans out code reviews and design questions to multiple LLM providers (Claude, OpenAI, Gemini, etc.) and aggregates their feedback into consensus recommendations.

## Arguments

| Flag | Description |
|------|-------------|
| `--provider <name>` | LLM provider to use (repeatable). Defaults to all in config. |
| `--file <path>` | Specify file to review (repeatable). Defaults to recent git changes. |
| `--timeout <seconds>` | Timeout per provider request. |
| `--list-sdks` | Show configured providers and required SDK packages. |
| `--debate` | Enable debate mode: multiple rounds with summarization between rounds. |
| `--rounds N` | Number of debate rounds (default: 2, requires --debate). |

## Path Setup

Set the path to the star-chamber skill directory:

```bash
STAR_CHAMBER_PATH="plugins/pragma/skills/star-chamber"
```

## Protocol

Read and follow the full protocol from `$STAR_CHAMBER_PATH/PROTOCOL.md`. It contains Steps 0-6: prerequisite checks, invocation mode detection (code review vs design question), review target identification, context injection, prompt construction, fan-out to providers, result aggregation, and presentation.
