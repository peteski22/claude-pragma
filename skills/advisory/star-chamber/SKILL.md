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

**Requirements:**
- Configuration file at `~/.config/star-chamber/providers.json`
- API keys: either individual keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) or single `ANY_LLM_KEY` from any-llm.ai platform

## Arguments

| Flag | Description | Manual Only |
|------|-------------|-------------|
| `--provider <name>` | LLM provider to use (repeatable, e.g., `--provider openai --provider gemini`). Defaults to all in config. | No |
| `--file <path>` | Specify file to review (repeatable). Defaults to recent git changes. | No |
| `--list-sdks` | Show configured providers, which have API keys set, and required SDK packages. Diagnostic only. | No |
| `--debate` | Enable debate mode: multiple rounds where each provider sees others' responses | **Yes** |
| `--rounds N` | Number of debate rounds (default: 2, requires --debate) | **Yes** |

**Manual-only flags** are ignored in automated workflows.

## Skill Base Directory

The skill loader provides the base directory in the header: `Base directory for this skill: <path>`. Use this to locate llm_council.py:

```bash
SKILL_BASE="<base directory from header>"
# e.g., SKILL_BASE="$HOME/.claude/skills/star-chamber"
```

## Step 0: Check Configuration

Before running, verify the provider configuration exists:

```bash
CONFIG_PATH="${STAR_CHAMBER_CONFIG:-$HOME/.config/star-chamber/providers.json}"
[[ -f "$CONFIG_PATH" ]] && echo "config:exists" || echo "config:missing"
```

**If config is missing**, ask how to manage API keys:

```
Star-Chamber requires provider configuration.

How would you like to manage API keys?

[any-llm.ai platform] - Single ANY_LLM_KEY, centralized key vault, usage tracking
[Direct provider keys] - Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY individually
[Skip] - I'll set it up manually later
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

Then show:
```
Created ~/.config/star-chamber/providers.json (platform mode)

Setup:
  1. Create account at https://any-llm.ai
  2. Create a project and add your provider API keys
  3. Copy your project key and set:
     export ANY_LLM_KEY="ANY.v1...."
```

**If user chooses "Direct provider keys":**

```bash
mkdir -p ~/.config/star-chamber
cat > ~/.config/star-chamber/providers.json << 'EOF'
{
  "providers": [
    {"provider": "openai", "model": "gpt-4o", "api_key": "${OPENAI_API_KEY}"},
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "api_key": "${ANTHROPIC_API_KEY}"},
    {"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "${GEMINI_API_KEY}"}
  ],
  "consensus_threshold": 2,
  "timeout_seconds": 60
}
EOF
```

Then show:
```
Created ~/.config/star-chamber/providers.json (direct keys mode)

Set these environment variables:
  export OPENAI_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
  export GEMINI_API_KEY="..."

Edit the config to remove providers you don't have keys for.
```

**If user chooses "Skip":**

```
To set up manually later, see the Configuration section below or run /star-chamber again.
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

First, determine which SDK packages are needed:

```bash
uvx --from any-llm-sdk python "$SKILL_BASE/llm_council.py" --list-sdks
```

This outputs JSON with `required_sdks` array listing needed packages (e.g., `["anthropic", "google-genai"]`).

Then execute the review, adding a `--with` flag for **each** SDK:

```bash
echo "$PROMPT" | uvx --from any-llm-sdk \
  --with anthropic --with google-genai \
  python "$SKILL_BASE/llm_council.py" \
  [--provider <name>...] \
  [--file <path>...] \
  [--debate] \
  [--rounds N]
```

**Important:** Each `--with` must be a separate argument. Do NOT quote multiple `--with` flags together.

The SDK mapping is built into llm_council.py and supports all any-llm providers.

**Execution modes:**

| Mode | Flags | Flow | Use Case |
|------|-------|------|----------|
| Parallel | (default) | All providers review independently at once | Fast consensus gathering |
| Debate | `--debate --rounds N` | Multiple rounds, each provider sees others' responses | Deep deliberation, refining ideas |

**Parallel (default):**
```
Prompt → [OpenAI] ──→ Response A
      → [Claude] ──→ Response B    (all at once, independent)
      → [Gemini] ──→ Response C
```

