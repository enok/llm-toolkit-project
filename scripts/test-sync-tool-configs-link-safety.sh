#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TMP_DIR="$(mktemp -d)"
NO_FORCE_OUT="$TMP_DIR/sync-no-force.out"
NO_FORCE_ERR="$TMP_DIR/sync-no-force.err"
FORCE_OUT="$TMP_DIR/sync-force.out"
FORCE_ERR="$TMP_DIR/sync-force.err"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p \
  "$TMP_DIR/rules" \
  "$TMP_DIR/workflows" \
  "$TMP_DIR/tool-subagents" \
  "$TMP_DIR/skills/example-skill" \
  "$TMP_DIR/.cursor/agents"

cat > "$TMP_DIR/rules/example-rule.md" <<'EOF'
---
description: Example rule for sync safety tests
---

# Example Rule
EOF

cat > "$TMP_DIR/workflows/example-workflow.md" <<'EOF'
# Example Workflow
EOF

cat > "$TMP_DIR/tool-subagents/example-agent.md" <<'EOF'
# Example Agent
EOF

cat > "$TMP_DIR/skills/example-skill/SKILL.md" <<'EOF'
---
name: example-skill
description: Example skill for sync safety tests.
---

# Example Skill
EOF

echo "do not delete without force" > "$TMP_DIR/.cursor/agents/stale.txt"

if bash "$ROOT/scripts/sync-tool-configs.sh" "$TMP_DIR" --skip-agents-md >"$NO_FORCE_OUT" 2>"$NO_FORCE_ERR"; then
  echo "FAIL: sync-tool-configs.sh succeeded despite a blocking .cursor/agents directory." >&2
  exit 1
fi

if [[ ! -f "$TMP_DIR/.cursor/agents/stale.txt" ]]; then
  echo "FAIL: blocking .cursor/agents content was removed without --force." >&2
  exit 1
fi

if ! grep -q -- "--force" "$NO_FORCE_ERR"; then
  echo "FAIL: no-force error did not explain the --force repair path." >&2
  cat "$NO_FORCE_ERR" >&2
  exit 1
fi

bash "$ROOT/scripts/sync-tool-configs.sh" "$TMP_DIR" --skip-agents-md --skip-github --force >"$FORCE_OUT" 2>"$FORCE_ERR"

if [[ -f "$TMP_DIR/.cursor/agents/stale.txt" ]]; then
  echo "FAIL: blocking .cursor/agents content survived --force repair." >&2
  exit 1
fi

if [[ ! -f "$TMP_DIR/.cursor/agents/example-agent.md" ]]; then
  echo "FAIL: .cursor/agents does not resolve to tool-subagents after --force repair." >&2
  exit 1
fi

if [[ -e "$TMP_DIR/.github/copilot-instructions.md" ]]; then
  echo "FAIL: --skip-github generated .github/copilot-instructions.md." >&2
  exit 1
fi

echo "PASS: sync-tool-configs preserves blocking paths unless --force is supplied."
