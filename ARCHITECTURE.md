# Architecture

This document explains the design decisions behind claude-pragma.

## User Flow: End-to-End

This diagram shows the complete workflow from project setup through implementation and review.

```mermaid
flowchart TB
    subgraph Setup["One-Time Setup"]
        S1["Clone claude-pragma repo"]
        S2["Set $CLAUDE_PRAGMA_PATH"]
        S3["Run /setup-project"]
        S1 --> S2 --> S3
        S3 --> S3a["Detects: backend/ (Python)<br/>frontend/ (TypeScript)<br/>services/go/ (Go)"]
        S3a --> S3b["Creates .claude/CLAUDE.md files"]
        S3b --> S3c["Links validator skills"]
    end

    subgraph Implement["Developer runs: /implement 'Add user authentication'"]
        direction TB

        subgraph P0["Phase 0: Rule Injection"]
            P0a["Identify target dirs:<br/>backend/, frontend/"]
            P0b["Walk up, collect rules"]
            P0c["Read & apply:<br/>• backend/.claude/CLAUDE.md<br/>• frontend/.claude/CLAUDE.md<br/>• .claude/CLAUDE.md"]
            P0a --> P0b --> P0c
        end

        subgraph P12["Phase 1-2: Understand & Implement"]
            P12a["Clarify requirements"]
            P12b["Write code following<br/>injected rules"]
            P12c["Files created:<br/>• backend/app/services/auth.py<br/>• backend/app/api/routes/auth.py<br/>• frontend/src/hooks/useAuth.ts"]
            P12a --> P12b --> P12c
        end

        subgraph P3["Phase 3: Validate"]
            P3a["Run linters:<br/>ruff + ty | biome + tsc"]
            P3b{Linters pass?}
            P3c["Fix lint errors"]
            P3d["Spawn semantic validators"]

            P3a --> P3b
            P3b -->|No| P3c --> P3a
            P3b -->|Yes| P3d

            subgraph Validators["Parallel Validators"]
                V1["security"]
                V2["python-style"]
                V3["typescript-style"]
            end

            P3d --> Validators
            Validators --> P3e["Aggregate results"]
            P3e --> P3f{All pass?}
            P3f -->|No| P3g["Fix violations"]
            P3g --> P3a
        end

        subgraph P4["Phase 4: Complete"]
            P4a["Generate report"]
        end

        P0 --> P12 --> P3
        P3f -->|Yes| P4
    end

    subgraph Review["Developer runs: /review"]
        R1["Get changed files"]
        R2["Inject rules (Step 2)"]
        R3["Run linters"]
        R4["Run validators"]
        R5["Generate report"]
        R1 --> R2 --> R3 --> R4 --> R5
    end

    subgraph Output["Final Output"]
        O1["JSON (machine-readable)"]
        O2["Report (human-readable)"]
    end

    Setup --> Implement
    Implement --> Review
    Review --> Output
```

## Output Examples

After `/implement` or `/review`, you get both formats:

### Human-Readable Report

```
## Implementation Complete

**Task:** Add user authentication

**Rules Applied:**
- backend/.claude/CLAUDE.md (Python)
- frontend/.claude/CLAUDE.md (TypeScript)
- .claude/CLAUDE.md (Universal)

**Files Changed:**
- backend/app/services/auth.py: AuthService with login/logout
- backend/app/api/routes/auth.py: POST /login, POST /logout endpoints
- frontend/src/hooks/useAuth.ts: useAuth hook with TanStack Query

**Validation:**
| Validator        | Status | Hard | Should | Warn |
|------------------|--------|------|--------|------|
| security         | ✓ Pass | 0    | 0      | 1    |
| python-style     | ✓ Pass | 0    | 0      | 0    |
| typescript-style | ✓ Pass | 0    | 0      | 0    |

**Warnings:**
- security: auth.py:45 - Consider adding rate limiting (advisory)

Ready for /review or commit.
```

### JSON Output (for tooling)

