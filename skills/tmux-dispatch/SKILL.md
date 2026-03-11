---
name: tmux-dispatch
description: >-
  通过 tmux 编排多个 Claude Code 进程来批量处理同质任务。当前 CC 作为调度方，
  tmux 中的 CC 作为执行方。支持 work-stealing 并发调度、任务内建质量门禁。
  当用户需要：(1) 批量处理多个独立同质任务（论文分析、代码审查、文档翻译等），
  (2) 单次 prompt 处理质量不够需要拆分独立执行，(3) 需要并发加速批量任务时使用。
  触发词：批量处理、tmux dispatch、并发执行、逐个处理。
---

# tmux-dispatch: 批量任务调度 Skill

通过 tmux 启动多个独立 Claude Code 进程，每个进程专注处理一个任务，解决单次 prompt 批量处理时的质量稀释问题。

## 角色分工

- **调度方**（当前 CC）：解析输入、生成任务文件、启动 tmux、分发任务、监控进度
- **执行方**（tmux 中的 CC）：读取任务文件、独立执行、自检质量、标记完成

## 执行流程

### Step 1: 解析用户输入，生成任务文件

从用户 prompt 中识别：
- **任务模板**：对每个 item 要做什么（技能调用、输出格式、质量要求）
- **批量内容**：item 列表（论文/文件/URL 等）
- **参数**：并发数（默认 3）、输出目录、超时时间（默认 20min）

为每个 item 生成独立的任务 prompt 文件：

```
/tmp/cc-batch/{session-id}/
├── task-00.md
├── task-01.md
├── ...
└── task-{N-1}.md
```

**任务文件模板**（调度方根据实际需求填充）：

```markdown
# 任务指示

你是一个独立的 Claude Code 执行方，请严格按照以下指示完成任务。

## 基本信息
- 任务编号: {id}
- 任务名称: {name}
- 输出目录: {output_dir}

## 工作目录
cd {work_dir}

## 执行步骤
{steps}

## 质量门禁（必须全部通过）

完成所有步骤后，逐项检查以下清单：

{checklist}

### 自检流程
1. 逐项检查上述清单
2. 未通过项：定位问题 → 修复 → 重新检查
3. 最多 3 轮自检修复循环
4. 全部通过后，执行完成标记命令
5. 3 轮后仍有未通过项，创建失败标记并说明原因

## 完成标记
全部通过后执行：
touch /tmp/cc-batch/{session-id}/done-{id}

3 轮自检仍未通过执行：
echo "未通过项: ..." > /tmp/cc-batch/{session-id}/failed-{id}
```

### Step 2: 启动 tmux session

```bash
bash ~/.claude/skills/tmux-dispatch/scripts/start-workers.sh {session-id} {num-workers} {work-dir}
```

等待 8 秒让所有 worker 的 claude 完成启动。

### Step 3: 分发初始任务

```bash
# 向每个 pane 分发第一批任务
bash ~/.claude/skills/tmux-dispatch/scripts/send-task.sh {session-id} 0 /tmp/cc-batch/{session-id}/task-00.md
bash ~/.claude/skills/tmux-dispatch/scripts/send-task.sh {session-id} 1 /tmp/cc-batch/{session-id}/task-01.md
bash ~/.claude/skills/tmux-dispatch/scripts/send-task.sh {session-id} 2 /tmp/cc-batch/{session-id}/task-02.md
```

每次分发间隔 3 秒，避免 API 峰值。

### Step 4: 监控进度

有两种监控方式：

**方式 A：使用 monitor.sh（后台自动调度）**

```bash
bash ~/.claude/skills/tmux-dispatch/scripts/monitor.sh {session-id} /tmp/cc-batch/{session-id} {num-workers} 30 20
```

monitor.sh 会自动执行 work-stealing：检测 done 文件 → 空闲 pane 领取下一个任务。

**方式 B：调度方手动监控（推荐）**

调度方自己轮询，灵活控制：

```bash
# 检查整体进度
bash ~/.claude/skills/tmux-dispatch/scripts/check-done.sh /tmp/cc-batch/{session-id}

# 某个任务完成后，手动分发下一个
bash ~/.claude/skills/tmux-dispatch/scripts/send-task.sh {session-id} {pane} /tmp/cc-batch/{session-id}/task-{next}.md
```

### Step 5: 汇总结果

全部任务完成后，调度方：
1. 读取各输出目录，检查产出物完整性
2. 生成汇总报告（可选）
3. 清理临时文件

## 调度方行为规范

1. **生成任务文件时**：每个任务 prompt 必须自包含，不依赖其他任务的输出
2. **监控时**：使用 `check-done.sh` 检查进度，不要 `tmux capture-pane` 读取 worker 输出（太碎片化）
3. **分发时**：确认 worker 处于等待输入状态再发任务（上一个任务的 done 文件已创建）
4. **异常处理**：发现 failed 标记时，读取失败原因，决定是重试还是跳过

## 用户可观察性

用户随时可以：
- `tmux attach -t {session-id}` 查看所有 worker 实时状态
- `Ctrl-b` + 方向键切换 pane，直接与某个 worker 交互
- `Ctrl-b d` detach 回到调度方

## 参数默认值

| 参数 | 默认值 | 说明 |
|------|--------|------|
| num-workers | 3 | 并发 worker 数 |
| poll-interval | 30s | 监控轮询间隔 |
| timeout | 20min | 单任务超时告警 |
| max-retries | 3 | 自检最大重试轮次 |
| stagger-delay | 3s | worker 间启动间隔 |
