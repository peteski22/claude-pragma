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
- Uses `any-llm-sdk` via `uv run` (no global Python install needed)
- Supports parallel and sequential review modes

**Requirements:**
- `uv` command (from [uv](https://docs.astral.sh/uv/) Python toolchain)
- Configuration file at `~/.config/star-chamber/providers.json`
- API keys: either individual keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) or single `ANY_LLM_KEY` from any-llm.ai platform

## Arguments

| Flag | Description | Manual Only |
|------|-------------|-------------|
| `--provider <name>` | LLM provider to use (repeatable, e.g., `--provider openai --provider gemini`). Defaults to all in config. | No |
| `--file <path>` | Specify file to review (repeatable). Defaults to recent git changes. | No |
| `--timeout <seconds>` | Timeout per provider request (overrides config `timeout_seconds`). | No |
| `--list-sdks` | Show configured providers, which have API keys set, and required SDK packages. Diagnostic only. | No |
| `--debate` | Enable debate mode: multiple rounds with summarization between rounds | **Yes** |
| `--rounds N` | Number of debate rounds (default: 2, requires --debate) | **Yes** |

**Manual-only flags** are skill invocation parameters interpreted by Claude Code, NOT flags passed to `llm_council.py`. Debate mode is orchestrated by Claude Code (see Step 4).

## Skill Base Directory

The skill loader provides the base directory in the header: `Base directory for this skill: <path>`. Use this to locate llm_council.py:

```bash
SKILL_BASE="<base directory from header>"
# e.g., SKILL_BASE="$HOME/.claude/skills/star-chamber"
```

## Step 0: Check Prerequisites

Before running, verify uv is available and configuration exists:

```bash
command -v uv >/dev/null 2>&1 && echo "uv:ok" || echo "uv:missing"
CONFIG_PATH="${STAR_CHAMBER_CONFIG:-$HOME/.config/star-chamber/providers.json}"
[[ -f "$CONFIG_PATH" ]] && echo "config:exists" || echo "config:missing"
```

**If uv is missing**, stop and show:
```
uv is required but not installed.

Install uv:
  curl -LsSf https://astral.sh/uv/install.sh | sh

See: https://docs.astral.sh/uv/getting-started/installation/
```

**STOP if uv is missing. Do not proceed.**

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
uv run python "$CLAUDE_PRAGMA_PATH/reference/star-chamber/generate_config.py" --platform
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
uv run python "$CLAUDE_PRAGMA_PATH/reference/star-chamber/generate_config.py" --direct
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
      "description": "What is wrong",
      "suggestion": "How to fix it"
    }
  ],
  "praise": ["What is done well"],
  "summary": "One paragraph overall assessment"
}
```

## Step 4: Fan Out to Star-Chamber

First, determine which SDK packages are needed:

```bash
uv run --with any-llm-sdk python "$SKILL_BASE/llm_council.py" --list-sdks
```

This outputs JSON with `required_sdks` array listing needed packages (e.g., `["anthropic", "google-genai"]`).

**Execution modes:**

| Mode     | Invocation            | Flow                                        | Use Case                          |
|----------|-----------------------|---------------------------------------------|-----------------------------------|
| Parallel | (default)             | All providers review independently at once  | Fast consensus gathering          |
| Debate   | `/star-chamber --debate --rounds N` | Multiple rounds with summarization between  | Deep deliberation, refining ideas |

### Parallel Mode (default)

The simplest approach: all providers review independently in a single round.

Execute a single parallel review. Write the prompt to a temp file first, then pipe it to avoid shell quoting issues:

```bash
cat << 'EOF' | uv run --with any-llm-sdk [--with <sdk>...] python "$SKILL_BASE/llm_council.py" [--provider <name>...] [--file <path>...]
{prompt}
EOF
```

**Important:** The `uv run` command and all its arguments must be on a **single line**. Do NOT use `\` line continuations — they break under Claude Code's Bash tool. The `--with` flags come from the `--list-sdks` output's `required_sdks` array (add `--with any-llm-sdk` plus `--with <sdk>` for each entry).

```text
Prompt → [Provider A] ──→ Response A
      → [Provider B] ──→ Response B    (all at once, independent)
      → [Provider C] ──→ Response C
```

### Debate Mode

For deeper deliberation, debate mode runs multiple rounds where providers respond to each other's feedback.

You (Claude Code) orchestrate the debate loop. The Python script handles parallel fan-out/fan-in for each round; you handle summarization between rounds.

**Note:** Debate mode involves multiple rounds of LLM calls, increasing both cost and response time compared to parallel mode.

**Debate flow:**

```text
Round 1: Fan out original prompt to all providers (parallel)
         ↓
         Collect responses: R1_A, R1_B, R1_C, ...
         ↓
For each subsequent round (2 to N):
         ↓
    Create ONE anonymous summary of ALL responses from the previous round
         ↓
    Build new prompt: original + "Other council members said: {summary}"
         ↓
    Fan out to all providers in parallel (single llm_council.py call)
         ↓
    Collect responses: RN_A, RN_B, RN_C, ...
         ↓
Final: Use last round responses for consensus building
```

**Round 1:** Call llm_council.py with the original prompt (all providers, parallel).

**Round 2+:** Create ONE anonymous summary of all responses from the previous round, then call llm_council.py again with the augmented prompt. All providers receive the same summary - this maintains parallel execution and aligns with the anonymous synthesis approach.

**Summarization (anonymous synthesis):** When summarizing for the next round, synthesize feedback by content themes WITHOUT attributing specific points to individual providers. Present the collective feedback anonymously, focusing on consolidating similar concerns and highlighting areas of agreement or disagreement. This encourages providers to engage with ideas rather than sources. Example:

```text
"## Other council members' feedback (round 1):

