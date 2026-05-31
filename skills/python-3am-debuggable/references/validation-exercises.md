# Validation Exercises

Use these fixtures to test whether a reviewer applies `python-3am-debuggable`
without drifting into generic Python style review.

Treat each snippet as an independent review target. Each exercise has one primary
expected outcome:

- `T1`: must flag
- `T2`: should flag
- `allowed`: should not flag

Some snippets intentionally include normal Python typing or boundary context that
could create a secondary lower-tier observation. The validation pass is about the
highest 3AM failure surface named by the expected outcome.

For `T1` and `T2`, a passing review names the tier, the concrete 3AM failure
surface, why debugging suffers, and the smallest useful fix. A failing review
only gives style advice, invents unrelated problems, or flags an `allowed`
snippet.

## Coverage Map

| Exercise | Expected | Skill rule tested |
|---|---:|---|
| 1 | `T1` | broad exception collapse |
| 2 | `T1` | hidden `asyncio.create_task` |
| 3 | `T1` | callback builder in background work |
| 4 | `T1` | mutable async capture |
| 5 | `T1` | mutable default |
| 6 | `T1` | fake seam / test-only alias |
| 7 | `T1` | dynamic dispatch hiding real callable |
| 8 | `T1` | hidden side effect |
| 9 | `T2` | single-caller wrapper |
| 10 | `T2` | decorator wrapper without `wraps` |
| 11 | `T2` | generic manager |
| 12 | `T2` | opaque public contract |
| 13 | `allowed` | visible `TaskGroup` ownership |
| 14 | `allowed` | key lambda |
| 15 | `allowed` | `default_factory` |
| 16 | `allowed` | specific exception preserving cause |
| 17 | `allowed` | real dependency injection |
| 18 | `allowed` | explicit dispatch map with named handlers |
| 19 | `T1` | `raise ... from None` erasing root cause |
| 20 | `allowed` | decorator preserving metadata with `wraps` |

## Should Flag

### 1. Broad exception collapse erases failure meaning

Expected: `T1`

Failure surface: exception meaning.

A passing review says callers cannot distinguish "missing file", "bad JSON",
"invalid user", and "storage failed" because all failures become `None`.
Minimal fix: catch only expected exceptions with clear fallbacks, or raise a
domain exception using `raise ... from exc`.

Do not accept: "add more logging" as the only fix.

```python
def load_user(path: str) -> dict[str, Any] | None:
    try:
        raw = storage.read_text(path)
        return parse_user(json.loads(raw))
    except Exception:
        logger.exception("failed to load user")
        return None
```

### 2. Helper hides a background task

Expected: `T1`

Failure surface: async lifecycle.

A passing review says `record_signup` looks synchronous, but it schedules work
whose exception, cancellation, and shutdown owner are unclear. Minimal fix: make
the caller await it, return/retain the task under an explicit owner, or move the
work into visible structured concurrency.

```python
def record_signup(user_id: str, source: str) -> None:
    payload = {"user_id": user_id, "source": source}
    asyncio.create_task(send_signup_metric(payload))
```

### 3. Background helper accepts a payload builder callback

Expected: `T1`

Failure surface: async lifecycle and real callable.

A passing review says the helper accepts "how to build the work" and executes it
later in a background task, hiding both traceback ownership and when captured
state is read. Minimal fix: build the payload in the visible caller and pass data,
or return an owned task/future with explicit lifecycle handling.

```python
def enqueue_receipt(build_receipt: Callable[[], dict[str, Any]]) -> None:
    async def runner() -> None:
        await send_receipt(build_receipt())

    asyncio.create_task(runner())
```

### 4. Async closure captures mutable state that keeps changing

Expected: `T1`

Failure surface: state capture.

A passing review says each scheduled task captures the same `batch` list, then
the loop mutates that list before the task runs. At 3AM the payload depends on
timing, not the line that scheduled the task. Minimal fix: snapshot the data
before crossing the async boundary, or pass immutable values into a named
coroutine.

