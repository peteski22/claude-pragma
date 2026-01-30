# Universal Rules

These rules apply to all projects regardless of language or framework.

## Research Practices

- Where possible, use WebSearch or WebFetch to lookup current documentation rather than relying on training data, especially for:
  - Library/framework APIs that change frequently
  - Cloud provider documentation (AWS, GCP, Azure)
  - Language features added recently
  - Version-specific behavior

## Git Workflow

We use feature branch workflow (GitHub Flow):

### Branching

- Never commit directly to `main`. Create a feature branch for each piece of work.
- Use descriptive branch names with prefixes:

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New functionality | `feature/add-user-auth` |
| `fix/` | Bug fixes | `fix/login-redirect-loop` |
| `refactor/` | Code improvements | `refactor/api-client-types` |
| `docs/` | Documentation only | `docs/update-readme` |
| `chore/` | Maintenance tasks | `chore/upgrade-dependencies` |

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

## Code Quality

- Never introduce security vulnerabilities (OWASP top 10).
- Avoid over-engineering. Only make changes that are directly requested or necessary.
- Do not add features, refactor code, or make "improvements" beyond what was asked.
- Keep solutions simple and focused.

## Communication

- Be direct and objective. Avoid sycophantic responses.
- If you made a mistake, acknowledge it specifically rather than generic agreement.
- When uncertain, investigate first and/or ask the user, rather than guessing.

## Rule Authority

If there is any discrepancy between CLAUDE.md guidance and validator agent behavior, the validator is authoritative. Validators encode the precise, enforceable rules.
