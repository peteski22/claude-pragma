# Universal Rules

These rules apply to all projects regardless of language or framework.

Rules are organized by timing: when they should be applied during the workflow.

**Contents:**
- [Pre-Implementation Setup](#pre-implementation-setup) - Actions to execute before coding
- [Implementation Guidelines](#implementation-guidelines) - Guidance to follow while coding
- [Pre-Completion Guidelines](#pre-completion-guidelines) - Verify before marking done

---

## Pre-Implementation Setup

Execute these actions before writing any code.

### Git Workflow

Check current branch:

```bash
git branch --show-current
```

**If on `main` or `master`**, create a feature branch:

```bash
# Replace <prefix> and <short-description> with actual values
git checkout -b <prefix>/<short-description>
```

**If not in a git repository**, skip git steps and note in report.

**If there are uncommitted changes**, you MUST ask the user before proceeding. Present these options:
- Stash the changes
- Commit the changes first
- Continue with uncommitted changes in the working tree

Do NOT stash, commit, or discard uncommitted changes without explicit user approval.

**If in detached HEAD state**, ask user whether to create a branch from current commit.

**If the proposed branch already exists**, ask user: switch to existing branch, or use a different name?

**If already on a feature branch**, confirm with user whether to continue on this branch or create a new one.

Use descriptive branch names with these prefixes:

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New functionality | `feature/add-user-auth` |
| `fix/` | Bug fixes | `fix/login-redirect-loop` |
| `refactor/` | Code improvements | `refactor/api-client-types` |
| `docs/` | Documentation only | `docs/update-readme` |
| `chore/` | Maintenance tasks | `chore/upgrade-dependencies` |

### Scope Verification

Before coding:

- If the task is ambiguous, clarify requirements with the user.
- If the task involves breaking changes to public APIs, confirm impact with the user.
- If the task scope seems larger than requested, verify intent before expanding.

### Pattern Discovery

Before proposing a solution, understand how the codebase already works.

**Core principle:** Ask "how does Y access X?" not "does X exist in Y?"

Checking if a directory exists tells you nothing about how code flows. Instead, trace the actual connections: grep for imports, check dependency files, examine how components are wired together.

**When implementing a new instance of something, find existing instances first.** Adding a new API endpoint? Study existing endpoints. New CLI command? Look at similar commands. New provider/adapter? Find existing providers. Copy their patterns unless there's a specific reason to deviate.

**Concrete checks before implementing:**
- **File paths/config locations:** Search for similar paths to find existing constants or variables instead of hardcoding strings.
- **Error messages:** Check how errors are formatted elsewhere (wrapping patterns, message style).
- **API responses:** Find existing response structures before creating new ones.
- **Logging:** Match existing log levels, formats, and context fields.
- **Dependencies:** Check if a package already provides the functionality you need.

**If the task involves sharing code between components**, find existing shared packages first and follow established patterns before proposing new ones.

**If a GitHub issue lists multiple approaches**, investigate each sufficiently to make an informed decision.

### Research

- Where possible, use WebSearch or WebFetch to lookup current documentation rather than relying on training data, especially for:
  - Library/framework APIs that change frequently.
  - Cloud provider documentation (AWS, GCP, Azure).
  - Language features added recently.
  - Version-specific behavior.

---

## Implementation Guidelines

Follow these while writing code.

### Code Quality

- Never introduce security vulnerabilities (OWASP top 10).
- Avoid over-engineering. Only make changes that are directly requested or necessary.
- Do not add features, refactor code, or make "improvements" beyond what was asked.
- Keep solutions simple and focused.

### Communication

- Be direct and objective. Avoid sycophantic responses.
- If you made a mistake, acknowledge it specifically rather than generic agreement.
- When uncertain, investigate first and/or ask the user, rather than guessing.

---

## Pre-Completion Guidelines

Verify these before marking work as done.

### Commits

- Follow atomic commit principles:
  - Each commit should represent one logical change.
  - Commits should be self-contained and independently reviewable.
  - Don't mix unrelated changes in a single commit.
  - Don't commit half-finished work; use stash if needed.
- Write clear commit messages that explain the "why", not just the "what".

### Pull Requests

- Push feature branches and create Pull Requests to merge into `main`.
- Keep PRs focused; large PRs are hard to review.
- Link PRs to issues using keywords: `Fixes #123`, `Closes #456`.
- Rebase feature branches onto `main` before merging to keep history linear.
- Squash commits if the PR contains fixup commits; preserve meaningful commit history otherwise.

---

## Rule Authority

If there is any discrepancy between CLAUDE.md guidance and validator agent behavior, the validator is authoritative. Validators encode the precise, enforceable rules.
