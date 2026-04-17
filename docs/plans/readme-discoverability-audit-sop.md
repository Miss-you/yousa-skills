# README 可发现性审计 SOP

> **适用角色**：以 "skill 用户" 视角审视仓库，检查 README.md 是否能在用户有具体需求时，帮助他们快速找到对的 skill，并理解它的作用。
>
> **核心前提**：本仓库大部分 skill 并非用于写代码，而是用于**学习、内容创作、数据抓取、社交分析**等非编码场景。README 必须优先服务这类用户。

---

## 一、审计目标

用户看完 README.md 后，应该能回答三个问题：

1. **这个 skill 是干啥的？** —— 描述是否足够具体，而非抽象的功能名词堆砌。
2. **我有 XX 需求时该用哪个？** —— 用户带着场景来，README 能否按场景快速索引到 skill。
3. **这个 skill 是必要的吗？有前置依赖吗？** —— 是否存在强依赖关系被隐藏，导致用户单独使用某个 skill 时会出错。

---

## 二、前置准备

审计前，必须同时打开以下文件：

- `README.md`（被审计对象）
- `README.zh-CN.md`（如同时维护）
- `docs/readme/skills.json`（README 的数据源）
- `skills/<name>/SKILL.md`（每个 skill 的真实使用说明，尤其关注 `When to Use`、`触发词`、`REQUIRED SUB-SKILL`）

**工具建议**：

```bash
# 快速提取所有 SKILL.md 中的触发关键词和依赖关系
grep -rh -A 2 "description:" skills/*/SKILL.md | grep -E "(触发|Use when|REQUIRED SUB-SKILL)"
```

---

## 三、四步审计流程

### Step 1：场景分组检查（可发现性）

**判断标准**：

README 里的 skill 不应该平铺在一个大表格里。必须按 "用户想做什么" 分组。

推荐的最小分组（根据本仓库实际 skill 集合）：

| 场景分组 | 典型用户诉求 | 本仓库对应 skill |
|---------|------------|----------------|
| **学习与理解** | "我想系统学习这段代码"、"你给我讲讲刚才做了啥" | `creating-sourcecode-learning-sops`, `explaining-completed-work` |
| **内容创作与校验** | "帮我检查下这篇文章"、"给我找几个好例子"、"这段对话怎么回" | `zh-proofreading`, `two-mirror-examples`, `structural-integrity-scan`, `social-strategist` |
| **数据抓取与归档** | "把这个网页存成 markdown"、"这个页面要登录才能看" | `cdp-page-to-md` |
| **批量任务调度** | "我有 20 个文件要逐个分析"、"能不能并发跑" | `tmux-dispatch` |
| **开发工作流** | "我要提交代码"、"帮我盯下 PR review"、"生成 TODO" | `secret-scan`, `writing-commit`, `writing-contextual-todos`, `pr-review-autofix`, `monitoring-pr-ai-reviews` |

**Checklist**：

- [ ] README 是否按上述场景（或等效场景）对 skill 进行了分组？
- [ ] 每个分组前是否有 1 句话说明 "这个分组解决什么问题"？
- [ ] 分组标题是否使用了 "用户语言" 而非 "技术名词"？（例如用 "学习与理解" 而非 "Knowledge Skills"）
- [ ] 非编码类 skill 是否被放在显眼位置，而不是被开发类 skill 淹没？

**如果失败，记录问题**：

```markdown
- [ ] **问题**：README 缺少场景分组，所有 skill 平铺在一个表格中。
  - **影响**：用户有 "找例子" 的需求时，需要在 13 行表格中逐行扫描，无法快速定位到 `two-mirror-examples`。
  - **修复建议**：将 skill 按 "学习/内容/数据/开发" 四大场景分组展示。
```

---

### Step 2：需求映射测试（匹配性）

**方法**：模拟 8 个典型用户诉求，仅凭 README 的描述，测试能否在 15 秒内找到正确 skill。

