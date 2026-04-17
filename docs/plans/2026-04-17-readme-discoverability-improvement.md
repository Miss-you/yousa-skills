# 任务：改进 README 可发现性（按场景分组与依赖明示）

> **创建日期**：2026-04-17
> **关联审计报告**：`readme-discoverability-audit-report-2026-04-17.md`
> **关联 SOP**：`readme-discoverability-audit-sop.md`
> **优先级**：P0

---

## 背景

本仓库目前包含 13 个 skill，其中大部分（如内容创作、学习、数据抓取、社交分析）并非编码类 skill。然而当前 `README.md` 将所有 skill 平铺在一个大表格中，导致：
- 非编码 skill 被开发类 skill 淹没，用户难以按需定位。
- 部分 skill 名称/描述过于抽象，用户无法将自身需求映射到对应 skill。
- 强制依赖关系（如 `writing-commit` 依赖 `secret-scan`）在 README 中完全不可见，单独安装时可能出错。

---

## 核心发现与对应修改建议

### 1. README 缺少场景分组，非编码 skill 可发现性差

**现状**：13 个 skill 平铺在一个大表格里。用户带着「我想系统学习一段代码」或「帮我找几个好例子」的需求来，需要逐行扫描整个表格。

**建议**：按用户场景分组展示，最小可行分组如下：

| 场景分组 | 对应 Skill |
|---------|-----------|
| **学习与理解** | `creating-sourcecode-learning-sops`, `explaining-completed-work` |
| **内容创作与校验** | `zh-proofreading`, `two-mirror-examples`, `structural-integrity-scan`, `social-strategist` |
| **数据抓取与归档** | `cdp-page-to-md` |
| **批量任务调度** | `tmux-dispatch` |
| **开发工作流** | `secret-scan`, `writing-commit`, `writing-contextual-todos`, `pr-review-autofix`, `monitoring-pr-ai-reviews` |

**关键要求**：
- 分组标题使用「用户语言」而非技术名词（如用「学习与理解」而非 Knowledge Skills）。
- 每个分组前用一句话说明「这个分组解决什么问题」。
- 非编码类分组（学习、内容、数据）应放在显眼位置，避免被开发类 skill 淹没。

---

### 2. 部分 Skill 名称/描述太抽象，需求映射困难

**现状示例**：
- `two-mirror-examples`：README 描述为 *"Find persuasive examples for a thesis using distant and near mirrors..."* —— 普通用户根本想不到这是「写文章缺例子时」该用的 skill。
- `tmux-dispatch`：描述使用了 *"orchestrate"、"work-stealing"、"quality gates"* 等技术黑话，非技术用户望而却步。
- `structural-integrity-scan`：聚焦 *"uneven comparisons"*，但没有说明「当你写完对比文章后可以用它来检查逻辑漏洞」。

**建议**：
- 重写 `two-mirror-examples` 描述，增加「写文章缺例子/找例证」的触发场景。
- 简化 `tmux-dispatch` 描述，降低术语门槛，突出「批量并发处理多个独立任务」的场景。
- 每个描述应同时包含：功能（What）、场景（When/Why）、触发词（用户说什么时会激活）。

---

### 3. 强制依赖关系在 README 中完全不可见

**现状示例**：
- `writing-commit` 的 `SKILL.md` 明确要求前置使用 `secret-scan`（`REQUIRED SUB-SKILL: Use secret-scan before git commit`），但 README 里没有任何提示。用户如果只装了 `writing-commit`，可能跳过密钥扫描，导致泄露风险。
- `pr-review-autofix`（全自动：本地 cron 监控并自动修复 review）与 `monitoring-pr-ai-reviews`（半自动：PR 已创建，需持续评估和手动处理）在 README 中孤立存在，用户无法判断该用哪个。

**建议**：
- 在 `skills.json` 或模板中增加依赖标注，例如：
  ```markdown
  | [writing-commit](skills/writing-commit/) | Create local git commits... | `secret-scan` (required) |
  ```
- 将 `pr-review-autofix` 与 `monitoring-pr-ai-reviews` 放在同一分组，并增加上下文说明它们的关系（自动 vs 半自动）。
- 对于 `secret-scan` 这种被多个 skill 依赖的基础能力，考虑在开发工作流分组顶部统一说明：「提交代码前请确保已安装 `secret-scan`」。

---

## 涉及文件

| 文件 | 改动内容 |
|-----|---------|
| `docs/readme/skills.json` | 增加 `category` 字段；重写部分 skill 描述；增加 `requires` 或依赖提示字段 |
| `docs/readme/templates/README.en.md.tmpl` | 支持按 `category` 分组渲染；增加依赖提示列或标签 |
| `docs/readme/templates/README.zh-CN.md.tmpl` | 同上 |
| `scripts/render_readmes.py` | 如需支持新字段（category、requires），同步调整渲染逻辑 |
| `tests/test_render_readmes.py` | 增加/更新测试用例，确保分组和依赖渲染正常 |
| `AGENTS.md` 或 `.claude/skills/contribute-skill/SKILL.md` | 如有必要，更新 skill 贡献工作流，要求新增 skill 时填写 category 和依赖信息 |

---

## 执行步骤（建议顺序）

1. **修改数据源**：先更新 `docs/readme/skills.json`（增加 category、重写描述、标注依赖）。
2. **调整模板**：修改 `README.en.md.tmpl` 和 `README.zh-CN.md.tmpl`，支持按 category 分组输出。
3. **调整渲染脚本**：如模板逻辑变化较大，同步更新 `scripts/render_readmes.py`。
4. **生成 README**：运行 `python3 scripts/render_readmes.py` 生成新的 `README.md` 和 `README.zh-CN.md`。
5. **运行测试**：执行 `python3 -m unittest tests/test_render_readmes.py` 确保通过。
6. **人工验收**：对照下方检查清单，确认改动符合预期。

---

## 验收检查清单

- [ ] 打开 `README.md`，能在 10 秒内找到「学习源码」和「写文章找例子」对应的 skill。
- [ ] `two-mirror-examples` 的描述包含「写文章缺例子/找例证」等触发场景。
- [ ] `tmux-dispatch` 的描述中没有「work-stealing」等黑话，或黑话旁边有解释。
- [ ] `writing-commit` 旁边有 `secret-scan` 依赖提示（如标签、括号标注或分组顶部说明）。
- [ ] `pr-review-autofix` 和 `monitoring-pr-ai-reviews` 不在表格中孤立存在，而是有上下文说明它们的关系（自动 vs 半自动）。
- [ ] 运行 `python3 scripts/render_readmes.py --check` 通过。
- [ ] 运行 `python3 -m unittest tests/test_render_readmes.py` 通过。

---

## 备注

- 本仓库的 README 是**生成式**的，**不要直接编辑 `README.md` 或 `README.zh-CN.md`**。所有改动应通过 `skills.json` + 模板 + 渲染脚本完成。
- 优先修复 P0 问题（场景分组 + 需求映射），P1 问题（依赖关系）可同步处理，避免二次返工。
