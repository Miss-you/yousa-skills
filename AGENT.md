# AGENT.md

## Repository Rules

This repository uses generated bilingual README files.

- `README.md` is the default English landing page.
- `README.zh-CN.md` is the peer Chinese landing page.
- Do not hand-edit either generated file.

## Skill Contribution Workflow

When adding or updating a skill:

1. Update the skill content under `skills/<skill-name>/`
2. Update `docs/readme/skills.json`
3. If page copy or structure changes, update the templates under `docs/readme/templates/`
4. Run `python3 scripts/render_readmes.py`
5. Verify both README outputs regenerated cleanly

## Expectations

- Keep descriptions consistent across the two README files.
- Treat `docs/readme/skills.json` as the source of truth for README-facing skill metadata.
- Treat `docs/readme/templates/` as the source of truth for README copy and structure.
- Prefer small, mechanical updates over manual edits to generated files.
