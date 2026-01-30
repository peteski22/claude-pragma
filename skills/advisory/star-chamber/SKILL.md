---
name: star-chamber
description: Advisory multi-LLM craftsmanship council for code and architecture review
user-invocable: true
model-invocable: true
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
| `--provider <name>` | LLM provider to use (repeatable, e.g., `--provider openai --provider gemini`). Defaults to all in config. | No |
| `--file <path>` | Specify file to review (repeatable). Defaults to recent git changes. | No |
| `--list-sdks` | Show configured providers, which have API keys set, and required SDK packages. Diagnostic only. | No |
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

Build a structured prompt for Star-Chamber:

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

## Step 4: Fan Out to Star-Chamber

First, determine which SDK packages are needed for the configured providers:

```bash
uvx --from any-llm-sdk python "$CLAUDE_CONFIG_PATH/skills/advisory/star-chamber/llm_council.py" \
  --list-sdks \
  [--provider <name>...]
```

This outputs JSON with `uvx_with_flags` containing the required `--with` arguments (e.g., `--with anthropic --with google-genai`).

Then execute the review with the dynamically determined SDKs:

```bash
echo "$PROMPT" | uvx --from any-llm-sdk $UVX_WITH_FLAGS \
  python "$CLAUDE_CONFIG_PATH/skills/advisory/star-chamber/llm_council.py" \
  [--provider <name>...] \
  [--file <path>...] \
  [--deliberate N] \
  [--interject N]
```

The SDK mapping is defined in `$CLAUDE_CONFIG_PATH/reference/star-chamber/sdk_map.json` and supports all any-llm providers.

**Execution modes:**

| Mode | Flag | Flow | Use Case |
|------|------|------|----------|
| Parallel | (default) | All providers review independently at once | Fast consensus gathering |
| Deliberate | `--deliberate N` | Sequential: each LLM sees previous responses | Deep debate, building on ideas |
| Interject | `--interject N` | Each provider responds N times in parallel | Multiple perspectives per model |

**Parallel (default):**
```
Prompt → [OpenAI] ──→ Response A
      → [Claude] ──→ Response B    (all at once)
      → [Gemini] ──→ Response C
```

**Deliberate (--deliberate 2):**
```
Prompt → OpenAI → "I think X..."
                     ↓
      "OpenAI said X" → Claude → "I agree but also Y..."
                                    ↓
               "Claude said Y" → Gemini → "Actually, Z..."
                                             ↓
                              (repeat for round 2)
```

**Interject (--interject 2):**
```
Prompt → [OpenAI] ──→ Response A1
      → [OpenAI] ──→ Response A2   (2 parallel calls per provider)
      → [Claude] ──→ Response B1
      → [Claude] ──→ Response B2
```

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

The output combines two dimensions:
- **Agreement** (section headers): How many providers flagged the issue (consensus = all, majority = 2+, individual = 1)
- **Severity** (issue labels): How serious - HIGH (security/correctness), MEDIUM (potential bugs), LOW (style/optimization)

```markdown
## Star-Chamber Review

**Files:** {list of reviewed files}
**Providers:** {list of providers used}

### Consensus Issues (All Providers Agree)
1. `{location}` [{SEVERITY}] - {description}

### Majority Issues (N/M Providers)
1. `{location}` [{SEVERITY}, {N}/{M}] - {description}

### Individual Observations
- **{Provider}**: `{location}` - {observation}

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
/star-chamber --file backend/app/auth.py --provider openai --provider anthropic

# Sequential deliberation - 3 rounds of debate
/star-chamber --deliberate 3

# Parallel interjections - each provider responds twice
/star-chamber --interject 2 --file frontend/src/hooks/useAuth.ts

# Combined workflow
/star-chamber --file auth.py --provider openai --provider gemini --deliberate 2
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
- This skill is advisory. Claude may invoke it for design decisions (without --deliberate/--interject).

## When Claude May Self-Invoke

Claude may invoke this skill (basic mode only, no --deliberate/--interject) when:
- Facing significant architectural decisions with multiple valid approaches
- Uncertain about design trade-offs that would benefit from diverse perspectives
- The user has asked for a "second opinion" or "what do others think"

Do NOT self-invoke for:
- Routine code changes
- Well-established patterns
- When time/cost is a concern (ask user first)

The --deliberate and --interject flags are manual-only and ignored in automated/self-invoked workflows.
