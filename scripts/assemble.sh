#!/bin/bash
# Assemble a CLAUDE.md from composable fragments.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

usage() {
    echo "Usage: $0 --lang <language> [--output <path>]"
    echo ""
    echo "Options:"
    echo "  --lang     Language(s) to include (comma-separated): go, python"
    echo "  --output   Output path (default: stdout)"
    echo ""
    echo "Examples:"
    echo "  $0 --lang go --output .claude/CLAUDE.md"
    echo "  $0 --lang go,python > CLAUDE.md"
    exit 1
}

LANGUAGES=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --lang)
            LANGUAGES="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

if [[ -z "$LANGUAGES" ]]; then
    echo "Error: --lang is required"
    usage
fi

assemble() {
    echo "# Project Rules"
    echo ""
    echo "<!-- Assembled from claude-config fragments -->"
    echo "<!-- Languages: $LANGUAGES -->"
    echo ""

    # Always include universal base.
    if [[ -f "$REPO_DIR/claude-md/universal/base.md" ]]; then
        cat "$REPO_DIR/claude-md/universal/base.md"
        echo ""
    fi

    # Include each language.
    IFS=',' read -ra LANG_ARRAY <<< "$LANGUAGES"
    for lang in "${LANG_ARRAY[@]}"; do
        lang=$(echo "$lang" | xargs)  # Trim whitespace.
        lang_file="$REPO_DIR/claude-md/languages/$lang/$lang.md"
        if [[ -f "$lang_file" ]]; then
            cat "$lang_file"
            echo ""
        else
            echo "# Warning: No rules found for language: $lang" >&2
        fi
    done
}

if [[ -n "$OUTPUT" ]]; then
    mkdir -p "$(dirname "$OUTPUT")"
    assemble > "$OUTPUT"
    echo "Assembled CLAUDE.md written to: $OUTPUT"
else
    assemble
fi