```json
{
  "task": "Add user authentication",
  "applied_rules": [
    "backend/.claude/CLAUDE.md",
    "frontend/.claude/CLAUDE.md",
    ".claude/CLAUDE.md"
  ],
  "rule_conflicts": [],
  "files_changed": [
    "backend/app/services/auth.py",
    "backend/app/api/routes/auth.py",
    "frontend/src/hooks/useAuth.ts"
  ],
  "validation": {
    "pass": true,
    "validators": [
      {"name": "security", "pass": true, "hard": 0, "should": 0, "warn": 1},
      {"name": "python-style", "pass": true, "hard": 0, "should": 0, "warn": 0},
      {"name": "typescript-style", "pass": true, "hard": 0, "should": 0, "warn": 0}
    ],
    "total": {"hard": 0, "should": 0, "warn": 1}
  },
  "warnings": [
    {
      "validator": "security",
      "location": "auth.py:45",
      "note": "Consider adding rate limiting"
    }
  ]
}
```

---

## The Problem

CLAUDE.md rules are **guidance** - they can be ignored or forgotten by the LLM. We needed:

1. Rules that are **mechanically injected**, not hoped-for
2. Validation that **verifies compliance**, not trusts it
3. A system that works for **monorepos with multiple languages**

## Core Principles

### 1. Validators are authoritative, not CLAUDE.md

CLAUDE.md provides guidance. Validators **enforce** rules.

If there's a conflict between what CLAUDE.md says and what a validator checks, the validator wins. This removes ambiguity.

### 2. Rules are injected, not remembered

`/implement` and `/review` **mechanically read** applicable CLAUDE.md files before doing any work. This is Phase 0 / Step 2 - it happens first, explicitly, and is recorded.

> **Critical**: Phase 0 (rule injection) is mandatory. It must complete before any other phase. This is the single most important design decision - it eliminates reliance on LLM memory.

The LLM doesn't need to "remember" rules - they're injected fresh every time.

### 3. Deterministic before semantic

Linters run first. If they fail, stop. Only then do semantic validators run.

This ensures validator signal quality - they're not wasting time on formatting issues.

### 4. Validators have contracts

Each validator declares:
- What it checks (scope)
- What it doesn't check (excludes)
- What it assumes ran before it (assumes)

This prevents overlap and makes maintenance clear.

## Monorepo Validator Map

This diagram shows the complete flow for a multi-language monorepo from `/implement` through validation.

```mermaid
flowchart TB
    subgraph Trigger["Trigger"]
        Start["/implement task"]
    end

    subgraph Phase0["Phase 0: Rule Injection"]
        P0[Identify changed files]
        P0 --> DetectLang{Detect language}

        DetectLang -->|.py files| PyRules["Load: backend/.claude/CLAUDE.md<br/>+ .claude/CLAUDE.md"]
        DetectLang -->|.ts/.tsx files| TSRules["Load: frontend/.claude/CLAUDE.md<br/>+ .claude/CLAUDE.md"]
        DetectLang -->|.go files| GoRules["Load: services/go/.claude/CLAUDE.md<br/>+ .claude/CLAUDE.md"]
    end

    subgraph Phase12["Phase 1-2: Implement"]
        Impl[Work done following injected rules]
    end

    subgraph Phase3["Phase 3: Validate"]
        subgraph DetChecks["Deterministic Linters"]
            PyRules --> PyLint["ruff + ty/mypy"]
            TSRules --> TSLint["biome + tsc"]
            GoRules --> GoLint["golangci-lint"]
        end

        PyLint & TSLint & GoLint --> LintPass{All pass?}
        LintPass -->|No| FixLint[Fix lint errors]
        FixLint --> PyLint & TSLint & GoLint

        subgraph SemVal["Semantic Validators"]
            LintPass -->|Yes| SecVal["security<br/>(all files)"]

            LintPass -->|Yes, .py| PyStyle["python-style"]
            LintPass -->|Yes, .ts/.tsx| TSStyle["typescript-style"]
            LintPass -->|Yes, .go| GoEff["go-effective"]
            LintPass -->|Yes, .go| GoProv["go-proverbs"]
        end

        SecVal & PyStyle & TSStyle & GoEff & GoProv --> Agg[Aggregate results]
        Agg --> ValPass{All pass?}
        ValPass -->|No| FixViol[Fix violations]
        FixViol --> PyLint & TSLint & GoLint
    end

    subgraph Phase4["Phase 4: Complete"]
        ValPass -->|Yes| Output["Output JSON:<br/>- applied_rules<br/>- files_changed<br/>- validation_results"]
    end

    Start --> P0
    PyRules & TSRules & GoRules --> Impl
    Impl --> Phase3
```

## Monorepo Directory Structure

