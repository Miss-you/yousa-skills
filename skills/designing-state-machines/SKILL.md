---
name: designing-state-machines
description: Use when designing or reviewing lifecycle status fields, finite state machines, async task/order/payment/upload/approval workflows, or when states are overlapping, action-shaped, ownerless, unsafe under retries, concurrency, timeouts, or terminal-state updates.
---

# Designing State Machines

## Core Principle

A state is a stable fact the system can prove, not an action, guess, reason, or temporary detail.

Define boundary, states, events, transitions, owners, illegal paths, idempotency, concurrency, side effects, metrics, and tests.

## When to Use

Use this for durable `status`, `state`, `phase`, or lifecycle fields in tasks, messages, uploads, orders, payments, approvals, reservations, leases, sagas, circuit breakers, sessions, and workflows.

Skip short-lived UI flags or in-memory booleans.

## Required Workflow

1. **Name the boundary**: "`<Object>` from `<start fact>` to `<terminal outcome>`."
2. **Write the happy path** before naming states.
3. **Keep only stable facts**. Delete action-shaped, duplicated, guessed, or reason-shaped states.
4. **Define each state strictly** enough to code from it.
5. **Model events, not endpoints**. One endpoint can emit different lifecycle events.
6. **Build a transition table**: state, event, guard, next state, owner, idempotency, side effects.
7. **Define illegal transitions explicitly** for every state/event pair.
8. **Protect persistence** with current-state, version, or lease-token conditions; never blind `setStatus`.
9. **Specify timeout, retry, compensation, and repair** for every non-terminal state.
10. **Keep side effects consistent** with transaction + outbox or idempotent recovery.
11. **Generate a test matrix** from `current state x event`.

## State Design Rules

| Smell | Better design |
| --- | --- |
| `PUSHING`, `CALLING`, `UPLOADING`, `CHECKING` | event log, attempt table, progress field, trace |
| `RUNNING` when the service cannot prove execution | `ACKED`, heartbeat, `lastSeenAt`, progress report |
| `FAILED_TIMEOUT`, `FAILED_NETWORK` | `status = FAILED`, `errorCode = TIMEOUT/NETWORK` |
| `ORDER_PAID_SHIPPING_INVOICED` | separate `orderStatus`, `paymentStatus`, `shipmentStatus`, `invoiceStatus` |

Ask for every state:

- Can the system prove this fact?
- Does it change permissions, allowed events, recovery, or metrics?
- Who owns the transition into it?
- Is it one lifecycle dimension?

## Transition Table Template

| Current state | Event | Guard | Next state | Owner | Idempotency | Side effects |
| --- | --- | --- | --- | --- | --- | --- |
| `PENDING` | `CLIENT_PULLED` | not expired | `ACKED` | pull API | repeat returns current task/status | set `ackTime`, write audit event |

For SQL-backed state, use compare-and-set:

```sql
UPDATE task
SET status = 'FINISHED', finish_time = NOW()
WHERE id = ?
  AND status = 'ACKED';
```

Zero affected rows must map to idempotent, stale, illegal, or conflict behavior.

## Review Gate

Do not accept a design until it answers:

- Are terminal states explicit and protected from overwrite?
- Are duplicate and out-of-order events handled?
- Are illegal transitions observable?
- Are timeout/retry owners clear?
- Are state update and side effects consistent?
- Are metrics defined for counts, dwell time, transitions, illegal paths, timeouts, repeats, and failure reasons?

For worked examples and common patterns, see [references/patterns-and-examples.md](references/patterns-and-examples.md).
