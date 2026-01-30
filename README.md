# Claude Code Skills

Custom skills for Claude Code.

## Usage

Symlink skills to your Claude config:

```bash
# Link a single skill
ln -s /path/to/claude-skills/skills/my-skill ~/.claude/skills/my-skill

# Or link the entire skills directory
ln -s /path/to/claude-skills/skills ~/.claude/skills
```

## Structure

```
skills/
├── example-skill/
│   └── SKILL.md
└── another-skill/
    ├── SKILL.md
    └── reference.md
```

## Creating a New Skill

1. Create a directory under `skills/`
2. Add a `SKILL.md` with YAML frontmatter
3. Symlink to `~/.claude/skills/`

See [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code) for details.