**Issues raised:**
- The config loader silently ignores missing env vars, risking runtime errors
- Linear search in get_resource_definition may be slow for large configs
- Consider adding a strict mode for env var validation

**Points of agreement:**
- Type hints are solid
- Overall code structure is clean

Please provide your perspective on these points. Note where you agree, disagree, or have additional insights."
```

**Error handling:** If a provider fails during a round, continue with the remaining providers. Note failed providers in the final output but do not block the debate.

**Convergence check:** If responses in round N are substantively the same as round N-1 (providers just agree with no new points), you may stop early. This is optional - completing all requested rounds is also acceptable.

**Prompt construction:** Pipe the prompt via heredoc (`cat << 'EOF' | uv run ...`) to avoid quoting issues with apostrophes and special characters. Never store the prompt in a shell variable — use heredoc piping directly.

**Important:** Each `--with` must be a separate argument. Do NOT quote multiple `--with` flags together. Keep the entire `uv run` command on one line.

## Step 5: Parse and Aggregate Results

For each successful provider response:

1. **Extract JSON** from the response. Providers often wrap JSON in markdown code blocks like ` ```json {...} ``` `. Extract the JSON object. If parsing fails, note the provider as having a malformed response.

2. **Normalize issues** by location and category to enable grouping.

3. **Group issues by similarity**:
   - Same file + same line range + same category = likely same issue
   - Similar descriptions across providers = same underlying concern

4. **Classify by agreement** (mutually exclusive buckets):
   - **Consensus** (all providers flagged it): Highest confidence
   - **Majority** (2+ providers, but not all): High confidence
   - **Individual** (1 provider only): Note but lower confidence

## Step 6: Present Results to User

Present the aggregated results using this format. Always show consensus issues first.

```markdown
## Star-Chamber Review

**Files:** {list of files reviewed}
**Providers:** {list of providers used}

### Consensus Issues (All Providers Agree)

These issues were flagged by every council member. Address these first.

1. `{file}:{line}` **[{SEVERITY}]** - {description}
   - **Suggestion:** {how to fix}

### Majority Issues ({N}/{M} Providers)

These issues were flagged by most council members.

1. `{file}:{line}` **[{SEVERITY}]** ({which providers}) - {description}
   - **Suggestion:** {how to fix}

### Individual Observations

Issues raised by a single provider. May be valid specialized insights.

- **{Provider}:** `{location}` - {observation}

### Summary

| Provider | Quality Rating | Issues Found |
|----------|---------------|--------------|
| {name}   | {rating}      | {count}      |

**Overall:** {1-2 sentence synthesis of the review}
```

**Important:**
- Always lead with consensus issues - these are the most actionable
- Include the suggestion/fix from providers when available
- Note which providers flagged majority issues for context
- Keep the summary concise - users want to know what to fix
- Do NOT include raw JSON output in the terminal summary - the markdown format above is for human consumption

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

Provider configuration is read from `~/.config/star-chamber/providers.json`.

The reference configuration with current models is maintained at `reference/star-chamber/providers.json` in this repository. Update models there and re-run `generate_config.py` with `--platform` or `--direct` to propagate changes to your local config.

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

Same as the reference config but with `"platform": "any-llm"` added and `api_key` fields removed — the library fetches keys from the platform automatically. The setup flow handles this transformation.

Note: `api_key` fields are omitted - the library fetches them from the platform automatically.

## Security Considerations

**API Key Storage:**
- **Prefer environment variables** over hardcoding keys in the config file
- Use `${ENV_VAR}` syntax in config to reference environment variables
- Never commit `providers.json` with actual API keys to version control
- The any-llm.ai platform mode is recommended for team environments

**Error Output:**
- API keys are automatically redacted from error messages (patterns: `sk-*`, `ANY.v1.*`, etc.)
- The `--list-sdks` command shows whether keys are set, not their values

## Troubleshooting

### Common Errors

**Authentication failed for {provider}:**
```json
{"provider": "openai", "success": false, "error": "Authentication failed for openai. Check OPENAI_API_KEY is set and valid."}
```
- Verify the environment variable is set: `echo $OPENAI_API_KEY`
- Check if the key is valid (not expired or revoked)
- For platform mode, verify `ANY_LLM_KEY` is set and the provider is configured in your any-llm.ai project

**Request timed out:**
```json
{"provider": "gemini", "success": false, "error": "Request timed out after 60s"}
```
- Increase timeout via `--timeout 120` or in config `timeout_seconds`
- Check network connectivity to the provider

**Missing SDK:**
```json
{"provider": "anthropic", "success": false, "error": "Missing SDK for anthropic. Install with: pip install anthropic (or add '--with anthropic' to uv run)"}
```
- Run `--list-sdks` to see required packages
- Add appropriate `--with` flags to the `uv run` command

**Provider not in sdk_map:**
```text
[star-chamber] Provider custom-llm not in sdk_map, assuming OpenAI-compatible
```
- This is a warning, not an error. Unknown providers are assumed to use the OpenAI-compatible API.
- If your provider needs a specific SDK, add it to `sdk_map.json`

### Partial Failures

When some providers succeed and others fail, the output includes both:

```json
{
  "reviews": [
    {"provider": "openai", "model": "gpt-4o", "success": true, "content": "..."}
  ],
  "failed_reviews": [
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "success": false, "error": "Request timed out after 60s"}
  ],
  "providers_used": ["openai", "anthropic"]
}
```

The review continues with available providers. Check `failed_reviews` for details on failures.

### Debate Convergence

In debate mode, the council may exit early if responses stabilize:
```text
[star-chamber] Debate converged after round 3
```

This means all successful providers gave the same responses in consecutive rounds. Providers that failed or timed out are excluded from convergence detection and listed under `failed_reviews`. The output will include `"converged": true`.

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
