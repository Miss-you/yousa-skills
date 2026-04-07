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


def _format_skill_rows(language: str, manifest: list[dict]) -> str:
    lines = []
    desc_key = "description_en" if language == "en" else "description_zh"
    for entry in manifest:
        lines.append(f"| [{entry['name']}](skills/{entry['name']}/) | {entry[desc_key]} |")
    return "\n".join(lines)


def _format_installation_examples(language: str, manifest: list[dict]) -> str:
    prefix = "Install each skill with one copy command:" if language == "en" else "使用一条复制命令安装每个 skill："
    lines = [prefix, "", "```bash"]
    for entry in manifest:
        lines.append(f"cp -r yousa-skills/skills/{entry['name']} ~/.claude/skills/{entry['name']}")
    lines.append("```")
    return "\n".join(lines)


def _skill_names(manifest: list[dict]) -> str:
    return " ".join(entry["name"] for entry in manifest)


def render_readme(language: str, manifest: list[dict], repo_root: Path | None = None) -> str:
    root = repo_root or Path.cwd()
    template = template_path(root, language).read_text(encoding="utf-8")
    rendered = template
    rendered = rendered.replace("{{language_switcher}}", _language_switcher(language))
    rendered = rendered.replace("{{skills_table}}", _format_skill_rows(language, manifest))
    rendered = rendered.replace("{{installation_examples}}", _format_installation_examples(language, manifest))
    rendered = rendered.replace("{{skill_names}}", _skill_names(manifest))
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
