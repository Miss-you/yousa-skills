#!/usr/bin/env bash
# Acceptance checks for the python-3am-debuggable heuristic scanner.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCAN="$REPO_ROOT/skills/python-3am-debuggable/scripts/scan.py"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cat > "$TMP/sample.py" <<'PY'
from __future__ import annotations

import asyncio
import dataclasses
import functools
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

send_metric_func = send_metric


def load_user(path: str) -> dict[str, Any] | None:
    try:
        return read_user(path)
    except Exception:
        logger.exception("failed to load user")
        return None


def write_audit(user_id: str) -> None:
    asyncio.create_task(send_audit(user_id))


def run_later(build_payload: Callable[[], dict[str, Any]]) -> None:
    asyncio.create_task(send_payload(build_payload()))


async def schedule_reports(rows: list[dict[str, Any]]) -> None:
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)

        async def report() -> None:
            await send_payload({"rows": batch})

        asyncio.create_task(report())


def remember(user_id: str, cache=[]) -> list[str]:
    cache.append(user_id)
    return cache


def dispatch(kind: str, payload: dict[str, Any]) -> Any:
    return globals()[kind](payload)


class WebhookRouter:
    def dispatch(self, kind: str, payload: dict[str, Any]) -> Any:
        handler = getattr(self, f"handle_{kind}")
        return handler(payload)


def normalize_user(user: dict[str, Any]) -> dict[str, Any]:
    user["email"] = user["email"].strip().lower()
    user.setdefault("roles", []).append("member")
    return user


def wrapper_for_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return build_payload(payload)


def audit_decorator(func):
    def wrapper(*args, **kwargs):
        logger.info("calling %s", func.__name__)
        return func(*args, **kwargs)

    return wrapper


class UserManager:
    def parse(self, raw: str) -> dict[str, Any]:
        return {"raw": raw}

    def validate(self, data: dict[str, Any]) -> bool:
        return bool(data)

    def save(self, data: dict[str, Any]) -> None:
        write_file("/tmp/users.json", data)

    def notify(self, user_id: str) -> None:
        send_metric_func(user_id)


async def allowed_task_group(users: list[str]) -> None:
    async with asyncio.TaskGroup() as tg:
        for user in users:
            tg.create_task(send_audit(user))


def allowed_sorted(items: list[object]) -> list[object]:
    return sorted(items, key=lambda item: item.score)


@dataclasses.dataclass
class AllowedState:
    items: list[str] = dataclasses.field(default_factory=list)


def allowed_error(path: str) -> User:
    try:
        return read_user(path)
    except FileNotFoundError as exc:
        raise DomainError(path) from exc


def collapse_error_cause(path: str) -> User:
    try:
        return read_user(path)
    except FileNotFoundError as exc:
        raise DomainError(path) from None


def allowed_metadata_decorator(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped
PY

output="$(python3 "$SCAN" "$TMP")"

assert_contains() {
  local needle="$1"
  if [[ "$output" != *"$needle"* ]]; then
    printf 'expected scanner output to contain %q\n\noutput:\n%s\n' "$needle" "$output" >&2
    exit 1
  fi
}

assert_not_contains() {
  local needle="$1"
  if [[ "$output" == *"$needle"* ]]; then
    printf 'expected scanner output not to contain %q\n\noutput:\n%s\n' "$needle" "$output" >&2
    exit 1
  fi
}

assert_contains "A. Silent/collapsed failure paths"
assert_contains "except Exception"
assert_contains "B. Hidden async/background boundaries"
assert_contains "asyncio.create_task"
assert_contains "C. Callback/lambda inversion across lifecycle boundary"
assert_contains "build_payload"
assert_contains "D. Mutable shared state and late-bound capture"
assert_contains "cache=[]"
assert_contains "send_payload({\"rows\": batch})"
assert_contains "E. Test-only seams / fake call indirection"
assert_contains "send_metric_func"
assert_contains "F. Dynamic dispatch hiding real callable"
assert_contains "globals()[kind]"
assert_contains "getattr(self, f\"handle_{kind}\")"
assert_contains "G. Opaque public contracts"
assert_contains "dict[str, Any]"
assert_contains "H. Local closure/lambda chains"
assert_contains "wrapper"
assert_contains "I. Single-caller wrappers and generic abstractions"
assert_contains "UserManager"
assert_contains "K. Hidden side effects/config checkpoints"
assert_contains "write_file(\"/tmp/users.json\", data)"
assert_contains "user[\"email\"] = user[\"email\"].strip().lower()"
assert_contains "raise DomainError(path) from None"
assert_contains "Summary"

assert_not_contains "TaskGroup"
assert_not_contains "key=lambda"
assert_not_contains "default_factory=list"
assert_not_contains "DomainError(path) from exc"
assert_not_contains "def wrapped"

python3 - <<'PY' "$REPO_ROOT"
from pathlib import Path
import json
import sys

root = Path(sys.argv[1])
skill = root / "skills" / "python-3am-debuggable" / "SKILL.md"
text = skill.read_text(encoding="utf-8")
assert text.startswith("---\n"), "missing frontmatter"
end = text.find("\n---\n", 4)
assert end != -1, "frontmatter not closed"
keys = []
for line in text[4:end].splitlines():
    if line.startswith("  "):
        continue
    if ":" in line:
        keys.append(line.split(":", 1)[0].strip())
assert keys == ["name", "description"], keys
assert "name: python-3am-debuggable" in text[4:end]

manifest = json.loads((root / "docs" / "readme" / "skills.json").read_text(encoding="utf-8"))
assert any(
    entry["name"] == "python-3am-debuggable"
    and entry["path"] == "skills/python-3am-debuggable"
    for entry in manifest
), "manifest entry missing"
PY

printf 'python-3am scan acceptance checks passed\n'
