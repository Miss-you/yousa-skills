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

## 安装

把需要的 skill 目录复制到本地 Claude Code skills 目录：

```bash
git clone https://github.com/Miss-you/yousa-skills.git
skill_paths=(skills/explaining-completed-work skills/tmux-dispatch skills/social-strategist skills/structural-integrity-scan skills/two-mirror-examples skills/cdp-page-to-md skills/zh-proofreading skills/secret-scan skills/pr-review-autofix skills/monitoring-pr-ai-reviews skills/writing-commit skills/writing-contextual-todos skills/creating-sourcecode-learning-sops)
for skill_path in "${skill_paths[@]}"; do
  skill_dir="${skill_path##*/}"
  cp -r "yousa-skills/${skill_path}" ~/.claude/skills/"${skill_dir}"
done
```

使用一条复制命令安装每个 skill：

```bash
cp -r yousa-skills/skills/explaining-completed-work ~/.claude/skills/explaining-completed-work
cp -r yousa-skills/skills/tmux-dispatch ~/.claude/skills/tmux-dispatch
cp -r yousa-skills/skills/social-strategist ~/.claude/skills/social-strategist
cp -r yousa-skills/skills/structural-integrity-scan ~/.claude/skills/structural-integrity-scan
cp -r yousa-skills/skills/two-mirror-examples ~/.claude/skills/two-mirror-examples
cp -r yousa-skills/skills/cdp-page-to-md ~/.claude/skills/cdp-page-to-md
cp -r yousa-skills/skills/zh-proofreading ~/.claude/skills/zh-proofreading
cp -r yousa-skills/skills/secret-scan ~/.claude/skills/secret-scan
cp -r yousa-skills/skills/pr-review-autofix ~/.claude/skills/pr-review-autofix
cp -r yousa-skills/skills/monitoring-pr-ai-reviews ~/.claude/skills/monitoring-pr-ai-reviews
cp -r yousa-skills/skills/writing-commit ~/.claude/skills/writing-commit
cp -r yousa-skills/skills/writing-contextual-todos ~/.claude/skills/writing-contextual-todos
cp -r yousa-skills/skills/creating-sourcecode-learning-sops ~/.claude/skills/creating-sourcecode-learning-sops
```

## 维护

更新这些页面时，技能元数据请修改 `docs/readme/skills.json`，页面文案或结构请修改 `docs/readme/templates/` 下的模板，然后重新运行 `python3 scripts/render_readmes.py`。
