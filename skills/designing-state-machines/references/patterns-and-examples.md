# State Machine Patterns And Examples

## Common Patterns

| Pattern | Shape | Key question |
| --- | --- | --- |
| Linear lifecycle | `CREATED -> PROCESSING -> SUCCEEDED/FAILED` | Are terminal states irreversible? |
| Acknowledgment | `PENDING -> ACKED -> FINISHED/FAILED` | What fact proves the receiver got it? |
| Worker lease | `READY -> CLAIMED -> SUCCEEDED/FAILED/DEAD` | How do expired workers lose ownership? |
| Resource reservation | `AVAILABLE -> RESERVED -> CONFIRMED/RELEASED` | How do timeout and payment race? |
| Approval flow | `DRAFT -> SUBMITTED -> APPROVED/REJECTED` | Are request status and node status separate? |
| Saga | step states plus compensation states | How does restart resume from recorded state? |
| Circuit breaker | `CLOSED -> OPEN -> HALF_OPEN` | Which guard moves each state? |
| Parent/child aggregate | parent derived from child states | Is parent state stored or computed? |

## Example: Client Task Dispatch

Use this when a server creates a task, push only wakes the client, the client pulls the task, and then reports a final result.

```text
Object: ClientTask
Boundary: server-created task from pending client pull to final client-reported outcome.

States:
PENDING: task exists on server; client has not pulled it. Push does not change this state.
ACKED: client pulled the task and server recorded that shared fact.
FINISHED: client reported successful completion; terminal.
FAILED: client reported failure or server timed out the task; terminal.

Events:
TASK_CREATED
CLIENT_PULLED
CLIENT_REPORTED_SUCCESS
CLIENT_REPORTED_FAILURE
PULL_TIMEOUT
EXEC_TIMEOUT
```

| Current state | Event | Next state | Rule |
| --- | --- | --- | --- |
| none | `TASK_CREATED` | `PENDING` | admin/server creates task |
| `PENDING` | `CLIENT_PULLED` | `ACKED` | pull API records `ackTime` |
| `ACKED` | `CLIENT_REPORTED_SUCCESS` | `FINISHED` | report API records result once |
| `ACKED` | `CLIENT_REPORTED_FAILURE` | `FAILED` | report API records error once |
| `PENDING` | `PULL_TIMEOUT` | `FAILED` | timeout scanner records `PULL_TIMEOUT` |
| `ACKED` | `EXEC_TIMEOUT` | `FAILED` | timeout scanner records `EXEC_TIMEOUT` |
| `FINISHED` | repeated success | `FINISHED` | idempotent; no duplicate side effects |
| `FAILED` | repeated failure | `FAILED` | idempotent; no duplicate side effects |

No `RUNNING` state is needed unless the server can prove execution. Use `ACKED` for the shared fact, and store execution details in progress, heartbeat, logs, or reports.

## Test Matrix Template

Every row is a current state. Every column is an event. Reuse the exact event names from the transition table above so the matrix is a direct, complete derivative of the example — including the distinct `PULL_TIMEOUT` and `EXEC_TIMEOUT` paths rather than a single merged timeout. Fill each cell with a transition, idempotent result, rejection, audit-only behavior, or repair path.

| Current state | `CLIENT_PULLED` | `CLIENT_REPORTED_SUCCESS` | `CLIENT_REPORTED_FAILURE` | `PULL_TIMEOUT` | `EXEC_TIMEOUT` |
| --- | --- | --- | --- | --- | --- |
| `PENDING` | `ACKED` | reject/audit | reject/audit | `FAILED` | reject/audit |
| `ACKED` | idempotent `ACKED` | `FINISHED` | `FAILED` | ignore/audit | `FAILED` |
| `FINISHED` | idempotent `FINISHED` | idempotent `FINISHED` | conflict/audit | ignore/audit | ignore/audit |
| `FAILED` | reject/audit | conflict/audit | idempotent `FAILED` | idempotent `FAILED` | idempotent `FAILED` |

## Review Questions

1. What is the single object and lifecycle boundary?
2. Is every state a stable fact the system can prove?
3. Are any states actions, reasons, guesses, or duplicated synonyms?
4. Are multiple lifecycle dimensions mixed into one field?
5. Who owns each transition?
6. Are events separate from endpoints?
7. Are terminal states explicit and protected from overwrite?
8. Are duplicate and out-of-order events handled?
9. Are illegal transitions documented for every state/event pair?
10. Does persistence enforce legal current state, version, or lease token?
11. Are timeout, retry, compensation, and manual repair rules explicit?
12. Are transition side effects atomic or outboxed?
13. Can the transition table become a test matrix?
