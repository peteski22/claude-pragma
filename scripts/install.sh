#!/usr/bin/env bash
# Install or uninstall pragma symlinks for a given agent.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_DIR="${REPO_ROOT}/plugins/pragma/skills"
AGENTS_SRC="${REPO_ROOT}/plugins/pragma/agents"

usage() {
    echo "Usage: $(basename "$0") <install|uninstall> <agent> [--project <path>]"
    echo ""
    echo "Agents:"
    echo "  claude    Legacy Claude Code install (deprecated)"
    echo "  opencode  OpenCode install"
    echo ""
    echo "Options:"
    echo "  --project <path>  Install into a specific project instead of globally"
    exit 1
}

# -- Argument parsing. --

if [[ $# -lt 2 ]]; then
    usage
fi

ACTION="$1"
AGENT="$2"
PROJECT=""
shift 2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            PROJECT="${2:?--project requires a path}"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            ;;
    esac
done

# -- Core: apply an action to a set of sources. --
# Usage: apply <install|uninstall> <target_dir> <label> <strip_ext> <sources...>
# Sources are pre-expanded by the caller (glob expansion happens at call site).

apply() {
    local action="$1" target_dir="$2" label="$3" strip_ext="$4"
    shift 4

    [[ "${action}" == "install" ]] && mkdir -p "${target_dir}"

    for src in "$@"; do
        [[ -e "${src}" ]] || continue
        local name
        name="$(basename "${src}" "${strip_ext}")"

        if [[ "${action}" == "install" ]]; then
            if [[ -d "${src}" ]]; then
                ln -sfn "${src}" "${target_dir}/$(basename "${src}")"
            else
                ln -sf "${src}" "${target_dir}/"
            fi
            echo "  Linked ${label}: ${name}"
        else
            rm -rf "${target_dir}/$(basename "${src}")"
            echo "  Removed ${label}: ${name}"
        fi
    done
}

# -- Generate OpenCode command files from SKILL.md frontmatter. --
# Skips skills with user-invocable: false (internal validators).

generate_commands() {
    local target_dir="$1"
    mkdir -p "${target_dir}"

    for skill_dir in "${SKILLS_DIR}"/*/; do
        local skill_file="${skill_dir}SKILL.md"
        [[ -f "${skill_file}" ]] || continue

        local name="" description="" user_invocable="true"
        local in_frontmatter=false

        while IFS= read -r line; do
            if [[ "${line}" == "---" ]]; then
                if "${in_frontmatter}"; then
                    break
                fi
                in_frontmatter=true
                continue
            fi
            "${in_frontmatter}" || continue

            case "${line}" in
                name:*)           name="${line#name: }" ;;
                description:*)    description="${line#description: }" ;;
                user-invocable:*) user_invocable="${line#user-invocable: }" ;;
            esac
        done < "${skill_file}"

        [[ "${user_invocable}" == "false" ]] && continue
        [[ -z "${name}" ]] && continue

        cat > "${target_dir}/${name}.md" <<EOF
---
description: ${description}
agent: build
---

Load the \`${name}\` skill using the skill tool, then follow its instructions.

\$ARGUMENTS
EOF
        echo "  Generated command: /${name}"
    done
}

remove_commands() {
    local target_dir="$1"

    for skill_dir in "${SKILLS_DIR}"/*/; do
        local skill_file="${skill_dir}SKILL.md"
        [[ -f "${skill_file}" ]] || continue

        local name=""
        local in_frontmatter=false

        while IFS= read -r line; do
            if [[ "${line}" == "---" ]]; then
                if "${in_frontmatter}"; then
                    break
                fi
                in_frontmatter=true
                continue
            fi
            "${in_frontmatter}" || continue

            case "${line}" in
                name:*) name="${line#name: }" ;;
            esac
        done < "${skill_file}"

        [[ -z "${name}" ]] && continue

        if [[ -f "${target_dir}/${name}.md" ]]; then
            rm -f "${target_dir}/${name}.md"
            echo "  Removed command: /${name}"
        fi
    done
}

# -- Generate OpenCode agent files from Claude Code agents. --
# Extracts description and shared body sections (Invocation Policy, Input,
# Arguments), replaces Claude-specific sections (Path Setup, Protocol, Memory)
# with a simple "load the skill" protocol.

generate_agents() {
    local target_dir="$1"
    mkdir -p "${target_dir}"

    for agent_file in "${AGENTS_SRC}"/*.md; do
        [[ -f "${agent_file}" ]] || continue

        local name
        name="$(basename "${agent_file}" .md)"

        # Extract description block from frontmatter (preserves >- multi-line YAML).
        local desc_block
        desc_block="$(awk '
            /^---$/ { if (n++) exit; next }
            /^description:/ { found=1; print; next }
            found && /^  / { print; next }
            found { exit }
        ' "${agent_file}")"

        # Extract body from after frontmatter up to Path Setup or Protocol.
        local head_content
        head_content="$(awk '
            BEGIN { in_fm=0; past_fm=0 }
            /^---$/ { if (!in_fm) { in_fm=1; next } else { past_fm=1; next } }
            !past_fm { next }
            /^## (Path Setup|Protocol)/ { exit }
            { print }
        ' "${agent_file}")"

        # Extract Arguments section if present (shared between both formats).
        local args_content
        args_content="$(awk '
            /^## Arguments/ { found=1; print; next }
            found && /^## / { exit }
            found { print }
        ' "${agent_file}")"

        # Assemble the OpenCode agent file.
        {
            cat <<EOF
---
${desc_block}
mode: subagent
model: anthropic/claude-sonnet-4-20250514
tools:
  write: false
  edit: false
---
EOF
            printf '%s\n' "${head_content}"
            cat <<EOF
## Protocol

Load the \`${name}\` skill using the skill tool, then follow its instructions.
EOF
            if [[ -n "${args_content}" ]]; then
                printf '\n%s\n' "${args_content}"
            fi
        } > "${target_dir}/${name}.md"

        echo "  Generated agent: ${name}"
    done
}

remove_agents() {
    local target_dir="$1"

    for agent_file in "${AGENTS_SRC}"/*.md; do
        [[ -f "${agent_file}" ]] || continue

        local name
        name="$(basename "${agent_file}" .md)"

        if [[ -f "${target_dir}/${name}.md" ]]; then
            rm -f "${target_dir}/${name}.md"
            echo "  Removed agent: ${name}"
        fi
    done
}

# -- Resolve target directory. --

case "${AGENT}" in
    opencode)
        if [[ -n "${PROJECT}" ]]; then
            target="${PROJECT}/.opencode"
        else
            target="${HOME}/.config/opencode"
        fi
        ;;
    claude)
        target="${HOME}/.claude"
        ;;
    *)
        echo "Unknown agent: ${AGENT}" >&2
        usage
        ;;
esac

# -- Dispatch. --

case "${ACTION}" in
    install)
        if [[ "${AGENT}" == "claude" ]]; then
            echo "WARNING: Legacy install is deprecated. Use the plugin marketplace instead:"
            echo "  /plugin marketplace add peteski22/agent-pragma"
            echo "  /plugin install pragma@agent-pragma"
            echo ""
        fi
        echo "Installing pragma for ${AGENT} (${target})..."
        ;;
    uninstall)
        echo "Removing pragma for ${AGENT} (${target})..."
        ;;
    *)
        usage
        ;;
esac

# Skills: symlinked for both agents.
apply "${ACTION}" "${target}/skills" "skill" "" "${REPO_ROOT}"/plugins/pragma/skills/*/

# Agents: generated for opencode, symlinked for claude.
if [[ "${AGENT}" == "opencode" ]]; then
    if [[ "${ACTION}" == "install" ]]; then
        generate_agents "${target}/agents"
    else
        remove_agents "${target}/agents"
    fi
else
    apply "${ACTION}" "${target}/agents" "agent" ".md" "${AGENTS_SRC}"/*.md
fi

# Commands: generated for opencode only.
if [[ "${AGENT}" == "opencode" ]]; then
    if [[ "${ACTION}" == "install" ]]; then
        generate_commands "${target}/commands"
    else
        remove_commands "${target}/commands"
    fi
fi

echo ""
echo "Done."
