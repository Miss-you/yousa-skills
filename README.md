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
| [designing-state-machines](skills/designing-state-machines/) | Design and review lifecycle state machines for durable status fields, async workflows, retries, terminal states, concurrency, and observability. |
| [writing-open-source-prs](skills/writing-open-source-prs/) | Draft, review, and update open source pull request descriptions so maintainers get issue context, behavior changes, tests, tradeoffs, and CI status without reading the diff first. |
| [judging-compounding-value](skills/judging-compounding-value/) | Judge whether an activity, skill, project, workflow, or career choice has compounding value or is mostly one-off consumption, using a six-dimension framework. |
| [auditing-dead-code](skills/auditing-dead-code/) | Audit dead code by reconciling static analysis, reference classification, and entrypoint/API risk before declaring symbols safe to remove, especially around RPC, config, generated code, and exported APIs. |
| [go-3am-debuggable](skills/go-3am-debuggable/) | Review or write Go code with a 3AM debuggability lens, focusing on readable panic stacks, visible async ownership, mock-only seams, callback inversion, closure chains, and low-value indirection. |
| [python-3am-debuggable](skills/python-3am-debuggable/) | Review or write Python code with a 3AM debuggability lens, focusing on tracebacks, async/background ownership, exception semantics, side effects, mutable state capture, dynamic dispatch, and low-value indirection. |
| [research-question-framing](skills/research-question-framing/) | Turn a fuzzy research topic into an evidence-seeking brief — question tree, evidence matrix with proof/non-proof, and validation scenarios — before any source-code study, investigation, or architecture inquiry begins. |
| [transcript-to-deep-minutes](skills/transcript-to-deep-minutes/) | Turn speaker-tagged meeting and roundtable transcripts into structured deep minutes by extracting judgments, mindsets, and cases through a multi-agent pipeline. |
| [minutes-sensitive-scan](skills/minutes-sensitive-scan/) | Scan and redact meeting minutes for sensitive identities, personnel signals, and traceable fingerprints before external release under the Chatham House Rule. |
| [youtube-video-analysis](skills/youtube-video-analysis/) | Run a four-step deep analysis on a YouTube video: pull subtitles, structure the summary, cross-check claims online, and output a reasonable/unreasonable/insight report. |
| [research-to-knowledge-note](skills/research-to-knowledge-note/) | Restructure finished research plus web evidence into a long-term archivable Chinese knowledge note with provenance, evidence table, methodology, reproduction steps, and AC self-check. |
| [claim-verification](skills/claim-verification/) | Audit a claim, video, article, or analysis for truthfulness: decompose arguments, cross-check key data online, surface the strongest opposition, and output an 8-dimension red/yellow/green diagnostic with a final objective verdict. |
| [narrative-truth-audit](skills/narrative-truth-audit/) | Stress-test financial, macro, geopolitical, or business narratives across fact, structure, and causal layers, with cross-country and historical counterexamples and a final go/no-go verdict. |
| [deep-research-verifier](skills/deep-research-verifier/) | Answer complex multi-source questions with a structured research-answer-verify framework: deconstruct the question and design an SOP, gather evidence by dimension, cross-check facts and logic, then output a verified answer with an evidence-tracking table. |
| [minutes-quality-eval](skills/minutes-quality-eval/) | Evaluate and compare meeting-minutes quality against the original transcript: fidelity spot-checks with risk-prioritized sampling, coverage inventory, distortion-pattern scan, and weighted multi-dimension scoring. |
| [improving-english-prompts](skills/improving-english-prompts/) | Correct rough English prompts into clear workplace English and create short practice quizzes from the user's mistakes. |
| [eacc-chat-daily-distill](skills/eacc-chat-daily-distill/) | Distill a day of investment group chat into a sourced, sender-weighted Markdown note focused on decision-relevant methodology, judgments, and know-how, with mandatory acceptance checks. |

## Installation

Clone the repo and run `./install.sh`. It syncs every skill under `skills/` into your personal Claude, Codex, and Trae skill directories (`~/.claude/skills`, `~/.codex/skills`, and `~/.trae-cn/skills`).

```bash
git clone https://github.com/Miss-you/yousa-skills.git
cd yousa-skills
./install.sh                                  # install all skills to Claude, Codex, and Trae
./install.sh writing-commit zh-proofreading   # install only the named skills
./install.sh --claude-only                    # only ~/.claude/skills
./install.sh --codex-only                     # only ~/.codex/skills
./install.sh --trae-only                      # only ~/.trae-cn/skills
./install.sh --claude-only --trae-only        # combine --*-only flags to install to a subset
./install.sh --backup                         # before overwriting, move the old skill to <target>.bak/
./install.sh --dry-run                        # print planned actions without changing anything
./install.sh --list                           # list installable skills
```

Re-run `./install.sh` to upgrade. The script only touches skill directories whose names appear under this repo's `skills/`: skills with **other names** are left alone, and skills with the **same name** are overwritten — pass `--backup` to keep the old copy first.

Override target directories with `CLAUDE_SKILLS_DIR`, `CODEX_SKILLS_DIR`, or `TRAE_SKILLS_DIR` if your installation lives somewhere else.

## Maintenance

To update these pages, edit `docs/readme/skills.json` for skill metadata or the templates in `docs/readme/templates/`, then rerun `python3 scripts/render_readmes.py`.
