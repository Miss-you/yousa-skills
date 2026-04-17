# README 可发现性审计报告

> **审计日期**：2026-04-17
> **审计版本**：README.md @ HEAD
> **审计人**：以 skill 用户视角执行 `readme-discoverability-audit-sop.md`

---

## 摘要

- **发现问题数**：6 个（P0 ×2, P1 ×3, P2 ×1）
- **核心结论**：当前 README.md 采用**单一表格平铺**所有 skill，没有按用户场景分组，导致非编码类 skill（内容创作、学习、数据抓取）的可发现性严重不足。同时，部分 skill 的强制依赖关系在 README 中完全不可见。

---

## 问题清单

### P0：用户可能找不到需要的 skill

#### P0-1：README 缺少场景分组，所有 skill 平铺在一个 13 行表格中

**证据**：

```markdown
## Skills

| Skill | Description |
|-------|-------------|
| [explaining-completed-work](skills/explaining-completed-work/) | Explain finished work with a Feynman-style walkthrough... |
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux... |
...（共 13 行）
```

**影响**：

- 用户想 "找文章例子" 时，需要在表格中逐行扫描，看到第 5 行才发现 `two-mirror-examples`，且光看名称和描述无法立刻理解它与 "找例子" 的关系。
- 用户想 "学习源码" 时，`creating-sourcecode-learning-sops` 被放在表格末尾（第 13 行），位置不直观。

**修复建议**：

在 `docs/readme/skills.json` 中增加 `category` 字段，并修改 `docs/readme/templates/README.*.md.tmpl`，将 skill 按场景分组渲染。最小可行分组：

- **学习与理解**：`creating-sourcecode-learning-sops`, `explaining-completed-work`
- **内容创作与校验**：`zh-proofreading`, `two-mirror-examples`, `structural-integrity-scan`, `social-strategist`
- **数据抓取与归档**：`cdp-page-to-md`
- **批量任务调度**：`tmux-dispatch`
- **开发工作流**：`secret-scan`, `writing-commit`, `writing-contextual-todos`, `pr-review-autofix`, `monitoring-pr-ai-reviews`

---

#### P0-2：`two-mirror-examples` 的名称和描述对非专业用户过于抽象

**证据**：

- `skills.json` 英文描述：`"Find persuasive examples for a thesis using distant and near mirrors that share the same underlying mechanism."`
- `SKILL.md` 触发词很明确："当用户需要为某个主题/观点找有说服力的例证时使用"
- 但 README 中完全没有这些触发词。

**影响**：

一个普通用户（甚至是一个想写文章找例子的用户）看到 `two-mirror-examples` 这个名称和 "distant and near mirrors" 的描述，大概率会跳过它，不知道这正是自己需要的 skill。

**修复建议**：

在 `skills.json` 中为该 skill 增加场景化描述（不改变原意，但增加触发场景）：

```json
{
  "name": "two-mirror-examples",
  "description_en": "Find persuasive examples for a thesis. Use when you need high-insight illustrations that combine historical depth (distant mirror) with everyday hidden patterns (near mirror).",
  "description_zh": "为文章论点寻找高洞见力的例子。适合写文章缺例证、需要既有历史纵深又有日常贴近感的场景。"
}
```

---

### P1：描述不清或依赖关系隐藏

#### P1-1：`writing-commit` 的强制前置依赖 `secret-scan` 在 README 中完全不可见

**证据**：

- `skills/writing-commit/SKILL.md` 明确声明：`**REQUIRED SUB-SKILL:** Use \`secret-scan\` before \`git commit\``
- 但 `README.md` 中 `writing-commit` 的描述只字未提 `secret-scan`：
  `Create local git commits by deriving scope and message from repository evidence, with secret scanning and verification gates.`

**影响**：

用户可能只安装了 `writing-commit`，在使用过程中发现它调用了 `secret-scan` 但自己并没有安装，导致执行失败或行为异常。或者更糟：用户误以为 "with secret scanning" 是内置的，不需要单独安装 `secret-scan`。

**修复建议**：

方案 A（推荐）：在 `skills.json` 中增加 `requires` 字段，在 README 模板中渲染为标签：

```markdown
| [writing-commit](skills/writing-commit/) | Create local git commits... | `secret-scan` (required) |
```

方案 B（快速修复）：在 `writing-commit` 的描述中显式提及：
`Create local git commits... (requires secret-scan to be installed first).`

---

#### P1-2：`tmux-dispatch` 的描述使用了过多技术黑话

**证据**：

- `skills.json` 英文描述：`"Orchestrate multiple Claude Code processes via tmux for parallel batch task processing, with work-stealing scheduling and built-in quality gates."`
- 对普通用户来说，"orchestrate"、"work-stealing"、"quality gates" 都是门槛。

**影响**：

