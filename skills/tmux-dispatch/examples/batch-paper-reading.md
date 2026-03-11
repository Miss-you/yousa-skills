# Example: Batch Paper Reading

Use tmux-dispatch to analyze multiple AI papers in parallel, each with independent quality checks.

## User Prompt

```
帮我用 tmux-dispatch 批量分析以下 5 篇论文，每篇论文：
1. 用 ai-paper-reader skill 进行结构化阅读
2. 输出到 ~/papers/2025-01/ 目录

论文列表：
- https://arxiv.org/abs/2401.xxxxx
- https://arxiv.org/abs/2401.yyyyy
- https://arxiv.org/abs/2401.zzzzz
- https://arxiv.org/abs/2401.aaaaa
- https://arxiv.org/abs/2401.bbbbb

并发数：3
```

## What Happens

1. **Dispatcher** (current Claude Code) generates 5 task files under `/tmp/cc-batch/{session-id}/`
2. Each task file contains the full paper-reading prompt with quality checklist
3. 3 tmux workers start, each running an independent Claude Code process
4. Workers pick up tasks via work-stealing — as one finishes, it grabs the next pending task
5. Each worker self-checks output quality (up to 3 rounds)
6. Dispatcher monitors progress and reports final summary

## Generated Task File (Example)

```markdown
# 任务指示

你是一个独立的 Claude Code 执行方，请严格按照以下指示完成任务。

## 基本信息
- 任务编号: 00
- 任务名称: paper-2401.xxxxx
- 输出目录: ~/papers/2025-01/2401.xxxxx/

## 执行步骤
1. 使用 paper-init skill 初始化论文目录
2. 使用 ai-paper-reader skill 完成 6 阶段结构化阅读
3. 将所有产出写入输出目录

## 质量门禁
- [ ] prompt.md 已生成
- [ ] 6 个阶段的阅读笔记均已完成
- [ ] 输出目录下文件完整

## 完成标记
touch /tmp/cc-batch/{session-id}/done-00
```

## Monitoring

```bash
# Attach to watch workers in real-time
tmux attach -t cc-batch

# Check progress from dispatcher
bash ~/.claude/skills/tmux-dispatch/scripts/check-done.sh /tmp/cc-batch/{session-id}
# Output: Total: 5 | Done: 3 | Failed: 0 | Running/Pending: 2
```
