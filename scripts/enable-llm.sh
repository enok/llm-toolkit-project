#!/bin/bash
# =============================================================================
# LLM Toolkit Enablement Script
# =============================================================================
# This script enables LLM support for a target project by creating symlinks
# or copying LLM configuration files locally.
#
# Compatible with: Linux, macOS, Git Bash on Windows
# Windows prerequisite: Developer Mode must be enabled (Settings > For developers)
# or Git Bash must be run as Administrator, otherwise directory symlinks will fail.
#
# Usage:
#   ./scripts/enable-llm.sh [TARGET_PROJECT_PATH] [OPTIONS]
#
# Arguments:
#   TARGET_PROJECT_PATH  Path to the project where LLM support should be enabled
#                        (default: current directory)
#
# Options:
#   --clean      Remove LLM files from target project
#   --dirs-only  Only link directories, skip AGENTS.md and CLAUDE.md
#               (use when project keeps these files locally)
#   --relative   Use relative paths for symlinks when toolkit and project share
#               the same parent directory (e.g., ../llm-toolkit/.windsurf)
#
# Examples:
#   ./scripts/enable-llm.sh /path/to/my/project
#   ./scripts/enable-llm.sh /path/to/my/project --clean
#   ./scripts/enable-llm.sh /path/to/my/project --dirs-only  # Skip AGENTS.md/CLAUDE.md
#   ./scripts/enable-llm.sh ../my-project --relative        # Use relative paths
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLM_TOOLKIT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Detect OS
is_windows() {
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
        *) return 1 ;;
    esac
}

is_macos() {
    [ "$(uname -s)" = "Darwin" ]
}

# Portable sed -i: GNU (Linux/Git Bash) needs sed -i; BSD (macOS) needs sed -i ''
sed_inplace() {
    if is_macos; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

# Convert a Windows-style path to Unix style if running under Git Bash
to_unix_path() {
    local p="$1"
    if is_windows && command -v cygpath &>/dev/null; then
        cygpath -u "$p"
    else
        echo "$p"
    fi
}

# Colors — disable when terminal doesn't support them (e.g. Windows Git Bash without TERM)
if [ "${NO_COLOR:-}" != "" ] || (is_windows && [ "${TERM:-}" = "" ]); then
    RED='' GREEN='' YELLOW='' BLUE='' NC=''
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
fi

# On Windows, warn if Developer Mode cannot be confirmed
check_windows_symlink_prereq() {
    if ! is_windows; then return 0; fi
    # Developer Mode registry key (readable without elevation)
    local reg_key="HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock"
    local val
    val="$(reg query "$reg_key" /v AllowDevelopmentWithoutDevLicense 2>/dev/null | grep -i AllowDevelopment || true)"
    if echo "$val" | grep -q "0x1"; then
        return 0  # Developer Mode is on
    fi
    echo -e "${YELLOW}Warning: Windows Developer Mode not detected.${NC}"
    echo "  Directory symlinks may fail. Either:"
    echo "    1. Enable Developer Mode: Settings > System > For developers"
    echo "    2. Run Git Bash as Administrator"
    echo ""
}

# Parse arguments
TARGET_PATH="${1:-$(pwd)}"
MODE="symlink"
ITEMS_SET="all"  # all or dirs-only
USE_RELATIVE=false  # use relative paths for symlinks

if [ $# -gt 1 ]; then
    for arg in "${@:2}"; do
        case "$arg" in
            --clean) MODE="clean" ;;
            --dirs-only) ITEMS_SET="dirs-only" ;;
            --relative) USE_RELATIVE=true ;;
        esac
    done
fi

# Normalise TARGET_PATH to an absolute Unix path
TARGET_PATH="$(to_unix_path "$TARGET_PATH")"
TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

# Select appropriate item set
if [ "$ITEMS_SET" = "dirs-only" ]; then
    LLM_ITEMS=("${LLM_DIRS_ONLY[@]}")
fi

# Determine if we can use relative paths (LLM toolkit and target share same parent)
use_relative_paths() {
    if [ "$USE_RELATIVE" = false ]; then
        return 1  # User didn't request relative paths
    fi
    
    local llm_parent="$(cd "$LLM_TOOLKIT_DIR/.." && pwd)"
    local target_parent="$(cd "$TARGET_PATH/.." && pwd)"
    
    if [ "$llm_parent" = "$target_parent" ]; then
        return 0  # Same parent, can use relative
    else
        return 1  # Different locations
    fi
}

echo "============================================================"
echo "LLM Toolkit Enablement"
echo "============================================================"
echo "LLM Toolkit:    $LLM_TOOLKIT_DIR"
echo "Target Project: $TARGET_PATH"
echo "Mode:           $MODE"
if is_windows; then
    echo "Platform:       Windows (Git Bash)"
fi
echo "============================================================"
check_windows_symlink_prereq
echo ""

# Verify target is a git repository
if [ ! -d "$TARGET_PATH/.git" ]; then
    echo -e "${YELLOW}⚠️  Warning: Target does not appear to be a git repository${NC}"
    echo "   LLM files should only be added to version-controlled projects."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Files and directories to enable (by default, includes all)
# Use --dirs-only to skip AGENTS.md and CLAUDE.md (for projects that keep them locally)
# Note: Only include items that exist in the LLM toolkit
LLM_ITEMS=(
    ".windsurf"
    ".cursor"
    ".agents"
    ".claude"
    ".codex"
    ".setup"
    "rubrics"
    ".cursorignore"
    ".cursorindexingignore"
    "AGENTS.md"
    "CLAUDE.md"
)

