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

When adding a skill, update `README.md`:
1. Add a row to the Skills table: `| [<name>](skills/<name>/) | <description> |`
2. Add an installation example in the Installation section

### Git Workflow

- Use feature branches: `feat/add-<skill-name>`
- Conventional Commits format: `feat: add <skill-name> skill`
- Create PRs via `gh pr create`

### Quality Checklist

- [ ] SKILL.md has valid frontmatter with `name` and `description`
- [ ] Description clearly states trigger conditions
- [ ] Workflow steps are sequential and explicit
- [ ] Common mistakes / edge cases documented
- [ ] README.md skills table updated
- [ ] README.md installation example updated
- [ ] No placeholder or TODO-only files committed
