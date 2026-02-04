# Context-Aware Rules

When working on files in a subdirectory, check if that subdirectory contains a `.claude/CLAUDE.md` file. If so, read it and apply those rules in addition to these universal rules.

For example:

- Editing `backend/app/main.py` → also read `backend/.claude/CLAUDE.md`
- Editing `frontend/src/App.tsx` → also read `frontend/.claude/CLAUDE.md`

Always apply the most specific rules available for the code you're working on.

## Local Supplements

If `.claude/local/CLAUDE.md` exists, read it and apply those rules in addition to the generated rules.

Local supplements are generally additive. The one exception: a "Validation Commands" section in local supplements overrides the default lint/test commands. This allows per-machine customization of validation scripts without modifying version-controlled rules.

Add `.claude/local/` to your `.gitignore` to keep personal rules out of version control.
