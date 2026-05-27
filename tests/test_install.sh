#!/usr/bin/env bash
# Acceptance tests for install.sh.
# Uses CLAUDE_SKILLS_DIR / CODEX_SKILLS_DIR env overrides to run against
# a temporary scratch directory — never touches the user's real ~/.claude
# or ~/.codex.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL="$REPO_ROOT/install.sh"

pass=0
fail=0
fail_msgs=()

ok()   { pass=$((pass+1)); printf '  PASS %s\n' "$*"; }
bad()  { fail=$((fail+1)); fail_msgs+=("$*"); printf '  FAIL %s\n' "$*"; }

snapshot() {
  # Stable hash of (path + content) for every file under given dirs.
  # Used to detect any modification.
  local out="$1"; shift
  : > "$out"
  for d in "$@"; do
    [[ -e "$d" ]] || continue
    ( cd "$d" && find . -type f -print0 | sort -z | xargs -0 shasum ) >> "$out"
  done
}

new_env() {
  TMP="$(mktemp -d)"
  CLAUDE="$TMP/claude/skills"
  CODEX="$TMP/codex/skills"
  mkdir -p "$CLAUDE" "$CODEX"

  # Pre-populate with "third-party" skills (not in this repo).
  mkdir -p "$CLAUDE/foreign-a" "$CLAUDE/foreign-b/sub"
  printf 'AAA\n' > "$CLAUDE/foreign-a/SKILL.md"
  printf 'extra-a\n' > "$CLAUDE/foreign-a/extra.txt"
  printf 'BBB\n' > "$CLAUDE/foreign-b/SKILL.md"
  printf 'nested\n' > "$CLAUDE/foreign-b/sub/nested.md"

  mkdir -p "$CODEX/foreign-c"
  printf 'CCC\n' > "$CODEX/foreign-c/SKILL.md"

  # Also pre-create a non-skill file in the target dir.
  printf 'stray\n' > "$CLAUDE/.notes.txt"
}

cleanup() { [[ -n "${TMP:-}" && -d "$TMP" ]] && rm -rf "$TMP"; }

# Pick three repo skills for assertions.
SKILL1="writing-commit"
SKILL2="zh-proofreading"
SKILL3="auditing-dead-code"

# ---------------------------------------------------------------- AC-1, AC-7
echo "[case 1] default install: scope is only repo skills; both targets installed"
new_env
snapshot "$TMP/before.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b" "$CODEX/foreign-c"
foreign_meta_before="$(stat -f '%N %m %z' "$CLAUDE/.notes.txt")"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" >/dev/null 2>"$TMP/err1.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc (err: $(cat "$TMP/err1.log"))"

snapshot "$TMP/after.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b" "$CODEX/foreign-c"
if diff -q "$TMP/before.foreign" "$TMP/after.foreign" >/dev/null; then
  ok "AC-1: third-party skills unchanged"
else
  bad "AC-1: third-party skills changed (diff: $(diff "$TMP/before.foreign" "$TMP/after.foreign"))"
fi

foreign_meta_after="$(stat -f '%N %m %z' "$CLAUDE/.notes.txt")"
[[ "$foreign_meta_before" == "$foreign_meta_after" ]] \
  && ok "AC-1b: stray file .notes.txt preserved" \
  || bad "AC-1b: .notes.txt mutated ($foreign_meta_before -> $foreign_meta_after)"

# Repo skills should now be installed in both targets.
for d in "$CLAUDE" "$CODEX"; do
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

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
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

# ---------------------------------------------------------------- AC-4
echo "[case 3] --dry-run: zero filesystem changes"
new_env
snapshot "$TMP/before.all" "$CLAUDE" "$CODEX"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" --dry-run >/dev/null 2>"$TMP/err3.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

snapshot "$TMP/after.all" "$CLAUDE" "$CODEX"
diff -q "$TMP/before.all" "$TMP/after.all" >/dev/null \
  && ok "AC-4: dry-run made no changes" \
  || bad "AC-4: dry-run modified files: $(diff "$TMP/before.all" "$TMP/after.all")"

