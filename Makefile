AGENT ?= claude

.PHONY: help install uninstall
.DEFAULT_GOAL := help

help:
	@echo "agent-pragma - Pragma directives for AI coding agents"
	@echo ""
	@echo "Claude Code (recommended):"
	@echo "  /plugin marketplace add peteski22/agent-pragma"
	@echo "  /plugin install pragma@agent-pragma"
	@echo ""
	@echo "OpenCode:"
	@echo "  make install AGENT=opencode                        Install globally (~/.config/opencode/)"
	@echo "  make install AGENT=opencode PROJECT=/path/to/app   Install into a specific project"
	@echo "  make uninstall AGENT=opencode                      Remove OpenCode install"
	@echo ""
	@echo "Legacy Claude Code (deprecated):"
	@echo "  make install                                       Link skills and agents"
	@echo "  make uninstall                                     Remove legacy links"
	@echo "  make help                                          Show this help"

install:
ifdef PROJECT
	@bash "$(CURDIR)/scripts/install.sh" install "$(AGENT)" --project "$(PROJECT)"
else
	@bash "$(CURDIR)/scripts/install.sh" install "$(AGENT)"
endif

uninstall:
ifdef PROJECT
	@bash "$(CURDIR)/scripts/install.sh" uninstall "$(AGENT)" --project "$(PROJECT)"
else
	@bash "$(CURDIR)/scripts/install.sh" uninstall "$(AGENT)"
endif
