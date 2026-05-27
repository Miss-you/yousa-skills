#!/usr/bin/env bash
# Install skills from this repo into personal Claude / Codex skill dirs.
# Default: overwrite existing skills. Use --backup to keep the old copy.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/skills"

CLAUDE_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"

install_claude=1
install_codex=1
do_backup=0
dry_run=0
do_list=0
selected=()

usage() {
  cat <<EOF
Usage: $(basename "$0") [options] [skill-name ...]

Install skills from $SRC_DIR into personal skill directories.
With no skill names, installs every skill under skills/.

Targets (default: both):
  --claude-only        Install to \$CLAUDE_SKILLS_DIR (default: ~/.claude/skills)
  --codex-only         Install to \$CODEX_SKILLS_DIR  (default: ~/.codex/skills)

Behavior:
  --backup             Move existing <skill>/ to <target>.bak/<skill>-<timestamp>/
                       before overwriting. Default is plain overwrite.
                       Backups live OUTSIDE the skills dir so the host (Claude/
                       Codex) doesn't load them as duplicate skills.
  --dry-run            Print planned actions without changing anything.
  --list               List skills available in this repo and exit.
  -h, --help           Show this help.

Env overrides:
  CLAUDE_SKILLS_DIR    Override Claude target directory.
  CODEX_SKILLS_DIR     Override Codex target directory.
EOF
}

log()  { printf '%s\n' "$*"; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --claude-only) install_codex=0 ;;
    --codex-only)  install_claude=0 ;;
    --backup)      do_backup=1 ;;
    --dry-run)     dry_run=1 ;;
    --list)        do_list=1 ;;
    -h|--help)     usage; exit 0 ;;
    --) shift; while [[ $# -gt 0 ]]; do selected+=("$1"); shift; done ;;
    -*) die "unknown option: $1 (try --help)" ;;
    *)  selected+=("$1") ;;
  esac
  shift
done

[[ -d "$SRC_DIR" ]] || die "skills source not found: $SRC_DIR"

# Collect available skills (any subdir of skills/ containing SKILL.md).
available=()
while IFS= read -r -d '' skill_md; do
  skill_dir="$(dirname "$skill_md")"
  available+=("$(basename "$skill_dir")")
done < <(find "$SRC_DIR" -mindepth 2 -maxdepth 2 -type f -name SKILL.md -print0)

IFS=$'\n' available=($(printf '%s\n' "${available[@]}" | sort)); unset IFS

if [[ $do_list -eq 1 ]]; then
  printf '%s\n' "${available[@]}"
  exit 0
fi

# Resolve which skills to install.
if [[ ${#selected[@]} -eq 0 ]]; then
  to_install=("${available[@]}")
else
  to_install=()
  for name in "${selected[@]}"; do
    found=0
    for a in "${available[@]}"; do
      [[ "$a" == "$name" ]] && { found=1; break; }
    done
    [[ $found -eq 1 ]] || die "skill not found in repo: $name"
    to_install+=("$name")
  done
fi

[[ ${#to_install[@]} -gt 0 ]] || die "no skills to install"

targets=()
[[ $install_claude -eq 1 ]] && targets+=("$CLAUDE_DIR")
[[ $install_codex  -eq 1 ]] && targets+=("$CODEX_DIR")
[[ ${#targets[@]} -gt 0 ]] || die "no install targets selected"

have_rsync=0
command -v rsync >/dev/null 2>&1 && have_rsync=1

run() {
  if [[ $dry_run -eq 1 ]]; then
    printf '  + %s\n' "$*"
  else
    eval "$@"
  fi
}

copy_skill() {
  local src="$1" dst="$2"
  if [[ $have_rsync -eq 1 ]]; then
    run "rsync -a --delete -- \"$src/\" \"$dst/\""
  else
    run "rm -rf -- \"$dst\""
    run "cp -R -- \"$src\" \"$dst\""
  fi
}

ts="$(date +%Y%m%d-%H%M%S)"
installed=0
upgraded=0
backed_up=0

log "source : $SRC_DIR"
for t in "${targets[@]}"; do log "target : $t"; done
log "skills : ${#to_install[@]} ($([[ ${#selected[@]} -eq 0 ]] && echo all || echo selected))"
[[ $dry_run -eq 1 ]] && log "mode   : dry-run (no changes)"
log ""

for target in "${targets[@]}"; do
  if [[ ! -d "$target" ]]; then
    log "creating target dir: $target"
    run "mkdir -p -- \"$target\""
  fi

  for name in "${to_install[@]}"; do
    src="$SRC_DIR/$name"
    dst="$target/$name"
    action="install"
    if [[ -e "$dst" ]]; then
      action="upgrade"
      if [[ $do_backup -eq 1 ]]; then
        backup_root="${target}.bak"
        backup="$backup_root/$name-$ts"
        log "backup : $dst -> $backup"
        run "mkdir -p -- \"$backup_root\""
        run "mv -- \"$dst\" \"$backup\""
        backed_up=$((backed_up + 1))
      fi
    fi
    log "$action: $name -> $target"
    copy_skill "$src" "$dst"
    if [[ "$action" == "upgrade" ]]; then
      upgraded=$((upgraded + 1))
    else
      installed=$((installed + 1))
    fi
  done
done

log ""
log "done. installed=$installed upgraded=$upgraded backed_up=$backed_up"
if [[ $dry_run -eq 1 ]]; then
  log "(dry-run: nothing was written)"
fi
exit 0
