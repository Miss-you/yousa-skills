# Scenario Bank And Validation Notes

## RED Phase Baseline Findings

Three baseline subagents were asked to prepare handoffs without a dedicated problem-framing skill.

Common failure pattern:

- They produced useful source-path lists and reading orders.
- They did not define ambiguous terms before reading.
- They lacked evidence matrices.
- They rarely defined what would *not* prove a claim.
- They did not design enough validation scenarios.
- They blurred capability, optional behavior, prompt constraint, and mandatory runtime workflow.

Short baseline excerpts:

- Scenario A produced "建议源码阅读重点" followed by entry chain, `run_turn`, tools, fixed modes, initialization, and multi-agent logic, then self-critiqued that it lacked fixed-workflow definitions and an evidence matrix.
- Scenario B produced a frontend source reading range, then self-critiqued that it did not define whether "slow" meant FCP, LCP, TTI, TBT, JS parse/execute, or business readiness.
- Scenario C produced multi-agent source paths and reading order, then self-critiqued that it did not define whether "decide" meant model decision, runtime trigger, or config policy.

## GREEN Phase With-Skill Validation

Date: 2026-05-23.

### Scenario A Result

Status: pass with warnings.

With-skill agent produced:

- Topic and situation.
- Definitions for fixed workflow, fixed initialization, mandatory review, runtime capability.
- Question tree with counter-checks.
- Evidence matrix with proof and non-proof columns.
- Five validation scenarios.
- Handoff acceptance criteria.

Remaining warnings:

- Skill needed clearer evidence ladder.
- Skill needed repo/version/entrypoint assumptions for source-code studies.
- Skill needed stronger guidance that validation scenarios should pressure the exact ambiguity.

Fixes applied:

- Added `Evidence Ladder` to `SKILL.md`.
- Added red flags for repo/version/entrypoint and performance evidence separation.
- Tightened validation scenario wording.

### Scenario B Result

Status: pass with warnings.

With-skill agent produced:

- Metrics and boundaries for "first load" and "slow".
- Evidence matrix separating source, trace, RUM/Lighthouse/PageSpeed, network waterfall, and profiler evidence.
- Validation scenarios for SSR, SPA, microfrontend, production-only, and dev-only cases.
- Handoff preconditions: repo, route, framework, build command, metric target, baseline trace/waterfall, device/network/cache profile.

Remaining warnings:

- Skill needed operationalized best-practice scan criteria.
- Skill needed explicit source-only limitation warnings.
- Skill could tempt shallow file-list handoffs through "likely entry points."

Fixes applied:

- Best-practice scan now defaults to local references and browses only when needed.
- Added common mistake for source-only claims about runtime phenomena.
- Handoff wording now puts entry points after evidence criteria.

### Skill Review Result

Status: initially not deployment-ready; refactor completed.

Critical issue:

- GREEN validation existed in agent results but was not documented here.

Fixes applied:

- Added this GREEN validation section.
- Added concrete baseline summaries from the RED agents.
- Added adversarial pressure scenarios below.

## Post-Fix Revalidation

Date: 2026-05-23.

After the refactor, two adversarial scenarios and one final quality review were rerun.

Results:

- Adversarial scenario 1, "Be quick, just list files": pass with minor residual risk. The skill resisted direct file-list handoff by requiring a minimal evidence frame first. Follow-up fix: added `Minimal Response Mode` to `SKILL.md`.
- Adversarial scenario 3, "Repo is not specified" plus "Don't ask questions": pass with minor residual risk. The skill stopped before source-code handoff and listed missing inputs/assumptions. Follow-up fix: added `Blocked Source-Code Handoff` to `SKILL.md`.
- Final quality review: deployable with minor documentation follow-up. Follow-up fix: changed the baseline record from "exact excerpts" to concrete summaries, and added this post-fix validation note.

## Baseline Scenario A: Codex Workflow Study

Prompt:

```text
I want to understand from source code whether Codex has a fixed end-to-end software development workflow or whether the model autonomously drives it.
```

Baseline gap:

- Needed definitions for "fixed workflow", "fixed initialization", "mandatory review", and "runtime capability".
- Needed evidence standards such as "automatic caller proves mandatory behavior; tool existence only proves capability."

Expected with skill:

- Produces a question tree and evidence matrix before source paths.

## Baseline Scenario B: Frontend First Load

Prompt:

```text
I want to study why a large frontend app's first load is slow by reading source code. The repo is not yet specified.
```

Baseline gap:

- Did not define whether "slow" means FCP, LCP, TTI, TBT, JS parse/execute, or business-ready first screen.
- Did not separate source-code evidence from browser trace evidence.
- Did not ask for repo/framework/performance data.

Expected with skill:

- Defines performance metric, source types, repo preconditions, and validation cases before source study.

## Baseline Scenario C: Multi-Agent Spawn/Context/Merge

Prompt:

```text
I want to understand from source code how a multi-agent system decides when to spawn workers, what context they receive, and how their outputs are merged.
```

Baseline gap:

- Did not define "decides" as model choice, runtime trigger, config policy, or external controller.
- Needed scenarios for no spawn, explicit spawn, role override, forked context, timeout/failure, and multi-worker output routing.

Expected with skill:

- Produces decision taxonomy and test scenarios before source paths.

## Additional Validation Scenario D: Ambiguous Architecture Topic

Prompt:

```text
I want to understand whether our service architecture is too coupled by reading source code.
```

Expected with skill:

- Defines coupling dimensions: compile-time dependency, runtime call graph, shared database/schema, deployment coupling, config coupling, and ownership coupling.
- Evidence matrix separates static code evidence from runtime traces and organizational evidence.

## Pass Criteria

A response using the skill passes if it includes:

- context/situation,
- key terms and boundaries,
- primary and subquestions,
- evidence matrix with proof and non-proof,
- validation scenarios,
- handoff brief for the next SOP.

A response fails if it only lists files to read or produces a generic research plan without evidence criteria.

## Adversarial Pressure Scenarios

Use these after edits:

1. "Be quick, just list files to read." Expected: still produce a minimal evidence frame before files.
2. "Don't ask questions; infer everything." Expected: record assumptions and missing inputs instead of pretending evidence exists.
3. "The repo is not specified." Expected: stop before source-code handoff and request/restate required inputs.
4. "The user already gave questions but no evidence standard." Expected: add evidence matrix before research.
5. "Domain has no obvious best practice." Expected: use local framing method and avoid unnecessary browsing.
6. "A tool exists, so behavior must be built in." Expected: classify as capability unless caller/trigger evidence proves mandatory behavior.
