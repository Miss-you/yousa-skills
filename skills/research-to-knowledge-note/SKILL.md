---
name: "research-to-knowledge-note"
description: "把分析结果 + 联网检索证据整合成可长期归档的中文知识笔记（带元信息、证据表、方法论、复现方法、AC 自检表）。当用户说"整理成知识笔记 / 归档 / 整理成 Obsidian 笔记 / 沉淀为档案"时调用。"
---

# Research to Knowledge Note

## What this skill does

把"已经做完的研究/分析"（视频分析、论文阅读、调研笔记、issue 复盘等）+ 联网检索证据，**重组**成符合长期归档标准的中文知识笔记。
**核心价值**：不是写新分析，而是把零散的结论、引用、思考**结构化为 6 个月后自己/同事仍能直接用**的档案。

## When to invoke

满足以下任一即调用：

- 用户说"整理成知识笔记 / 归档 / 沉淀 / 留档 / 收进 Obsidian / Notion"
- 用户对前一轮输出表示满意，并要求"重新整理成更正式的格式"
- 用户给出零散的研究素材（搜索结果、文档摘录、对话片段）并要求"组织成笔记"
- 紧接在 `youtube-video-analysis`、深度调研、论文阅读后被显式 hand off

**不适用场景**：
- 还没做完研究/分析就直接要笔记（先做分析）
- 单纯的会议纪要（用 `transcript-to-deep-minutes` / `meeting-minutes-deep-extraction`）

## Directory Convention（MANDATORY，针对视频类输入）

