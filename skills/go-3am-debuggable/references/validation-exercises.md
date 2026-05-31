# Validation Exercises

Use these fixtures to test whether a reviewer applies `go-3am-debuggable`
without over-reporting normal Go style.

Each exercise has one expected outcome:

- `T1`: must flag
- `T2`: should flag
- `allowed`: should not flag

The snippets are intentionally small review fixtures; some use project-local
types or package names without full declarations.

## Should Flag

### 1. Mock-only seam

Expected: `T1`

Why: `sendMetricFunc` exists only as a test seam around a real function. In a
codebase using mockey, patch `sendMetric` directly instead of routing runtime
code through an indirect package variable.

```go
package recall

import "context"

type Metric struct {
	Name  string
	Count int
}

var sendMetricFunc = sendMetric

func ReportRecall(ctx context.Context, metric Metric) error {
	return sendMetricFunc(ctx, metric)
}

func sendMetric(ctx context.Context, metric Metric) error {
	return nil
}
```

### 2. Callback inversion inside async helper

Expected: `T1`

Why: the helper accepts "how to build the payload" as a callback, then invokes
that callback inside an async boundary. Even though the helper name says
`Async`, the callback parameter still creates callback inversion and a harder
stack trace.

```go
package recall

import (
	"context"
	"time"

	trpc "example.com/project/trpc"
)

type Group struct {
	Name string
}

type Request struct {
	UserID string
}

func HandleRecall(ctx context.Context, req Request) {
	reportRecallAsync(ctx, req.UserID, func() []Group {
		return buildRecallGroups(req)
	})
}

func reportRecallAsync(ctx context.Context, userID string, buildGroups func() []Group) {
	trpc.Go(ctx, 2*time.Second, func(ctx context.Context) {
		groups := buildGroups()
		sendRecallReport(ctx, userID, groups)
	})
}
```

### 3. Closure chain upgrade

Expected: `T1`

Why: two local closure variables form a call chain. The stack frame becomes an
anonymous `.func1/.func2` path, so this upgrades beyond a plain local closure
T2 finding.

```go
package recall

type Group struct {
	Name string
}

type Request struct {
	Primary   string
	Secondary []string
}

func BuildGroups(req Request) []Group {
	groups := make([]Group, 0, 4)

	add := func(name string) {
		if name != "" {
			groups = append(groups, Group{Name: name})
		}
	}

	addMany := func(names []string) {
		for _, name := range names {
			add(name)
		}
	}

	add(req.Primary)
	addMany(req.Secondary)
	return groups
}
```

### 4. Hidden async plus context.Background

Expected: `T1`

Why: the caller sees a plain helper call, but the helper starts a goroutine and
drops/detaches from the request context with `context.Background()`. The async
boundary and cancellation behavior are hidden from the caller.

```go
package recall

import (
	"context"
	"time"

	trpc "example.com/project/trpc"
)

type Request struct {
	UserID string
}

func HandleRecall(ctx context.Context, req Request) {
	writeAudit(ctx, req.UserID)
}

func writeAudit(ctx context.Context, userID string) {
	trpc.Go(context.Background(), 2*time.Second, func(ctx context.Context) {
		saveAudit(context.Background(), userID)
	})
}
```

### 5. Mutable capture across async

Expected: `T1`

Why: the async closure captures mutable local state and a mutable request
pointer, then the outer function mutates both after scheduling. Take immutable
snapshots before `trpc.Go` and pass those snapshots to a named function.

```go
package recall

import (
	"context"
	"strings"
	"time"

	trpc "example.com/project/trpc"
)

type Request struct {
	UserID string
}

func HandleRecall(ctx context.Context, req *Request) {
	status := "queued"

	trpc.Go(ctx, time.Second, func(ctx context.Context) {
		reportStatus(ctx, req.UserID, status)
	})

	status = "sent"
	req.UserID = strings.TrimSpace(req.UserID)
}
```

### 6. Single-caller wrapper

Expected: `T2`

Why: `buildReportGroupsForHandleRecall` is only a thin single-caller wrapper.
Inline it into the caller until there are at least three callers and enough
shared logic to justify extraction.

```go
package recall

import "context"

type Group struct {
	Name string
}

type Request struct {
	UserID string
	Scene  string
}

func HandleRecall(ctx context.Context, req Request) {
	groups := buildReportGroupsForHandleRecall(req)
	sendRecallReport(ctx, req.UserID, groups)
}

func buildReportGroupsForHandleRecall(req Request) []Group {
	groups := make([]Group, 0, 2)
	groups = append(groups, Group{Name: req.Scene})
	groups = append(groups, Group{Name: "default"})
	return groups
}
```

### 7. Stateful local closure

Expected: `T2`

Why: a non-trivial local closure captures and mutates `groups`. This is not a
closure chain, so it stays T2, but it should be simplified by unifying control
flow first. A named builder method is only a fallback if state really must be
held and reused.

```go
package recall

type Group struct {
	Name   string
	Weight int
}

type Request struct {
	Primary string
	Backup  string
}

func BuildWeightedGroups(req Request) []Group {
	groups := make([]Group, 0, 2)

	addGroup := func(name string, baseWeight int) {
		if name == "" {
			return
		}
		weight := baseWeight
		if name == req.Primary {
			weight += 10
		}
		groups = append(groups, Group{Name: name, Weight: weight})
	}

	addGroup(req.Primary, 100)
	addGroup(req.Backup, 50)
	return groups
}
```

## Should Not Flag

### 8. Legal sort.Slice

Expected: `allowed`

Why: `sort.Slice` requires a comparator callback. The anonymous function is a
small predicate, has no nested function literal, and contains no business flow.

```go
package recall

import (
	"sort"
	"time"
)

type Candidate struct {
	ID       string
	LastHit time.Time
}

func SortCandidates(candidates []Candidate) {
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].LastHit.After(candidates[j].LastHit)
	})
}
```

### 9. Legal thin trpc.Go

Expected: `allowed`

Why: the async boundary is visible in the caller, the anonymous function is
forced by the API shape, and the body only calls a named function with immutable
snapshots.

```go
package recall

import (
	"context"
	"time"

	trpc "example.com/project/trpc"
)

type Request struct {
	UserID string
	Scene  string
}

func HandleRecall(ctx context.Context, req Request) {
	userID := req.UserID
	scene := req.Scene

	trpc.Go(ctx, 2*time.Second, func(ctx context.Context) {
		reportRecallByScene(ctx, userID, scene)
	})
}
```

### 10. Generic Go style

Expected: `allowed`

Why: early returns, simple loops, and small structs are not findings by
themselves. There is no mock seam, callback inversion, hidden async boundary,
single-caller helper, or anonymous closure chain.

```go
package recall

import "strings"

type Group struct {
	Name string
}

type GroupBuilder struct {
	defaultName string
}

func (b GroupBuilder) Build(names []string) []Group {
	groups := make([]Group, 0, len(names)+1)
	for _, name := range names {
		cleaned := strings.TrimSpace(strings.ToLower(name))
		if cleaned == "" {
			continue
		}
		groups = append(groups, Group{Name: cleaned})
	}
	if len(groups) == 0 {
		groups = append(groups, Group{Name: b.defaultName})
	}
	return groups
}
```
