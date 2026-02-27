---
name: implement
description: Implement a feature or fix with automatic validation
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, WebFetch, WebSearch
---

# Implement with Validation

Implement the requested feature/fix, then validate before completing.

**Phase 0 is mandatory and must complete successfully before any other phase.**

## Task

$ARGUMENTS

## Phase 0: Inject Applicable Rules

Before starting work, collect and read all applicable CLAUDE.md rules.

### Step 1: Identify target directories

Based on the task, identify which directories will contain files to be created or modified.

If uncertain, err on the side of including more directories rather than fewer. Extra rules being applied is safe; missing rules is not.

### Step 2: Walk up and collect rules

For each directory, walk upward to repo root collecting `.claude/CLAUDE.md` files:

```
For a file in backend/app/handlers/:
  Check: backend/app/handlers/.claude/CLAUDE.md
  Check: backend/app/.claude/CLAUDE.md
  Check: backend/.claude/CLAUDE.md
  Check: .claude/CLAUDE.md (root)
```

Use the Read tool to check each path. Collect those that exist and are readable. A file is considered "found" only if it exists and can be successfully read.

### Step 2a: Check for local supplements

Check for `CLAUDE.local.md` at the project root and read it if present:

```bash
[[ -f CLAUDE.local.md ]] && echo "local-supplements:exists"
```

If it exists, read it. Pay particular attention to any "Validation Commands" section, which overrides defaults. Claude Code may also auto-load this file into context; the explicit read here ensures local supplements are always applied regardless of execution environment.

### Step 3: Read and apply rules

Read each discovered CLAUDE.md file.
Apply rules in order of precedence (most specific first):

```
1. backend/app/.claude/CLAUDE.md (if exists) - highest precedence
2. backend/.claude/CLAUDE.md (if exists)
3. .claude/CLAUDE.md (root) - lowest precedence
```

Earlier rules override later rules where they conflict.

If two rules conflict and precedence is unclear, prefer the more specific rule and note the conflict in the final report.

### Step 3a: Fallback baseline (conditional)

**This step only applies if NO `.claude/CLAUDE.md` files were found in Step 2.**

If project-specific rules were found and loaded, skip this step entirely and note in report: "Fallback baseline: not needed (project rules loaded)"

If no project-specific rules were found, attempt to load the universal baseline from the plugin:

1. **Resolve plugin root:** The skill loader provides the base directory in the header: `Base directory for this skill: <path>`. Derive `PLUGIN_ROOT` as `<base directory>/../..` (skills live at `<plugin-root>/skills/<name>/`, so two levels up).

2. **Validate plugin root:** Check that `$PLUGIN_ROOT/.claude-plugin/plugin.json` exists.
   - If missing → skip fallback, note in report: "Fallback baseline: failed (plugin root invalid at $PLUGIN_ROOT)"

3. **Validate baseline file:** Does `$PLUGIN_ROOT/claude-md/universal/base.md` exist and is it readable?
   - If file missing or unreadable → skip fallback, note in report: "Fallback baseline: failed (file not found at $PLUGIN_ROOT/claude-md/universal/base.md)"

4. **Load baseline:** If both checks pass, read `$PLUGIN_ROOT/claude-md/universal/base.md` as the baseline rules.
   - Note in report: "Fallback baseline: loaded from pragma plugin"

This fallback ensures projects without `/setup-project` still get essential rules (branch creation, scope verification, etc.).

### Step 4: Record applied rules

Track which rule files were loaded for the final report, including:
- Which project-specific CLAUDE.md files were loaded (if any)
- Fallback baseline status: not needed, loaded, skipped, or failed (with reason)
- CLAUDE.local.md (auto-loaded or explicitly read in Step 2a)

### Step 5: Execute pre-implementation setup

The "Pre-Implementation Setup" section of the loaded rules contains **actions to execute**, not just guidance to follow. The rules file is the single source of truth; this step is the executor.

**If no "Pre-Implementation Setup" section exists** in any loaded rules, skip this step and note in the final report that no pre-implementation setup was defined.

**How to execute:**

1. **Locate the section:** Find the "Pre-Implementation Setup" section in the loaded rules.

