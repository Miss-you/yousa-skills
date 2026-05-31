# Case Study: Async Report Flow

这是一个经过脱敏的真实结构案例：业务函数把两路结果分组、分片，并异步上报到日志系统。第一次实现为了"灵活"引入了 mock-only seam、callback 参数、异步 helper 和局部 closure chain；两轮重构后，调用图和 panic stack 都变平了。

## Oracle Expectations

这份 case study 是 `go-3am-debuggable` 的验证样本。使用本 skill review 时，应得到这些结论：

- **第一轮重构前**：A mock-only seam、B callback 参数、D 单 caller async helper 都应被识别；异步 callback 调用外层传入的 `build` closure 应作为 T1 callback inversion 处理，而不是误称为语法上的嵌套匿名 func。
- **第一轮重构后**：mock seam、callback helper、隐藏 async helper 消失；只剩 API 形态强制的 `trpc.Go(..., func(ctx){...})`，不应被误报。
- **第二轮重构前**：两个局部 closure 互相调用，必须从 T2 升级到 T1，因为 panic stack 会出现 `.func1.func2`。
- **第二轮重构后**：closure chain 消失，主循环用数据归一化表达业务分支。

## 痛点

原始实现包含四类压力状态下很难 debug 的结构：

1. **mock-only seam**：包级 `var reportLogFunc = reportLog`、`var goFunc = trpc.Go`，只为了测试替换。
2. **callback inversion**：caller 把"怎么构造 groups"作为 `func() []Group` 传给 helper。
3. **隐藏异步边界**：`reportGroupsAsync` 名字虽然有 Async，但它把 `trpc.Go`、错误处理和 callback 调用包在一起，caller 仍要跳进去才看得懂。
4. **closure chain**：`appendUser` 调 `ensureGroup`，panic 栈帧会显示 `buildGroups.func1` / `buildGroups.func2`。

原始 panic stack 的阅读体验：

```text
reportGroupsAsync.func1
  -> reportRecallResults.func1
     -> buildGroupsFunc
```

半夜看到这串名字，第一步不是定位业务问题，而是猜每个 `func1` 对应哪条路径。

## 第一轮：拆掉跨函数 fake seam / callback / hidden async

### 重构前

```go
var (
    reportLogFunc  = reportLog
    goFunc         = trpc.Go
    buildGroupsFunc = buildGroups
    nowFunc        = time.Now
)

func reportRecallResults(ctx context.Context, userID int64, traceID string, rows []*RecallRow) {
    reportGroupsAsync(ctx, userID, traceID, func() []Group {
        return buildGroupsFunc(rows)
    })
}

func reportFinalResults(ctx context.Context, userID int64, traceID string, rows []*FinalRow) {
    reportGroupsAsync(ctx, userID, traceID, func() []Group {
        return []Group{buildFinalGroup(rows)}
    })
}

func reportGroupsAsync(ctx context.Context, userID int64, traceID string, build func() []Group) {
    if userID <= 0 || strings.TrimSpace(traceID) == "" {
        return
    }

    err := goFunc(ctx, 5*time.Second, func(ctx context.Context) {
        groups := build()
        if len(groups) == 0 {
            return
        }
        reportGroups(ctx, userID, traceID, groups)
    })
    if err != nil {
        log.ErrorContextf(ctx, "report groups async failed: %v", err)
    }
}
```

测试代码也被 fake seam 污染：

```go
func captureLogs(t *testing.T) *[]CapturedLog {
    oldReport := reportLogFunc
    oldGo := goFunc
    oldBuild := buildGroupsFunc
    reportLogFunc = func(table string, args ...interface{}) { ... }
    goFunc = func(ctx context.Context, timeout time.Duration, fn func(context.Context)) error {
        fn(ctx)
        return nil
    }
    buildGroupsFunc = func(rows []*RecallRow) []Group { ... }

    t.Cleanup(func() {
        reportLogFunc = oldReport
        goFunc = oldGo
        buildGroupsFunc = oldBuild
    })
    return &logs
}
```

