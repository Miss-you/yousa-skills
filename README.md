# yousa-skills

A curated collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for enhancing AI-assisted workflows.

[English](README.md) | [简体中文](README.zh-CN.md)

## Skills

| Skill | Description | Activity |
|-------|-------------|----------|
| [explaining-completed-work](skills/explaining-completed-work/) | Explain finished work with a Feynman-style walkthrough covering what changed, how it works, why it was chosen, and where the boundaries are. | 10 in 3 mo / 🟢 active |
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux for parallel batch task processing, with work-stealing scheduling and built-in quality gates. | 0 in 3 mo / ⚪ inactive |
| [social-strategist](skills/social-strategist/) | Analyze dialogue and chat screenshots for subtext, emotion, power dynamics, and reply strategies. | 10 in 3 mo / 🟢 active |
| [structural-integrity-scan](skills/structural-integrity-scan/) | Scan comparison-style articles for uneven comparisons, hidden asymmetry, and narrative-driven conclusions. | 6 in 3 mo / 🟢 active |
| [two-mirror-examples](skills/two-mirror-examples/) | Find persuasive examples for a thesis using distant and near mirrors that share the same underlying mechanism. | 3 in 3 mo / 🟡 low |
| [cdp-page-to-md](skills/cdp-page-to-md/) | Fetch authenticated or JavaScript-rendered web pages via Chrome CDP and convert them into clean Markdown. | 1 in 3 mo / 🟡 low |
| [zh-proofreading](skills/zh-proofreading/) | Scan Chinese prose for typos, grammar issues, punctuation problems, and mixed Chinese-Latin formatting issues. | 0 in 3 mo / ⚪ inactive |
| [secret-scan](skills/secret-scan/) | Scan staged or changed files for leaked secrets before commit, push, or PR creation. | 185 in 3 mo / 🟢 active |
| [pr-review-autofix](skills/pr-review-autofix/) | Watch open PRs for AI code review comments and auto-fix them from local cron. | 1 in 3 mo / 🟡 low |
| [monitoring-pr-ai-reviews](skills/monitoring-pr-ai-reviews/) | Use when implementation is already complete, a GitHub PR exists or must be opened, and follow-up work is still needed because Copilot or other AI review comments may arrive after the initial push. | 7 in 3 mo / 🟢 active |
| [writing-commit](skills/writing-commit/) | Create local git commits by deriving scope and message from repository evidence, with secret scanning and verification gates. | 10 in 3 mo / 🟢 active |
| [writing-contextual-todos](skills/writing-contextual-todos/) | Write TODO docs as handoff artifacts with full context, acceptance criteria, and source attribution so future readers understand without chat history. | 15 in 3 mo / 🟢 active |
| [creating-sourcecode-learning-sops](skills/creating-sourcecode-learning-sops/) | Create verified, multi-phase Study Operating Procedures for systematically learning a codebase feature, combining learning science with hands-on code verification. | 0 in 3 mo / ⚪ inactive |
| [checking-upstream-before-work](skills/checking-upstream-before-work/) | Check upstream for overlapping open PRs and recent merges before starting implementation, bugfix, refactor, or investigation work. | 122 in 3 mo / 🟢 active |
| [designing-state-machines](skills/designing-state-machines/) | Design and review lifecycle state machines for durable status fields, async workflows, retries, terminal states, concurrency, and observability. | 0 in 3 mo / ⚪ inactive |
| [writing-open-source-prs](skills/writing-open-source-prs/) | Draft, review, and update open source pull request descriptions so maintainers get issue context, behavior changes, tests, tradeoffs, and CI status without reading the diff first. | 2 in 3 mo / 🟡 low |
| [judging-compounding-value](skills/judging-compounding-value/) | Judge whether an activity, skill, project, workflow, or career choice has compounding value or is mostly one-off consumption, using a six-dimension framework. | 4 in 3 mo / 🟡 low |
| [auditing-dead-code](skills/auditing-dead-code/) | Audit dead code by reconciling static analysis, reference classification, and entrypoint/API risk before declaring symbols safe to remove, especially around RPC, config, generated code, and exported APIs. | 76 in 3 mo / 🟢 active |
| [go-3am-debuggable](skills/go-3am-debuggable/) | Review or write Go code with a 3AM debuggability lens, focusing on readable panic stacks, visible async ownership, mock-only seams, callback inversion, closure chains, and low-value indirection. | 109 in 3 mo / 🟢 active |
| [python-3am-debuggable](skills/python-3am-debuggable/) | Review or write Python code with a 3AM debuggability lens, focusing on tracebacks, async/background ownership, exception semantics, side effects, mutable state capture, dynamic dispatch, and low-value indirection. | 0 in 3 mo / ⚪ inactive |
| [research-question-framing](skills/research-question-framing/) | Turn a fuzzy research topic into an evidence-seeking brief — question tree, evidence matrix with proof/non-proof, and validation scenarios — before any source-code study, investigation, or architecture inquiry begins. | 8 in 3 mo / 🟢 active |
| [transcript-to-deep-minutes](skills/transcript-to-deep-minutes/) | Turn speaker-tagged meeting and roundtable transcripts into structured deep minutes by extracting judgments, mindsets, and cases through a multi-agent pipeline. | 5 in 3 mo / 🟢 active |
| [minutes-sensitive-scan](skills/minutes-sensitive-scan/) | Scan and redact meeting minutes for sensitive identities, personnel signals, and traceable fingerprints before external release under the Chatham House Rule. | 13 in 3 mo / 🟢 active |
| [youtube-video-analysis](skills/youtube-video-analysis/) | Run a four-step deep analysis on a YouTube video: pull subtitles, structure the summary, cross-check claims online, and output a reasonable/unreasonable/insight report. | 3 in 3 mo / 🟡 low |
| [research-to-knowledge-note](skills/research-to-knowledge-note/) | Restructure finished research plus web evidence into a long-term archivable Chinese knowledge note with provenance, evidence table, methodology, reproduction steps, and AC self-check. | 0 in 3 mo / ⚪ inactive |
| [claim-verification](skills/claim-verification/) | Audit a claim, video, article, or analysis for truthfulness: decompose arguments, cross-check key data online, surface the strongest opposition, and output an 8-dimension red/yellow/green diagnostic with a final objective verdict. | 23 in 3 mo / 🟢 active |
| [narrative-truth-audit](skills/narrative-truth-audit/) | Stress-test financial, macro, geopolitical, or business narratives across fact, structure, and causal layers, with cross-country and historical counterexamples and a final go/no-go verdict. | 10 in 3 mo / 🟢 active |
| [deep-research-verifier](skills/deep-research-verifier/) | Answer complex multi-source questions with a structured research-answer-verify framework: deconstruct the question and design an SOP, gather evidence by dimension, cross-check facts and logic, then output a verified answer with an evidence-tracking table. | 26 in 3 mo / 🟢 active |
| [minutes-quality-eval](skills/minutes-quality-eval/) | Evaluate and compare meeting-minutes quality against the original transcript: fidelity spot-checks with risk-prioritized sampling, coverage inventory, distortion-pattern scan, and weighted multi-dimension scoring. | 7 in 3 mo / 🟢 active |
| [improving-english-prompts](skills/improving-english-prompts/) | Correct rough English prompts into clear workplace English and create short practice quizzes from the user's mistakes. | 0 in 3 mo / ⚪ inactive |
| [eacc-chat-daily-distill](skills/eacc-chat-daily-distill/) | Distill a day of investment group chat into a sourced, sender-weighted Markdown note focused on decision-relevant methodology, judgments, and know-how, with mandatory acceptance checks. | 218 in 3 mo / 🟢 active |
| [kospi-mobile-web-design](skills/kospi-mobile-web-design/) | Design KOSPI Monitor phone pages and shareable reports with readable metrics, touch controls, and responsive layouts. | 0 in 3 mo / ⚪ inactive |
| [kospi-desktop-dashboard-design](skills/kospi-desktop-dashboard-design/) | Design KOSPI Monitor desktop dashboards and reports with clear information hierarchy, charts, and precise values. | 0 in 3 mo / ⚪ inactive |
| [prepare-audio-library](skills/prepare-audio-library/) | Organize long audio, videos, and OST collections into playable tracks, verify track identities and cut points, and add user-provided covers and evidence-backed music tags. | 5 in 3 mo / 🟢 active |
| [triaging-github-ai-reviews](skills/triaging-github-ai-reviews/) | Assess AI review feedback on open-source GitHub PRs using correctness, necessity, complexity reduction, and long-term maintainability before selective fixes and authorized merging. | 0 in 3 mo / ⚪ inactive |
| [safe-rebase-push](skills/safe-rebase-push/) | Safely rebase and push after a rejected push by checking file overlap with remote commits first and verifying that no remote change was lost. | 164 in 3 mo / 🟢 active |
| [overengineering-audit](skills/overengineering-audit/) | Run a subtractive review of a finished change against its goal, cutting speculative abstractions, unused knobs, and impossible edge-case handling. | 126 in 3 mo / 🟢 active |
| [auditing-change-scope](skills/auditing-change-scope/) | Audit a change or plan before commit or handover, classifying each hunk as in-scope, needs-decision, or hand-off to catch scope creep and drive-by edits. | 85 in 3 mo / 🟢 active |
| [multi-agent-staged-acceptance](skills/multi-agent-staged-acceptance/) | Review spec or working-tree changes with independent agents that infer scope from Git evidence and report severity-ordered findings with file:line proof. | 53 in 3 mo / 🟢 active |
| [deriving-solution-scope](skills/deriving-solution-scope/) | Turn a problem, goal, incident, or vague direction into candidate work items, decision principles, and a second-pass recommended scope. | 18 in 3 mo / 🟢 active |
| [writing-conclusion-first-briefs](skills/writing-conclusion-first-briefs/) | Write durable Markdown research briefs, retrospectives, and decision memos that put the answer first, followed by evidence, limits, and next checks. | 15 in 3 mo / 🟢 active |
| [go-service-risk-review](skills/go-service-risk-review/) | Run a lightweight production-risk review of a finished Go backend change across observability, compatibility, performance, isolation, and concurrency. | 40 in 3 mo / 🟢 active |
| [smart-commit](skills/smart-commit/) | Generate a structured commit message from the staged diff and an optional design doc, with an optional ticket reference that follows the repo's own convention, then commit after confirmation. | 237 in 3 mo / 🟢 active |
| [spec-to-techdoc](skills/spec-to-techdoc/) | Generate a technical design doc from change specs (e.g. OpenSpec) plus the actual code, serving both client developers (API docs) and backend developers (decisions, tests, config, todos). | 16 in 3 mo / 🟢 active |
| [tech-validation-doc](skills/tech-validation-doc/) | Turn research notes, validation results, and confirmed conclusions into a maintainable technical validation doc covering decisions, known constraints, and phased todos. | 50 in 3 mo / 🟢 active |
| [writing-tech-doc](skills/writing-tech-doc/) | Write Chinese backend technical docs in three passes: content draft, structure assets checked by a bundled lint script, then a style pass that removes AI-sounding prose. | 15 in 3 mo / 🟢 active |
| [auditing-code-comments](skills/auditing-code-comments/) | Run a subtraction-only review of comments on a finished change: delete or shrink comments that restate code, replay design debates, duplicate tests, or reference missing symbols, keeping only the ones that prevent intuitive-but-wrong edits. | 86 in 3 mo / 🟢 active |
| [polishing-go-readability](skills/polishing-go-readability/) | Lower the reading cost of a finished, reviewed Go diff right before commit with a few behavior-preserving readability edits, deferring bugs and performance to a separate list. | 53 in 3 mo / 🟢 active |
| [aligning-new-interface-fields](skills/aligning-new-interface-fields/) | Before implementing a new or changed interface, reconcile RPC names, route aliases, req/rsp messages, and field names/types against existing protos so new fields follow the conventions already in use. | 26 in 3 mo / 🟢 active |
| [constraint-first-proposal](skills/constraint-first-proposal/) | Before proposing a technical approach, pin down four decisive constraints (reversibility, project phase, blast radius, which hat) so the proposal isn't reworked round after round. | 23 in 3 mo / 🟢 active |
| [config-switch-review](skills/config-switch-review/) | Review new runtime config and feature switches from the operator's point of view: build the realistic switch-combination table, predict behavior from key names alone, then diff against the code to catch hidden mutual exclusion, fully-on defaults, misleading names, and unrollbackable switches. | 19 in 3 mo / 🟢 active |

