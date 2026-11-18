---
name: smart-commit
description: Use when the user wants to commit code in any git repository and get a well-structured commit message generated from the staged/working-tree diff, optionally with a ticket reference (e.g. `[ABC-123]` or a `Refs: #123` footer) and an optional design doc whose technical approach should be summarized. Analyzes the changes, drafts the message, asks for confirmation, then runs git commit. 触发词：commit、提交、git commit、生成 commit log、代码提交、写提交信息。For the codetok repository, use writing-commit instead.
---

# Smart Commit

分析代码改动，生成结构化的 commit message（改动点 + 技术方案），确认后执行 `git commit`。适用于任意 git 仓库。

**核心原则：** commit message 从实际 diff 推导，不靠猜；只提交经过检查、属于同一逻辑改动的文件；提交前必须跑 `secret-scan`。

## When to Use

- 用户要提交代码，并希望自动生成高质量的 commit message
- 用户给了一个工单/需求编号，希望写进 commit header
- 用户给了设计文档，希望 commit message 体现技术方案和取舍

**不适用：**

- codetok 仓库：用 `writing-commit`（无输入、不确认的流程）
- 修改历史提交（`--amend`）、交互式 rebase、`git push`：本 skill 都不做

## 输入参数（均可选）

用户可以在自然语言请求里带上这些"参数"：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--ticket=<ID> <描述>` | 工单/需求引用和简短描述 | `--ticket=ABC-123 修复搜索结果显示旧用户名` |
| `--doc=<路径>` | 设计文档路径 | `--doc=docs/design/order-retry.md` |
| `--yes` / `--no-confirm` | 跳过确认直接提交 | `/smart-commit --yes` |

## 工作流程

### Step 1: 确定工单引用格式（可选）

工单引用是可选的。按以下顺序确定格式，找到即停：

1. 用户在请求里直接给出（如 `--ticket=ABC-123 ...`、`Refs: #123`）
2. 仓库约定：`CLAUDE.md`、`AGENTS.md`、`CONTRIBUTING.md` 里写明的 commit 规范
3. 历史惯例：`git log --format=%s -20`，看 header 是否稳定带有某种引用，例如：
   - `[PROJ-123] <描述>`
   - `<type>: <描述>` + footer `Refs: #123`

处理规则：

- 仓库有引用惯例但用户没给编号：用 `AskUserQuestion` 询问编号和简短描述；用户说没有就省略
- 仓库没有引用惯例且用户没给：直接省略，不要追问，也不要编造编号
- 格式跟随仓库惯例，不要自创新格式

### Step 2: 盘点改动

```bash
git status --short
git diff --cached --name-status   # 暂存区
git diff --name-status            # 工作区
git ls-files --others --exclude-standard   # 未跟踪文件
```

- 暂存区和工作区都为空：提示"没有改动，无需提交"，结束
- 已暂存的文件视为用户意图；检查未暂存改动是否属于同一逻辑改动
- 混入了无关改动：停下来问用户提交范围，不要一起提交

### Step 3: 分析改动内容

```bash
git diff --cached --stat
git diff --cached        # 暂存区为空时改看 git diff
```

- 关注关键改动，不逐行复述
- 未跟踪文件先读内容再决定是否纳入
- 从以下角度提炼改动点：架构（分层、模块拆分、接口变更）、功能（新增/优化/错误处理）、性能（算法、缓存、并发、索引）、可观测性（metrics、日志、链路追踪）、安全（权限、校验、敏感信息）、可维护性（重构、测试、文档）

### Step 4: 读取设计文档（可选）

来源：用户指定的 `--doc`；否则看本次 diff 中改动的 Markdown，或 `docs/`、`doc/`、`<module>/docs/` 下与改动明显相关的文档。找不到就跳过，不要硬凑。

从文档中只提取能放进 commit message 的内容：

- 架构选型（如"用 Redis ZSET 做延迟重试队列"）
- 性能优化点（如"批量查询减少 N+1"）
- 设计取舍及原因（如"牺牲实时性换取稳定性"）

### Step 5: 生成 Commit Message

格式（header 跟随 Step 1 确定的惯例；没有工单引用就用仓库的常规 header，如 Conventional Commits）：

```
<header：工单引用（可选）+ 需求描述，或 <type>: <具体结果>>

<改动总结>：
- <改动点 1>
- <改动点 2>
- <改动点 3>

[Refs: #123]   ← 仅当仓库惯例是 footer 引用时
```

规则：

- 总长度控制在 10 行左右
- 改动总结一句话说明改动类型；列 3-5 个改动点，每点一行，以 `-` 开头
- 先写行为/业务效果，再写实现细节；有设计文档时补一条技术方案
- 避免 `update code`、`misc fixes`、只列文件名这类空洞描述

