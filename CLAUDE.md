# CLAUDE.md

## Project Overview

yousa-skills is a curated collection of Claude Code skills. Each skill is a self-contained directory under `skills/` with at minimum a `SKILL.md` file.

## Skill Contribution Standards

When adding or modifying skills in this repository, you **MUST** follow the `contribute-skill` workflow defined in `.claude/skills/contribute-skill/SKILL.md`. Key requirements:

### Skill Structure

- Each skill must be a directory under `skills/<skill-name>/`
- Directory name uses kebab-case, matching the `name` field in SKILL.md frontmatter
- Must contain a `SKILL.md` with valid YAML frontmatter (`name` and `description` fields)
- Optional subdirectories: `examples/`, `scripts/`, `references/`

### SKILL.md Format

```yaml
---
name: <skill-name>
description: <trigger conditions and what the skill does>
---
```

Followed by: overview, when-to-use/triggers, core workflow (step-by-step), examples, and common mistakes.

### README.md Updates

`README.md` and `README.zh-CN.md` are generated files and must not be hand-edited.

When adding or updating a skill:
1. Update `docs/readme/skills.json` for README-facing skill metadata
2. If page copy or structure changes, update the templates under `docs/readme/templates/`
3. Run `python3 scripts/render_readmes.py`
4. Verify both `README.md` and `README.zh-CN.md` were regenerated cleanly

### Git Workflow

- Use feature branches: `feat/add-<skill-name>`
- Conventional Commits format: `feat: add <skill-name> skill`
- Create PRs via `gh pr create`

### Quality Checklist

- [ ] SKILL.md has valid frontmatter with `name` and `description`
- [ ] Description clearly states trigger conditions
- [ ] Workflow steps are sequential and explicit
- [ ] Common mistakes / edge cases documented
- [ ] `docs/readme/skills.json` updated for the skill
- [ ] `README.md` regenerated from source
- [ ] `README.zh-CN.md` regenerated from source
- [ ] No placeholder or TODO-only files committed