新增一个 mock 依赖就要多一个包级变量、保存旧值、替换、恢复。生产代码读者也要分辨每个 `xxxFunc` 是真实能力还是测试钩子。

### 重构后

应用规则：

- **T1 #3 mock-only seam**：删掉 `xxxFunc = realFn`，测试直接用 mockey patch 真实函数。
- **T1 #4 callback inversion**：不再把 `func() []Group` 传给 helper。
- **T1 #2 async boundary ownership**：`trpc.Go` 出现在 caller 里，caller 一眼看见异步边界。
- **T2 #7 重复 < 错误抽象**：两个 caller 共享几行 async 壳子时，复制比抽 helper 更可 debug。

```go
func reportRecallResults(ctx context.Context, userID int64, traceID string, rows []*RecallRow) {
    if userID <= 0 || strings.TrimSpace(traceID) == "" {
        return
    }

    err := trpc.Go(ctx, 5*time.Second, func(ctx context.Context) {
        groups := buildGroups(rows)
        if len(groups) == 0 {
            return
        }
        reportGroups(ctx, userID, traceID, groups)
    })
    if err != nil {
        log.ErrorContextf(ctx, "reportRecallResults trpc.Go failed: %v", err)
    }
}

func reportFinalResults(ctx context.Context, userID int64, traceID string, rows []*FinalRow) {
    if userID <= 0 || strings.TrimSpace(traceID) == "" {
        return
    }

    err := trpc.Go(ctx, 5*time.Second, func(ctx context.Context) {
        groups := []Group{buildFinalGroup(rows)}
        reportGroups(ctx, userID, traceID, groups)
    })
    if err != nil {
        log.ErrorContextf(ctx, "reportFinalResults trpc.Go failed: %v", err)
    }
}
```

现在 panic stack 至少能直接对应业务路径：

```text
reportRecallResults.func1
reportFinalResults.func1
```

测试同步改成 patch 真实函数：

```go
mockey.Mock(reportLog).To(func(table string, args ...interface{}) {
    logs = append(logs, CapturedLog{Table: table, Args: args})
}).Build()

mockey.Mock(trpc.Go).To(func(ctx context.Context, timeout time.Duration, fn func(context.Context)) error {
    fn(ctx)
    return nil
}).Build()
```

## 第二轮：函数内部 closure chain 升级为 T1

第一轮拆掉跨函数过度抽象后，`buildGroups` 内部还残留两个局部 closure，且 `appendUser` 调 `ensureGroup`。

### 重构前

```go
func buildGroups(rows []*RecallRow) []Group {
    groups := make([]Group, 0, len(rows))
    groupIndex := make(map[string]int, len(rows))

    ensureGroup := func(name string) (int, bool) {
        if strings.TrimSpace(name) == "" {
            return 0, false
        }
        idx, ok := groupIndex[name]
        if !ok {
            idx = len(groups)
            groupIndex[name] = idx
            groups = append(groups, Group{Name: name})
        }
        return idx, true
    }

    appendUser := func(name string, userID int64) {
        if userID <= 0 {
            return
        }
        idx, ok := ensureGroup(name) // closure chain: appendUser -> ensureGroup
        if !ok {
            return
        }
        groups[idx].UserIDs = append(groups[idx].UserIDs, userID)
    }

    for _, row := range rows {
        if row == nil {
            continue
        }
        if len(row.UserIDs) == 0 {
            ensureGroup(row.Name)
            continue
        }
        if len(row.Sources) == 0 {
            for _, userID := range row.UserIDs {
                appendUser(row.Name, userID)
            }
            continue
        }
        for _, userID := range row.UserIDs {
            sources := row.Sources[userID]
            if len(sources) == 0 {
                appendUser(row.Name, userID)
                continue
            }
            for _, source := range sources {
                appendUser(source, userID)
            }
        }
    }
    return groups
}
```

这不是普通 T2。关键判据是 panic stack：

```text
buildGroups.func2
  -> buildGroups.func1
```