# No new dirs/files should have appeared anywhere under $TMP.
extra=$(find "$TMP" -mindepth 1 -newer "$INSTALL" 2>/dev/null | wc -l | tr -d ' ')
# Hard to assert with --newer; instead make sure no .bak roots were created.
[[ ! -e "$TMP/claude/skills.bak" && ! -e "$TMP/codex/skills.bak" ]] \
  && ok "AC-4: no backup roots created" \
  || bad "AC-4: dry-run created a backup root"
cleanup

# ---------------------------------------------------------------- AC-5
echo "[case 4] nonexistent skill name → error, no changes"
new_env
snapshot "$TMP/before.all" "$CLAUDE" "$CODEX"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" does-not-exist >/dev/null 2>"$TMP/err4.log"
rc=$?
[[ $rc -ne 0 ]] && ok "AC-5: non-zero exit on bad skill name" \
  || bad "AC-5: should have failed but exited 0"

grep -q "skill not found" "$TMP/err4.log" \
  && ok "AC-5: clear error message" \
  || bad "AC-5: error message missing (got: $(cat "$TMP/err4.log"))"

snapshot "$TMP/after.all" "$CLAUDE" "$CODEX"
diff -q "$TMP/before.all" "$TMP/after.all" >/dev/null \
  && ok "AC-5: no filesystem changes on error" \
  || bad "AC-5: error path mutated files"
cleanup

# ---------------------------------------------------------------- AC-6
echo "[case 5] fallback (no rsync) path is also scope-safe"
new_env
snapshot "$TMP/before.foreign" "$CLAUDE/foreign-a" "$CLAUDE/foreign-b"

# Force fallback by hiding rsync from PATH.
NORSYNC_BIN="$TMP/nopath"
mkdir -p "$NORSYNC_BIN"
# Build a minimal PATH that excludes rsync.
PATH_WITHOUT_RSYNC="$NORSYNC_BIN:/usr/bin:/bin"
command -v rsync >/dev/null && rsync_was="yes" || rsync_was="no"

PATH="$PATH_WITHOUT_RSYNC" CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
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
echo "[case 6] --claude-only does not touch codex target"
new_env
snapshot "$TMP/before.codex" "$CODEX"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" --claude-only "$SKILL1" >/dev/null 2>"$TMP/err6.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

snapshot "$TMP/after.codex" "$CODEX"
diff -q "$TMP/before.codex" "$TMP/after.codex" >/dev/null \
  && ok "AC-7: codex target unchanged under --claude-only" \
  || bad "AC-7: codex target mutated"
cleanup

echo "[case 7] --codex-only does not touch claude target"
new_env
snapshot "$TMP/before.claude" "$CLAUDE"

CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" --codex-only "$SKILL1" >/dev/null 2>"$TMP/err7.log"
rc=$?
[[ $rc -eq 0 ]] && ok "exit 0" || bad "exit $rc"

snapshot "$TMP/after.claude" "$CLAUDE"
diff -q "$TMP/before.claude" "$TMP/after.claude" >/dev/null \
  && ok "AC-7: claude target unchanged under --codex-only" \
  || bad "AC-7: claude target mutated"
cleanup

# ---------------------------------------------------------------- AC-8
echo "[case 8] idempotent: two runs in a row converge"
new_env
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" >/dev/null 2>&1
snapshot "$TMP/run1" "$CLAUDE" "$CODEX"
CLAUDE_SKILLS_DIR="$CLAUDE" CODEX_SKILLS_DIR="$CODEX" \
  "$INSTALL" >/dev/null 2>&1
snapshot "$TMP/run2" "$CLAUDE" "$CODEX"
diff -q "$TMP/run1" "$TMP/run2" >/dev/null \
  && ok "AC-8: idempotent" \
  || bad "AC-8: second run changed state: $(diff "$TMP/run1" "$TMP/run2" | head -20)"
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
