---
name: star-chamber
description: Advisory multi-LLM craftsmanship council for code and architecture review
user-invocable: true
allowed-tools: Bash, Read, Glob, Grep
---

# Star-Chamber: Multi-LLM Craftsmanship Council

Advisory skill that fans out code reviews to multiple LLM providers (Claude, OpenAI, Gemini, etc.) and aggregates their feedback into consensus recommendations.

**Key characteristics:**
- Advisory only (doesn't block like validators)
- Uses `any-llm-sdk` via `uvx` (no global Python install needed)
- Supports parallel and sequential review modes

## Arguments

| Flag | Description | Manual Only |
|------|-------------|-------------|
| `--provider <list>` | Comma-separated LLM providers (e.g., `openai,claude`) | No |
| `--file <path>` | Specify file to review (repeatable) | No |
| `--deliberate N` | Sequential chaining - pass through N rounds of LLMs | **Yes** |
| `--interject N` | Parallel interjections - each LLM can respond N times | **Yes** |

**Manual-only flags** are ignored in automated workflows.

## Step 0: Check Configuration

Before running, verify the provider configuration exists:

```bash
CONFIG_PATH="${STAR_CHAMBER_CONFIG:-$HOME/.config/star-chamber/providers.json}"
[[ -f "$CONFIG_PATH" ]] && echo "config:exists" || echo "config:missing"
```

**If config is missing**, offer to create it:

```
Star-Chamber requires provider configuration.

Would you like me to create the default configuration?

Location: ~/.config/star-chamber/providers.json

This will configure:
- OpenAI (gpt-4o)
- Anthropic (claude-sonnet-4-20250514)
- Gemini (gemini-2.0-flash)

API keys are read from environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY

[Yes, create it] / [No, I'll set it up manually]
```

**If user accepts**, create the config:

```bash
mkdir -p ~/.config/star-chamber
cp "$CLAUDE_CONFIG_PATH/reference/star-chamber/providers.json" ~/.config/star-chamber/providers.json
```

Then show:
```
Created ~/.config/star-chamber/providers.json

Make sure these environment variables are set:
  export OPENAI_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
  export GEMINI_API_KEY="..."

You can edit the config to:
- Remove providers you don't have keys for
- Change models (e.g., gpt-4-turbo instead of gpt-4o)
- Add other providers supported by any-llm-sdk
```

**If user declines**, show manual setup instructions:

```
To set up manually:

1. Create the config directory:
   mkdir -p ~/.config/star-chamber

2. Copy the reference config:
   cp $CLAUDE_CONFIG_PATH/reference/star-chamber/providers.json ~/.config/star-chamber/

3. Edit to match your available API keys:
   $EDITOR ~/.config/star-chamber/providers.json

4. Set your API keys as environment variables

Re-run /star-chamber when ready.
```

**STOP if config is missing. Do not proceed without configuration.**

## Step 1: Identify Review Targets

Determine what code to review:

**If `--file` arguments provided:**
```bash
# Use specified files
FILES=("${FILE_ARGS[@]}")
```

**Otherwise, use recent changes:**
```bash
# Get recently changed files
git diff HEAD~1 --name-only --diff-filter=ACMRT 2>/dev/null || git diff --cached --name-only
```

Filter to code files (exclude generated, vendor, etc.):
```bash
# Exclude patterns
echo "$FILES" | grep -v -E '(node_modules|vendor|\.min\.|\.generated\.|__pycache__|\.pyc$)'
```

## Step 2: Inject Context

Gather context to include with the review prompt:

**Project rules (if they exist):**
```bash
# Walk up from target files to find CLAUDE.md rules
[[ -f .claude/CLAUDE.md ]] && cat .claude/CLAUDE.md
for dir in $(dirname "$FILE" | tr '/' '\n' | head -3); do
  [[ -f "${dir}/.claude/CLAUDE.md" ]] && cat "${dir}/.claude/CLAUDE.md"
done
```

**Architecture context (if exists):**
```bash
[[ -f ARCHITECTURE.md ]] && cat ARCHITECTURE.md
```

## Step 3: Construct Review Prompt

Build a structured prompt for the LLM council:

```
You are a senior software craftsman reviewing code for quality, idioms, and architectural soundness.

## Project Context
{Injected CLAUDE.md rules}
{Architecture context if available}

## Code to Review
{File contents}

## Review Focus
1. Craftsmanship: Is this idiomatic, clean, well-structured?
2. Architecture: Does this fit the project's patterns? Any design concerns?
3. Correctness: Any logical issues, edge cases, or bugs?
4. Maintainability: Will this be easy to understand and modify later?

## Output Format
Provide your review as structured JSON:
{
  "provider": "your-name",
  "quality_rating": "excellent|good|fair|needs-work",
  "issues": [
    {
      "severity": "high|medium|low",
      "location": "file:line",
      "category": "craftsmanship|architecture|correctness|maintainability",
      "description": "What's wrong",
      "suggestion": "How to fix it"
    }
  ],
  "praise": ["What's done well"],
  "summary": "One paragraph overall assessment"
}
```

## Step 4: Fan Out to LLM Council

Execute the multi-LLM review using uvx:

```bash
echo "$PROMPT" | uvx --from any-llm-sdk python "$CLAUDE_CONFIG_PATH/skills/advisory/star-chamber/llm_council.py" \
  ${PROVIDERS:+$(echo "$PROVIDERS" | sed 's/,/ --provider /g' | sed 's/^/--provider /')} \
  ${FILES:+$(echo "$FILES" | sed 's/ / --file /g' | sed 's/^/--file /')} \
  ${DELIBERATE:+--deliberate $DELIBERATE} \
  ${INTERJECT:+--interject $INTERJECT}
```

**Execution modes:**
- Default: parallel independent calls to all providers
- `--deliberate N`: sequential chaining, feeding output to next LLM (debate mode)
- `--interject N`: multiple parallel interjections per provider (rubber-ducking mode)

## Step 5: Aggregate Results

Parse JSON responses from each provider and build consensus:

**Consensus issues** (all providers agree):
- Flag with "CONSENSUS" marker
- Highest confidence for action

**Majority issues** (2+ providers agree):
- Flag with provider count
- High confidence

**Individual observations** (single provider):
- List under provider name
- Lower confidence, but may be valid specialized insight

## Step 6: Output Report

Generate both human-readable and machine-readable output:

### Markdown Report

```markdown
## Star-Chamber Review

**Files:** {list of reviewed files}
**Providers:** {list of providers used}

### Consensus Issues (All Providers)
1. **{SEVERITY}** - `{location}` - {description}

### Majority Issues (2+ Providers)
1. **{SEVERITY}** - `{location}` - {description}

### Individual Observations
- **{Provider}**: {observation}

### Summary
| Provider | Quality | Issues |
|----------|---------|--------|
| GPT-4o   | Good    | 3      |
| Claude   | Good    | 4      |
| Gemini   | Fair    | 2      |
```

### JSON Output

```json
{
  "files_reviewed": ["path/to/file.py"],
  "providers_used": ["openai", "anthropic", "gemini"],
  "consensus_issues": [],
  "majority_issues": [],
  "individual_issues": {},
  "quality_ratings": {},
  "summary": {
    "total_issues": 0,
    "consensus_count": 0,
    "majority_count": 0
  }
}
```

## Usage Examples

```bash
# Basic - review recent changes with default providers
/star-chamber

# Specific files and providers
/star-chamber --file backend/app/auth.py --provider openai,claude

# Sequential deliberation - 3 rounds of debate
/star-chamber --deliberate 3

# Parallel interjections - each provider responds twice
/star-chamber --interject 2 --file frontend/src/hooks/useAuth.ts

# Combined workflow
/star-chamber --file auth.py --provider openai,gemini --deliberate 2 --interject 1
```

## Configuration

Provider configuration is read from `~/.config/star-chamber/providers.json`:

```json
{
  "providers": [
    {"provider": "openai", "model": "gpt-4o", "api_key": "${OPENAI_API_KEY}"},
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "api_key": "${ANTHROPIC_API_KEY}"},
    {"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "${GEMINI_API_KEY}"}
  ],
  "consensus_threshold": 2,
  "timeout_seconds": 60
}
```

Override config path with `STAR_CHAMBER_CONFIG` environment variable.

## Cost Warning

Each invocation calls all configured providers. With 3 providers reviewing ~2000 tokens:
- ~$0.02-0.10 per invocation depending on models
- This skill is advisory and opt-in, never runs automatically
