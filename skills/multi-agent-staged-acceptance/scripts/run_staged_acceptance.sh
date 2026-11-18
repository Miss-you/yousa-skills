#!/usr/bin/env bash
set -euo pipefail
for arg in "$@"; do
  if [ "$arg" = "--run-tests" ]; then
    echo 'Automatic test execution was removed: select repository-specific commands and test the declared target state. See SKILL.md.' >&2
    exit 2
  fi
done
skill_script_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$skill_script_dir/collect_review_scope.py" "$@"
