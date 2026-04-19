#!/usr/bin/env bash
# Import Anthropic's source-available skills (pdf, docx, pptx, xlsx) locally.
# These skills are NOT open-source — do NOT commit them.
# Their contents are gitignored in this toolkit.
#
# Usage:
#   bash scripts/import-anthropic-skills.sh

set -euo pipefail

TOOLKIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$TOOLKIT_ROOT/skills"
TMP="$(mktemp -d)"

echo "Cloning anthropics/skills (shallow)..."
git clone --depth 1 --single-branch https://github.com/anthropics/skills.git "$TMP/anthropic-skills"

for skill in pdf docx pptx xlsx; do
  src="$TMP/anthropic-skills/skills/$skill"
  dest="$SKILLS_DIR/$skill"
  if [[ ! -d "$src" ]]; then
    echo "Skipping $skill (not found in anthropic repo)"
    continue
  fi
  rm -rf "$dest"
  cp -R "$src" "$dest"
  echo "Imported: $skill"
done

rm -rf "$TMP"
echo ""
echo "Done. Note: these skills are source-available under Anthropic's terms,"
echo "not open source. They are gitignored; do not commit them."
