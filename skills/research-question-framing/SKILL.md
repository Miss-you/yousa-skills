---
name: research-question-framing
description: Use when a research topic has unclear scope, ambiguous terms, missing evidence criteria, or is likely to become a source-code learning study, investigation, audit, architecture explanation, or design inquiry
---

# Research Question Framing

## Purpose

Turn a fuzzy research topic into an evidence-seeking brief before source-code study begins.

**Core principle:** Do not start reading broadly until the question, context, evidence standard, and test cases are explicit.

## When to Use

Use before a source-code learning SOP, architecture investigation, performance diagnosis, agent-system study, or design research task when the user has a topic but not a clear research frame.

Do not use for single-symbol lookups, direct bug fixes, or tasks where the user already gave precise questions and evidence criteria.

## Workflow

```text
topic -> context -> divergent questions -> refined questions
-> evidence matrix -> validation scenarios -> handoff brief
```

1. Frame context: user, decision, system, scope, non-goals, and why the answer matters.
2. Check method basis: start with `references/best-practices.md`; search externally only when requested, unfamiliar, high-stakes, unstable/current, or dependent on domain standards.
3. Generate 8-12 candidate questions without answering them.
4. Improve questions: turn vague yes/no questions into answerable open questions, and broad open questions into closed checks where needed.
5. Prioritize 3-5 primary/subquestions plus 2-3 negative checks.
6. Build an evidence matrix: source-code, runtime, docs, tests, traces, metrics, and negative evidence.
7. Create 3-5 validation scenarios that pressure the topic's exact ambiguity.
8. Handoff only after evidence criteria; likely entry points come last.

## Minimal Response Mode

When the user asks for speed or says "just list files," still include:

- one-sentence topic,
- definitions for the ambiguous terms,
- 2-3 proof / non-proof criteria,
- likely entry points only after those criteria.

## Blocked Source-Code Handoff

If a source-code study lacks the repo, branch/version, entrypoint, metric, or target behavior, do not hand off to source reading yet.

If the user says not to ask questions, state assumptions and missing inputs as requirements:

```markdown
## Handoff Status
Blocked: missing <repo/version/entrypoint/metric/target behavior>.

## Required Inputs
- ...

## Assumptions If Forced To Proceed Later
- ...
```

## Brief Template

```markdown
# Research Brief

## Topic
One sentence.

## Situation
User/context, decision to support, constraints, and what confusion must be removed.

## Key Terms And Boundaries
Define ambiguous words and what would count as in/out of scope.

## Question Tree
- Primary question
- Subquestions
- Negative checks

## Evidence Matrix
| Question | Evidence needed | Source type | What would prove it | What would not prove it |
|---|---|---|---|---|

## Validation Scenarios
3-5 cases that should still produce a useful frame.

## Handoff To Source-Code SOP
Scope, likely entry points, required artifacts, and acceptance criteria.
```

## Evidence Ladder

Use the strongest available evidence: runtime caller/state transition > config default/feature gate > integration/unit test > tool spec/API/command > prompt/instruction text > docs/README > absence after documented search.

Rules:

- Tool/API existence proves capability, not mandatory behavior.
- Prompt text proves guidance, not runtime enforcement.
- Source code alone rarely proves performance or production behavior; require traces, logs, metrics, or field data.
- Absence is only useful when search scope and terms are recorded.

## Skill Deployment Test Cases

Use `tests/scenario-bank.md` before deploying or changing this skill. Validate at least:

- source-code agent workflow study,
- frontend first-load performance investigation,
- multi-agent spawn/context/merge study,
- ambiguous product/architecture research with no repo yet.

## Red Flags

- "Read these files" appears before "what would prove the answer."
- The handoff cannot distinguish capability from mandatory behavior.
- The topic contains terms like "fixed workflow", "slow", "decide", "autonomous", or "architecture" without definitions.
- There is no `What would not prove it` column.
- There are no test scenarios.
- The brief lacks repo/version/entrypoint assumptions for source-code studies.
- Performance claims do not separate lab, field, source, and runtime evidence.
- A bespoke process is invented before checking the local method reference.

## Handoff Rule

Only hand off to a source-code SOP when the Research Brief has: context, boundaries, prioritized questions, evidence matrix, validation scenarios, and acceptance criteria.
