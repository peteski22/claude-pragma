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

```
                         ┌─────────────────────────────┐
                         │       Root CLAUDE.md        │
                         │  (Universal rules + meta)   │
                         └───────────┬─────────────────┘
                                     │
               ┌─────────────────────┴─────────────────────┐
               │                                           │
    ┌─────────────────────┐                     ┌─────────────────────┐
    │  Subdir CLAUDE.md   │                     │  Subdir CLAUDE.md   │
    │  backend/.claude/   │                     │  frontend/.claude/  │
    │  (Python rules)     │                     │  (TypeScript rules) │
    └───────────┬─────────┘                     └───────────┬─────────┘
                │                                           │
    ┌───────────┴───────────┐                   ┌───────────┴───────────┐
    │                       │                   │                       │
┌──────────┐          ┌──────────┐        ┌──────────┐          ┌──────────┐
│/implement│          │ /review  │        │/implement│          │ /review  │
├──────────┤          ├──────────┤        ├──────────┤          ├──────────┤
│ Phase 0: │          │ Step 2:  │        │ Phase 0: │          │ Step 2:  │
│ Load     │          │ Load     │        │ Load     │          │ Load     │
│ rules    │          │ rules    │        │ rules    │          │ rules    │
│ (walk up)│          │ (walk up)│        │ (walk up)│          │ (walk up)│
└──────────┘          └──────────┘        └──────────┘          └──────────┘
       │                    │                   │                    │
       └────────────────────┴───────────────────┴────────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────┐
                    │ Validator Agents (forked)   │
                    │ - validate-go-effective     │
                    │ - validate-go-proverbs      │
                    │ - validate-security         │
                    └─────────────────────────────┘
```

## System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           /implement <task>                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0: Inject Rules                                                       │
│                                                                             │
│   1. Identify target directories                                            │
│   2. Walk up from each directory to repo root                               │
│   3. Collect .claude/CLAUDE.md files                                        │
│   4. Read and apply (most specific first)                                   │
│   5. Record applied_rules                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1-2: Understand & Implement                                           │
│                                                                             │
│   Work is done following the injected rules                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Validate                                                           │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ Deterministic (linters)                                             │   │
│   │   • golangci-lint (Go)                                              │   │
│   │   • pre-commit (Python)                                             │   │
│   │   • If fail → STOP, fix first                                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ Semantic (validators in parallel)                                   │   │
│   │                                                                     │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │   │
│   │   │  security   │  │go-effective │  │ go-proverbs │                │   │
│   │   │             │  │             │  │             │                │   │
│   │   │ CRITICAL    │  │ HARD        │  │ SHOULD      │                │   │
│   │   │ WARNING     │  │ SHOULD      │  │             │                │   │
│   │   │             │  │ WARN        │  │             │                │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘                │   │
│   │          │                │                │                        │   │
│   │          └────────────────┴────────────────┘                        │   │
│   │                           │                                         │   │
│   │                           ▼                                         │   │
│   │                    Aggregate Results                                │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ Fix violations                                                      │   │
│   │   • HARD/CRITICAL: must fix                                         │   │
│   │   • SHOULD: fix or justify                                          │   │
│   │   • WARN: note only                                                 │   │
│   │   • Re-validate if fixes made                                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Complete                                                           │
│                                                                             │
│   Output includes:                                                          │
│     • Rules Applied (audit trail)                                           │
│     • Files Changed                                                         │
│     • Validation Results                                                    │
│     • Warnings                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Rule Injection Detail

```
Changed file: backend/app/handlers/user.go

Walk up from backend/app/handlers/:

    backend/app/handlers/.claude/CLAUDE.md  ←─ check (if exists, highest precedence)
              │
              ▼
    backend/app/.claude/CLAUDE.md           ←─ check
              │
              ▼
    backend/.claude/CLAUDE.md               ←─ check
              │
              ▼
    .claude/CLAUDE.md                       ←─ check (root, lowest precedence)

Collect all that exist, read them, apply in order.
Record in output as "Rules Applied".
```

## Validator Contract

Each validator has a `contract.json`:

```json
{
  "name": "go-effective",
  "scope": ["Naming", "Error handling", "Interface design"],
  "excludes": ["Security", "Go Proverbs", "Formatting"],
  "assumes": ["gofmt", "golangci-lint"]
}
```

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

## Why This Works

| Failure Mode | How We Prevent It |
|--------------|-------------------|
| LLM forgets rules | Rules are mechanically injected in Phase 0 |
| Rules not applied | Output includes "Rules Applied" - observable |
| Validators overlap | Contracts declare scope/excludes |
| Validation skipped | `/implement` won't complete until validation passes |
| Silent failures | Validators echo `applied_rules` in JSON output |

## Meta-rule (fallback only)

The root CLAUDE.md contains a meta-rule telling Claude to read subdirectory rules. This is a **fallback** for ad-hoc interactions, not the primary mechanism.

For `/implement` and `/review`, rule injection is mechanical and explicit. The meta-rule exists for:
- Manual Claude interactions
- Documentation of intent
- Edge cases where someone bypasses the workflow

It is **not** on the critical path.
