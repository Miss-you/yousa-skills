---
name: multi-agent-staged-acceptance
description: Use when asked to review code for a spec or OpenSpec change, review staged or working-tree changes, or assess merge/release readiness with multiple agents and concrete file:line evidence.
---

# Multi-Agent Staged Acceptance

Infer scope from **Git evidence + requirements**, then verify implementation across layers. The name is retained for compatibility; “staged” does not restrict review to the index. Green tests alone do not prove acceptance.

## When to Use

- Reviewing code against a spec or OpenSpec change, or reviewing staged or working-tree changes.
- Assessing merge/release readiness where green tests alone would give false confidence.
- Producing severity-ordered findings with concrete file:line evidence.

## 1. Establish scope before delegation

Read applicable project instructions and the named spec, proposal, design, and tasks. Use the repository root, including sibling services. Collect candidates with `scripts/collect_review_scope.py` relative to this skill's actual directory (not an assumed project-local copy).

| User request | Target state |
|---|---|
| Spec / ordinary code review | Default: HEAD → working tree, including staged, unstaged, untracked, deleted and renamed files |
| Explicit staged-only review | Index; inspect `git show :path`, not working-tree content |
| PR / branch / revision review | Resolved base and target commits; derive merge-base from the requested PR/branch when appropriate |

Record exact base/target revisions. Do not invent `HEAD~1`. If a spec spans earlier commits, inspect relevant history and extend the base with evidence; label uncommitted overlays separately. An empty diff is **not acceptance**: inspect history/spec or report insufficient scope.

The collector inventories candidates, not semantic relevance. Read diff hunks and create a scope manifest:

- **Included changes:** path/hunks → requirement or necessary supporting change.
- **Related context:** unchanged callers, consumers, configuration, generated bindings, or reference code needed to validate the requirement, with reasons.
- **Excluded changes:** unrelated files/hunks and reasons. Neither include every dirty file nor limit review to paths literally named in the spec.
- **Evidence:** target state, fingerprints, unresolved scope assumptions, applicable tests.

Proceed with a stated, evidence-backed scope; ask only when ambiguity materially changes the review. Do not stage, stash, reset, edit product code, or commit merely to prepare review. Recollect fingerprints before the verdict; review changed files again if scope drifted.

## 2. Dispatch independent review roles

Use the prompts in `references/acceptance_blindspots_checklist.md`. Give every agent the same scope manifest, spec, target state, exclusions and accepted risks.

| Role | Deliverable |
|---|---|
| Vertical | Relevant tests/builds; exact commands, exit codes, environment and coverage gaps |
| Horizontal | Requirement → implementation/reference → test coverage; missing touchpoints |
| Chain | Each new field/option: define → serialize → transport → consume, plus failures/rollback |
| Fact (conditional) | Official-source verification of material unstable external claims; otherwise mark not applicable |
| Judge (after evidence) | Challenge/deduplicate findings and deliver a severity-ordered verdict |

Run Vertical, Horizontal and Chain concurrently within available slots. Queue Fact/Judge or reuse idle agents; do not require all roles simultaneously. The orchestrator resolves scope and evidence conflicts. Prefer project structural tools (e.g. CodeGraph); use text search for literals or documented fallback when unavailable.

## 3. Validate the reviewed state

Select repository-appropriate commands, flags and module roots, including affected languages. Existing package tests must actually exercise changed paths. Working-tree tests **cannot prove staged/commit acceptance when states differ**: use an isolated snapshot or explicitly report the evidence gap. Never silently skip an unlistable package and declare success. Distinguish code failures, baseline failures and environment blocks; call something baseline only with comparative evidence.

## 4. Report

1. Findings (`high/P1`, `medium/P2`, `low/P3`): trigger, impact, exact file:line, requirement and remedy. Report confirmed regressions or omissions; identify explicitly accepted tradeoffs separately.
2. Scope, assumptions and unresolved questions.
3. Commands/results and residual testing or deployment gaps.
4. Verdict: `accepted`, `accepted-with-risk`, or `rejected`. Missing scope/critical evidence cannot be `accepted`; use `rejected (insufficient evidence)` when evaluation is impossible. No findings must be stated explicitly and does not imply deployment readiness.

## Common Mistakes

- Treating green tests or an empty diff as acceptance.
- Inventing `HEAD~1` as the base, or reviewing every dirty file without a scope manifest.
- Running working-tree tests and claiming they prove staged/commit acceptance when the states differ.
- Silently skipping an unlistable package and declaring success.
- Calling a failure "baseline" without comparative evidence.
- Staging, stashing, resetting, editing product code, or committing just to prepare review.
- Skipping the fingerprint recheck before the verdict after scope drifted.