| 改动类型 | 描述方式 | 示例 |
|---------|---------|------|
| 新增功能 | 新增 XX 功能/模块 | 新增支付失败重试队列 |
| 功能优化 | 优化 XX 性能/逻辑 | 优化订单列表查询性能 |
| Bug 修复 | 修复 XX 问题 | 修复搜索结果显示旧用户名的问题 |
| 代码重构 | 重构 XX | 重构 DAO 层 |
| 可观测性 | 新增 XX 监控/日志 | 新增缓存刷新失败 metrics |
| 配置调整 | 调整 XX 配置 | 重试次数调整为 3 次 |

### Step 6: 确认

展示生成的 commit message 和将要提交的文件列表（`git diff --cached --name-only`），然后用 `AskUserQuestion` 询问（用户指定 `--yes` / `--no-confirm` 时跳过）：

- 确认提交
- 修改 commit message
- 取消

### Step 7: 提交

1. 如需暂存，只 `git add <明确的文件路径>`，不要 `git add .` / `git add -A`
2. 运行 `secret-scan` skill 检查待提交内容；有发现就停下，先处理敏感信息
3. 用带单引号的 heredoc 提交，避免 shell 变量替换和特殊字符问题：

   ```bash
   git commit -F - <<'EOF'
   <commit message>
   EOF
   ```

4. 展示结果：`git log -1 --stat`

### 异常处理

| 情况 | 处理 |
|------|------|
| 没有改动 | 提示无需提交，结束 |
| pre-commit hook 失败 | 展示错误，建议修复后重新提交；不要用 `--no-verify` 绕过 |
| secret-scan 有发现 | 停止提交，列出发现项 |
| 用户取消 | 提示"已取消提交"，不做任何改动 |

## 示例

### 示例 1：带工单引用和设计文档

```
用户: /smart-commit --ticket=ABC-123 修复搜索结果显示旧用户名的问题 --doc=docs/design/cache-refresh.md

助手:
仓库惯例（git log）：`[ABC-123] <描述>`

暂存区改动：
M  services/search/metrics.go
M  services/search/refresh.go

改动分析：
- 新增 2 个 metrics counter
- refreshCacheEntry 失败时上报 metrics 并打印 warn 日志
- 重试用尽时上报 metrics 并打印 error 日志

设计文档要点：失败条目进入延迟重试队列，最多重试 3 次

生成的 Commit Message：
------------------------------------------
[ABC-123] 修复搜索结果显示旧用户名的问题

新增缓存刷新失败监控：
- 新增 2 个 metrics：刷新失败、重试用尽
- 刷新失败时上报 metrics 并打印 warn 日志
- 失败条目进入延迟重试队列，重试 3 次用尽后打印 error 日志
------------------------------------------

将要提交的文件：
- services/search/metrics.go
- services/search/refresh.go

[询问确认] → 用户: 确认提交
[运行 secret-scan：无发现]

提交成功：
commit a1b2c3d
 services/search/metrics.go |  5 +++++
 services/search/refresh.go | 24 ++++++++++++++++++++++--
 2 files changed, 27 insertions(+), 2 deletions(-)
```

### 示例 2：仓库无工单惯例

```
用户: 帮我提交一下

助手:
[git log 显示仓库使用 Conventional Commits，无工单引用 → 省略引用，不追问]

生成的 Commit Message：
------------------------------------------
feat: add retry queue for failed payment callbacks

- enqueue failed callbacks into a delayed retry queue (max 3 attempts)
- emit a metric and error log when retries are exhausted
- add unit tests for retry scheduling
------------------------------------------

[询问确认 → secret-scan → git commit → git log -1 --stat]
```

## Common Mistakes

| 错误 | 正确做法 |
|------|---------|
| 仓库没有工单惯例却追问或编造编号 | 省略引用 |
| 自创引用格式（如仓库用 footer `Refs:` 却写成标题前缀） | 跟随 `git log` / CLAUDE.md 中的惯例 |
| `git add .` 把无关改动一起提交 | 只暂存检查过的、同一逻辑改动的文件 |
| 只看暂存区，漏掉同一改动必需的未暂存文件 | 分别检查暂存、未暂存、未跟踪文件 |
| commit message 逐行复述 diff 或只列文件名 | 写行为效果 + 3-5 个关键改动点 |
| 跳过 secret-scan | 提交前必须运行 |
| pre-commit 失败后用 `--no-verify` 绕过 | 展示错误，修复后重新提交 |
| 顺手 `--amend` 或 `git push` | 本 skill 只做一次新提交 |
