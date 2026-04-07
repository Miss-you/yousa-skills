# yousa-skills

A curated collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for enhancing AI-assisted workflows.

[English](README.md) | [简体中文](README.zh-CN.md)

## Skills

| Skill | Description |
|-------|-------------|
| [explaining-completed-work](skills/explaining-completed-work/) | Explain finished work with a Feynman-style walkthrough covering what changed, how it works, why it was chosen, and where the boundaries are. |
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux for parallel batch task processing, with work-stealing scheduling and built-in quality gates. |
| [social-strategist](skills/social-strategist/) | Analyze dialogue and chat screenshots for subtext, emotion, power dynamics, and reply strategies. |
| [structural-integrity-scan](skills/structural-integrity-scan/) | Scan comparison-style articles for uneven comparisons, hidden asymmetry, and narrative-driven conclusions. |
| [two-mirror-examples](skills/two-mirror-examples/) | Find persuasive examples for a thesis using distant and near mirrors that share the same underlying mechanism. |
| [cdp-page-to-md](skills/cdp-page-to-md/) | Fetch authenticated or JavaScript-rendered web pages via Chrome CDP and convert them into clean Markdown. |
| [zh-proofreading](skills/zh-proofreading/) | Scan Chinese prose for typos, grammar issues, punctuation problems, and mixed Chinese-Latin formatting issues. |
| [secret-scan](skills/secret-scan/) | Scan staged or changed files for leaked secrets before commit, push, or PR creation. |
| [pr-review-autofix](skills/pr-review-autofix/) | Watch open PRs for AI code review comments and auto-fix them from local cron. |

## Installation

Copy a skill directory into your local Claude Code skills folder:

```bash
git clone https://github.com/Miss-you/yousa-skills.git
skill_paths=(skills/explaining-completed-work skills/tmux-dispatch skills/social-strategist skills/structural-integrity-scan skills/two-mirror-examples skills/cdp-page-to-md skills/zh-proofreading skills/secret-scan skills/pr-review-autofix)
for skill_path in "${skill_paths[@]}"; do
  skill_dir="${skill_path##*/}"
  cp -r "yousa-skills/${skill_path}" ~/.claude/skills/"${skill_dir}"
done
```

Install each skill with one copy command:

```bash
cp -r yousa-skills/skills/explaining-completed-work ~/.claude/skills/explaining-completed-work
cp -r yousa-skills/skills/tmux-dispatch ~/.claude/skills/tmux-dispatch
cp -r yousa-skills/skills/social-strategist ~/.claude/skills/social-strategist
cp -r yousa-skills/skills/structural-integrity-scan ~/.claude/skills/structural-integrity-scan
cp -r yousa-skills/skills/two-mirror-examples ~/.claude/skills/two-mirror-examples
cp -r yousa-skills/skills/cdp-page-to-md ~/.claude/skills/cdp-page-to-md
cp -r yousa-skills/skills/zh-proofreading ~/.claude/skills/zh-proofreading
cp -r yousa-skills/skills/secret-scan ~/.claude/skills/secret-scan
cp -r yousa-skills/skills/pr-review-autofix ~/.claude/skills/pr-review-autofix
```

## Maintenance

To update these pages, edit `docs/readme/skills.json` for skill metadata or the templates in `docs/readme/templates/`, then rerun `python3 scripts/render_readmes.py`.
