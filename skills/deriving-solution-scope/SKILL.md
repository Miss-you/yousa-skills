---
name: deriving-solution-scope
description: Use when a user brings a problem, goal, incident, proposal, technical方案, or vague direction and needs to figure out what should be done, what is necessary, what can wait, or how to 二次评估 scope
---

# Deriving Solution Scope

## Overview

从一个问题、目标或技术方案出发，先推导“可能应该做哪些事”，再基于约束原则二次收敛成“本轮应该做哪些事”。不要一开始就跳到优先级；先把工作项的候选空间梳理清楚。

## When to Use

Use when the user asks:
- 这个问题应该怎么处理？
- 这个方案落地需要做哪些事？
- 为了达成这个目标，我们要拆哪些工作？
- 先帮我列出来，再判断哪些必须做、哪些可延后。

Do not use when the user already gave a precise implementation task, or only needs a single command executed.

## SOP

### 1. Identify the Input Type

Classify the starting point:

| Input | First Question |
|---|---|
| Problem / incident | 什么失败了，影响谁，证据是什么？ |
| Technical proposal | 方案要改变什么行为，依赖哪些系统？ |
| Goal / outcome | 成功状态是什么，必须满足哪些约束？ |
| Existing action list | 这些动作分别解决哪个 failure mode？ |

If the input is vague, state assumptions instead of blocking unless a wrong assumption would be risky.

### 2. Derive Candidate Work Items

Generate work items by asking these lenses in order:

| Lens | Heuristic Question |
|---|---|
| Correctness | 要让核心行为真的正确，需要改什么？ |
| Compatibility | 有没有真实输入、协议、历史数据、调用方语义需要兼容？ |
| Observability | 如果再失败一次，我们能不能立刻发现并定位？ |
| Verification | 用什么样本、测试、回归或线上观察证明它生效？ |
| Resilience | 需要重试、降级、幂等、兜底或限流吗？ |
| Rollout | 上线、灰度、回滚、配置开关有没有特殊风险？ |
| Operations | 值班、告警、Runbook、人工处理链路是否要补？ |
| Hygiene | 文档、重构、清理、体验优化是否值得顺手做？ |

Write candidates as action + why:

```markdown
- 修正 X 解析：解决真实回调字段类型不兼容。
- 增加 Y 指标：避免同类失败继续被 0,0 掩盖。
```

### 3. State Decision Principles

Before classifying items, write the principles that will decide scope:

- Must: 用户可见错误、数据丢失/错发、安全合规、线上失败被掩盖、已知协议兼容缺口、没有测试会让同类问题高概率复发。
- Should: 显著缩短下次定位时间、补齐关键指标/告警、降低同类事故概率，但不直接决定本次修复是否生效。
- Optional / Defer: 主要提升便利性、长期可维护性、文档完整度或仪表盘体验，当前事故链路不依赖它。
- Do Not Do Now: 扩大影响面、改变外部契约、引入重试风暴、证据不足或需要单独设计评审的动作。

### 4. Run the Second-Pass Evaluation

Classify every candidate. If an item cannot be classified, mark it as `Need Evidence` and say what evidence would decide it.

Use this output shape:

```markdown
## Starting Point
问题/目标/方案：
当前证据：
关键约束：

## Candidate Work Items
- ...

## Decision Principles
- ...

## Second-Pass Evaluation
Must:
- ...

Should:
- ...

Optional / Defer:
- ...

Do Not Do Now:
- ...

Need Evidence:
- ...

## Recommended Scope
本轮做到：
本轮不做：
判断依据：
```

## Red Flags

- 直接给优先级，却没有先推导候选工作项。
- 只列开发改动，漏掉验证、观测、上线和回滚。
- 把“修 bug”当作全部闭环，漏掉失败暴露。
- 所有项都被判成 must，说明没有真正做判断。
- 把高风险架构调整混进当前问题修复。
- 结论没有说明“本轮做到哪里”和“本轮不做什么”。
