---
name: go-service-risk-review
description: Use when a completed Go backend service change needs a lightweight production-risk review for observability, compatibility, performance, isolation, or Go concurrency concerns.
---

# Go Service Risk Review

## Overview

Use this after implementation when the question is not "find every bug", but "what could make this Go service change risky in production?" Review only risks introduced or touched by the change, and keep the output high-signal.

## When to Use

- A Go backend service change is implemented and needs a production-risk pass before merge or release.
- The change touches metrics, logging, goroutines, locks, config defaults, or API response shapes.
- Not for: broad bug hunting, style review, or reviewing code the change did not touch.

## Risk Lenses

Use only the lenses touched by the change:

- Observability: Can the new signals explain success, failure, count growth, and latency movement?
- Compatibility: Could callers, configs, dashboards, alerts, or rollout assumptions break?
- Cost: Did hot-path work add meaningful CPU, allocation, lock, goroutine, IO, log, or metric cost?
- Isolation: Can non-critical helpers fail, panic, or time out without breaking the core path?
- Go runtime risks: context, goroutines, locks, shared state, channels, and metric cardinality.
- Simplicity: Is the solution understandable without a large wrapper hiding business stages or error semantics?

## Go-Specific Signals

- Observability signals should answer a concrete production question and point to the next action. Counts, latency, errors, and stages should not be ambiguous when the change regresses.
- Metrics labels must be bounded: avoid `user_id`, `trace_id`, room/order IDs, raw path/query/payload, and `err.Error()`. Prefer `operation`, route template, `stage`, `result`, `error_class`, or bucketed codes.
- For stage latency, confirm the phases form a useful diagnosis path. If `total` rises but no stage explains it, note missing boundaries, parallel wait time, or outer work.
- Histogram buckets and sampling must match QPS and diagnosis needs. Full-sample low-cardinality metrics are usually fine; high-QPS item-level histograms are not.
- New goroutines need an owner, exit condition, context propagation, bounded channel behavior, and panic isolation at goroutine boundaries.
- Async goroutines must not drop errors silently. Every non-critical RPC/reporting failure needs a bounded signal such as structured log, metric, retry queue, or explicit best-effort comment.
- Flag `context.Background()` in request-scoped RPC/DB/cache work unless the change intentionally detaches work with bounded lifetime and explicit ownership.
- Locks should not wrap RPC/IO, logging bursts, metrics reporting, or unbounded loops. Shared maps need synchronization.
- Non-critical observability, audit, async reporting, or helper cache failures should not fail the main business path, but must leave a signal.
- API response compatibility includes field type changes, field meaning changes, error-code taxonomy changes, and client retry/alert behavior. Treat these as breaking unless versioned, dual-supported, or explicitly migrated.
- Config default changes are rollout changes. A previously unset config should not silently enable new behavior unless blast radius, rollback, and migration are explicit.

## Workflow

1. Read the diff and note which risk lenses it touches; skip the rest.
2. For each touched lens, check the matching Go-Specific Signals against the changed code only.
3. Separate core-path failures from non-critical helper failures, and confirm the latter leave a signal.
4. Drop weak or speculative findings; keep only risks with a clear production impact.
5. Write up findings in the Output format, ordered by severity, each with a mitigation or verification step.

## Output

Lead with concrete production risks, ordered by severity. Each finding should include:

- risk
- why it matters in production
- a concrete mitigation or verification step

Prefer 3-6 findings. If no meaningful risk is found, say that and name any unreviewed gaps.

## Avoid

- Turning this into broad bug review, style review, or all-project audit.
- Saying "add metrics" without naming the diagnostic question.
- Treating all errors as fatal; separate core business errors from observability/helper failures.
- Proposing large abstractions when a small bounded helper or guard is enough.
