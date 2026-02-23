# Context-Aware Rules

When working on files in a subdirectory, check if that subdirectory contains a `.claude/CLAUDE.md` file. If so, read it and apply those rules in addition to these universal rules.

For example:

- Editing `backend/app/main.py` → also read `backend/.claude/CLAUDE.md`
- Editing `frontend/src/App.tsx` → also read `frontend/.claude/CLAUDE.md`

Always apply the most specific rules available for the code you're working on.

## Local Supplements

`CLAUDE.local.md` at the project root contains per-user, per-project instructions. Claude Code auto-loads it and adds it to `.gitignore`; if you create the file manually, verify it is in your `.gitignore`.

Rules from `CLAUDE.local.md` are additive to the rules in this file. The one exception: if `CLAUDE.local.md` contains a "Validation Commands" section, use those commands instead of the defaults. This allows per-machine customization of validation scripts without modifying version-controlled rules.