2. **Identify actionable items:** Look for:
   - Bash code blocks (` ```bash `) - these are commands to run
   - Imperative instructions ("Check...", "Create...", "Verify...")
   - Conditional actions ("**If...**" statements)

3. **Execute in order:** For each actionable item:
   - Run bash code blocks using the Bash tool
   - Evaluate conditionals and take the action specified in the rules
   - When a conditional requires a decision, ask the user
   - Record outcomes for the final report

4. **Handle failures:** If any command fails or a situation isn't covered by the rules, ask the user for guidance before proceeding.

5. **Record for report:** Track what was executed and outcomes (e.g., branch created, steps skipped, user decisions).

---

## Phase 1: Understand

1. Clarify requirements if ambiguous.
2. **Discover existing patterns before proposing solutions:**
   - Ask "how does Y access X?" not "does X exist in Y?" - directory existence alone doesn't reveal how code flows.
   - Check dependency files (pyproject.toml, package.json, go.mod) for workspace/monorepo patterns.
   - Grep for imports to understand how code flows between components.
   - Look for build artifacts (.egg-info, .venv, dist/, node_modules/, target/) indicating local packages.
   - If the task involves sharing code, find existing shared packages first.
   - If the GitHub issue lists multiple approaches, investigate each sufficiently to make an informed decision.
   - **Architecture violation guard:** If discovered patterns violate architecture rules from the project's CLAUDE.md or language-specific validators (e.g., models defined in route files, business logic in handlers, services that are actually repositories):
     1. Do not replicate the violations — follow documented layer responsibilities instead.
     2. Note the pre-existing deviation in the Phase 4 report.
     3. If the codebase systematically deviates (e.g., no repository layer exists, all models are in route files), follow correct architecture for new code where feasible without breaking existing imports or interfaces.
     4. If correct architecture would require creating new layers or significant refactoring, note this in the Phase 4 report and recommend a dedicated refactoring task.
   - **State model scrutiny guard:** If the task involves modifying state enums, status fields, transition logic, or terminal/final state classifications:
     1. For each state classified as terminal/final, verify that all running processes, background jobs, or external systems are actually stopped or cleaned up when entering that state.
     2. If a state is "terminal" only from one system's perspective (e.g., API/UI marks it as done) but not another's (e.g., a worker/Lambda is still running), it is not truly terminal — flag this before implementing.
     3. Check whether entering a terminal state creates a cancellation signal or cleanup action, not just a status label.
     4. If the existing codebase has states where "terminal" means "UI considers it done" but runtime processes continue, note this in the Phase 4 report and ensure new code does not compound the problem.
3. Identify files that need changes based on discovered patterns.

---

## Phase 2: Implement

1. Make the necessary code changes.
2. Follow the rules loaded in Phase 0.
3. Keep changes focused - don't over-engineer.

---

## Phase 3: Validate

After implementation is complete, run validation.

**Before running validators:** Re-check whether any new directories were introduced during implementation. If so, repeat Phase 0 for those directories and include any newly discovered rules.

1. **Run linters first** (deterministic checks):

   **Check rules for custom validation commands:**
   Look for a "Validation Commands" section in these sources, in precedence order:
   1. `CLAUDE.local.md` (from Step 2a — highest priority)
   2. Directory-specific `.claude/CLAUDE.md` files (from Step 2)
   3. Root `.claude/CLAUDE.md` (from Step 2)

   If custom commands exist at any level, use the highest-precedence match. Otherwise, fall back to these defaults:
   - Go: `golangci-lint run --fix -v`
   - Python: `uv run pre-commit run --all-files`
   - TypeScript: `pnpm run lint` or `npx biome check .`

   **Priority order:** See `claude-md/universal/validation-precedence.md` for the canonical precedence rules. In short: CLAUDE.local.md > subdirectory rules > root rules > built-in defaults. CLAUDE.local.md has the highest priority to allow per-machine customization without modifying version-controlled rules.

   Fix any issues before proceeding.

2. **Run semantic validators** (LLM checks):
   - Use the Task tool to spawn validators in parallel. For each validator, create a Task with `subagent_type: "general-purpose"` and a prompt instructing the subagent to invoke the validator skill (e.g., `pragma:security`) via the Skill tool and return the JSON result verbatim.
   - Do NOT use validator names as the `subagent_type` — most validators are skills, not agents. Always use `general-purpose` as the subagent type.
   - **Collect all validator JSON results internally.** Do NOT display raw validator JSON to the user — you will aggregate these results into the Phase 4 summary.
   - Note: This duplicates the dispatch logic in `validate` intentionally — implement needs inline control for the fix-and-re-validate loop. Keep both in sync.
     - `security` (always)
     - `state-machine` (always)
     - `go-effective` (if Go files changed)
     - `go-proverbs` (if Go files changed)
     - `python-style` (if Python files changed)
     - `typescript-style` (if TypeScript files changed)

3. **Fix violations**:
   - HARD violations: must fix.
   - SHOULD violations: fix or justify.
   - WARN: note but don't block.

4. **Re-validate** if fixes were made.

5. **After all validators pass, proceed to Phase 4.** Do not stop here — the final output must be the Phase 4 summary, not raw validator output.

---

## Phase 4: Complete

Only after validation passes:

1. Summarize what was implemented.
2. List files changed.
3. List rules that were applied (from Phase 0).
4. Note any warnings or justified SHOULD violations.
5. Note any rule conflicts encountered.

## Output Format

```
## Implementation Complete

**Task:** [what was requested]

**Branch:** `branch-name` (created | existing | continued | skipped)

**Rules Applied:**
- backend/.claude/CLAUDE.md
- .claude/CLAUDE.md
- CLAUDE.local.md (from Step 2a)

**Changes:**
- file.go: [what changed]
- file_test.go: [what changed]

**Validation:**
- Linting: ✓ passed
- Security: ✓ passed (no HARD, no unexplained SHOULD)
- Go Effective: ✓ passed (no HARD, 1 SHOULD justified, 1 WARN noted)

**Justified SHOULD items:**
- security:42 - Deferred input sanitization (handled by upstream middleware)
- go-effective:78 - 6-parameter function (options pattern would over-complicate here)

**Warnings:**
- [any WARN items to be aware of]

Ready for review or commit.
```

## Rules

- Phase 0 is mandatory. Do NOT skip rule injection.
- Do NOT skip validation.
- Do NOT say "done" until validation passes.
- Do NOT ignore HARD or SHOULD violations.
- If stuck in a validation loop (3+ attempts), report the issue and ask for guidance.
