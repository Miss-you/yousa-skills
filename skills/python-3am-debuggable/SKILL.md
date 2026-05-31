---
name: python-3am-debuggable
description: >-
  Review or write Python code with a 3AM debuggability lens, focusing on readable tracebacks, visible async/background ownership, exception semantics, hidden side effects, mutable state capture, callback/closure chains, dynamic magic, and low-value indirection.
---

# Python 3AM-Debuggable

## One-Line Principle

Python code is cheap to make pass once and expensive to debug at 3 a.m. The question is not "is it Pythonic?" or "does Ruff like it?" The question is whether a tired maintainer can read the traceback, identify who owns the failure, see side effects and state, and change one behavior without understanding half the module.

This skill is a narrow sibling of `go-3am-debuggable`. It reviews Python for pressure-state diagnosability, not broad style.

## Non-Goals

Do not turn this into a generic Python review checklist. Unless the issue creates a 3AM failure surface, do not report:

- PEP 8, Black, Ruff, import order, quote style, or formatting nits
- mandatory docstrings, mandatory type hints, or "use pathlib" style advice
- generic "more Pythonic" taste
- broad AI-code-smell commentary without concrete traceback, contract, state, error, side-effect, or lifecycle risk
- performance or algorithmic correctness unless it affects safe debugging or maintenance

## 3AM Questions

When reviewing Python code, ask:

1. If this fails, will the traceback name real domain functions, or only `wrapper`, `<lambda>`, dynamic handlers, and inner closures?
2. Can the caller tell whether work is awaited, scheduled, retried, threaded, or fire-and-forget?
3. Can the caller distinguish "not found", "invalid input", and "operation failed"?
4. Are inputs, outputs, exceptions, side effects, and mutation visible at the boundary?
5. Does any closure/task/thread capture state that the caller later mutates?
6. Is an indirection layer real production behavior, or only a test seam / fake flexibility?
7. Would inlining five lines make ownership and traceback flatter?

## Tier Model

| Tier | Meaning | Handling |
|------|---------|----------|
| **T1 must clear** | Hides traceback meaning, async ownership, failure semantics, side effects, mutable state, or the real callable | Fix it. Ask for the smallest safe fix, not whether to keep it. |
| **T2 should fix** | Adds avoidable indirection or weakens pressure-state scanning, while the failure is still mostly attributable | Default to fixing or justify the real benefit. |

Do not introduce `Blocker/Major/Minor/Nit`; keep T1/T2.

## T1: Must Clear

### #1. Silent Or Collapsed Failure Paths

Broad exception handling that erases failure meaning is a 3AM failure surface.

Flag:

- `except Exception` / bare `except` with `pass`, `return None`, `{}`, `[]`, `False`, or logging-only recovery
- `raise ... from None` when it hides useful root cause
- converting specific failures into a vague fallback where callers cannot tell what happened

Allowed: specific exception recovery with a clear fallback, or raising a domain exception with `raise DomainError(...) from exc`.

### #2. Hidden Async / Background Boundaries

`asyncio.create_task`, `ensure_future`, threads, executor submit, schedulers, Celery/FastAPI background tasks, or fire-and-forget work must be visible from the caller or named as background/async work.

Flag:

- ordinary helpers that schedule background work without returning/retaining a task
- background work with no timeout/cancel/error reporting story
- helper names that sound synchronous but hide task/thread ownership
- task exceptions that can disappear into logs or event loop warnings

Allowed: visible `asyncio.TaskGroup`, awaited `gather`, explicit worker ownership, or framework-required background hooks whose lifecycle is obvious.

### #3. Callback Inversion Across A Lifecycle Boundary

Do not pass "how to do the work" into a helper that runs it later, elsewhere, in a retry wrapper, or in the background.

Flag:

```python
def run_later(build_payload: Callable[[], dict[str, Any]]) -> None:
    asyncio.create_task(send_payload(build_payload()))
```

Prefer passing data, calling a named function in the visible caller, or returning a task/future whose owner is clear.

### #4. Mutable Or Late-Bound State Capture

Python closures make it easy to capture state whose value changes before the work runs.

Flag:

- mutable default arguments such as `cache=[]`
- loop variables, request objects, session objects, dict/list accumulators, or status flags captured by tasks/threads/callbacks and then mutated
- local closures that hold shared mutable state across lifecycle boundaries

Allowed: `dataclasses.field(default_factory=list)`, explicit snapshots, immutable values, or constructor-injected dependencies used by real production wiring.

### #5. Hidden Side Effects And Shared State

A pure-looking function should not secretly mutate inputs, globals, environment, files, network, database, time/random state, or process state.

Flag:

- public-looking functions that mutate arguments without stating it
- `global` mutation or module-level mutable caches/registries without ownership
- reading env/files/network/time inside code that looks like transformation logic
- hidden I/O mixed into validation or mapping functions

### #6. Test-Only Seams And Fake Call Indirection

Python tests can patch real imports or inject real production dependencies. Do not add module aliases only for tests.

Flag:

```python
send_metric_func = send_metric
_now = time.time
_post = requests.post
```

