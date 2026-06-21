#!/usr/bin/env bash
# Verify that yousa-skills are correctly installed into Trae's skill dir
# AND that each one is loadable (valid YAML frontmatter, correct name match).
# This is an end-to-end "did Trae actually accept it" verification.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TRAE_DIR="${TRAE_SKILLS_DIR:-$HOME/.trae-cn/skills}"
CONFIG="${TRAE_CONFIG_PATH:-$HOME/.trae-cn/skill-config.json}"

pass=0
fail=0
check_pass() { pass=$((pass+1)); echo "  PASS $*"; }
check_fail() { fail=$((fail+1)); echo "  FAIL $*"; }

echo "[1] Repo skills present on disk under Trae skills dir ($TRAE_DIR)"
expected_skills="$(bash "$REPO_ROOT/install.sh" --list)"
for s in $expected_skills; do
  if [[ -d "$TRAE_DIR/$s" && -f "$TRAE_DIR/$s/SKILL.md" ]]; then
    check_pass "exists: $s"
  else
    check_fail "missing: $s"
  fi
done

echo ""
echo "[2] Frontmatter integrity (name & description fields parse cleanly)"
for s in $expected_skills; do
  f="$TRAE_DIR/$s/SKILL.md"
  [[ -f "$f" ]] || { check_fail "no SKILL.md: $s"; continue; }
  fm="$(awk '/^---$/{n++; next} n==1' "$f")"
  name="$(printf '%s\n' "$fm" | awk '/^name:/{sub(/^name:[[:space:]]*/,""); print; exit}')"
  desc="$(printf '%s\n' "$fm" | awk '/^description:/{sub(/^description:[[:space:]]*/,""); print; exit}')"
  # Strip matching surrounding quotes (single or double); YAML allows both,
  # and AGENTS.md explicitly recommends them for long descriptions.
  name="${name#\"}"; name="${name%\"}"
  name="${name#\'}"; name="${name%\'}"
  if [[ -z "$name" || -z "$desc" ]]; then
    check_fail "invalid frontmatter: $s"
    continue
  fi
  if [[ "$name" != "$s" ]]; then
    check_fail "name mismatch: dir=$s frontmatter-name=$name"
    continue
  fi
  check_pass "valid: $s"
done

echo ""
echo "[3] Content matches source skills/ directory byte-for-byte"
for s in $expected_skills; do
  if diff -rq "$REPO_ROOT/skills/$s" "$TRAE_DIR/$s" >/dev/null 2>&1; then
    check_pass "matches repo: $s"
  else
    check_fail "diff from repo: $s"
  fi
done

echo ""
echo "[4] Trae skill-config.json: yousa skills are not in disabledSkills"
if [[ -f "$CONFIG" ]]; then
  disabled_list="$(python3 -c "import json; print('\n'.join(json.load(open('$CONFIG')).get('disabledSkills', [])))")"
  for s in $expected_skills; do
    if printf '%s\n' "$disabled_list" | grep -F -x -q "$s"; then
      check_fail "DISABLED in skill-config.json: $s"
    else
      check_pass "enabled: $s"
    fi
  done
else
  check_fail "skill-config.json not found at $CONFIG"
fi

echo ""
echo "[5] Adjacent foreign skills (e.g. lark-*) preserved"
foreign_count=$(ls "$TRAE_DIR" | grep -v -F -x -f <(printf '%s\n' $expected_skills) | wc -l | tr -d ' ')
if [[ "$foreign_count" -gt 0 ]]; then
  check_pass "$foreign_count non-yousa skills preserved"
  ls "$TRAE_DIR" | grep -v -F -x -f <(printf '%s\n' $expected_skills) | head -5 | sed 's/^/    - /'
else
  check_fail "all non-yousa skills disappeared (script over-reached!)"
fi

echo ""
echo "Summary: $pass passed, $fail failed"
[[ $fail -eq 0 ]] && exit 0 || exit 1