```mermaid
graph TD
    Root[".claude/CLAUDE.md<br/>(Universal rules)"]

    Root --> Backend["backend/.claude/CLAUDE.md<br/>(Python rules)"]
    Root --> Frontend["frontend/.claude/CLAUDE.md<br/>(TypeScript rules)"]
    Root --> Services["services/go/.claude/CLAUDE.md<br/>(Go rules)"]

    Backend --> PyFiles["backend/**/*.py"]
    Frontend --> TSFiles["frontend/**/*.ts,tsx"]
    Services --> GoFiles["services/go/**/*.go"]
```

## System Flow

```mermaid
flowchart TD
    subgraph Phase0["Phase 0: Inject Rules (MANDATORY)"]
        P0A[Identify target directories]
        P0B[Walk up to repo root]
        P0C[Collect .claude/CLAUDE.md files]
        P0D[Read and apply - most specific first]
        P0E[Record applied_rules]
        P0A --> P0B --> P0C --> P0D --> P0E
    end

    subgraph Phase12["Phase 1-2: Understand & Implement"]
        P12[Work done following injected rules]
    end

    subgraph Phase3["Phase 3: Validate"]
        subgraph Deterministic["Deterministic Checks"]
            Lint[pre-commit / golangci-lint / biome]
            LintFail{Pass?}
            Lint --> LintFail
        end

        subgraph Semantic["Semantic Validators (by language)"]
            SecVal[security - all languages]
            PyVal[python-style - Python]
            TSVal[typescript-style - TypeScript]
            GoEff[go-effective - Go]
            GoProv[go-proverbs - Go]
        end

        Agg[Aggregate Results]
        Fix[Fix violations]
        ReVal{Re-validate?}

        LintFail -->|No| FixLint[Fix lint errors]
        FixLint --> Lint
        LintFail -->|Yes| SecVal & PyVal & TSVal & GoEff & GoProv
        SecVal & PyVal & TSVal & GoEff & GoProv --> Agg
        Agg --> Fix
        Fix --> ReVal
        ReVal -->|Yes| Lint
    end

    subgraph Phase4["Phase 4: Complete"]
        Output[Output: Rules Applied, Files Changed, Validation Results]
    end

    Start["/implement task"] --> Phase0
    Phase0 --> Phase12
    Phase12 --> Phase3
    ReVal -->|No| Phase4
```

## Rule Injection Detail

Rule injection walks up from the changed file to the repo root, collecting `.claude/CLAUDE.md` files. Most specific rules take precedence.

### Go Example

```mermaid
flowchart TD
    File["Changed file:<br/>services/go/handlers/user.go"]

    File --> Check1{"services/go/handlers/<br/>.claude/CLAUDE.md?"}
    Check1 -->|missing| Check2

    Check2{"services/go/<br/>.claude/CLAUDE.md?"}
    Check2 -->|exists| Rule2["Load Go rules"]
    Check2 -->|missing| Check3

    Rule2 --> Check3{".claude/CLAUDE.md?<br/>(root)"}
    Check3 -->|exists| Rule3["Load universal rules"]

    Rule3 --> Apply["Apply: Go rules + Universal"]
```

### Python Example

```mermaid
flowchart TD
    File["Changed file:<br/>backend/app/services/users.py"]

    File --> Check1{"backend/app/services/<br/>.claude/CLAUDE.md?"}
    Check1 -->|missing| Check2

    Check2{"backend/<br/>.claude/CLAUDE.md?"}
    Check2 -->|exists| Rule2["Load Python rules"]

    Rule2 --> Check3{".claude/CLAUDE.md?<br/>(root)"}
    Check3 -->|exists| Rule3["Load universal rules"]

    Rule3 --> Apply["Apply: Python rules + Universal"]
```

### TypeScript Example

```mermaid
flowchart TD
    File["Changed file:<br/>frontend/src/components/Button.tsx"]

    File --> Check1{"frontend/src/components/<br/>.claude/CLAUDE.md?"}
    Check1 -->|missing| Check2

    Check2{"frontend/<br/>.claude/CLAUDE.md?"}
    Check2 -->|exists| Rule2["Load TypeScript rules"]

    Rule2 --> Check3{".claude/CLAUDE.md?<br/>(root)"}
    Check3 -->|exists| Rule3["Load universal rules"]

    Rule3 --> Apply["Apply: TypeScript rules + Universal"]
```