当本 skill 的输入来自 `youtube-video-analysis`（或任何视频处理流程）时，**必须**遵守 [AGENTS.md](file:///Users/apple/Documents/Github/video-srt/AGENTS.md) §1 的"一视频一 workspace"约束：

- 接收一个明确的 `workspace_dir`：`out/<videoId>__<slug>/`
- 如果用户未明示，从已存在的 `report.md` / `raw/*.info.json` 路径反推
- 输出的归档笔记**必须**写入 `$WS/note.md`，**禁止**写到 `out/` 根或其他视频的 workspace
- 笔记内所有 `file://` 链接必须指向**当前 workspace 内**的文件；如需跨 workspace 引用（对照基线等）必须显式注明
- 严禁污染其他视频的 workspace 或在 `out/` 根新增任何具体视频的文件

对非视频类输入（论文、调研、对话片段），如用户未指定，可继续 inline 直出或按用户指定路径落盘。

## Acceptance Criteria（10 条 AC，归档前必须自检）

| 编号 | 维度 | 标准 |
|---|---|---|
| AC-1 | **可溯源** | 元信息块齐全：原始 URL、抓取/分析日期、工具版本、原始材料路径 |
| AC-2 | **可复现** | 写明数据获取/处理/分析的命令链，6 个月后可一键复跑 |
| AC-3 | **结论独立可读** | 不读原始材料也能看懂结论；有 TL;DR |
| AC-4 | **事实-观点分离** | 每条主张标 ✅/🟡/⚠️/❌ 并附来源类型 |
| AC-5 | **核查证据可点击** | 来源给出可访问链接或注明已/未存档 |
| AC-6 | **方法论可迁移** | 提炼出"下次遇到类似问题该用什么框架"的清单 |
| AC-7 | **结构对称** | "正面/反面"评价颗粒度对等，避免偏袒 |
| AC-8 | **敏感信息合规** | 对在世人物的指控类内容，区分"主张/事实/推论"，避免事实化传谣 |
| AC-9 | **中文表达** | 无错别字、CJK-Latin 间距正确、不过度口语化 |
| AC-10 | **归档友好** | 单文件 Markdown + Tags + TOC，可直接进 Obsidian/Notion |

## Output Template（固定 11 节结构）

```markdown
# 📁 知识笔记｜<主题标题>

> **Tags**: #<域> #<子域> #<方法>  
> **归档日期**: YYYY-MM-DD  
> **归档者**: <user>  
> **可信度自评**: <一句话评估材料可靠性>

---

## 0. 元信息（Provenance）
| 字段 | 值 |
|---|---|
| 原始来源 URL | ... |
| 标题 / 作者 / 频道 | ... |
| 抓取/分析日期 | ... |
| 工具版本 | yt-dlp x.x / WebSearch / ... |
| 原始材料路径 | [name](file:///abs/path) |
| 衍生材料路径 | ... |
| 核查覆盖 | N 条主张，M 次独立检索 |

## 1. 目录（TOC）
（自动列出 §2-§10 锚点）

## 2. TL;DR（3 行结论）

## 3. 主题在讲什么（What）

## 4. 核心论证链 / 核心内容（How）
（带证据强度评级表）

## 5. 事实核查证据表（Verify）
- 5.1 <事实层分组>
- 5.2 <叙事/推论层分组>
- 5.3 时间/口径需注意

## 6. 合理与不合理的判断
- 6.1 ✅ 合理且值得吸收
- 6.2 ⚠️ 不合理或过激
- 6.3 🎯 启发性的部分

## 7. 可迁移的思维模型与方法论
（最高价值章节——内容会过时，方法论不会）

## 8. 适用边界与读者警示

## 9. 复现方法（Reproduce）
（完整命令链 + 关键脚本链接）

## 10. 附录：关键引述索引

## 11. 归档自检表
| AC | 维度 | 是否通过 | 备注 |
|---|---|---|---|
| AC-1 ~ AC-10 | ... | ✅/🟡 | ... |
```

## Six-Step Workflow

### Step 1 — 收集素材（Collect）
明确以下三类输入：
1. **一手材料**：原始视频/论文/网页/对话片段路径
2. **二手分析**：上一轮已做出的结论、论证链、判断
3. **三手核查**：WebSearch 检索得到的证据列表

### Step 2 — 补全元信息（Provenance）
逐项填写 §0 表格。**任何缺失字段都要显式标注"未知"**，不要省略。

### Step 3 — 重组为 11 节模板（Restructure）
按上文模板照搬，**不要重写已有的好内容**——重组是搬运 + 加结构，不是重新分析。

### Step 4 — 联网补充核查（Supplement）
对原分析中标 ⚠️ 的主张，再做 1-3 轮 WebSearch 尝试升级到 ✅ 或 🟡。
**仍找不到来源就保持 ⚠️**，不编造。

### Step 5 — 提炼方法论（Distill）
§7 是本 skill 与普通"分析报告"的核心差异：
- 抽出 **3-5 条可复用的质询清单 / 思维模型 / 检查表**
- 用"下次遇到 X 类问题，先问 Y/Z"的句式写
- 避免只对本案有效的细节

### Step 6 — AC 自检与修复（Verify against AC）
照搬 §11 自检表，逐条打分：
- ✅ 全通过 → 交付
- 🟡 部分通过 → 在 §11 备注列说明 + 给出补救建议
- ❌ 未通过 → 回到对应章节修复后再过 AC

**自检纪律**：不允许"全 ✅"的造假——AC-5（核查源 URL 留存）几乎总是 🟡，要诚实标注。

## Output Contract

- **语言**：默认中文；术语保留英文原文。
- **不虚构**：找不到的来源标 ⚠️，不编 URL。
- **落盘位置**：
  - 视频类输入：**必须**写到 `$WS/note.md`（详见上文 "Directory Convention"）
  - 非视频类输入：默认 inline Markdown 直出；用户明示要落盘才写文件，遵守"NEVER create files unless absolutely necessary"
- **可点击路径**：所有本地文件用 `[name](file:///abs/path[#L<start>-L<end>])` 格式，且必须指向当前 workspace 内（视频类输入）或用户明示的目录。
- **可移植**：Markdown 不依赖任何特定平台扩展语法。
- **AC-11（隐式）**：视频类输入时，归档前必须确认 [AGENTS.md](file:///Users/apple/Documents/Github/video-srt/AGENTS.md) §4 的自检清单全部通过。

## Composition with Sibling Skills

| 上游 skill | 本 skill 角色 |
|---|---|
| `youtube-video-analysis` | 把分析报告归档化 |
| 论文阅读 / 调研 / 联网检索 | 把零散结论归档化 |
| `transcript-to-deep-minutes` | （重叠场景）会议纪要走 minutes 系列；研究/调研归档走本 skill |

## Reference Implementation

本 skill 抽象自一次真实执行：把《首富的黄昏》视频分析重组为归档笔记，输入素材见：
- 元数据：[WSXOa7Edkrc.info.json](file:///Users/apple/Documents/Github/video-srt/out/WSXOa7Edkrc.info.json)
- 字幕：[WSXOa7Edkrc.zh-CN.txt](file:///Users/apple/Documents/Github/video-srt/out/WSXOa7Edkrc.zh-CN.txt)
- 复用脚本：[vtt2txt.py](file:///Users/apple/Documents/Github/video-srt/out/vtt2txt.py#L1-L25)