```python
async def publish_batches(rows: list[dict[str, Any]]) -> None:
    batch: list[dict[str, Any]] = []

    for row in rows:
        batch.append(row)

        async def publish() -> None:
            await send_batch({"rows": batch})

        asyncio.create_task(publish())
        batch.clear()
```

### 5. Mutable default cache

Expected: `T1`

Failure surface: shared state.

A passing review says `seen=[]` is shared across calls and silently turns a local
parameter into process-lifetime state. Minimal fix: use `None` plus a new list,
or make the cache an explicit owned object.

```python
def remember_user(user_id: str, seen: list[str] = []) -> list[str]:
    seen.append(user_id)
    return seen
```

### 6. Test-only seam hides the real dependency

Expected: `T1`

Failure surface: real callable.

A passing review says production calls aliases that exist only to make tests
patchable, so incidents and patches point at `_post_json` / `_now` instead of the
real dependency. Minimal fix: patch the real import in tests or use explicit
production dependency injection.

```python
_post_json = requests.post
_now = time.time


def emit_event(endpoint: str, payload: dict[str, Any]) -> None:
    _post_json(endpoint, json={**payload, "sent_at": _now()})
```

### 7. Dynamic dispatch hides which handler failed

Expected: `T1`

Failure surface: real callable and traceback.

A passing review says `getattr` constructs the callable name at runtime, making
the handler hard to grep and easy to break by typo or user input. Minimal fix:
use an explicit map from event names to named functions and preserve the selected
key and target in errors.

```python
class WebhookRouter:
    def dispatch(self, event_type: str, payload: dict[str, Any]) -> Any:
        handler = getattr(self, f"handle_{event_type}")
        return handler(payload)
```

### 8. Pure-looking mapper mutates its input

Expected: `T1`

Failure surface: hidden side effect.

A passing review says `normalize_user` looks like a transformation, but it mutates
the caller's dictionary in place. The side effect is invisible at the boundary and
can corrupt later debugging evidence. Minimal fix: return a new dictionary, or
rename/document the mutation at the public boundary.

```python
def normalize_user(user: dict[str, Any]) -> dict[str, Any]:
    user["email"] = user["email"].strip().lower()
    user.setdefault("roles", []).append("member")
    return user
```

### 9. Thin single-caller wrapper adds traceback tax

Expected: `T2`

Failure surface: traceback.

A passing review says `_prepare_payload` has one production caller and only wraps
obvious field selection, so it adds a frame without a contract. Minimal fix:
inline it, or give it a real named contract if it is expected to grow.

```python
def handle_signup(payload: dict[str, Any]) -> dict[str, Any]:
    return _prepare_payload(payload)


def _prepare_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {"id": payload["id"], "email": payload["email"]}
```

### 10. Decorator returns anonymous `wrapper`

Expected: `T2`

Failure surface: traceback.

A passing review says tracebacks, logs, and introspection will show `wrapper`
instead of the decorated function. Minimal fix: use `functools.wraps` and keep
side effects or exception behavior explicit.

```python
def audit_call(func):
    def wrapper(*args, **kwargs):
        logger.info("calling %s", func.__name__)
        return func(*args, **kwargs)

    return wrapper
```

### 11. Generic manager mixes unrelated responsibilities

Expected: `T2`

Failure surface: boundary contract and side effects.

A passing review says `UserManager` is not one coherent abstraction: parsing,
validation, persistence, file I/O, and notification failures all land in one
generic class. Minimal fix: name the real responsibilities and split ownership at
side-effect boundaries.

```python
class UserManager:
    def parse_csv(self, raw: str) -> list[dict[str, Any]]: ...
    def validate_signup(self, row: dict[str, Any]) -> bool: ...
    def save_user(self, row: dict[str, Any]) -> None: ...
    def write_import_report(self, rows: list[dict[str, Any]]) -> None: ...
    def notify_welcome(self, user_id: str) -> None: ...
```

### 12. Public boundary has opaque return shapes

Expected: `T2`

Failure surface: boundary contract.

A passing review says callers cannot tell whether `None`, `False`, or a dict
means "not found", "invalid", "forbidden", or "failed". Minimal fix: return a
named result type or raise specific domain exceptions with documented semantics.

