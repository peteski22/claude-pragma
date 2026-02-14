.PHONY: help install uninstall
.DEFAULT_GOAL := help

help:
	@echo "claude-pragma - Pragma directives for Claude Code"
	@echo ""
	@echo "Usage:"
	@echo "  make install    Link setup-project skill and all agents"
	@echo "  make uninstall  Remove setup-project skill and agent links"
	@echo "  make help       Show this help"

install:
	@echo "Installing claude-pragma skills and agents..."
	@mkdir -p ~/.claude/skills
	@ln -sf "$(CURDIR)/skills/universal/setup-project" ~/.claude/skills/
	@echo "Linked skill: /setup-project"
	@mkdir -p ~/.claude/agents
	@for agent in "$(CURDIR)"/agents/*.md; do \
		if [ -f "$$agent" ]; then \
			ln -sf "$$agent" ~/.claude/agents/; \
			echo "Linked agent: $$(basename $$agent .md)"; \
		fi; \
	done
	@echo ""
	@echo "Add to your shell profile (~/.zshrc or ~/.bashrc):"
	@echo "  export CLAUDE_PRAGMA_PATH=\"$(CURDIR)\""
	@echo ""
	@echo "Then in Claude Code, run /setup-project in any project to set up validators."

uninstall:
	@echo "Removing claude-pragma skills and agents..."
	@rm -f ~/.claude/skills/setup-project
	@echo "Removed skill: /setup-project"
	@for agent in "$(CURDIR)"/agents/*.md; do \
		if [ -f "$$agent" ]; then \
			rm -f ~/.claude/agents/$$(basename "$$agent"); \
			echo "Removed agent: $$(basename $$agent .md)"; \
		fi; \
	done
	@echo ""
	@echo "Note: Other skills linked by /setup-project are not removed."
	@echo "To remove all, run: rm -rf ~/.claude/skills/* ~/.claude/agents/*"