## Validator Contracts

Each validator has a `contract.json` defining its scope:

| Validator | Language | Scope | Excludes | Assumes |
|-----------|----------|-------|----------|---------|
| **go-effective** | Go | Naming, Error handling, Interface design, Control flow | Security, Go Proverbs, Formatting | gofmt, golangci-lint |
| **go-proverbs** | Go | Idiomatic Go philosophy, Concurrency patterns, Abstraction | Security, Effective Go details, Formatting | golangci-lint |
| **python-style** | Python | Google docstrings, Type hints, Error handling, Layered architecture | Security, Performance | ruff, ty/mypy, pre-commit |
| **typescript-style** | TypeScript | Strict mode, React patterns, Hooks usage, State management | Security, Performance | biome, pre-commit |
| **security** | All | Secrets, Injection, Path traversal, Auth gaps | Code style, Language idioms, Performance | (none) |

### Validator Dependency Chain

Semantic validators assume deterministic linters have passed. This is enforced by Phase 3 ordering.

```mermaid
flowchart LR
    subgraph Det["Deterministic (must pass first)"]
        ruff["ruff"]
        ty["ty/mypy"]
        biome["biome"]
        tsc["tsc"]
        golangci["golangci-lint"]
    end

    subgraph Sem["Semantic (run after deterministic)"]
        pystyle["python-style"]
        tsstyle["typescript-style"]
        goeff["go-effective"]
        goprov["go-proverbs"]
        sec["security"]
    end

    ruff --> pystyle
    ty --> pystyle
    biome --> tsstyle
    tsc --> tsstyle
    golangci --> goeff
    golangci --> goprov

    sec -.->|"no dependencies"| Det
```

**HARD vs SHOULD by validator:**

| Validator | HARD Rules | SHOULD Rules |
|-----------|------------|--------------|
| **go-effective** | Doc comments, Error return position, No pointer-to-interface | Interface size, Early returns, Parameter count |
| **go-proverbs** | Share memory by communicating, Errors are values, Handle errors gracefully | Interface size, Zero value, Clear vs clever |
| **python-style** | Exception chaining with `from e`, No bare `except:` | Google docstrings, Modern type hints (`str \| None`) |
| **typescript-style** | Strict mode enabled, Functional components only | Proper hook dependencies, TanStack Query for server state |
| **security** | Secrets, Injection, Path traversal, Auth gaps | Insecure configurations |

This prevents:
- Validators reporting on the same thing (noise)
- Validators assuming work that didn't happen
- Scope creep over time

## Severity Model

All validators use the same unified schema:

| Level | Meaning | Action |
|-------|---------|--------|
| **HARD** | Must fix | Blocks completion |
| **SHOULD** | Fix or justify | Requires explicit justification |
| **WARN** | Advisory | Note in output, don't block |

This is intentionally simple. More levels create ambiguity.

## Example Output

### Single Validator Output

Each validator produces JSON in this schema:

```json
{
  "validator": "python-style",
  "applied_rules": [
    "backend/.claude/CLAUDE.md",
    ".claude/CLAUDE.md"
  ],
  "files_checked": ["backend/app/services/users.py"],
  "pass": false,
  "hard_violations": [
    {
      "rule": "Exception chaining required",
      "location": "users.py:45",
      "explanation": "raise UserNotFoundError() should use 'from e'"
    }
  ],
  "should_violations": [],
  "warnings": [],
  "summary": { "hard_count": 1, "should_count": 0, "warning_count": 0 }
}
```

### Aggregated Output (Phase 4)

Phase 4 combines all validator results into a single output:

```json
{
  "task": "implement user authentication",
  "applied_rules": [
    "backend/.claude/CLAUDE.md",
    "frontend/.claude/CLAUDE.md",
    ".claude/CLAUDE.md"
  ],
  "rule_conflicts": [],
  "files_changed": [
    "backend/app/services/auth.py",
    "backend/app/api/routes/auth.py",
    "frontend/src/hooks/useAuth.ts"
  ],
  "validation": {
    "pass": false,
    "validators": [
      {
        "name": "security",
        "pass": true,
        "hard_count": 0,
        "should_count": 0,
        "warning_count": 1
      },
      {
        "name": "python-style",
        "pass": false,
        "hard_count": 1,
        "should_count": 0,
        "warning_count": 0
      },
      {
        "name": "typescript-style",
        "pass": true,
        "hard_count": 0,
        "should_count": 0,
        "warning_count": 0
      }
    ],
    "total": {
      "hard_count": 1,
      "should_count": 0,
      "warning_count": 1
    }
  },
  "blocking_violations": [
    {
      "validator": "python-style",
      "rule": "Exception chaining required",
      "location": "auth.py:67",
      "explanation": "raise AuthenticationError() should use 'from e'"
    }
  ]
}
```

