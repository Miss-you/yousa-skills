#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

# Keep the repo-level entrypoint stable for workflows and tests while the
# canonical implementation lives with the skill it belongs to.
_CANONICAL_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "monitoring-pr-ai-reviews"
    / "scripts"
    / "pr_ai_review_monitor.py"
)

if not _CANONICAL_SCRIPT.is_file():
    raise FileNotFoundError(f"Missing canonical monitor script: {_CANONICAL_SCRIPT}")

_namespace = globals()
_original_name = __name__
_original_file = __file__

try:
    _namespace["__file__"] = str(_CANONICAL_SCRIPT)
    _namespace["__name__"] = "_pr_ai_review_monitor_impl"
    exec(
        compile(_CANONICAL_SCRIPT.read_text(encoding="utf-8"), str(_CANONICAL_SCRIPT), "exec"),
        _namespace,
        _namespace,
    )
finally:
    _namespace["__file__"] = _original_file
    _namespace["__name__"] = _original_name

del _namespace
del _original_name
del _original_file


if __name__ == "__main__":
    raise SystemExit(main())
