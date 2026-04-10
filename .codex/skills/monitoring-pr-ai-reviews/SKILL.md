---
name: monitoring-pr-ai-reviews
description: >-
  Use when implementation is already complete, a GitHub PR exists or must be
  opened, and follow-up work is still needed because Copilot or other AI review
  comments may arrive after the initial push.
---

# Monitoring PR AI Reviews

## Overview

Close the loop after implementation: open the PR, keep AI review visible on a schedule, and handle each suggestion with compatibility-first judgment instead of blind agreement.

**Core principle:** AI review comments are inputs to evaluate, not orders. Fix real bugs, races, contract gaps, and missing tests. Reject speculative public APIs, overdesign, or premature abstractions.

**REQUIRED SUB-SKILLS:** `github:gh-address-comments`, `receiving-code-review`, `verification-before-completion`

## When to Use

Use this skill when:

- the task code is already implemented and verified
- a PR exists or must be created now
- Copilot or other AI review comments may still arrive after the first push
- the remaining work is PR refresh, comment triage, fixes, replies, and thread resolution

Do not use this skill for:

- initial feature design
- implementing the original task from scratch
- human review that changes product direction and needs a new design decision

## The Flow

1. Confirm the task is really ready for PR.
   - Run fresh verification.
   - Open a non-draft PR.
2. Keep periodic monitoring enabled.
   - Scheduled workflow: `.github/workflows/pr-ai-review-monitor.yml`
   - Local or CI scan from this skill directory: `python3 ./scripts/pr_ai_review_monitor.py --repo <owner/name> [--pr <number>] [--ai-login <login>]`
   - Manual workflow run: `gh workflow run pr-ai-review-monitor.yml`
3. Read review threads, not flat comments.
   - Keep thread ids, file anchors, outdated state, and resolution state.
4. Evaluate each AI suggestion against repo principles.
   - preserve user-visible compatibility first
   - prefer the smallest fix that closes the real issue
   - keep internal test seams internal unless a real external caller needs them
   - reject "future provider" abstractions without concrete current need
5. Implement only justified changes.
   - Tie each code change to a review thread.
   - Run the narrowest proving test first, then broader repo gates.
6. Refresh the PR.
   - push
   - reply with fix or rejection rationale
   - resolve threads only after the code or rationale is visible on the PR
7. Re-scan until no unresolved AI review remains, or only explicit user-owned decisions remain.

## Quick Reference

Commands below are relative to this skill directory.

| Need | Action |
| --- | --- |
| Open or refresh PR | create a non-draft PR from the verified task branch |
| Scan all open PRs | `python3 ./scripts/pr_ai_review_monitor.py --repo <owner/name>` |
| Scan one PR | `python3 ./scripts/pr_ai_review_monitor.py --repo <owner/name> --pr <number>` |
| Include another AI reviewer login | `python3 ./scripts/pr_ai_review_monitor.py --repo <owner/name> --ai-login <login>` |
| Resolve a review thread | `gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved id}}}' -F id=<thread-id>` |
| Re-check after push | run the monitor again and confirm zero unresolved AI review threads |

## Evaluation Rules

Accept when the comment identifies:

- a real bug, race, broken contract, missing verification, or missing typed error handling
- a concrete startup or runtime failure for actual callers
- spec drift or parity drift

Reject when the comment mainly asks for:

- new exported APIs without current callers
- public hooks whose only consumer is same-package test code
- cross-provider abstractions added "for later"
- refactors that widen task scope after the task is already complete

## Common Mistakes

- resolving threads before the fix or rationale is visible in the PR
- treating Copilot suggestions as mandatory
- expanding the public API to satisfy test-only feedback
- re-running only package tests after a repo-wide behavioral change
- forgetting that new AI review may arrive after the first fix push
