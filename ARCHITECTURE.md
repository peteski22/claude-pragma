# Architecture

This document explains the design decisions behind claude-config.

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

## Monorepo Structure

```mermaid
graph TD
    Root[".claude/CLAUDE.md<br/>(Universal rules + meta)"]

    Root --> Backend["backend/.claude/CLAUDE.md<br/>(Python rules)"]
    Root --> Frontend["frontend/.claude/CLAUDE.md<br/>(TypeScript rules)"]

    Backend --> BI["/implement<br/>Phase 0: Load rules"]
    Backend --> BR["/review<br/>Step 2: Load rules"]

    Frontend --> FI["/implement<br/>Phase 0: Load rules"]
    Frontend --> FR["/review<br/>Step 2: Load rules"]

    BI --> Validators["Validator Agents<br/>(forked)"]
    BR --> Validators
    FI --> Validators
    FR --> Validators

    Validators --> GoEff["go-effective"]
    Validators --> GoProv["go-proverbs"]
    Validators --> Sec["security"]
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
            Lint[golangci-lint / pre-commit]
            LintFail{Pass?}
            Lint --> LintFail
        end

        subgraph Semantic["Semantic Validators (parallel)"]
            V1[security]
            V2[go-effective]
            V3[go-proverbs]
        end

        Agg[Aggregate Results]
        Fix[Fix violations]
        ReVal{Re-validate?}

        LintFail -->|No| FixLint[Fix lint errors]
        FixLint --> Lint
        LintFail -->|Yes| V1 & V2 & V3
        V1 & V2 & V3 --> Agg
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

```mermaid
flowchart TD
    File["Changed file:<br/>backend/app/handlers/user.go"]

    File --> Check1{"backend/app/handlers/<br/>.claude/CLAUDE.md?"}
    Check1 -->|exists| Rule1["Load (highest precedence)"]
    Check1 -->|missing| Check2

    Rule1 --> Check2{"backend/app/<br/>.claude/CLAUDE.md?"}
    Check2 -->|exists| Rule2["Load"]
    Check2 -->|missing| Check3

    Rule2 --> Check3{"backend/<br/>.claude/CLAUDE.md?"}
    Check3 -->|exists| Rule3["Load"]
    Check3 -->|missing| Check4

    Rule3 --> Check4{".claude/CLAUDE.md?<br/>(root)"}
    Check4 -->|exists| Rule4["Load (lowest precedence)"]

    Rule4 --> Apply["Apply in order<br/>Record as 'Rules Applied'"]
```

## Validator Contracts

Each validator has a `contract.json` defining its scope:

| Validator | Scope | Excludes | Assumes |
|-----------|-------|----------|---------|
| **go-effective** | Naming, Error handling, Interface design, Control flow | Security, Go Proverbs, Formatting | gofmt, golangci-lint |
| **go-proverbs** | Idiomatic Go philosophy, Concurrency patterns, Abstraction | Security, Effective Go details, Formatting | golangci-lint |
| **security** | Secrets, Injection, Path traversal, Auth gaps | Code style, Language idioms, Performance | (none) |

This prevents:
- Validators reporting on the same thing (noise)
- Validators assuming work that didn't happen
- Scope creep over time

## Severity Model

| Level | Meaning | Action |
|-------|---------|--------|
| **HARD** / **CRITICAL** | Must fix | Blocks completion |
| **SHOULD** | Fix or justify | Requires explicit justification |
| **WARN** | Advisory | Note in output, don't block |

This is intentionally simple. More levels create ambiguity.

## Example Output

```json
{
  "validator": "go-effective",
  "applied_rules": [
    "backend/.claude/CLAUDE.md",
    ".claude/CLAUDE.md"
  ],
  "files_checked": [
    "backend/app/handlers/user.go",
    "backend/app/handlers/user_test.go"
  ],
  "pass": false,
  "hard_violations": [
    {
      "rule": "Exported identifiers MUST have doc comments",
      "location": "user.go:45",
      "explanation": "Function CreateUser is exported but has no doc comment"
    }
  ],
  "should_violations": [
    {
      "rule": "Functions SHOULD do one thing",
      "location": "user.go:78",
      "justification_required": true
    }
  ],
  "warnings": [
    {
      "rule": "Overly complex functions",
      "location": "user.go:120",
      "note": "Consider breaking into smaller functions"
    }
  ],
  "summary": {
    "hard_count": 1,
    "should_count": 1,
    "warning_count": 1
  }
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
| >50 files changed | Process in batches |
| Conflicting rules | Prefer more specific rule, note conflict |
| New directories created during implementation | Re-run Phase 0 before validation |

## Meta-rule (fallback only)

The root CLAUDE.md contains a meta-rule telling Claude to read subdirectory rules. This is a **fallback** for ad-hoc interactions, not the primary mechanism.

For `/implement` and `/review`, rule injection is mechanical and explicit. The meta-rule exists for:
- Manual Claude interactions
- Documentation of intent
- Edge cases where someone bypasses the workflow

It is **not** on the critical path.

## Future Validators

Placeholder for planned validators:

| Validator | Language | Status |
|-----------|----------|--------|
| go-effective | Go | ✅ Done |
| go-proverbs | Go | ✅ Done |
| security | All | ✅ Done |
| python-style | Python | Planned |
| typescript-style | TypeScript | Planned |