## Why This Works

| Failure Mode | How We Prevent It |
|--------------|-------------------|
| LLM forgets rules | Rules are mechanically injected in Phase 0 |
| Rules not applied | Output includes "Rules Applied" - observable |
| Validators overlap | Contracts declare scope/excludes |
| Validation skipped | `/implement` won't complete until validation passes |
| Silent failures | Validators echo `applied_rules` in JSON output |

## Edge Cases

| Scenario | Handling |
|----------|----------|
| First commit / no HEAD~1 | Fall back to staged files, then unstaged |
| Detached HEAD | Use `--diff-filter=ACMRT` to detect changes |
| >50 files changed | Process in batches of 50, note batch number |
| Conflicting rules | Prefer more specific rule, log in `rule_conflicts` array |
| New directories created during implementation | Re-run Phase 0 before validation |

### Rule Conflict Logging

When rules conflict (e.g., subdirectory rule contradicts root rule), the conflict is logged for auditability:

```json
{
  "rule_conflicts": [
    {
      "rule": "line-length",
      "root_value": 80,
      "override_value": 120,
      "source": "backend/.claude/CLAUDE.md",
      "resolution": "Used override (more specific)"
    }
  ]
}
```

The more specific rule always wins, but the conflict is recorded so it can be reviewed.

## Meta-rule (fallback only)

The root CLAUDE.md contains a meta-rule telling Claude to read subdirectory rules. This is a **fallback** for ad-hoc interactions, not the primary mechanism.

For `/implement` and `/review`, rule injection is mechanical and explicit. The meta-rule exists for:
- Manual Claude interactions
- Documentation of intent
- Edge cases where someone bypasses the workflow

It is **not** on the critical path.

## Validators

| Validator | Language | Status |
|-----------|----------|--------|
| go-effective | Go | ✅ Done |
| go-proverbs | Go | ✅ Done |
| python-style | Python | ✅ Done |
| typescript-style | TypeScript | ✅ Done |
| security | All | ✅ Done |

---

## Advisory Skills

Advisory skills provide optional, non-blocking feedback. Unlike validators, they don't gate commits or deployments - they offer additional perspectives and insights.

### Star-Chamber: Multi-LLM Craftsmanship Council

The `/star-chamber` skill fans out code reviews to multiple LLM providers (Claude, OpenAI, Gemini, etc.) and aggregates their feedback into consensus recommendations.

**Key characteristics:**
- Advisory only (doesn't block like validators)
- Uses `any-llm-sdk` via `uv run` (no global Python install needed)
- Supports parallel and sequential review modes

**Execution modes:**
| Mode | Invocation | Description |
|------|------------|-------------|
| Parallel | (default) | Independent calls to all providers simultaneously |
| Debate | `/star-chamber --debate --rounds N` | Multiple rounds with anonymous synthesis between rounds |

**Debate mode** uses [Chatham House rules](https://www.chathamhouse.org/about-us/chatham-house-rule) for inter-round summarization: feedback from each round is synthesized by content themes without attributing points to specific providers. This encourages engagement with ideas rather than sources, and reduces bias from provider reputation.

**Integration:**
```mermaid
flowchart LR
    subgraph Validators["Blocking Validators"]
        V1[security]
        V2[python-style]
        V3[go-proverbs]
    end

    subgraph Advisory["Advisory Skills"]
        A1[star-chamber]
    end

    Impl["/implement"] --> Validators
    Validators -->|"must pass"| Complete[Complete]

    Complete -.->|"optional"| Advisory
    Advisory -.->|"feedback"| Developer
```

**Output:**
- Markdown report with consensus/majority/individual issues
- JSON for tooling integration
- Quality ratings per provider

**Cost consideration:** Each invocation calls all configured providers (~$0.02-0.10 per run). Use intentionally, not automatically.
