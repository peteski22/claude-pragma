.PHONY: help install uninstall
.DEFAULT_GOAL := help

help:
	@echo "claude-pragma - Pragma directives for Claude Code"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Link setup-project skill to ~/.claude/skills/"
	@echo "  make uninstall  Remove setup-project skill link"
	@echo "  make help       Show this help"

install:
	@echo "Installing claude-pragma skills..."
	@mkdir -p ~/.claude/skills
	@ln -sf "$(CURDIR)/skills/universal/setup-project" ~/.claude/skills/
	@echo "Linked: /setup-project"
	@echo ""
	@echo "Add to your shell profile (~/.zshrc or ~/.bashrc):"
	@echo "  export CLAUDE_PRAGMA_PATH=\"$(CURDIR)\""
	@echo ""
	@echo "Then in Claude Code, run /setup-project in any project to set up validators."

uninstall:
	@echo "Removing claude-pragma skills..."
	@rm -f ~/.claude/skills/setup-project
	@echo "Removed: /setup-project"
	@echo ""
	@echo "Note: Other skills linked by /setup-project are not removed."
	@echo "To remove all, run: rm -rf ~/.claude/skills/*"