**Debate (--debate --rounds 3):**
```
Round 1 (parallel, all get original prompt):
  [OpenAI] ──→ "X looks problematic..."
  [Claude] ──→ "I'd focus on Y..."
  [Gemini] ──→ "Consider Z as well..."

Round 2 (parallel, each sees what OTHERS said):
  [OpenAI] sees Claude + Gemini responses ──→ "Agree with Claude on Y, but..."
  [Claude] sees OpenAI + Gemini responses ──→ "Good point about X, however..."
  [Gemini] sees OpenAI + Claude responses ──→ "Building on both points..."

Round 3 (parallel, each sees round 2 responses):
  [OpenAI] sees others' round 2 ──→ final thoughts
  [Claude] sees others' round 2 ──→ final thoughts
  [Gemini] sees others' round 2 ──→ final thoughts
```

In debate mode, the final round responses are used for consensus building.

**Example debate evolution:**

```
Round 1 - OpenAI:
  "The config loader silently ignores missing env vars. This could cause
   runtime errors when OAuth credentials are empty strings."

Round 1 - Claude:
  "Good separation of concerns. However, the linear search in
   get_resource_definition could be slow for large configs."

Round 1 - Gemini:
  "Type hints look solid. Consider adding a strict mode for env var
   validation in production environments."

Round 2 - OpenAI (after seeing Claude + Gemini):
  "Agree with Gemini on strict mode - that would address my env var concern.
   Claude's point about linear search is valid but likely premature optimization
   for typical config sizes (<100 resources)."

Round 2 - Claude (after seeing OpenAI + Gemini):
  "OpenAI and Gemini both flagged the silent env var handling - this is now
   a consensus issue. I'll upgrade my assessment. The strict mode suggestion
   elegantly solves it."

Round 2 - Gemini (after seeing OpenAI + Claude):
  "Strong agreement forming around env var validation. Claude's performance
   concern is noted but I agree with OpenAI it's not critical for v1."
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
# Basic - review recent changes with default providers (parallel, single round)
/star-chamber

# Specific files and providers
/star-chamber --file backend/app/auth.py --provider openai --provider anthropic

# Debate mode - 2 rounds (default) where each provider sees others' responses
/star-chamber --debate

# Debate mode - 3 rounds of deliberation
/star-chamber --debate --rounds 3

# Debate with specific files
/star-chamber --debate --rounds 2 --file auth.py --provider openai --provider gemini
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

## Using any-llm.ai Managed Platform (Optional)

Instead of setting individual API keys, you can use the [any-llm.ai](https://any-llm.ai) managed platform for:
- **Centralized key management** - Store provider keys securely (encrypted client-side)
- **Usage tracking** - Automatic cost and token tracking across all providers
- **Single authentication** - One `ANY_LLM_KEY` instead of multiple provider keys

### Platform Setup

1. Create account at https://any-llm.ai
2. Create a project and add your provider API keys (OpenAI, Anthropic, Gemini, etc.)
3. Copy your project key
4. Set environment variable:
   ```bash
   export ANY_LLM_KEY="ANY.v1.abc123..."
   ```
5. Enable platform mode in your config (`~/.config/star-chamber/providers.json`):
   ```json
   {
     "platform": "any-llm",
     ...
   }
   ```

### What Gets Tracked

The platform tracks **metadata only** (never prompts/responses):
- Provider and model used
- Token counts (input/output)
- Request timestamps
- Cost estimates

### Platform Config Example

```json
{
  "platform": "any-llm",
  "providers": [
    {"provider": "openai", "model": "gpt-4o"},
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}
  ]
}
```

Note: `api_key` fields are omitted - the library fetches them from the platform automatically.

## Cost Warning

Each invocation calls all configured providers. With 3 providers reviewing ~2000 tokens:
- ~$0.02-0.10 per invocation depending on models
- This skill is advisory. Claude may invoke it for design decisions (without --debate).

## When Claude May Self-Invoke

Claude may invoke this skill (basic mode only, no --debate) when:
- Facing significant architectural decisions with multiple valid approaches
- Uncertain about design trade-offs that would benefit from diverse perspectives
- The user has asked for a "second opinion" or "what do others think"

Do NOT self-invoke for:
- Routine code changes
- Well-established patterns
- When time/cost is a concern (ask user first)

The --debate and --rounds flags are manual-only and ignored in automated/self-invoked workflows.
