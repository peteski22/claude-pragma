# Modular Rules

Project rules are organized in `.claude/rules/*.md` at the project root. Claude Code auto-loads all `.md` files in this directory. Language-specific rules use `paths:` frontmatter to scope them to matching files only.

For example:
- `.claude/rules/universal.md` — applies to all files
- `.claude/rules/python.md` with `paths: ["backend/**/*.py"]` — applies only to Python files in `backend/`

## Local Supplements

`CLAUDE.local.md` at the project root contains per-user, per-project instructions. Claude Code auto-loads it and adds it to `.gitignore`; if you create the file manually, verify it is in your `.gitignore`.

Rules from `CLAUDE.local.md` are additive to the rules in `.claude/rules/`. The one exception: if `CLAUDE.local.md` contains a "Validation Commands" section, use those commands instead of the defaults. This allows per-machine customization of validation scripts without modifying version-controlled rules.
