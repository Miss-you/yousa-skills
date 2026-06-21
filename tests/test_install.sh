#!/usr/bin/env bash
# Acceptance tests for install.sh.
# Uses CLAUDE_SKILLS_DIR / CODEX_SKILLS_DIR / TRAE_SKILLS_DIR env overrides
# to run against a temporary scratch directory — never touches the user's
# real ~/.claude, ~/.codex, or ~/.trae-cn.
#
# Portable across macOS (BSD coreutils) and Linux (GNU coreutils): chooses
# sha256sum vs `shasum -a 256` and snapshots files by content hash rather
# than `stat` (whose flag syntax differs across platforms).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL="$REPO_ROOT/install.sh"

if command -v sha256sum >/dev/null 2>&1; then
  HASH=(sha256sum)
elif command -v shasum >/dev/null 2>&1; then
  HASH=(shasum -a 256)
else
  echo "error: need sha256sum or shasum on PATH" >&2
  exit 2
fi

pass=0
fail=0
fail_msgs=()

ok()  { pass=$((pass+1)); printf '  PASS %s\n' "$*"; }
bad() { fail=$((fail+1)); fail_msgs+=("$*"); printf '  FAIL %s\n' "$*"; }

# Stable content hash for every file under given dirs. Used to detect any
# modification. Order is sorted so output is reproducible.
snapshot() {
  local out="$1"; shift
  : > "$out"
  for d in "$@"; do
    [[ -e "$d" ]] || continue
    ( cd "$d" && find . -type f -print0 | sort -z | xargs -0 "${HASH[@]}" ) >> "$out"
  done
}

# Hash a single file's content (portable across BSD/GNU).
file_hash() { "${HASH[@]}" < "$1" | awk '{print $1}'; }

new_env() {
  TMP="$(mktemp -d)"
  CLAUDE="$TMP/claude/skills"
  CODEX="$TMP/codex/skills"
  TRAE="$TMP/trae/skills"
  mkdir -p "$CLAUDE" "$CODEX" "$TRAE"

  # Pre-populate with "third-party" skills (not in this repo).
  mkdir -p "$CLAUDE/foreign-a" "$CLAUDE/foreign-b/sub"
  printf 'AAA\n' > "$CLAUDE/foreign-a/SKILL.md"
  printf 'extra-a\n' > "$CLAUDE/foreign-a/extra.txt"
  printf 'BBB\n' > "$CLAUDE/foreign-b/SKILL.md"
  printf 'nested\n' > "$CLAUDE/foreign-b/sub/nested.md"

  mkdir -p "$CODEX/foreign-c"
  printf 'CCC\n' > "$CODEX/foreign-c/SKILL.md"

  mkdir -p "$TRAE/foreign-d"
  printf 'DDD\n' > "$TRAE/foreign-d/SKILL.md"

  # Also pre-create a non-skill file in the target dir.
  printf 'stray\n' > "$CLAUDE/.notes.txt"
}

cleanup() { [[ -n "${TMP:-}" && -d "$TMP" ]] && rm -rf "$TMP"; }

# Pick three repo skills for assertions.
SKILL1="writing-commit"
SKILL2="zh-proofreading"
SKILL3="auditing-dead-code"

# ---------------------------------------------------------------- AC-1
echo "[case 1] default install: scope is only repo skills; all three targets installed"
new_env
snapshot "$TMP/before.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b" "$CODEX/foreign-c" "$TRAE/foreign-d"
notes_before="$(file_hash "$CLAUDE/.notes.txt")"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" >/dev/null 2>"$TMP/err1.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc (err: $(cat "$TMP/err1.log"))"

snapshot "$TMP/after.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b" "$CODEX/foreign-c" "$TRAE/foreign-d"
if diff -q "$TMP/before.foreign" "$TMP/after.foreign" >/dev/null; then
  ok "AC-1: third-party skills unchanged"
else
  bad "AC-1: third-party skills changed (diff: $(diff "$TMP/before.foreign" "$TMP/after.foreign"))"