半夜无法从函数名看出哪个是 `appendUser`、哪个是 `ensureGroup`，所以 closure chain 升级为 T1。

### 关键洞察：先统一控制流

直觉反应是把两个 closure 改成 struct method。但更好的问题是：

> 这些 helper 是否只是因为外层分支太多？如果先把分支归一成数据，helper 是否会消失？

观察分支：

- 空 lane：只确保 group 存在，不挂 userID
- userID 有 sources：挂到 sources
- userID 没 sources：fallback 到 row.Name

把"这个 userID 应该落到哪些 group"归一成 `dests []string`，控制流就能合并。

### 重构后

```go
func buildGroups(rows []*RecallRow) []Group {
    groups := make([]Group, 0, len(rows))
    groupIndex := make(map[string]int, len(rows))

    for _, row := range rows {
        if row == nil {
            continue
        }

        if len(row.UserIDs) == 0 {
            name := row.Name
            if strings.TrimSpace(name) == "" {
                continue
            }
            if _, ok := groupIndex[name]; !ok {
                groupIndex[name] = len(groups)
                groups = append(groups, Group{Name: name})
            }
            continue
        }

        for _, userID := range row.UserIDs {
            if userID <= 0 {
                continue
            }

            dests := row.Sources[userID]
            if len(dests) == 0 {
                dests = []string{row.Name}
            }

            for _, dest := range dests {
                if strings.TrimSpace(dest) == "" {
                    continue
                }
                idx, ok := groupIndex[dest]
                if !ok {
                    idx = len(groups)
                    groupIndex[dest] = idx
                    groups = append(groups, Group{Name: dest})
                }
                groups[idx].UserIDs = append(groups[idx].UserIDs, userID)
            }
        }
    }
    return groups
}
```

结果：

- 没有局部 closure 变量。
- 没有 closure chain。
- "ensure group + append user" 只在主循环里出现一次。
- `dests = []string{row.Name}` 把多个分支变成数据归一化。

## Micro Cases

### request-scoped async work 切断 context

```go
func report(ctx context.Context, groups []Group) {
    trpc.Go(context.Background(), 5*time.Second, func(ctx context.Context) {
        reportGroups(ctx, groups)
    })
}
```

这是 T1 检查点。`context.Background()` 切断 caller 的 trace、deadline、cancel。只有明确 detach 的后台任务可以例外，而且名字或注释必须写出 owner 和 timeout。

### async closure 捕获持续变化的 request state

```go
func reportAll(ctx context.Context, groups []Group) {
    batch := make([]Group, 0, len(groups))
    for _, group := range groups {
        batch = append(batch, group)
        trpc.Go(ctx, 5*time.Second, func(ctx context.Context) {
            reportBatch(ctx, batch)
        })
    }
}
```

这是 T1 检查点。异步 closure 捕获外层还会继续 append 的 `batch`，reader 需要推断 goroutine 看到的是哪个版本。优先在 launch 前 snapshot：

```go
func reportAll(ctx context.Context, groups []Group) {
    batch := make([]Group, 0, len(groups))
    for _, group := range groups {
        batch = append(batch, group)
        snapshot := append([]Group(nil), batch...)
        trpc.Go(ctx, 5*time.Second, func(ctx context.Context) {
            reportBatch(ctx, snapshot)
        })
    }
}
```

## 取舍说明

- 两个 report 函数各自保留 `if err != nil log...` 是可接受重复。抽一个 helper 会重新引入 callback / hidden async。
- `trpc.Go` callback 仍是匿名 func，因为这是 API 形态强制。callback body 内只调用具名函数或少量直白逻辑，不再嵌套 closure。
- `buildGroups` 主循环还有多层嵌套，但每层是有业务意义的迭代轴。它不是"为了灵活"引入的间接层。

判断口诀：盯着 panic stack 想——这一帧叫什么名字？如果是 `func1` / `func2` 这种序号名，就是 T1，不论它发生在函数内还是跨函数。
