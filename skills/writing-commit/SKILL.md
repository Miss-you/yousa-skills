---
name: writing-commit
description: Use when creating local git commits in codetok from existing changes, especially when scope, staging, verification, or message clarity could drift.
---

# Writing Commit

## Overview

Create local commits without story IDs, supplied summaries, or confirmation prompts. Derive scope and message from inspected repository evidence.

**Core principle:** no-input means no missing description input; it does not mean guessing, sweeping unrelated files, or skipping verification.

**REQUIRED SUB-SKILL:** Use `secret-scan` before `git commit`.

## Use And Stop

Use when the user asks to commit current codetok changes or write a commit message without a description. Do not amend, rebase, push, tag, or rewrite history.

Stop instead of asking for a description when there are no changes, mixed scope, failed or unavailable verification after final scope selection, a secret leak, or uninspected files.

## Procedure

Inventory before staging:

```bash
git status --short
git diff --cached --name-status
git diff --name-status
git ls-files --others --exclude-standard
```

Select one coherent scope:

- Existing staged files are likely intent; inspect unstaged edits required for the same logical change.
- If nothing is staged, stage only clearly related files.
- Inspect untracked candidates before staging.
- Never run `git add .` or `git add -A`; stage inspected pathspecs only.
- Stop if unrelated user work is mixed in.

Analyze message evidence:

```bash
git diff --cached --stat
git diff --cached
git diff --stat
git diff
```

For untracked files, read content or listings before staging. Describe behavior or docs contract first, implementation and tests second.

Verify after the final intended scope is known:

| Scope | Required |
| --- | --- |
| Docs-only | inspect diff; no Go test gate unless generated docs or examples changed |
| Go code or CLI behavior | narrow relevant test first, then `make test` |
| Formatting-sensitive Go | `make fmt` before tests |
| Build/release wiring | add `make build`, `make vet`, or workflow smoke as relevant |

Earlier checks count only if run after the final selected diff with no later relevant edits; name the command in the final response. Failed checks block unless explicitly unrelated.

Use recent `git log --format=%s -20` style: mostly Conventional Commit subjects, occasional `[codex]`.

```text
<type>: <specific result>

- <what changed and why it matters>
- <important implementation or test detail>
```

Avoid `update docs`, `misc fixes`, and filename-only messages. Run `secret-scan`, commit with a message file or quoted heredoc, then show `git log -1 --stat`.

## Acceptance Criteria

- Inventory: inspected `git status --short`; considered staged, unstaged, and untracked changes separately.
- Scope: no `git add .`, no `git add -A`, and no uninspected untracked file.
- Message and checks: actual behavior/docs change described; verification fresh after final scope selection; failed checks blocked unless unrelated.
- Safety/reporting: `secret-scan` before `git commit`; final response reports hash, files, verification, and intentionally uncommitted files.

## Common Mistakes

Red flags: adding everything, committing only staged files without checking required unstaged edits, vague docs messages, and relying on stale tests.