| 编号 | 用户诉求（内心独白） | 预期 skill | 测试方法 |
|-----|-------------------|-----------|---------|
| A | "我想系统学习一个代码库的功能，生成一份源码阅读指南" | `creating-sourcecode-learning-sops` | 搜索 "learn"、"SOP"、"源码"、"学习" 等词 |
| B | "你刚帮我改完代码，给我讲清楚你到底改了什么" | `explaining-completed-work` | 搜索 "explain"、"completed"、"walkthrough"、"讲解" |
| C | "我要抓取一个需要登录才能看的网页，保存成 markdown" | `cdp-page-to-md` | 搜索 "fetch"、"authenticated"、"markdown"、"登录"、"抓取" |
| D | "我写文章需要一些高洞见力的例子，要有历史纵深感的" | `two-mirror-examples` | 搜索 "example"、"thesis"、"例证"、"例子" |
| E | "我写了篇对比分析的文章，想检查逻辑有没有问题" | `structural-integrity-scan` | 搜索 "comparison"、"scan"、"对比"、"逻辑"、"结构" |
| F | "帮我分析这段聊天记录，对方什么意思，怎么回" | `social-strategist` | 搜索 "dialogue"、"chat"、"对话"、"回复"、"社交" |
| G | "我有 20 篇论文要分析，能不能并发批量处理" | `tmux-dispatch` | 搜索 "batch"、"parallel"、"批量"、"并发"、"tmux" |
| H | "我要提交代码" | `writing-commit` + `secret-scan` | 搜索 "commit"、"git"、"提交" |

**Checklist**：

- [ ] 每个诉求是否都能通过 README 中的关键词直接定位到目标 skill？
- [ ] 如果找不到，是因为关键词缺失，还是因为分组/标题不够直观？
- [ ] 诉求 H（提交代码）是否能同时发现 `secret-scan` 这个强前置依赖？

**如果失败，记录问题**：

```markdown
- [ ] **问题**：诉求 D "找例子" 在 README 中无法快速定位。
  - **实际路径**：用户需要扫描整个表格，看到 `two-mirror-examples` 后仍无法理解它与 "找例子" 的关系。
  - **根因**：README 描述为 "Find persuasive examples for a thesis using distant and near mirrors..."，过于文学化，缺少 "当你写文章需要举例时" 的场景提示。
  - **修复建议**：在分组标题和描述中增加触发场景："写文章缺例子时 → `two-mirror-examples`"
```

---

### Step 3：依赖关系检查（必要性）

**方法**：读取每个 `SKILL.md`，提取其中声明的 `REQUIRED SUB-SKILL` 或显式依赖，检查 README 是否做了对应提示。

本仓库已知的关键依赖：

| Skill | 依赖声明（来源：SKILL.md） | README 是否提示？ |
|------|-------------------------|-----------------|
| `writing-commit` | "REQUIRED SUB-SKILL: Use `secret-scan` before `git commit`" | 待检查 |
| `monitoring-pr-ai-reviews` | "REQUIRED SUB-SKILLS: `github:gh-address-comments`, `receiving-code-review`, `verification-before-completion`" | 待检查 |

**Checklist**：

- [ ] 所有标有 `REQUIRED` 的依赖，README 中是否有标注？
- [ ] 强关联的 skill（如 `pr-review-autofix` 和 `monitoring-pr-ai-reviews`）是否有交叉引用？
- [ ] 对于 `secret-scan` 这种被多个 skill 依赖的基础能力，README 是否将其标识为 "基础/必要"？

**如果失败，记录问题**：

```markdown
- [ ] **问题**：`writing-commit` 强制要求前置使用 `secret-scan`，但 README 中无任何提示。
  - **影响**：用户单独安装 `writing-commit` 后可能跳过密钥扫描，导致泄露风险。
  - **修复建议**：在 `writing-commit` 的描述后增加 `(Requires: secret-scan)` 标签，或在开发工作流分组顶部统一说明："提交代码前请确保已安装 `secret-scan`"
```

---

### Step 4：描述准确性检查（可理解性）

**方法**：逐条对比 `docs/readme/skills.json` 中的描述和对应 `SKILL.md` 的 `description` + `When to Use`。

**判断标准**：

一个好的 README 描述应该同时包含：
1. **功能**（What）
2. **场景**（When / Why）
3. **触发词**（用户说什么时会激活这个 skill）

**当前 README 描述的典型反例**：

- `monitoring-pr-ai-reviews`：描述长达 40+ 词，但缺少 "当你想自动监控 PR review 时" 的简化场景提示。
- `tmux-dispatch`：描述使用了 "work-stealing scheduling" 等技术黑话，对非技术用户不友好。
- `structural-integrity-scan`：描述聚焦 "uneven comparisons"，但没有说 "当你写完对比文章后可以用它来检查逻辑漏洞"。

