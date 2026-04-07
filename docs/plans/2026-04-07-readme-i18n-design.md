# README I18n Maintenance Design

## Background

The repository currently uses a single root `README.md` that mixes English and Chinese descriptions. This creates two problems:

1. GitHub's default landing page is not language-consistent.
2. README maintenance is tied to manual edits, so adding a skill risks drift and inconsistent formatting.

The target state is:

- `README.md` remains the default English landing page.
- `README.zh-CN.md` becomes a first-class Chinese landing page.
- Both pages stay structurally aligned and are regenerated from shared source data.

## Goals

- Keep two top-level README entry pages with parallel structure.
- Make English the default GitHub landing page.
- Remove mixed-language skill descriptions from generated README output.
- Define a single, explicit maintenance workflow for future skill additions.
- Update repository agent instructions so contributors follow the new workflow.

## Non-Goals

- Translating every `SKILL.md` into both languages.
- Building a general-purpose i18n framework for the whole repository.
- Introducing external dependencies or a documentation site generator.

## Proposed Architecture

### Output Files

- `README.md`: generated English landing page
- `README.zh-CN.md`: generated Chinese landing page

### Source Files

- `docs/readme/skills.json`: canonical metadata for README skill entries
- `docs/readme/templates/README.en.md.tmpl`: English README template
- `docs/readme/templates/README.zh-CN.md.tmpl`: Chinese README template

### Generator

- `scripts/render_readmes.py`

The generator reads the skill metadata manifest, builds the skills table and installation example block, injects them into both templates, and writes the two top-level README files. It also provides a `--check` mode that fails if generated output is stale.

## Content Model

Each skill entry in `docs/readme/skills.json` stores:

- `name`
- `path`
- `description_en`
- `description_zh`

This keeps README-facing descriptions bilingual without forcing `SKILL.md` frontmatter to become a documentation source of truth for both languages.

Shared README structure stays fixed across both templates:

- Title and short project intro
- Language switcher
- Skills table
- Installation
- Maintenance notes

## Maintenance Workflow

When a skill is added or updated:

1. Update `skills/<skill-name>/`
2. Add or update the corresponding entry in `docs/readme/skills.json`
3. Run `python3 scripts/render_readmes.py`
4. Verify `README.md` and `README.zh-CN.md` are regenerated cleanly

Repository guidance files must reflect the same workflow:

- `CLAUDE.md`
- `AGENT.md`
- `.claude/skills/contribute-skill/SKILL.md`

## Error Handling

The generator should fail fast when:

- a manifest entry is missing required fields
- duplicate skill names are present
- a skill path in the manifest does not exist
- generated output differs in `--check` mode

## Testing Strategy

Add lightweight Python unit tests for the generator:

- render output includes bilingual descriptions
- installation examples are generated from manifest entries
- manifest validation rejects duplicates or missing paths

Final verification should use:

- `python3 -m unittest`
- `python3 scripts/render_readmes.py --check`

## Why This Approach

This keeps the landing-page experience close to the `superpowers` model: a clean root README and details split out when needed. At the same time, it avoids the main failure mode of manual bilingual maintenance by moving volatile README content into a single structured source and generated outputs.
