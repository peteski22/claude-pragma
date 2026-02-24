.PHONY: help install uninstall
.DEFAULT_GOAL := help

help:
	@echo "claude-pragma - Pragma directives for Claude Code"
	@echo ""
	@echo "DEPRECATED: Use the plugin marketplace instead:"
	@echo "  /plugin marketplace add peteski22/claude-pragma"
	@echo "  /plugin install pragma@claude-pragma"
	@echo ""
	@echo "Legacy commands (for migration):"
	@echo "  make install    Link setup-project skill and all agents (deprecated)"
	@echo "  make uninstall  Remove setup-project skill and agent links"
	@echo "  make help       Show this help"

install:
	@echo "WARNING: make install is deprecated. Use the plugin marketplace instead:"
	@echo "  /plugin marketplace add peteski22/claude-pragma"
	@echo "  /plugin install pragma@claude-pragma"
	@echo ""
	@echo "Installing legacy symlinks for migration..."
	@mkdir -p ~/.claude/skills
	@ln -sf "$(CURDIR)/plugins/pragma/skills/setup-project" ~/.claude/skills/
	@echo "Linked skill: /setup-project (deprecated; use /setup-project via plugin install)"
	@mkdir -p ~/.claude/agents
	@for agent in "$(CURDIR)"/plugins/pragma/agents/*.md; do \
		if [ -f "$$agent" ]; then \
			ln -sf "$$agent" ~/.claude/agents/; \
			echo "Linked agent: $$(basename $$agent .md)"; \
		fi; \
	done
	@echo ""
	@echo "Legacy install complete. Consider migrating to the plugin marketplace."

uninstall:
	@echo "Removing claude-pragma skills and agents..."
	@rm -f ~/.claude/skills/setup-project
	@echo "Removed skill: /setup-project"
	@for agent in "$(CURDIR)"/plugins/pragma/agents/*.md; do \
		if [ -f "$$agent" ]; then \
			rm -f ~/.claude/agents/$$(basename "$$agent"); \
			echo "Removed agent: $$(basename $$agent .md)"; \
		fi; \
	done
	@echo ""
	@echo "Note: Other skills linked by /setup-project are not removed."
	@echo "To remove all, run: rm -rf ~/.claude/skills/* ~/.claude/agents/*"
