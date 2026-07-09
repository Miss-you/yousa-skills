# yousa-skills

这是一个面向 AI 辅助工作流的 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills 精选集合。

[English](README.md) | [简体中文](README.zh-CN.md)

## 技能

| 技能 | 说明 |
|------|------|
| [explaining-completed-work](skills/explaining-completed-work/) | 用费曼式讲解回顾已完成的工作，说明改了什么、怎么工作的、为什么这样选、边界在哪里。 |
| [tmux-dispatch](skills/tmux-dispatch/) | 通过 tmux 编排多个 Claude Code 进程来并行批量处理任务，支持 work-stealing 调度和内建质量门禁。 |
| [social-strategist](skills/social-strategist/) | 分析对话记录或聊天截图中的潜台词、情绪和权力动态，并给出多种回复策略。 |
| [structural-integrity-scan](skills/structural-integrity-scan/) | 扫描并列对比型文章中的不对称比较、隐性偏差和被叙事推动的结论。 |
| [two-mirror-examples](skills/two-mirror-examples/) | 用远镜和近镜寻找能支撑论点的高洞见例子，重点是找同构机制而不是相似故事。 |
| [cdp-page-to-md](skills/cdp-page-to-md/) | 通过 Chrome CDP 获取需要登录或由 JavaScript 渲染的网页，并转换成干净的 Markdown。 |
| [zh-proofreading](skills/zh-proofreading/) | 逐段扫描中文文章的错别字、语病、标点问题和中英混排格式问题。 |
| [secret-scan](skills/secret-scan/) | 在提交、推送或创建 PR 之前扫描已暂存或已修改的文件，检查是否泄露密钥。 |
| [pr-review-autofix](skills/pr-review-autofix/) | 通过本地定时任务盯住打开的 PR，发现 AI code review 评论后自动修复。 |
| [monitoring-pr-ai-reviews](skills/monitoring-pr-ai-reviews/) | 当实现已经完成、GitHub PR 已存在或即将创建，而且还需要继续跟进 Copilot 或其他 AI review 评论时使用。 |
| [writing-commit](skills/writing-commit/) | 通过检查仓库状态自动推导提交范围和提交信息来创建本地 git commit，内置密钥扫描和验证门禁。 |
| [writing-contextual-todos](skills/writing-contextual-todos/) | 将 TODO 文档写成交接产物，包含完整上下文、验收标准和来源归属，让未来读者无需聊天记录即可理解。 |
| [creating-sourcecode-learning-sops](skills/creating-sourcecode-learning-sops/) | 创建经过验证的多阶段源码学习 SOP，结合学习科学和动手代码验证，系统性地学习代码库中的某个功能。 |
| [checking-upstream-before-work](skills/checking-upstream-before-work/) | 开工前先检查上游仓库是否已有相关的 open PR 或近 5 天内合入的 PR，避免重复劳动或和他人冲突。 |
| [designing-state-machines](skills/designing-state-machines/) | 设计和评审生命周期状态机，覆盖持久状态字段、异步流程、重试、终态、并发控制和可观测性。 |
| [writing-open-source-prs](skills/writing-open-source-prs/) | 为开源项目的 Pull Request 撰写、复核和更新描述，让维护者无需先读 diff 就能掌握 issue 背景、行为变化、测试覆盖、取舍和 CI 状态。 |
| [judging-compounding-value](skills/judging-compounding-value/) | 用六维框架判断一项活动、技能、项目、工作流或职业选择是否具有复利价值，还是主要属于一次性消耗。 |
| [auditing-dead-code](skills/auditing-dead-code/) | 通过静态分析、引用分类和入口/接口风险对账来审计死代码，避免仅凭 grep 计数就判定某个符号可以删除，尤其针对 RPC、配置、生成代码和导出 API 等场景。 |
| [go-3am-debuggable](skills/go-3am-debuggable/) | 用“凌晨 3 点能 debug”的视角评审或编写 Go 代码，聚焦 panic stack 可读性、异步归属、mock-only seam、callback 反转、闭包链和低价值间接层。 |
| [python-3am-debuggable](skills/python-3am-debuggable/) | 用“凌晨 3 点能 debug”的视角评审或编写 Python 代码，聚焦 traceback、异步/后台任务归属、异常语义、副作用、可变状态捕获、动态分发和低价值间接层。 |
| [research-question-framing](skills/research-question-framing/) | 在开始读源码、做调研或架构探究之前，把模糊的研究主题转化为带问题树、证据矩阵（含「能证明 / 不能证明」两列）和验证场景的研究纲要。 |
| [transcript-to-deep-minutes](skills/transcript-to-deep-minutes/) | 通过多 agent 流水线将带说话人标签的会议和圆桌转录提炼成「判断→思维模型→实证案例」三层的结构化深度纪要。 |
| [minutes-sensitive-scan](skills/minutes-sensitive-scan/) | 在对外发布前按查塔姆宫规则扫描并脱敏会议纪要，去除人名机构、人事信号和可反查的指纹细节。 |
| [youtube-video-analysis](skills/youtube-video-analysis/) | 对 YouTube 视频做四步深度分析：抓字幕 → 结构化总结 → 联网事实核查 → 输出「合理/不合理/启发」判断报告。 |
| [research-to-knowledge-note](skills/research-to-knowledge-note/) | 把已完成的分析结果与联网检索证据整合成可长期归档的中文知识笔记，带元信息、证据表、方法论、复现方法和 AC 自检表。 |
| [claim-verification](skills/claim-verification/) | 对一段陈述、视频、文章或分析报告做真实性验收：拆解论点链 → 联网核查关键数据 → 找出强反方证据 → 输出 8 维度红绿灯诊断与最终客观判断。 |
| [narrative-truth-audit](skills/narrative-truth-audit/) | 对金融、宏观、政经或商业叙事做真实性与逻辑性校验：拆命题 → 查数据 → 验结构 → 找反例 → 打分 → 输出可决策/观察/拒绝的明确验收结论。 |
| [deep-research-verifier](skills/deep-research-verifier/) | 用「研究-回答-验证」四阶段框架回答需要多源信息支撑的复杂问题：解构问题并设计 SOP → 按维度搜集证据 → 交叉验证事实与逻辑 → 输出经验证的结论与证据追踪表。 |
| [minutes-quality-eval](skills/minutes-quality-eval/) | 对照原始转录评估/对比会议纪要质量：按风险优先级抽查保真度、盘点覆盖度、扫描九类失真模式，输出多维度加权打分与失真清单。 |
| [eacc-chat-daily-distill](skills/eacc-chat-daily-distill/) | 按日提炼投资群聊记录，产出带溯源、按发言人权重加权的 Markdown 笔记，聚焦对投资决策有价值的方法论、关键判断与 Know-how，并强制执行数据验收。 |

