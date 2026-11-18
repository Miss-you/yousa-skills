from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def manifest_path(root: Path) -> Path:
    return root / "docs" / "readme" / "skills.json"


def template_path(root: Path, language: str) -> Path:
    return root / "docs" / "readme" / "templates" / f"README.{language}.md.tmpl"


def output_path(root: Path, language: str) -> Path:
    return root / ("README.md" if language == "en" else "README.zh-CN.md")


def usage_path(root: Path) -> Path:
    return root / "docs" / "readme" / "usage.json"


def load_usage(repo_root: Path | None = None) -> dict:
    """Usage stats from scripts/skill_usage_stats.py; empty when not generated yet."""
    path = usage_path(repo_root or Path.cwd())
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_manifest(repo_root: Path | None = None) -> list[dict]:
    root = repo_root or Path.cwd()
    with manifest_path(root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _scan_skill_dirs(root: Path) -> dict[str, Path]:
    skills_root = root / "skills"
    discovered: dict[str, Path] = {}
    if not skills_root.exists():
        return discovered
    for skill_dir in sorted(skills_root.iterdir(), key=lambda path: path.name):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
            discovered[f"skills/{skill_dir.name}"] = skill_dir
    return discovered


def validate_manifest(manifest: list[dict], repo_root: Path | None = None) -> None:
    root = repo_root or Path.cwd()
    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a list of skill entries.")

    required_keys = {"name", "path", "description_en", "description_zh"}
    seen_names: set[str] = set()
    seen_paths: set[str] = set()

    for entry in manifest:
        if not isinstance(entry, dict):
            raise ValueError("Each manifest entry must be an object.")
        missing = required_keys - entry.keys()
        if missing:
            raise ValueError(f"Manifest entry {entry!r} is missing required keys: {sorted(missing)}")

        name = entry["name"]
        path = entry["path"]
        if name in seen_names:
            raise ValueError(f"Duplicate skill name: {name}")
        if path in seen_paths:
            raise ValueError(f"Duplicate skill path: {path}")

        seen_names.add(name)
        seen_paths.add(path)

    for entry in manifest:
        skill_md = root / entry["path"] / "SKILL.md"
        if not skill_md.is_file():
            raise ValueError(f"Manifest path does not point to a skill directory with SKILL.md: {entry['path']}")

    discovered = set(_scan_skill_dirs(root))
    if discovered != seen_paths:
        missing = sorted(discovered - seen_paths)
        extra = sorted(seen_paths - discovered)
        details = []
        if missing:
            details.append(f"missing from manifest: {missing}")
        if extra:
            details.append(f"not found in repo: {extra}")
        raise ValueError("Manifest does not match repository skill directories: " + "; ".join(details))


def _language_switcher(language: str) -> str:
    if language == "en":
        return "[English](README.md) | [简体中文](README.zh-CN.md)"
    return "[English](README.md) | [简体中文](README.zh-CN.md)"


def _skill_source_path(entry: dict) -> str:
    return entry["path"].rstrip("/")


_STATUS_LABELS = {
    "en": {"active": "🟢 active", "low": "🟡 low", "inactive": "⚪ inactive"},
    "zh-CN": {"active": "🟢 活跃", "low": "🟡 低频", "inactive": "⚪ 未使用"},
}


def _format_activity(language: str, stats: dict | None) -> str:
    if not stats:
        return "—"
    count = stats["recent_3m"]
    label = _STATUS_LABELS[language].get(stats["status"], stats["status"])
    if language == "en":
        return f"{count} in 3 mo / {label}"
    return f"近3月 {count} 次 / {label}"


def _format_usage_note(language: str, usage: dict) -> str:
    window = usage.get("window", {}).get("recent_3m")
    if not window:
        if language == "en":
            return "Activity has not been generated yet; see `scripts/skill_usage_stats.py`."
        return "活跃度数据尚未生成，见 `scripts/skill_usage_stats.py`。"
    as_of = usage.get("generated_at", "")
    if language == "en":
        return (
            f"Activity counts the maintainer's own uses in local Claude Code and Codex sessions, "
            f"{window} (as of {as_of}): 5+ uses is active, 1–4 is low, 0 is inactive, "
            "and — means no data yet. Older logs are incomplete, so 0 means no recorded use, "
            "not proof of no use. Refresh monthly with `scripts/skill_usage_stats.py`."
        )
    return (
        f"活跃度统计的是维护者本人在本地 Claude Code 和 Codex 会话里的使用次数，"
        f"区间 {window.replace(' to ', ' 至 ')}（截至 {as_of}）：≥5 次为活跃，1–4 次为低频，0 次为未使用，— 表示暂无数据。"
        "更早的日志不完整，0 次只说明没有留下记录，不代表从未用过。每月用 `scripts/skill_usage_stats.py` 刷新一次。"
    )


def _format_skill_rows(language: str, manifest: list[dict], usage: dict | None = None) -> str:
    lines = []
    desc_key = "description_en" if language == "en" else "description_zh"
    usage_skills = (usage or {}).get("skills", {})
    for entry in manifest:
        skill_dir = _skill_source_path(entry).rsplit("/", 1)[-1]
        activity = _format_activity(language, usage_skills.get(skill_dir))
        lines.append(f"| [{entry['name']}]({_skill_source_path(entry)}/) | {entry[desc_key]} | {activity} |")
    return "\n".join(lines)


def render_readme(
    language: str, manifest: list[dict], repo_root: Path | None = None, usage: dict | None = None
) -> str:
    root = repo_root or Path.cwd()
    usage_data = usage if usage is not None else load_usage(root)
    template = template_path(root, language).read_text(encoding="utf-8")
    rendered = template
    rendered = rendered.replace("{{language_switcher}}", _language_switcher(language))
    rendered = rendered.replace("{{skills_table}}", _format_skill_rows(language, manifest, usage_data))
    rendered = rendered.replace("{{usage_note}}", _format_usage_note(language, usage_data))
    return rendered.rstrip() + "\n"


def render_readmes(repo_root: Path | None = None, manifest: list[dict] | None = None) -> dict[str, str]:
    root = repo_root or Path.cwd()
    manifest_data = manifest if manifest is not None else load_manifest(root)
    validate_manifest(manifest_data, root)
    return {
        "README.md": render_readme("en", manifest_data, root),
        "README.zh-CN.md": render_readme("zh-CN", manifest_data, root),
    }


def write_readmes(repo_root: Path | None = None, manifest: list[dict] | None = None) -> None:
    root = repo_root or Path.cwd()
    outputs = render_readmes(root, manifest)
    for filename, content in outputs.items():
        output_path(root, "en" if filename == "README.md" else "zh-CN").write_text(content, encoding="utf-8")


def _check_outputs(root: Path, outputs: dict[str, str]) -> list[str]:
    stale = []
    for filename, expected in outputs.items():
        path = root / filename
        if not path.exists():
            stale.append(filename)
            continue
        if path.read_text(encoding="utf-8") != expected:
            stale.append(filename)
    return stale


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render bilingual README files from a shared manifest.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if generated output is stale.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = repo_root()

    if args.check:
        outputs = render_readmes(root)
        stale = _check_outputs(root, outputs)
        if stale:
            print("Stale README output:", ", ".join(stale))
            return 1
        return 0

    write_readmes(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
