#!/usr/bin/env bash
# Security check for toolkit changes.
# Run before committing changes to the toolkit repository.
#
# Usage: ./scripts/security-check-toolkit.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ERRORS=0
WARNINGS=0

echo "=========================================="
echo "Security Check: LLM Toolkit"
echo "=========================================="
echo ""

# 1. Check for hardcoded secrets/credentials
echo "[1/6] Checking for hardcoded secrets..."
SECRET_PATTERNS=(
    'password\s*=\s*["\047][^"\047]+["\047]'
    'api[_-]?key\s*=\s*["\047][^"\047]+["\047]'
    'token\s*=\s*["\047][^"\047]+["\047]'
    'secret\s*=\s*["\047][^"\047]+["\047]'
    'aws_access_key_id\s*=\s*["\047]'
    'aws_secret_access_key\s*=\s*["\047]'
)

found_secrets=0
for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -riE "$pattern" "$TOOLKIT_ROOT/scripts" "$TOOLKIT_ROOT/.agents" "$TOOLKIT_ROOT/.windsurf" 2>/dev/null | grep -v "^Binary"; then
        ((found_secrets++)) || true
    fi
done

if [[ $found_secrets -gt 0 ]]; then
    echo "  WARNING: Potential hardcoded secrets found. Review above."
    ((WARNINGS++)) || true
else
    echo "  OK: No obvious hardcoded secrets detected."
fi

# 2. Check for .env files that might contain secrets
echo ""
echo "[2/6] Checking for committed .env files..."
ENV_FILES=$(find "$TOOLKIT_ROOT" -name ".env*" -type f ! -path "*/.git/*" 2>/dev/null || true)
if [[ -n "$ENV_FILES" ]]; then
    echo "  WARNING: .env files found (should be gitignored):"
    echo "$ENV_FILES" | while read -r f; do echo "    - $f"; done
    ((WARNINGS++)) || true
else
    echo "  OK: No .env files in repository."
fi

# 3. Check for proper .gitattributes (line endings)
echo ""
echo "[3/6] Checking .gitattributes..."
if [[ -f "$TOOLKIT_ROOT/.gitattributes" ]]; then
    if grep -q "eol=lf" "$TOOLKIT_ROOT/.gitattributes"; then
        echo "  OK: .gitattributes enforces LF line endings."
    else
        echo "  WARNING: .gitattributes may not enforce LF line endings."
        ((WARNINGS++)) || true
    fi
else
    echo "  WARNING: .gitattributes not found. LF enforcement recommended."
    ((WARNINGS++)) || true
fi

# 4. Check for cloud-sync duplicate files (e.g., "file (1).ext")
echo ""
echo "[4/6] Checking for cloud-sync duplicate files..."
DUPLICATES=$(find "$TOOLKIT_ROOT" -name '* ([0-9]).*' -type f ! -path "*/.git/*" 2>/dev/null || true)
if [[ -n "$DUPLICATES" ]]; then
    echo "  ERROR: Cloud-sync duplicates found (will cause conflicts):"
    echo "$DUPLICATES" | while read -r f; do echo "    - $f"; done
    ((ERRORS++)) || true
else
    echo "  OK: No cloud-sync duplicates found."
fi

# 5. Check for PII in example/template files
echo ""
echo "[5/6] Checking for PII in templates/examples..."
PII_PATTERNS=(
    '[0-9]{3}-[0-9]{2}-[0-9]{4}'  # SSN pattern
    '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'  # Email
)

found_pii=0
for pattern in "${PII_PATTERNS[@]}"; do
    if grep -riE "$pattern" "$TOOLKIT_ROOT/scripts/templates" 2>/dev/null; then
        ((found_pii++)) || true
    fi
done

if [[ $found_pii -gt 0 ]]; then
    echo "  WARNING: Potential PII patterns found in templates."
    ((WARNINGS++)) || true
else
    echo "  OK: No obvious PII patterns in templates."
fi

# 6. Check for executable permissions on scripts
echo ""
echo "[6/6] Checking script permissions..."
MISSING_EXEC=0
for script in "$SCRIPT_DIR"/*.sh; do
    if [[ -f "$script" && ! -x "$script" ]]; then
        echo "  WARNING: $script is not executable"
        ((MISSING_EXEC++)) || true
    fi
done

if [[ $MISSING_EXEC -eq 0 ]]; then
    echo "  OK: Shell scripts have executable permissions."
else
    echo "  INFO: $MISSING_EXEC script(s) may need chmod +x"
fi

echo ""
echo "=========================================="
echo "Results:"
echo "  Errors:   $ERRORS"
echo "  Warnings: $WARNINGS"
echo "=========================================="

if [[ $ERRORS -gt 0 ]]; then
    echo "FAILED: Fix errors before committing."
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo "PASSED WITH WARNINGS: Review warnings."
    exit 0
else
    echo "PASSED: All checks OK."
    exit 0
fi