用户有 "批量处理 20 个文件" 的需求时，看到这段描述可能会因为术语门槛而忽略这个 skill。

**修复建议**：

```json
{
  "name": "tmux-dispatch",
  "description_en": "Batch-process many independent tasks in parallel using multiple Claude Code workers. Useful when you have a list of items (papers, files, URLs) to analyze or transform together.",
  "description_zh": "批量并发处理多个独立同质任务。当你有一堆文件/论文/链接需要逐个分析，又嫌单次 prompt 处理太慢或质量下降时使用。"
}
```

---

#### P1-3：`monitoring-pr-ai-reviews` 和 `pr-review-autofix` 的关系没有说明

**证据**：

- `pr-review-autofix`："Watch open PRs for AI code review comments and auto-fix them from local cron."
- `monitoring-pr-ai-reviews`："Use when implementation is already complete, a GitHub PR exists or must be opened, and follow-up work is still needed because Copilot or other AI review comments may arrive after the initial push."

**影响**：

用户看到这两个 skill 会困惑：它们都处理 PR AI review，到底该用哪个？

实际上：
- `pr-review-autofix` 是**自动化**（本地 cron 自动修复+合并）。
- `monitoring-pr-ai-reviews` 是**半自动化**（PR 已开，需要持续监控、评估、手动修复）。

但 README 没有说明这个区别。

**修复建议**：

在开发工作流分组中，将这两个 skill 放在一起，并增加一句说明：

```markdown
**PR AI Review 处理**
- `pr-review-autofix`：全自动（本地 cron 监控并自动修复 review 评论）。
- `monitoring-pr-ai-reviews`：半自动（PR 已创建，需要持续评估和手动处理 AI review 意见）。
```

---

### P2：格式或维护性优化

#### P2-1：`skills.json` 描述与 `SKILL.md` frontmatter 存在细微不一致

**证据**：

| Skill | `skills.json` 描述 | `SKILL.md` frontmatter description | 差异 |
|------|-------------------|-----------------------------------|------|
| `monitoring-pr-ai-reviews` | `...follow-up work is still needed because Copilot or other AI review comments may arrive after the initial push.` | `...follow-up work is still needed because Copilot or other AI review comments may arrive after the initial push.` | 一致 |
| `writing-commit` | `...with secret scanning and verification gates.` | `Use when creating local git commits in codetok from existing changes, especially when scope, staging, verification, or message clarity could drift.` | **不一致**：SKILL.md 提到了 `codetok`（内部术语），且未在 README 描述中体现 "verification gates" 的具体含义。 |

**影响**：

虽然大部分描述一致，但 `writing-commit` 的 `SKILL.md` frontmatter 使用了 "codetok" 这个看起来是内部项目的术语。如果 `skills.json` 是从 `SKILL.md` 复制来的，说明复制时做了 sanitize，但 "verification gates" 对普通用户仍然过于抽象。

**修复建议**：

统一维护 `skills.json` 作为 README 的单一数据源，定期同步 `SKILL.md` 的触发场景到 `skills.json`，但避免把内部术语带入 README。

---

## 修复优先级与建议行动

| 优先级 | 行动项 | 涉及文件 |
|-------|-------|---------|
| **P0** | 在 README 模板中增加场景分组 | `docs/readme/templates/README.en.md.tmpl`, `docs/readme/templates/README.zh-CN.md.tmpl`, `docs/readme/skills.json`（增加 `category`） |
| **P0** | 重写 `two-mirror-examples` 的描述，增加 "找例子/写文章缺例证" 的触发场景 | `docs/readme/skills.json` |
| **P1** | 为 `writing-commit` 标注 `secret-scan` 依赖 | `docs/readme/skills.json` 或模板 |
| **P1** | 简化 `tmux-dispatch` 的描述，降低术语门槛 | `docs/readme/skills.json` |
| **P1** | 在 README 中说明 `pr-review-autofix` 与 `monitoring-pr-ai-reviews` 的区别 | `docs/readme/templates/README.*.md.tmpl` |
| **P2** | 建立 `skills.json` ↔ `SKILL.md` frontmatter 的定期同步检查机制 | `AGENTS.md` 或 contribute-skill 工作流 |

---

## 验收检查

修复完成后，按以下清单验证：

- [ ] 打开 `README.md`，能在 10 秒内找到 "学习源码" 和 "写文章找例子" 对应的 skill。
- [ ] `writing-commit` 旁边有 `secret-scan` 依赖提示。
- [ ] `tmux-dispatch` 的描述中没有 "work-stealing" 等黑话，或黑话旁边有解释。
- [ ] `pr-review-autofix` 和 `monitoring-pr-ai-reviews` 不在表格中孤立存在，而是有上下文说明它们的关系。
- [ ] 运行 `python3 scripts/render_readmes.py --check` 通过。
