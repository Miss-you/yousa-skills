---
name: go-3am-debuggable
description: >-
  评审或新写 Go 代码时，用“凌晨 3 点能 debug”原则检查 panic stack 可读性、异步边界可见性、mock-only 间接层、callback 参数、闭包链、隐藏 goroutine 和单 caller 包装。
---

# Go 3AM-Debuggable

## 一句话原则

**代码的真正成本在凌晨 3 点告警响的时候。** 每加一层间接，stack trace 多一帧 `func1.func2`，半夜你不知道哪一帧是你的。"灵活"和"可调试"经常冲突。

本 skill 只看一件事：这段 Go 代码会不会让维护者在压力状态下看不清调用关系、异步归属、错误归属或 panic 栈帧。

## Non-Goals

不要把本 skill 扩成通用 Go review checklist。除非它们直接造成下面的 3AM 失败面，否则不输出这些问题：

- receiver 命名、package 命名、doc comment、pointer/value 风格、named return
- 泛泛的 `%w` 错误包装建议、table test 风格、exported API 文档、package 分层
- gofmt/import/nit、广义资源管理、依赖选择、"不像 Go" 这类宽泛风格问题

这些可以属于另一个 `go-maintainability-review` skill；这里默认不报。

## 判断问题

看到 helper、closure、callback、goroutine、mock seam 时先问：

1. 如果这里 panic，栈帧叫什么名字？是业务函数名，还是 `func1.func2`？
2. caller 一眼能看出这是异步吗？
3. 谁拥有 cancel、timeout、error、panic、生命周期？
4. 这层间接是真实生产能力，还是只为测试 / mock / "灵活" 服务？
5. 复制 5 行是否比抽 helper 让调用图更平？
6. 匿名 func 是否捕获了 caller 还会继续修改的 map/slice/pointer/error？

## 优先级分级

| Tier | 含义 | 处理 |
|------|------|------|
| **T1（硬性，必清）** | 直接破坏 stack trace、异步可见性、错误归属、测试结构 | 看到就改。问"怎么改成本最低"，不问"要不要改"。 |
| **T2（应修）** | 削弱压力状态下的扫读和改动安全，但 panic 栈仍基本可读 | 默认应改。保留时说明真实收益和代价。 |

不要引入 `Blocker/Major/Minor/Nit` 另一套等级；本 skill 只用 T1/T2。

## T1：必清，按失败面分类

### #1. 栈帧失名：不允许闭包套闭包和闭包链

panic 栈、火焰图、debugger 单步都依赖函数名。`.func1.func2.func3` 这种栈帧名半夜读不懂。

具体禁止：

- **嵌套匿名 func**：`func(...) { ... func(...) { ... } }`
- **闭包链调用**：同一函数内定义 `a := func(...)`、`b := func(...)`，且 `b` 内部调 `a`
- **异步 callback 体内再传匿名 callback**：`trpc.Go(ctx, t, func(ctx){ ... someFn(func(){...}) })`
- **跨异步边界捕获可变 request state**：goroutine/callback 捕获外层继续修改的 map、slice、pointer、`err` 变量等

单个局部 closure 本来是 T2；一旦它链到另一个 closure、藏住异步归属、或捕获会跨 caller 生命周期的可变状态，升级为 T1。

修法优先级：**统一控制流消掉 helper 理由 → 内联 → 提成具名函数 → 抽 builder struct/method**。struct 是 fallback，不是第一反应。

### #2. 异步边界必须可见、可归属

`go func`、`trpc.Go`、`errgroup.Go` 必须出现在 caller 函数体里，或被一个名字明确的 `Async` / `Go` / `Background` helper 包住。caller 不能误以为这是同步函数。

```go
// ✅ caller 一眼看见异步边界
trpc.Go(ctx, 5*time.Second, func(ctx context.Context) {
    reportXxx(ctx, groups)
})

// ❌ 异步藏在普通 helper 里
reportXxx(ctx, groups) // 内部偷偷 trpc.Go
```

异步边界还必须交代归属：

- 谁负责 cancel / timeout？
- error 是返回、记录、上报，还是明确 best-effort 丢弃？
- panic 是否由框架接住，还是需要 recover/report？
- goroutine 什么时候退出？

禁止在 request-scoped async work 中随手改成 `context.Background()` / `context.TODO()`，这会切断 trace、deadline、鉴权、cancel。只有明确 detach 的后台任务可例外，名字或注释要写出 owner 和 timeout，例如 `startBackgroundReport...`。

允许的例外：helper 名字含 `Async` / `Go` / `Background`，且 helper 内部不再接 `func()` 参数；否则会叠加 #1 和 #4。

### #3. 不为测试加间接层

项目用 `bytedance/mockey` 时，runtime 可以直接 patch 包函数、method、闭包。禁止这种纯测试壳：

```go
// ❌ 反例（mock-only fake seam）
var (
    reportLogFunc   = tlog.ReportLog
    trpcGoFunc      = trpc.Go
    buildGroupsFunc = buildGroups
)
```

直接 `mockey.Mock(tlog.ReportLog).To(...).Build()`。每多一个 `xxxFunc` 包装，读者都要猜"这是真函数还是测试钩子？"。

唯一豁免：mock 目标是 method value 且对象尚未实例化，必须提前替换。其他一律删。

### #4. 不把"怎么做"作为 callback 参数传给 helper

传数据，不传 closure。

```go
// ❌ caller 把"怎么造数据"包成 closure 传进去
func reportAsync(ctx context.Context, buildFn func() []Group) { ... }

// ✅ caller 自己造好或在可见的 goroutine body 里造好，再传数据
func reportAsync(ctx context.Context, groups []Group) { ... }
```

豁免只有两个：

