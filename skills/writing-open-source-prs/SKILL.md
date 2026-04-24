---
name: writing-open-source-prs
description: Use when drafting, reviewing, or updating pull request descriptions for open source projects where maintainers need issue context, behavior changes, tests, tradeoffs, or CI status to review confidently.
---

# Writing Open Source PRs

## Overview

Write PR descriptions for maintainers, not for yourself. The goal is to let reviewers quickly decide whether the change is necessary, scoped, tested, and safe.

## When to Use

Use this for GitHub pull requests that involve bug fixes, behavior changes, CI fixes, docs tied to behavior, or any PR where context matters.

Do not use it for trivial typo-only PRs unless the project template still requires structure.

## SOP

1. Gather context: issue, user-visible symptom, project conventions, changed files, tests, local verification, remote CI status, and relevant history if available.
2. Verify context completeness before writing. If missing context changes the story, fetch it; if it cannot be fetched, state the assumption.
3. Draft the PR body around reviewer questions: what problem, why it happens, what this PR changes, what it intentionally does not change, how tests guard it, and what was verified.
4. Verify the draft against the checklist below. If it fails, revise. Try at most 3 times, then stop and report the blocker.
5. Before submitting or updating the PR, verify final state: issue reference, title format, local checks, remote CI status, and whether the body mentions pending failures honestly.

## PR Body Shape

Use this structure unless the project template says otherwise:

```markdown
Closes #123

## Goal and constraints
User-visible problem, important background, and behavior that must remain unchanged.

## Diagnosis
Where the behavior comes from. Separate evidence from inference.

## Approach
Short-term fix in this PR. Longer-term direction if the problem is broader. Tradeoffs and non-goals.

## Changes
Reviewer-relevant implementation changes only.

## Test coverage
Overall target: what behavior boundary the tests protect.

| Area | Scenario guarded |
| --- | --- |
| ... | ... |

## Verification
Commands run and CI status. Say pass, fail, or pending.
```

## Verification Gates

| Gate | Pass condition |
| --- | --- |
| Context gate | The draft has the issue/symptom, root cause or bug class, project constraints, and known CI/local status. |
| Draft/goal gate | A maintainer can understand the goal, behavior boundary, approach, tradeoffs, non-goals, and total-then-detail test coverage without reading the diff first. |
| Final gate | Issue reference, title format, local checks, remote CI status, pending failures, skipped checks, and assumptions are accurate before publishing or updating. |

If a gate fails, fix the PR body and re-check. Stop after 3 failed repair attempts instead of publishing a misleading PR.

## Quick Reference

| Include | Avoid |
| --- | --- |
| Problem before implementation | A changelog of touched files |
| Short-term and long-term framing when relevant | Pretending a tactical fix is the full design |
| Explicit tradeoffs and non-goals | Over-promising future work |
| Tests as reviewed behavior | "Added tests" with no scenario meaning |
| Accurate CI/local status | Saying "all green" while checks are pending |

## Common Mistakes

- **Diff-first summary:** "Changed X file" does not explain why the change matters.
- **Test-file inventory:** Reviewers need behavior coverage, not a file list.
- **Hidden assumptions:** If root cause is inferred from blame/history, say so.
- **Scope creep:** Do not make the long-term plan sound implemented in this PR.
- **Stale verification:** After CI fixes or new commits, update the PR body so it does not describe old failures.
