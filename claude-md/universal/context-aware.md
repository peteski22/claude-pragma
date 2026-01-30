# Context-Aware Rules

When working on files in a subdirectory, check if that subdirectory contains a `.claude/CLAUDE.md` file. If so, read it and apply those rules in addition to these universal rules.

For example:

- Editing `backend/app/main.py` → also read `backend/.claude/CLAUDE.md`
- Editing `frontend/src/App.tsx` → also read `frontend/.claude/CLAUDE.md`

Always apply the most specific rules available for the code you're working on.