- 构造非常昂贵，且大多数路径会跳过
- 构造依赖目标 goroutine 才存在的上下文

"想让构造也在 goroutine 里跑"不算豁免；把构造代码写进 caller 可见的 goroutine body 即可。

## T2：应修

### #5. 单 caller 包装 = 带间接的 inline

包级 helper 只有 1 个生产调用点时，通常是过度提取。inline 它，等真有第二个 caller 再抽。

豁免：API handler、cron entrypoint、接口实现、测试入口等天然入口，即使单 caller 也合理。

### #6. 单层局部闭包变量

`xxx := func(...) {...}` 把闭包赋给变量，panic 栈帧显示 `.func1` 而非 `xxx`。

修法优先级：

1. 不捕获本地可变状态 → 提成包级具名函数
2. 因为外层多个分支相似才写 closure → 先用 #8 统一控制流
3. 真需要持有状态又要复用 → 抽 builder struct，闭包变 method
4. 小于等于 3 行、单次使用、不持有重要 captured state → 可保留匿名 func

同一函数出现 2 个以上局部 closure 时，必须检查是否互相调用；互调就是 T1 #1。

### #7. 重复 < 错误抽象

两个 caller 共享 5 行 `trpc.Go(ctx, timeout, func(ctx){...})` 壳子时，复制通常比抽 helper 好。

抽象阈值：**至少 3 个 caller，且共用逻辑不少于 10 行有意义代码**。低于这个阈值，优先复制；复制的两份可以独立演化，抽象会把读者拖进 callback/helper 调用图。

### #8. 看到 helper closure，先统一控制流

不要先把闭包机械改成 struct method。先问：

> helper 是否只是因为外层分支太多？能不能把分支归一成数据，再用一个主循环处理？

典型 pattern：多分支都是"对某个名字 ensure + append"。先把目标名归一成 `dests []string`，再统一进入 `for _, dest := range dests`。这样 helper 往往直接消失。

如果读者必须在长函数里追踪多个 map/slice/index 的远距离变更，或多个分支各自偷偷改同一组 accumulator，这也是 T2。修法仍然是：**归一数据和控制流 > 内联 > 具名函数 > struct method**。

## 合法匿名 func（不要改）

满足下面两条的匿名 func 是 Go 生态标准用法，不算反模式：

- 外部 API 形态强制：`trpc.Go(ctx, t, func(ctx){...})`、`sort.Slice(s, func(i,j int) bool{...})`、`sync.Once.Do(func(){...})`、`http.HandleFunc(...)`
- 函数体只做薄转发或少量局部表达：调用具名函数、不嵌套其它 func、不内联超过 3 行的业务逻辑

例子：

```go
sort.Slice(items, func(i, j int) bool {
    return items[i].Score > items[j].Score
})
```

## 工作流

### 写新代码

先写直白的同步扁平版，真有 3+ caller 才抽公共函数。

1. 主流程同步、平铺写下来
2. 只在最外层 caller 放 `trpc.Go` / `go func` / `errgroup.Go`
3. 异步 body 内只调用具名函数或少量直白逻辑；不要再传 callback
4. 搜 `func() T` 参数、`xxxFunc = realFn`、局部 `xxx := func`
5. 检查异步 body 是否切断 `ctx`、吞 error、捕获可变 state
6. 对单 caller helper 做 inline；对相似分支优先统一控制流

### Review 已有代码

1. 跑 `bash scripts/scan.sh <go-dir>`，把输出当作可疑线索，不当 gate
2. 先处理 T1：mock-only seam、callback 参数、嵌套匿名 func、闭包链、隐藏/无归属异步边界
3. 再处理 T2：单 caller helper、单层局部 closure、低价值公共壳子、压力状态下难追的 accumulator
4. 对每个 T1，问"最小可行修法是什么"
5. 对每个 T2，问"这层间接的真实收益是什么；inline / 去间接会损失什么；panic 栈帧叫什么"

### 用户问"是不是过度抽象"

按 Tier 输出，不空谈：

1. T1 命中先列，说明对应 3AM 失败面
2. T2 命中随后列，说明是否建议现在改
3. 给 before/after 代码片段
4. 说明改动后 stack frame、异步归属、测试 seam 或调用图具体怎么变平

## 输出格式

review 时每个 finding 至少包含：

- **Tier**：T1 / T2
- **Location**：文件、函数、代码片段；没有精确行号时不要编造
- **失败面**：栈帧失名 / 异步边界不可见 / fake seam / callback inversion / 低价值间接
- **为什么半夜难 debug**：具体说明 stack、trace、context、error、lifecycle 或调用图会怎么变差
- **最小修法**：inline、传数据、显式 async、snapshot、统一控制流、具名函数或 struct fallback
- **Confidence**：High / Medium / Low

不要输出只有"建议优化""可以更清晰"这类没有 3AM 失败面的泛泛意见。

## 参考资料

- **真实 case study**: [references/case-study.md](references/case-study.md) — 脱敏 async report flow 的两轮 before/after。第一轮是跨函数 fake seam / callback / hidden async；第二轮是函数内部 closure chain。
- **扫描脚本**: `bash scripts/scan.sh <go-dir>` — 启发式扫描，始终退出 0：
  - A. [T1] 测试间接函数变量 `var xxxFunc = realFn`
  - B. [T1] callback 参数 `func() T`
  - C. [T1] 嵌套匿名 func
  - D. [T2] 单 caller helper
  - E. [T2→T1?] 局部 closure 变量
  - F/G. [Inspect] 异步边界和 `context.Background/TODO` 线索

中心思想来自 Go 文化里的 **clarity > cleverness**、**explicit > magic**，但本 skill 只保留会影响 3AM 调试的部分。
