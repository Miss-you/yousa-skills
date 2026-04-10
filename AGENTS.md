# AGENTS.md

## Scope

- Maintain `yousa-skills` as a curated repository of reusable skills.
- Keep repository guidance short and durable. Put task-specific detail in PRs or `docs/plans/` if the repo later adds that structure.
- Preserve skill portability across published `skills/` entries and project-level `.claude/.codex` mirrors.

## Source Of Truth

- Repository overview and contribution rules: `CLAUDE.md`
- Skill contribution workflow: `.claude/skills/contribute-skill/SKILL.md`
- Project-level Codex mirror of the workflow: `.codex/skills/contribute-skill/SKILL.md`
- If docs and repo state disagree, trust the checked-in files and update the stale docs in the same change.

## Skill Rules

- Each published skill lives in `skills/<skill-name>/`.
- The directory name, frontmatter `name`, and install path must match and stay kebab-case.
- `SKILL.md` frontmatter supports only `name` and `description`.
- `description` must explain when to use the skill, not summarize the workflow.
- Keep frontmatter YAML-safe. Prefer quotes or `>-` for long descriptions or text containing `: `.
- Optional support material belongs in `examples/`, `scripts/`, or `references/`.

## Repository Workflow

- When adding or changing a skill, follow the `contribute-skill` workflow.
- Keep `.claude/skills/` and `.codex/skills/` mirrors in sync when the project relies on those local copies.
- Update `README.md` whenever a published skill is added or its public description changes.
- Do not commit placeholder-only files or half-copied skill directories.

## Verification

- Parse every changed `SKILL.md` frontmatter before commit.
- Run targeted checks for any changed automation, such as scripts or GitHub workflows.
- Before opening a PR, make sure published skills, project-level mirrors, and repo automation still agree.
