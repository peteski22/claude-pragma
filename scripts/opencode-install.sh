#!/usr/bin/env bash
set -euo pipefail

# claude-pragma installer for OpenCode
# Installs skills, agents, and commands globally or per-project.
#
# Usage:
#   ./scripts/opencode-install.sh              # Global install (~/.config/opencode/)
#   ./scripts/opencode-install.sh --project    # Project install (.opencode/ in current dir)
#   ./scripts/opencode-install.sh --uninstall  # Remove global install
#   ./scripts/opencode-install.sh --project --uninstall  # Remove project install

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults.
MODE="global"
ACTION="install"

for arg in "$@"; do
  case "$arg" in
    --project) MODE="project" ;;
    --uninstall) ACTION="uninstall" ;;
    --help|-h)
      echo "Usage: $0 [--project] [--uninstall]"
      echo ""
      echo "  (default)     Install globally to ~/.config/opencode/"
      echo "  --project     Install to .opencode/ in the current directory"
      echo "  --uninstall   Remove installed symlinks"
      echo ""
      echo "Global install makes skills, agents, and commands available"
      echo "in all OpenCode sessions. Project install only affects the"
      echo "current directory."
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Run $0 --help for usage."
      exit 1
      ;;
  esac
done

if [[ "$MODE" == "global" ]]; then
  TARGET_DIR="$HOME/.config/opencode"
else
  TARGET_DIR="$(pwd)/.opencode"
fi

SKILLS=(
  security
  python-style
  typescript-style
  go-effective
  go-proverbs
  state-machine
  implement
  review
  validate
  setup-project
  star-chamber
)

AGENTS=(
  security
  star-chamber
)

COMMANDS=(
  implement
  review
  validate
  setup-project
  star-chamber
)

uninstall() {
  echo "Removing claude-pragma from $TARGET_DIR..."

  for skill in "${SKILLS[@]}"; do
    target="$TARGET_DIR/skills/$skill"
    if [[ -L "$target" ]]; then
      rm -f "$target"
      echo "  Removed skill: $skill"
    fi
  done

  for agent in "${AGENTS[@]}"; do
    target="$TARGET_DIR/agents/$agent.md"
    if [[ -L "$target" ]]; then
      rm -f "$target"
      echo "  Removed agent: $agent"
    fi
  done

  for cmd in "${COMMANDS[@]}"; do
    target="$TARGET_DIR/commands/$cmd.md"
    if [[ -L "$target" ]]; then
      rm -f "$target"
      echo "  Removed command: $cmd"
    fi
  done

  echo ""
  echo "Uninstall complete."
  echo ""
  echo "Note: opencode.json instructions (if added) must be removed manually."
}

install() {
  echo "Installing claude-pragma to $TARGET_DIR..."
  echo ""

  # Create directories.
  mkdir -p "$TARGET_DIR/skills"
  mkdir -p "$TARGET_DIR/agents"
  mkdir -p "$TARGET_DIR/commands"

  # Symlink skills.
  echo "Skills:"
  for skill in "${SKILLS[@]}"; do
    source="$REPO_ROOT/.opencode/skills/$skill"
    target="$TARGET_DIR/skills/$skill"
    if [[ -e "$target" && ! -L "$target" ]]; then
      echo "  SKIP $skill (exists and is not a symlink -- remove manually to replace)"
      continue
    fi
    ln -sfn "$source" "$target"
    echo "  Linked: $skill"
  done

  echo ""

  # Symlink agents.
  echo "Agents:"
  for agent in "${AGENTS[@]}"; do
    source="$REPO_ROOT/.opencode/agents/$agent.md"
    target="$TARGET_DIR/agents/$agent.md"
    if [[ -e "$target" && ! -L "$target" ]]; then
      echo "  SKIP $agent (exists and is not a symlink -- remove manually to replace)"
      continue
    fi
    ln -sf "$source" "$target"
    echo "  Linked: $agent"
  done

  echo ""

  # Symlink commands.
  echo "Commands:"
  for cmd in "${COMMANDS[@]}"; do
    source="$REPO_ROOT/.opencode/commands/$cmd.md"
    target="$TARGET_DIR/commands/$cmd.md"
    if [[ -e "$target" && ! -L "$target" ]]; then
      echo "  SKIP $cmd (exists and is not a symlink -- remove manually to replace)"
      continue
    fi
    ln -sf "$source" "$target"
    echo "  Linked: /$cmd"
  done

  echo ""
  echo "Install complete."
  echo ""

  if [[ "$MODE" == "global" ]]; then
    echo "Skills, agents, and commands are now available in all OpenCode sessions."
    echo ""
    echo "To also inject the pragma rule files as context, add this to your"
    echo "project's opencode.json (adjust the path to where you cloned the repo):"
    echo ""
    echo '  {'
    echo '    "instructions": ['
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/universal/base.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/universal/context-aware.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/universal/validation-precedence.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/languages/go/go.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/languages/python/python.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/languages/typescript/typescript.md\""
    echo '    ]'
    echo '  }'
  else
    echo "Skills, agents, and commands are now available in this project."
    echo ""
    echo "To also inject the pragma rule files as context, add this to your"
    echo "project's opencode.json:"
    echo ""
    echo '  {'
    echo '    "instructions": ['
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/universal/base.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/universal/context-aware.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/universal/validation-precedence.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/languages/go/go.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/languages/python/python.md\","
    echo "      \"$REPO_ROOT/plugins/pragma/claude-md/languages/typescript/typescript.md\""
    echo '    ]'
    echo '  }'
  fi
  echo ""
  echo "Or run /setup-project in OpenCode to auto-generate .claude/CLAUDE.md files"
  echo "with the appropriate rules for your project's detected languages."
}

if [[ "$ACTION" == "uninstall" ]]; then
  uninstall
else
  install
fi