**Checklist**：

- [ ] 每个 skill 的描述是否在 20 个汉字/单词以内传达了 "这是干啥的"？
- [ ] 每个描述是否包含至少一个触发场景？
- [ ] 名称抽象的 skill（如 `two-mirror-examples`、`tmux-dispatch`）是否有额外的场景说明？
- [ ] `skills.json` 中的描述是否与 `SKILL.md` 的 frontmatter `description` 保持一致？（若不一致，以 `SKILL.md` 为准，因为那是运行时真正被 LLM 读取的）

---

## 四、问题汇总模板

审计完成后，统一输出到以下格式：

```markdown
## 审计结果摘要

- **审计日期**：YYYY-MM-DD
- **审计版本**：README.md @ <commit-hash>
- **发现问题数**：N 个
- **严重程度**：P0（阻碍使用）/ P1（显著影响发现）/ P2（可优化）

## 问题清单

### P0：用户可能找不到需要的 skill

1. ...

### P1：描述不清或依赖关系隐藏

1. ...

### P2：格式或维护性优化

1. ...

## 修复建议（按优先级排序）

1. ...
```

---

## 五、修复执行 SOP

发现问题后，按以下顺序修复：

### 5.1 改数据源，再生成 README

本仓库的 README 是**生成式**的（`docs/readme/skills.json` + `scripts/render_readmes.py`）。**不要直接编辑 `README.md`**。

修复顺序：

1. 修改 `docs/readme/skills.json` 中的描述或分组元数据（如果未来模板支持分组）。
2. 修改 `docs/readme/templates/README.en.md.tmpl` 和 `README.zh-CN.md.tmpl`（如果需要调整结构、增加分组标题或依赖提示）。
3. 运行 `python3 scripts/render_readmes.py`。
4. 运行 `python3 -m unittest tests/test_render_readmes.py` 确保生成逻辑正常。
5. 人工 diff 检查 `README.md` 和 `README.zh-CN.md` 的输出是否符合预期。

### 5.2 最小改动原则

- 优先改 `skills.json` 中的描述文字（影响最小）。
- 如果需要增加分组或依赖提示，再改模板文件。
- 不要一次性重写所有描述，优先修复 P0 和 P1 问题。

---

## 六、验收标准

README 通过本次审计，当且仅当：

- [ ] 存在至少 2 个明确的用户场景分组（如 "学习与理解"、"内容创作"、"数据抓取"、"开发工作流"）。
- [ ] 任意一个非编码类需求（学习/内容/数据）能在 15 秒内通过 README 定位到对应 skill。
- [ ] 所有 `SKILL.md` 中标记为 `REQUIRED` 的依赖，在 README 中有可见提示。
- [ ] `skills.json` 中每个描述与 `SKILL.md` 的 frontmatter `description` 无明显矛盾。

---

## 附录：快速参考 —— 本仓库 skill 触发词速查

| Skill | 用户可能说的话 | 核心场景 |
|------|--------------|---------|
| `creating-sourcecode-learning-sops` | "帮我设计一个学习源码的文档"、"如何系统学习这段代码" | 学习 |
| `explaining-completed-work` | "你刚才做了啥"、"给我讲讲原理"、"为什么这样改" | 学习/理解 |
| `cdp-page-to-md` | "把这个网页存下来"、"需要登录的页面怎么抓" | 数据抓取 |
| `two-mirror-examples` | "给我找几个例子"、"写文章缺例证" | 内容创作 |
| `structural-integrity-scan` | "帮我检查这篇文章的逻辑"、"对比分析有没有问题" | 内容校验 |
| `social-strategist` | "对方什么意思"、"怎么回复"、"帮我分析这段对话" | 社交分析 |
| `zh-proofreading` | "校对"、"查错别字"、"typo 检查" | 内容校验 |
| `tmux-dispatch` | "批量处理"、"并发执行"、"逐个分析" | 批量调度 |
| `writing-commit` | "commit 一下"、"提交代码" | 开发工作流 |
| `secret-scan` | "检查下有没有泄露密钥" | 开发工作流（基础） |
| `writing-contextual-todos` | "写个 TODO"、"记录后续工作" | 开发工作流 |
| `pr-review-autofix` | "自动修复 review"、"盯着这个 PR" | 开发工作流 |
| `monitoring-pr-ai-reviews` | "PR 还有 AI review 要处理" | 开发工作流 |
