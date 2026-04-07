import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import render_readmes as renderer
from scripts.render_readmes import (
    load_manifest,
    render_readme,
    render_readmes,
    validate_manifest,
)


def _copy_templates(repo_root: Path) -> None:
    source_root = Path(__file__).resolve().parents[1]
    template_dir = repo_root / "docs" / "readme" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("README.en.md.tmpl", "README.zh-CN.md.tmpl"):
        (template_dir / filename).write_text(
            (source_root / "docs" / "readme" / "templates" / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


class RenderReadmesTest(unittest.TestCase):
    def test_validate_manifest_rejects_duplicate_skill_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            skills_dir = repo_root / "skills"
            skills_dir.mkdir()
            for name in ("alpha", "alpha-duplicate"):
                skill_dir = skills_dir / name
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text("---\nname: %s\ndescription: test\n---\n" % name)

            manifest = [
                {
                    "name": "alpha",
                    "path": "skills/alpha",
                    "description_en": "Alpha skill.",
                    "description_zh": "Alpha 技能。",
                },
                {
                    "name": "alpha",
                    "path": "skills/alpha-duplicate",
                    "description_en": "Duplicate alpha skill.",
                    "description_zh": "重复的 Alpha 技能。",
                },
            ]

            with self.assertRaisesRegex(ValueError, "Duplicate skill name"):
                validate_manifest(manifest, repo_root=repo_root)

    def test_validate_manifest_rejects_missing_skill_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            skills_dir = repo_root / "skills"
            skills_dir.mkdir()
            skill_dir = skills_dir / "alpha"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: alpha\ndescription: test\n---\n")

            manifest = [
                {
                    "name": "alpha",
                    "path": "skills/missing",
                    "description_en": "Alpha skill.",
                    "description_zh": "Alpha 技能。",
                }
            ]

            with self.assertRaisesRegex(ValueError, "Manifest path does not point"):
                validate_manifest(manifest, repo_root=repo_root)

    def test_validate_manifest_rejects_skill_dirs_missing_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            skills_dir = repo_root / "skills"
            skills_dir.mkdir()
            for name in ("alpha", "beta"):
                skill_dir = skills_dir / name
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n")

            manifest = [
                {
                    "name": "alpha",
                    "path": "skills/alpha",
                    "description_en": "Alpha skill.",
                    "description_zh": "Alpha 技能。",
                }
            ]

            with self.assertRaisesRegex(ValueError, "missing from manifest"):
                validate_manifest(manifest, repo_root=repo_root)

    def test_render_readme_uses_language_specific_descriptions(self):
        manifest = [
            {
                "name": "example",
                "path": "skills/example",
                "description_en": "Example skill in English.",
                "description_zh": "示例技能的中文说明。",
            }
        ]

        english = render_readme(
            language="en",
            manifest=manifest,
            repo_root=Path("."),
        )
        chinese = render_readme(
            language="zh-CN",
            manifest=manifest,
            repo_root=Path("."),
        )

        self.assertIn("Example skill in English.", english)
        self.assertNotIn("示例技能的中文说明。", english)
        self.assertIn("## 技能", chinese)
        self.assertIn("示例技能的中文说明。", chinese)
        self.assertNotIn("Example skill in English.", chinese)

    def test_render_readme_uses_manifest_path_for_links_and_install_commands(self):
        manifest = [
            {
                "name": "display-name",
                "path": "skills/real-skill-dir",
                "description_en": "Example skill in English.",
                "description_zh": "示例技能的中文说明。",
            }
        ]

        english = render_readme(
            language="en",
            manifest=manifest,
            repo_root=Path("."),
        )

        self.assertIn("[display-name](skills/real-skill-dir/)", english)
        self.assertIn(
            "cp -r yousa-skills/skills/real-skill-dir ~/.claude/skills/real-skill-dir",
            english,
        )
        self.assertNotIn("cp -r yousa-skills/skills/display-name", english)

    def test_render_readmes_includes_every_skill_in_installation_examples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _copy_templates(repo_root)
            skills_dir = repo_root / "skills"
            skills_dir.mkdir()
            for name in ("alpha", "beta"):
                skill_dir = skills_dir / name
                skill_dir.mkdir()
                (skill_dir / "SKILL.md").write_text("---\nname: %s\ndescription: test\n---\n" % name)

            manifest = [
                {
                    "name": "alpha",
                    "path": "skills/alpha",
                    "description_en": "Alpha skill.",
                    "description_zh": "Alpha 技能。",
                },
                {
                    "name": "beta",
                    "path": "skills/beta",
                    "description_en": "Beta skill.",
                    "description_zh": "Beta 技能。",
                },
            ]
            manifest_path = repo_root / "docs" / "readme" / "skills.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

            outputs = render_readmes(repo_root=repo_root, manifest=manifest)

            self.assertIn("alpha", outputs["README.md"])
            self.assertIn("beta", outputs["README.md"])
            self.assertIn("alpha", outputs["README.zh-CN.md"])
            self.assertIn("beta", outputs["README.zh-CN.md"])

    def test_check_mode_reports_stale_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _copy_templates(repo_root)
            docs_dir = repo_root / "docs" / "readme"
            skills_dir = repo_root / "skills"
            skills_dir.mkdir()
            skill_dir = skills_dir / "alpha"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: alpha\ndescription: test\n---\n")
            (docs_dir / "skills.json").write_text(
                json.dumps(
                    [
                        {
                            "name": "alpha",
                            "path": "skills/alpha",
                            "description_en": "Alpha skill.",
                            "description_zh": "Alpha 技能。",
                        }
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )

            manifest = load_manifest(repo_root=repo_root)
            outputs = render_readmes(repo_root=repo_root, manifest=manifest)

            (repo_root / "README.md").write_text("stale english")
            (repo_root / "README.zh-CN.md").write_text("stale chinese")

            original_repo_root = renderer.repo_root
            try:
                renderer.repo_root = lambda: repo_root
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(renderer.main(["--check"]), 1)
            finally:
                renderer.repo_root = original_repo_root


if __name__ == "__main__":
    unittest.main()
