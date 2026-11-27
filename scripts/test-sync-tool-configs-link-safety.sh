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

if [[ ! -f "$TMP_DIR/.cursor/rules/example-rule.mdc" ]] || [[ -L "$TMP_DIR/.cursor/rules" ]]; then
  echo "FAIL: .cursor/rules is not a generated directory of .mdc files." >&2
  exit 1
fi

if [[ -e "$TMP_DIR/.cursor/workflows" ]]; then
  echo "FAIL: .cursor/workflows was created although it is no longer a Cursor surface." >&2
  exit 1
fi

if [[ -e "$TMP_DIR/.github/copilot-instructions.md" ]]; then
  echo "FAIL: --skip-github generated .github/copilot-instructions.md." >&2
  exit 1
fi

# Consumer with its own tool-subagents/: hand-written *.toml stay visible to Codex.
for kind in toml md; do
  C="$TMP_DIR/consumer-$kind"
  mkdir -p "$C/tool-subagents" "$C/rules"
  echo "# Own Agent" > "$C/tool-subagents/own-agent.md"
  [[ "$kind" == toml ]] && printf 'name = "own-agent"\n' > "$C/tool-subagents/own-agent.toml"
  bash "$ROOT/scripts/sync-tool-configs.sh" "$C" --skip-agents-md --skip-github >/dev/null 2>&1 || true
  if [[ "$kind" == toml ]]; then
    if [[ ! -L "$C/.codex/agents" ]] || [[ ! -f "$C/.codex/agents/own-agent.toml" ]]; then
      echo "FAIL: consumer .codex/agents is not linked to its own tool-subagents/ holding .toml." >&2
      exit 1
    fi
  elif [[ -e "$C/.codex/agents" ]]; then
    echo "FAIL: consumer with only .md agents got a .codex/agents link." >&2
    exit 1
  fi
  if [[ -e "$C/tool-subagents/.generated" ]] || [[ "$(find "$C/tool-subagents" -type f | wc -l)" -gt 2 ]]; then
    echo "FAIL: sync wrote into the consumer's tool-subagents/." >&2
    exit 1
  fi
done

echo "PASS: sync-tool-configs preserves blocking paths unless --force is supplied."