# Directories only (when using --dirs-only)
LLM_DIRS_ONLY=(
    ".windsurf"
    ".cursor"
    ".agents"
    ".claude"
    ".codex"
    ".setup"
    "rubrics"
    ".cursorignore"
    ".cursorindexingignore"
)

enable_item() {
    local item="$1"
    local source="$LLM_TOOLKIT_DIR/$item"
    local target="$TARGET_PATH/$item"
    local link_source="$source"
    
    # Use relative path for symlinks if requested and possible
    if [ "$MODE" = "symlink" ] && use_relative_paths; then
        local llm_dirname="$(basename "$LLM_TOOLKIT_DIR")"
        link_source="../$llm_dirname/$item"
    fi
    
    if [ ! -e "$source" ]; then
        echo -e "${YELLOW}⚠️  Source not found: $item${NC}"
        return 1
    fi
    
    # Remove existing
    if [ -e "$target" ] || [ -L "$target" ]; then
        echo -e "${YELLOW}   Removing existing: $item${NC}"
        rm -rf "$target"
    fi
    
    if ln -s "$link_source" "$target"; then
        if use_relative_paths; then
            echo -e "${GREEN}✓ Linked: $item (relative: $link_source)${NC}"
        else
            echo -e "${GREEN}✓ Linked: $item${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to link: $item${NC}"
        if is_windows; then
            echo "  Ensure Developer Mode is on or run Git Bash as Administrator."
        fi
        return 1
    fi
}

disable_item() {
    local item="$1"
    local target="$TARGET_PATH/$item"
    
    if [ -e "$target" ] || [ -L "$target" ]; then
        rm -rf "$target"
        echo -e "${GREEN}✓ Removed: $item${NC}"
    else
        echo -e "${YELLOW}   Not found: $item${NC}"
    fi
}

# Also need to create docs/llm directory structure
create_docs_structure() {
    local docs_llm="$TARGET_PATH/docs/llm"
    
    if [ "$MODE" = "clean" ]; then
        if [ -d "$docs_llm" ]; then
            rm -rf "$docs_llm"
            echo -e "${GREEN}✓ Removed: docs/llm${NC}"
        fi
        return
    fi
    
    mkdir -p "$docs_llm/workflows"
    mkdir -p "$docs_llm/rules"
    mkdir -p "$docs_llm/references"
    
    # Copy docs/llm content
    if [ -d "$LLM_TOOLKIT_DIR/docs/llm" ]; then
        cp -r "$LLM_TOOLKIT_DIR/docs/llm/"* "$docs_llm/" 2>/dev/null || true
        echo -e "${GREEN}✓ Installed: docs/llm${NC}"
    fi
}

# Main execution
echo "Processing LLM configuration..."
echo ""

if [ "$MODE" = "clean" ]; then
    echo -e "${YELLOW}Cleaning LLM files from target project...${NC}"
    for item in "${LLM_ITEMS[@]}"; do
        disable_item "$item"
    done
    create_docs_structure

    # Update .gitignore
    if [ -f "$TARGET_PATH/.gitignore" ]; then
        sed_inplace '/# LLM Tooling/d' "$TARGET_PATH/.gitignore"
        sed_inplace '/\.windsurf/d' "$TARGET_PATH/.gitignore"
        sed_inplace '/\.cursor/d' "$TARGET_PATH/.gitignore"
        sed_inplace '/\.agents/d' "$TARGET_PATH/.gitignore"
        sed_inplace '/AGENTS\.md/d' "$TARGET_PATH/.gitignore"
        echo -e "${GREEN}OK Cleaned .gitignore${NC}"
    fi

    echo ""
    echo -e "${GREEN}Done: LLM files removed from target project.${NC}"
else
    echo -e "${BLUE}Installing LLM configuration...${NC}"
    for item in "${LLM_ITEMS[@]}"; do
        enable_item "$item"
    done
    create_docs_structure
    
    # Update .gitignore if needed
    if [ -f "$TARGET_PATH/.gitignore" ]; then
        if ! grep -q "# LLM Tooling" "$TARGET_PATH/.gitignore" 2>/dev/null; then
            echo "" >> "$TARGET_PATH/.gitignore"
            echo "# LLM Tooling (local-only, do not commit)" >> "$TARGET_PATH/.gitignore"
            echo ".windsurf/" >> "$TARGET_PATH/.gitignore"
            echo ".cursor/" >> "$TARGET_PATH/.gitignore"
            echo ".agents/" >> "$TARGET_PATH/.gitignore"
            if [ "$ITEMS_SET" = "all" ]; then
                echo "AGENTS.md" >> "$TARGET_PATH/.gitignore"
                echo "CLAUDE.md" >> "$TARGET_PATH/.gitignore"
            fi
            echo -e "${GREEN}✓ Updated .gitignore${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Done: LLM support enabled for: $TARGET_PATH${NC}"
    if [ "$ITEMS_SET" = "dirs-only" ]; then
        echo ""
        echo "Note: AGENTS.md and CLAUDE.md were NOT linked (--dirs-only mode)"
        echo "      These files should be managed locally in your project."
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Review the linked/copied LLM configuration files"
    echo "  2. Start using LLM assistance with your project"
    echo "  3. To disable: ./scripts/enable-llm.sh $TARGET_PATH --clean"
fi

echo ""
echo "============================================================"