fi

notes_after="$(file_hash "$CLAUDE/.notes.txt")"
[[ "$notes_before" == "$notes_after" ]] \
  && ok "AC-1b: stray file .notes.txt preserved" \
  || bad "AC-1b: .notes.txt mutated"

# Repo skills should now be installed in all three targets.
for d in "$CLAUDE" "$CODEX" "$TRAE"; do
  for s in "$SKILL1" "$SKILL2" "$SKILL3"; do
    if diff -rq "$d/$s" "$REPO_ROOT/skills/$s" >/dev/null 2>&1; then
      ok "installed $s into $(basename "$(dirname "$d")")"
    else
      bad "missing/mismatched $s in $d"
    fi
  done
done
cleanup

# ---------------------------------------------------------------- AC-2, AC-3
echo "[case 2] --backup: collision skill is moved to .bak, others untouched"
new_env
# Create a colliding skill with the same name as a repo skill.
mkdir -p "$CLAUDE/$SKILL1"
printf 'OLD-VERSION\n' > "$CLAUDE/$SKILL1/SKILL.md"
snapshot "$TMP/before.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --backup --claude-only "$SKILL1" >/dev/null 2>"$TMP/err2.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

# Backup dir should exist OUTSIDE of $CLAUDE.
bak_root="$TMP/claude/skills.bak"
bak_count=$(find "$bak_root" -mindepth 1 -maxdepth 1 -type d -name "$SKILL1-*" 2>/dev/null | wc -l | tr -d ' ')
[[ "$bak_count" == "1" ]] \
  && ok "AC-3: exactly one backup at $bak_root/$SKILL1-*" \
  || bad "AC-3: expected 1 backup, found $bak_count"

# Backup must hold the OLD content, not the new repo content.
bak_dir="$(find "$bak_root" -maxdepth 1 -type d -name "$SKILL1-*" | head -1)"
if grep -q "OLD-VERSION" "$bak_dir/SKILL.md" 2>/dev/null; then
  ok "AC-3: backup contains old version"
else
  bad "AC-3: backup missing or wrong content"
fi

# New content should match the repo.
diff -rq "$CLAUDE/$SKILL1" "$REPO_ROOT/skills/$SKILL1" >/dev/null \
  && ok "AC-2: collision skill overwritten with repo version" \
  || bad "AC-2: skill content mismatch"

# Foreign skills must still be byte-identical.
snapshot "$TMP/after.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b"
diff -q "$TMP/before.foreign" "$TMP/after.foreign" >/dev/null \
  && ok "AC-1 (under --backup): foreign skills unchanged" \
  || bad "AC-1 (under --backup): foreign skills changed"

# Skill list inside $CLAUDE should NOT contain any *.bak* directories.
stray_bak=$(find "$CLAUDE" -mindepth 1 -maxdepth 1 -name '*.bak*' 2>/dev/null | wc -l | tr -d ' ')
[[ "$stray_bak" == "0" ]] \
  && ok "AC-3: no backup pollution inside skills dir" \
  || bad "AC-3: found backup dir(s) inside $CLAUDE"
cleanup

# ---------------------------------------------------------------- AC-3b (trailing slash)
echo "[case 2b] trailing slash in CLAUDE_SKILLS_DIR still places backup OUTSIDE"
new_env
mkdir -p "$CLAUDE/$SKILL1"
printf 'OLD\n' > "$CLAUDE/$SKILL1/SKILL.md"

# Intentionally pass with trailing slash.
CLAUDE_SKILLS_DIR="$CLAUDE/" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --backup --claude-only "$SKILL1" >/dev/null 2>"$TMP/err2b.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0 with trailing slash" || bad "exit $rc"

# Hidden ".bak" directory inside $CLAUDE would be a regression.
if [[ -e "$CLAUDE/.bak" ]]; then
  bad "AC-3 (slash): backup landed INSIDE skills dir at $CLAUDE/.bak"
