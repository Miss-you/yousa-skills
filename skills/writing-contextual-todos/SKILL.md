---
name: writing-contextual-todos
description: Use when creating docs/todo entries, follow-up work records, or post-validation TODOs that future humans or agents must understand without chat history
---

# Writing Contextual TODOs

## Overview

Write TODO docs as handoff artifacts, not reminders. A future reader should understand what happened, why the follow-up matters, what is already proven, and what must be true before the TODO can close.

## When to Use

Use this when asked to record follow-up work after validation, debugging, investigation, implementation, or a boundary discovery.

Do not use it for one-line personal reminders or issue titles that already have full context elsewhere.

## Core Pattern

1. State the reader standard before writing: understandable without chat context, necessary, concise.
2. Gather facts: original goal, verified behavior, invalid evidence, boundary gaps, source-of-truth decisions, links to detailed evidence.
3. Create or update `docs/todo/<date>-<topic>.md`.
4. Include acceptance standards that can fail, including negative cases such as wrong project, manual side effects, or missing observability.
5. Have a subagent review against the reader standard and project boundaries.
6. Patch the TODO from review feedback, then run a formatting/diff check.

## TODO Shape

Use these sections unless the repo has a stronger local template:

- `Writing Principles`: who the doc is for and what “good” means.
- `Context`: the story in a few paragraphs, not a transcript.
- `What Was Verified`: proven behavior only.
- `Boundary Problems`: each gap with why it matters.
- `Follow-up Work`: concrete implementation slices.
- `Acceptance Standard`: observable pass/fail criteria.
- `Problems Encountered`: traps future agents must not repeat.

## Source Attribution

Separate product behavior from operator behavior.

- Product behavior: code/runtime/hooks/tools executed by the system being validated.
- Operator behavior: manual shell, direct API calls, manual GitHub/Linear edits, or cleanup.

Manual actions can prepare or inspect; they must not be counted as acceptance evidence.

## Reviewer Prompt

Ask an independent subagent:

```text
Review docs/todo/<file>. Check: can someone without chat context understand the goal, why it matters, what was proven, what remains, source attribution, architecture boundaries, actionability, and brevity? Return Critical / Important / Minor / Verdict. Do not edit files.
```

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Vague TODO like “productize this” | Name the exact missing behavior and acceptance criteria. |
| No source of truth | Record where project/repo/issue identity comes from. |
| Manual actions counted as success | Mark them invalid or operator-only. |
| Narrative dump | Link detailed evidence; keep TODO focused on future work. |
| Skipping reviewer | Review catches context gaps the writer no longer sees. |