```python
def resolve_account(user_id: str) -> dict[str, Any] | bool | None:
    if not user_id:
        return False
    if not account_exists(user_id):
        return None
    return {"id": user_id, "plan": load_plan(user_id)}
```

### 19. Domain exception hides the original cause

Expected: `T1`

Failure surface: exception meaning.

A passing review says `from None` removes the original traceback chain, so the
domain error no longer reveals whether storage, parsing, or config lookup failed.
Minimal fix: preserve the cause with `raise UserConfigMissing(path) from exc`
unless there is a deliberate security or UX reason to suppress it.

```python
def load_user_without_cause(path: str) -> UserConfig:
    try:
        return parse_user(storage.read_text(path))
    except FileNotFoundError:
        raise UserConfigMissing(path) from None
```

## Should Not Flag

### 13. Visible structured concurrency with `TaskGroup`

Expected: `allowed`

Why allowed: task ownership is visible at the caller, child tasks are awaited by
the context manager, and cancellation/error behavior belongs to the group.

```python
async def send_all_audits(users: list[str]) -> None:
    async with asyncio.TaskGroup() as tg:
        for user_id in users:
            tg.create_task(send_audit(user_id))
```

### 14. Sorting key lambda

Expected: `allowed`

Why allowed: this is a small API-shaped expression. It does not cross a lifecycle
boundary, hide mutable state, or make a meaningful traceback harder to read.

```python
def ranked(users: list[User]) -> list[User]:
    return sorted(users, key=lambda user: user.score)
```

### 15. Dataclass `default_factory`

Expected: `allowed`

Why allowed: `default_factory` creates a new list per instance and avoids shared
mutable defaults.

```python
@dataclasses.dataclass
class ImportState:
    errors: list[str] = dataclasses.field(default_factory=list)
```

### 16. Specific exception preserves cause

Expected: `allowed`

Why allowed: callers receive a domain exception while the original
`FileNotFoundError` remains visible in the traceback chain.

```python
def load_user(path: str) -> UserConfig:
    try:
        return parse_user(storage.read_text(path))
    except FileNotFoundError as exc:
        raise UserConfigMissing(path) from exc
```

### 17. Real dependency injection used by production wiring

Expected: `allowed`

Why allowed: the dependency is explicit behavior selected by production wiring,
not a module alias created only so tests can monkeypatch it.

```python
class UserReporter:
    def __init__(self, metrics: MetricsClient) -> None:
        self._metrics = metrics

    def report_signup(self, user_id: str) -> None:
        self._metrics.increment("signup", tags={"user_id": user_id})


def build_reporter(settings: Settings) -> UserReporter:
    return UserReporter(MetricsClient(settings.metrics_url))
```

### 18. Explicit handler map keeps callable ownership visible

Expected: `allowed`

Why allowed: the allowed event names and target functions are grepable, and the
error preserves the selected key instead of constructing a callable name
dynamically.

```python
class EventPayload(TypedDict):
    user_id: str


HANDLERS: dict[str, Callable[[EventPayload], None]] = {
    "signup": handle_signup,
    "cancel": handle_cancel,
}


def dispatch(event_type: str, payload: EventPayload) -> None:
    try:
        handler = HANDLERS[event_type]
    except KeyError as exc:
        raise UnknownEventType(event_type) from exc

    handler(payload)
```

### 20. Decorator preserves wrapper metadata

Expected: `allowed`

Why allowed: `functools.wraps` keeps the decorated function name and metadata
visible to tracebacks and introspection, and the wrapper does not change
exception semantics.

```python
def audited(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapped
```

## Reviewer Pass Criteria

A reviewer passes this validation set when they:

- Flag exercises 1-8 and 19 as `T1`.
- Flag exercises 9-12 as `T2`.
- Leave exercises 13-18 and 20 unflagged.
- Explain each finding in terms of traceback, async lifecycle, exception
  meaning, side effects, state capture, real callable visibility, or boundary
  contract.
- Avoid generic Python style comments that do not name a 3AM failure surface.