else
  ok "AC-3 (slash): no .bak inside skills dir"
fi
# The proper sibling location must exist.
[[ -d "$TMP/claude/skills.bak" ]] \
  && ok "AC-3 (slash): backup sibling dir exists" \
  || bad "AC-3 (slash): expected $TMP/claude/skills.bak to exist"
cleanup

# ---------------------------------------------------------------- AC-4
echo "[case 3] --dry-run: zero filesystem changes"
new_env
snapshot "$TMP/before.all" "$CLAUDE" "$CODEX" "$TRAE"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --dry-run >/dev/null 2>"$TMP/err3.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

snapshot "$TMP/after.all" "$CLAUDE" "$CODEX" "$TRAE"
diff -q "$TMP/before.all" "$TMP/after.all" >/dev/null \
  && ok "AC-4: dry-run made no changes" \
  || bad "AC-4: dry-run modified files: $(diff "$TMP/before.all" "$TMP/after.all")"

[[ ! -e "$TMP/claude/skills.bak" && ! -e "$TMP/codex/skills.bak" && ! -e "$TMP/trae/skills.bak" ]] \
  && ok "AC-4: no backup roots created" \
  || bad "AC-4: dry-run created a backup root"
cleanup

# ---------------------------------------------------------------- AC-5
echo "[case 4] nonexistent skill name → error, no changes"
new_env
snapshot "$TMP/before.all" "$CLAUDE" "$CODEX" "$TRAE"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" does-not-exist >/dev/null 2>"$TMP/err4.log"
rc=$?
[[ $rc -ne 0 ]] && ok "AC-5: non-zero exit on bad skill name" \
  || bad "AC-5: should have failed but exited 0"

grep -q "skill not found" "$TMP/err4.log" \
  && ok "AC-5: clear error message" \
  || bad "AC-5: error message missing (got: $(cat "$TMP/err4.log"))"

snapshot "$TMP/after.all" "$CLAUDE" "$CODEX" "$TRAE"
diff -q "$TMP/before.all" "$TMP/after.all" >/dev/null \
  && ok "AC-5: no filesystem changes on error" \
  || bad "AC-5: error path mutated files"
cleanup

# ---------------------------------------------------------------- AC-6
echo "[case 5] fallback (no rsync) path is also scope-safe (INSTALL_NO_RSYNC=1)"
new_env
snapshot "$TMP/before.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b"

INSTALL_NO_RSYNC=1 CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --claude-only "$SKILL2" >/dev/null 2>"$TMP/err5.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0 in fallback path" || bad "exit $rc (err: $(cat "$TMP/err5.log"))"

snapshot "$TMP/after.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b"
diff -q "$TMP/before.foreign" "$TMP/after.foreign" >/dev/null \
  && ok "AC-6: fallback path leaves foreign skills untouched" \
  || bad "AC-6: fallback path mutated foreign skills"

diff -rq "$CLAUDE/$SKILL2" "$REPO_ROOT/skills/$SKILL2" >/dev/null \
  && ok "AC-6: fallback installed correctly" \
  || bad "AC-6: fallback install mismatch"
cleanup

# ---------------------------------------------------------------- AC-7
echo "[case 6] --claude-only does not touch codex or trae targets"
new_env
snapshot "$TMP/before.codex" "$CODEX"
snapshot "$TMP/before.trae"  "$TRAE"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --claude-only "$SKILL1" >/dev/null 2>"$TMP/err6.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

snapshot "$TMP/after.codex" "$CODEX"
snapshot "$TMP/after.trae"  "$TRAE"
diff -q "$TMP/before.codex" "$TMP/after.codex" >/dev/null \
  && ok "AC-7: codex target unchanged under --claude-only" \
  || bad "AC-7: codex target mutated"
diff -q "$TMP/before.trae" "$TMP/after.trae" >/dev/null \
  && ok "AC-7: trae target unchanged under --claude-only" \
  || bad "AC-7: trae target mutated"
cleanup

