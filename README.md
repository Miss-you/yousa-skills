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
| [monitoring-pr-ai-reviews](skills/monitoring-pr-ai-reviews/) | Use when implementation is already complete, a GitHub PR exists or must be opened, and follow-up work is still needed because Copilot or other AI review comments may arrive after the initial push. |
| [writing-commit](skills/writing-commit/) | Create local git commits by deriving scope and message from repository evidence, with secret scanning and verification gates. |
| [writing-contextual-todos](skills/writing-contextual-todos/) | Write TODO docs as handoff artifacts with full context, acceptance criteria, and source attribution so future readers understand without chat history. |
| [creating-sourcecode-learning-sops](skills/creating-sourcecode-learning-sops/) | Create verified, multi-phase Study Operating Procedures for systematically learning a codebase feature, combining learning science with hands-on code verification. |
| [checking-upstream-before-work](skills/checking-upstream-before-work/) | Check upstream for overlapping open PRs and recent merges before starting implementation, bugfix, refactor, or investigation work. |
| [writing-open-source-prs](skills/writing-open-source-prs/) | Draft, review, and update open source pull request descriptions so maintainers get issue context, behavior changes, tests, tradeoffs, and CI status without reading the diff first. |
| [judging-compounding-value](skills/judging-compounding-value/) | Judge whether an activity, skill, project, workflow, or career choice has compounding value or is mostly one-off consumption, using a six-dimension framework. |
| [auditing-dead-code](skills/auditing-dead-code/) | Audit dead code by reconciling static analysis, reference classification, and entrypoint/API risk before declaring symbols safe to remove, especially around RPC, config, generated code, and exported APIs. |
| [research-question-framing](skills/research-question-framing/) | Turn a fuzzy research topic into an evidence-seeking brief — question tree, evidence matrix with proof/non-proof, and validation scenarios — before any source-code study, investigation, or architecture inquiry begins. |

## Installation

Clone the repo and run `./install.sh`. It syncs every skill under `skills/` into your personal Claude and Codex skill directories (`~/.claude/skills` and `~/.codex/skills`).

```bash
git clone https://github.com/Miss-you/yousa-skills.git
cd yousa-skills
./install.sh                                  # install all skills to both Claude and Codex
./install.sh writing-commit zh-proofreading   # install only the named skills
./install.sh --claude-only                    # only ~/.claude/skills
./install.sh --codex-only                     # only ~/.codex/skills
./install.sh --backup                         # before overwriting, move the old skill to <target>.bak/
./install.sh --dry-run                        # print planned actions without changing anything
./install.sh --list                           # list installable skills
```

Re-run `./install.sh` to upgrade. The script only touches skill directories it owns — skills installed from other sources are never modified.

## Maintenance

To update these pages, edit `docs/readme/skills.json` for skill metadata or the templates in `docs/readme/templates/`, then rerun `python3 scripts/render_readmes.py`.