Activity counts the maintainer's own uses in local Claude Code and Codex sessions, 2026-09 to 2026-11 (as of 2026-11-18): 5+ uses is active, 1–4 is low, 0 is inactive, and — means no data yet. Older logs are incomplete, so 0 means no recorded use, not proof of no use. Refresh monthly with `scripts/skill_usage_stats.py`.

## Installation

Clone the repo and run the installer for your shell. It syncs every skill under `skills/` into your personal Claude, Codex, and Trae skill directories (`~/.claude/skills`, `~/.codex/skills`, and `~/.trae-cn/skills`).

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

```powershell
git clone https://github.com/Miss-you/yousa-skills.git
cd yousa-skills
.\install.ps1                                  # install all skills to Claude, Codex, and Trae
.\install.ps1 writing-commit zh-proofreading   # install only the named skills
.\install.ps1 --claude-only                    # only ~/.claude/skills
.\install.ps1 --codex-only                     # only ~/.codex/skills
.\install.ps1 --trae-only                      # only ~/.trae-cn/skills
.\install.ps1 --claude-only --trae-only        # combine --*-only flags to install to a subset
.\install.ps1 --backup                         # before overwriting, move the old skill to <target>.bak/
.\install.ps1 --dry-run                        # print planned actions without changing anything
.\install.ps1 --list                           # list installable skills
```

Re-run `./install.sh` or `.\install.ps1` to upgrade. The installer only touches skill directories whose names appear under this repo's `skills/`: skills with **other names** are left alone, and skills with the **same name** are overwritten — pass `--backup` to keep the old copy first.

Override target directories with `CLAUDE_SKILLS_DIR`, `CODEX_SKILLS_DIR`, or `TRAE_SKILLS_DIR` if your installation lives somewhere else.

## Maintenance

To update these pages, edit `docs/readme/skills.json` for skill metadata or the templates in `docs/readme/templates/`, then rerun `python3 scripts/render_readmes.py`. To refresh the Activity column, first run `python3 scripts/skill_usage_stats.py --emit-repo-usage docs/readme/usage.json` (monthly is enough).