echo "[case 7] --codex-only does not touch claude or trae targets"
new_env
snapshot "$TMP/before.claude" "$CLAUDE"
snapshot "$TMP/before.trae"   "$TRAE"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --codex-only "$SKILL1" >/dev/null 2>"$TMP/err7.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

snapshot "$TMP/after.claude" "$CLAUDE"
snapshot "$TMP/after.trae"   "$TRAE"
diff -q "$TMP/before.claude" "$TMP/after.claude" >/dev/null \
  && ok "AC-7: claude target unchanged under --codex-only" \
  || bad "AC-7: claude target mutated"
diff -q "$TMP/before.trae" "$TMP/after.trae" >/dev/null \
  && ok "AC-7: trae target unchanged under --codex-only" \
  || bad "AC-7: trae target mutated"
cleanup

# ---------------------------------------------------------------- AC-7b (Trae scope)
echo "[case 7b] --trae-only installs to trae and does not touch claude or codex"
new_env
snapshot "$TMP/before.claude" "$CLAUDE"
snapshot "$TMP/before.codex"  "$CODEX"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --trae-only "$SKILL1" >/dev/null 2>"$TMP/err7b.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc (err: $(cat "$TMP/err7b.log"))"

snapshot "$TMP/after.claude" "$CLAUDE"
snapshot "$TMP/after.codex"  "$CODEX"
diff -q "$TMP/before.claude" "$TMP/after.claude" >/dev/null \
  && ok "AC-7b: claude target unchanged under --trae-only" \
  || bad "AC-7b: claude target mutated"
diff -q "$TMP/before.codex" "$TMP/after.codex" >/dev/null \
  && ok "AC-7b: codex target unchanged under --trae-only" \
  || bad "AC-7b: codex target mutated"
diff -rq "$TRAE/$SKILL1" "$REPO_ROOT/skills/$SKILL1" >/dev/null \
  && ok "AC-7b: skill installed into trae target" \
  || bad "AC-7b: skill missing/mismatched in trae"
cleanup

# ---------------------------------------------------------------- AC-7c (combined --*-only flags are additive)
echo "[case 7c] --claude-only --trae-only installs to both, skipping codex"
new_env
snapshot "$TMP/before.codex" "$CODEX"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --claude-only --trae-only "$SKILL1" >/dev/null 2>"$TMP/err7c.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc (err: $(cat "$TMP/err7c.log"))"

snapshot "$TMP/after.codex" "$CODEX"
diff -q "$TMP/before.codex" "$TMP/after.codex" >/dev/null \
  && ok "AC-7c: codex target unchanged under --claude-only --trae-only" \
  || bad "AC-7c: codex target mutated"
diff -rq "$CLAUDE/$SKILL1" "$REPO_ROOT/skills/$SKILL1" >/dev/null \
  && ok "AC-7c: skill installed into claude target" \
  || bad "AC-7c: skill missing/mismatched in claude"
diff -rq "$TRAE/$SKILL1" "$REPO_ROOT/skills/$SKILL1" >/dev/null \
  && ok "AC-7c: skill installed into trae target" \
  || bad "AC-7c: skill missing/mismatched in trae"
cleanup

# ---------------------------------------------------------------- AC-7d (Trae --backup goes to sibling)
echo "[case 7d] --backup on trae target places backups OUTSIDE trae skills dir"
new_env
mkdir -p "$TRAE/$SKILL1"
printf 'TRAE-OLD\n' > "$TRAE/$SKILL1/SKILL.md"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --backup --trae-only "$SKILL1" >/dev/null 2>"$TMP/err7d.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc (err: $(cat "$TMP/err7d.log"))"

trae_bak_root="$TMP/trae/skills.bak"
trae_bak_count=$(find "$trae_bak_root" -mindepth 1 -maxdepth 1 -type d -name "$SKILL1-*" 2>/dev/null | wc -l | tr -d ' ')
[[ "$trae_bak_count" == "1" ]] \
  && ok "AC-7d: trae backup at $trae_bak_root/$SKILL1-*" \
  || bad "AC-7d: expected 1 trae backup, found $trae_bak_count"