## 安装

克隆仓库后运行 `./install.sh`，它会把 `skills/` 下的全部 skill 同步到你个人的 Claude、Codex 与 Trae skill 目录（`~/.claude/skills`、`~/.codex/skills` 和 `~/.trae-cn/skills`）。

```bash
git clone https://github.com/Miss-you/yousa-skills.git
cd yousa-skills
./install.sh                                  # 安装全部 skill 到 Claude、Codex 与 Trae
./install.sh writing-commit zh-proofreading   # 只安装指定的 skill
./install.sh --claude-only                    # 只装到 ~/.claude/skills
./install.sh --codex-only                     # 只装到 ~/.codex/skills
./install.sh --trae-only                      # 只装到 ~/.trae-cn/skills
./install.sh --claude-only --trae-only        # 组合 --*-only 标志，可装到任意子集
./install.sh --backup                         # 覆盖前把旧版本备份到 <target>.bak/
./install.sh --dry-run                        # 只打印计划，不动文件
./install.sh --list                           # 列出所有可装 skill
```

```powershell
git clone https://github.com/Miss-you/yousa-skills.git
cd yousa-skills
.\install.ps1                                  # install all skills to Claude, Codex, and Trae
.\install.ps1 writing-commit zh-proofreading   # install only the named skills
.\install.ps1 --claude-only                    # only ~/.claude/skills
.\install.ps1 --codex-only                     # only ~/.codex/skills
.\install.ps1 --trae-only                      # only ~/.trae-cn/skills
.\install.ps1 --claude-only --trae-only        # combine --*-only flags to install to a subset
.\install.ps1 --backup                         # before overwriting, move the old skill to <target>.bak/
.\install.ps1 --dry-run                        # print planned actions without changing anything
.\install.ps1 --list                           # list installable skills
```

重新运行 `./install.sh` 或 `.\install.ps1` 即可升级。安装器只动名字出现在本仓库 `skills/` 下的目录：**其他名字**的 skill 不受影响；**同名**的 skill 会被覆盖，想保留旧版本请加 `--backup`。

如果你的目录位置不同，可通过 `CLAUDE_SKILLS_DIR`、`CODEX_SKILLS_DIR` 或 `TRAE_SKILLS_DIR` 环境变量覆盖默认路径。

## 维护

更新这些页面时，技能元数据请修改 `docs/readme/skills.json`，页面文案或结构请修改 `docs/readme/templates/` 下的模板，然后重新运行 `python3 scripts/render_readmes.py`。