Allowed: explicit constructor/function dependency injection that production code also uses.

### #7. Dynamic Magic Hiding The Real Callable

Dynamic dispatch is T1 when it hides which handler failed or makes incidents ungrepable.

Flag:

- `globals()[kind](payload)`, `locals()[name]`, `getattr(obj, name)(...)`
- `importlib` dispatch, registries, factories, `eval`, or `exec`
- dynamic dispatch combined with broad exception handling

Allowed: small explicit maps like `HANDLERS: dict[str, Callable] = {"email": send_email}` when errors preserve the selected key and target.

## T2: Should Fix

### #8. Thin Single-Caller Wrappers

A wrapper with one production caller and no contract is usually a traceback tax.

Flag helpers such as `_prepare`, `_process`, `_handle`, `_send`, or `build_payload_wrapper` when they only wrap a few obvious lines.

Allowed: framework entrypoints, interface implementations, public API boundaries, or helpers with a real contract.

### #9. Local Closures, Lambdas, And Decorator Wrappers

Local functions and lambdas are normal Python, but they become risky when they obscure traceback names or hide state.

Flag:

- non-trivial nested functions/lambdas that capture mutable state
- chains of local functions calling local functions
- decorators returning `wrapper` without `functools.wraps`
- decorators that hide side effects or exception behavior

Allowed: `sorted(items, key=lambda item: item.score)`, small predicates, `default_factory`, pytest/framework callbacks, and decorators that preserve `wraps` and make side effects obvious.

### #10. Opaque Public Contracts

At public boundaries, the maintainer must see shape and failure semantics.

Flag:

- `dict[str, Any]`, bare `dict`, broad `Any`, or bare tuples at public boundaries when they hide important shape
- mixed return shapes such as `None | dict | bool`
- unclear `None` semantics
- undocumented side effects or raised exceptions on handlers, CLI entrypoints, library functions, and public methods

Do not demand exhaustive types for tiny private helpers or obvious locals.

### #11. Long / Deep / Mixed-Responsibility Functions

Line count alone is not a finding. Flag long or deep functions only when they obscure state, side effects, error ownership, or lifecycle.

Typical signals:

- validation, parsing, business logic, persistence, logging, and response formatting in one function
- nested branches that duplicate most logic
- many flags simulating a state machine
- I/O mixed with pure transformation

Preferred fix order: clarify contract, isolate side effects, split responsibility, then reduce duplication.

### #12. Generic Managers, Fake Modularity, And Premature Abstraction

Flag:

- `Manager`, `Processor`, `Handler`, `Service`, or `Helper` classes whose methods do not share one coherent abstraction
- `utils.py`, `helpers.py`, `common.py` modules that collect unrelated behavior
- registries, factories, plugin systems, or abstract base classes before real variation exists
- abstraction added only to avoid two harmless lines of duplication

Prefer meaningful duplication over fake abstraction.

## Allowed Patterns

Do not flag these by default:

- `sorted(..., key=lambda item: item.score)`
- `dataclasses.field(default_factory=list)`
- visible `asyncio.TaskGroup` or awaited `asyncio.gather`
- framework-required callbacks when lifecycle is obvious
- specific exception recovery or `raise DomainError(...) from exc`
- real dependency injection used by production wiring
- context managers that make resource lifetime obvious

## Workflow

### Writing New Code

1. Write the main flow plainly first.
2. Keep async/background boundaries visible at the caller.
3. State public contracts: inputs, outputs, exceptions, side effects, mutation.
4. Preserve exception cause unless there is a deliberate security or UX reason not to.
5. Snapshot mutable state before crossing task/thread/callback boundaries.
6. Add abstraction only after it reduces real complexity.

### Reviewing Existing Code

1. Run `python3 scripts/scan.py <paths>` if shell access is available. Treat output as clues, not a gate.
2. Fix T1 findings first: silent failure, hidden background work, lifecycle callback inversion, mutable capture, fake seams, dynamic magic.
3. Then review T2: wrappers, closures, opaque contracts, long mixed functions, generic managers, fake modularity.
4. For every finding, name the specific 3AM failure surface.

## Output Format

Each finding must include:

- **Tier**: T1 / T2
- **Location**: file, function/class, or snippet; do not invent line numbers
- **Failure surface**: traceback / async lifecycle / exception meaning / side effect / state capture / real callable / boundary contract
- **Why 3AM debugging suffers**: concrete debugging or change-safety impact
- **Minimal fix**: pass data, await/return task, preserve cause, snapshot, inline, clarify contract, isolate side effect, or name the abstraction
- **Confidence**: High / Medium / Low

Optionally include "What I would not change" to prevent unnecessary churn.

## References

- **Scanner**: `python3 scripts/scan.py <py-file-or-dir>` — advisory AST scan, exits 0 for findings.
- **Validation exercises**: [references/validation-exercises.md](references/validation-exercises.md) — fixtures covering expected T1/T2/allowed outcomes.

Center every review on concrete 3AM failure surfaces. If you cannot name one, do not report the issue.