trae_bak_dir="$(find "$trae_bak_root" -maxdepth 1 -type d -name "$SKILL1-*" | head -1)"
grep -q "TRAE-OLD" "$trae_bak_dir/SKILL.md" 2>/dev/null \
  && ok "AC-7d: trae backup contains old version" \
  || bad "AC-7d: trae backup missing or wrong content"

# No backup pollution inside the trae skills dir itself.
stray_trae_bak=$(find "$TRAE" -mindepth 1 -maxdepth 1 -name '*.bak*' 2>/dev/null | wc -l | tr -d ' ')
[[ "$stray_trae_bak" == "0" ]] \
  && ok "AC-7d: no backup pollution inside trae skills dir" \
  || bad "AC-7d: found backup dir(s) inside $TRAE"
cleanup

# ---------------------------------------------------------------- AC-8
echo "[case 8] idempotent: two runs in a row converge"
new_env
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" >/dev/null 2>&1
snapshot "$TMP/run1" "$CLAUDE" "$CODEX" "$TRAE"
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" >/dev/null 2>&1
snapshot "$TMP/run2" "$CLAUDE" "$CODEX" "$TRAE"
diff -q "$TMP/run1" "$TMP/run2" >/dev/null \
  && ok "AC-8: idempotent" \
  || bad "AC-8: second run changed state: $(diff "$TMP/run1" "$TMP/run2" | head -20)"
cleanup

# ---------------------------------------------------------------- AC-9 (-- parsing)
echo "[case 9] '--' separator works without shift-count errors"
new_env
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --claude-only -- "$SKILL1" >"$TMP/out9.log" 2>"$TMP/err9.log"
rc=$?
[[ $rc -eq 0 ]] && ok "AC-9: -- separator: exit 0" \
  || bad "AC-9: -- separator: exit $rc (err: $(cat "$TMP/err9.log"))"
grep -q "shift count out of range" "$TMP/err9.log" \
  && bad "AC-9: leaked shift-count error" \
  || ok "AC-9: no shift-count error"
[[ -d "$CLAUDE/$SKILL1" ]] \
  && ok "AC-9: -- consumed and skill installed" \
  || bad "AC-9: skill not installed after --"

# Bare '--' with no following args must also be safe.
new_env
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" --claude-only --dry-run -- >/dev/null 2>"$TMP/err9b.log"
rc=$?
[[ $rc -eq 0 ]] && ok "AC-9b: bare '--' exit 0" \
  || bad "AC-9b: bare '--' exit $rc (err: $(cat "$TMP/err9b.log"))"
cleanup

# ---------------------------------------------------------------- run() safety
echo "[case 10] no-eval: skill name with shell metacharacters does not execute"
new_env
# Marker file: if any shell expansion fires, the command substitution would
# create this file. After running install.sh, the file must NOT exist.
canary="$TMP/canary"
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" TRAE_SKILLS_DIR="$TRAE" \
  "$INSTALL" "\$(touch $canary)" >/dev/null 2>"$TMP/err10.log"
rc=$?
[[ $rc -ne 0 ]] && ok "case10: tricky skill name rejected" \
  || bad "case10: tricky skill name accepted (no eval guard?)"
[[ ! -e "$canary" ]] \
  && ok "case10: no command substitution executed" \
  || bad "case10: skill name was eval'd — canary file created"
grep -q "skill not found" "$TMP/err10.log" \
  && ok "case10: clean 'skill not found' error" \
  || bad "case10: unexpected error: $(cat "$TMP/err10.log")"
cleanup

# -----------------------------------------------------------------
echo ""
echo "Summary: $pass passed, $fail failed"
if [[ $fail -gt 0 ]]; then
  printf '\nFailures:\n'
  for m in "${fail_msgs[@]}"; do printf '  - %s\n' "$m"; done
  exit 1
fi
exit 0
