---
name: "youtube-video-analysis"
description: "对 YouTube 视频做四步深度分析：抓字幕 → 结构化总结 → 联网事实核查 → 输出"合理/不合理/启发"判断报告。当用户给出 YouTube 链接并要求分析、梳理、批判性解读、判断真伪、提炼观点时调用。"
---

# YouTube Video Analysis

## What this skill does

输入一个 YouTube 视频 URL，输出一份**带事实核查标签**的中文深度分析报告。
**核心价值**：不只总结视频"说了什么"，更要判断"说的对不对"和"哪些值得学"。

## When to invoke

满足以下任一条件即调用本 skill：

- 用户消息包含 `youtube.com/watch?v=` 或 `youtu.be/` 链接
- 用户要求"分析这个视频 / 梳理这个视频 / 判断视频观点是否合理 / 视频核查"
- 用户要求对视频内容做批判性解读、事实核查、思维框架提炼
- 用户要求把视频内容转成可归档的分析文档

**不适用场景**：
- 单纯只要逐字稿（直接用 yt-dlp 即可，不需要本 skill）
- 视频是音乐/纯娱乐/无观点表达类（核查无意义）

## Prerequisites（首次使用前自检）

```bash
which yt-dlp || brew install yt-dlp        # 字幕抓取
python3 --version                          # 内置 re/pathlib 即可
```

可选（字幕不存在时的兜底）：
```bash
which whisper || pip install -U openai-whisper
which ffmpeg || brew install ffmpeg
```

## Directory Convention（MANDATORY）

**必须遵守 [AGENTS.md](file:///Users/apple/Documents/Github/video-srt/AGENTS.md) §1 的"一视频一 workspace"约束**：

- 每个视频独占一个目录：`out/<videoId>__<slug>/`
- 子目录：`raw/`（原始素材）、`transcript/`（清洗文本）、`logs/`（日志）、`scratch/`（中间产物）
- 报告固定命名为 `report.md`，归档笔记固定命名为 `note.md`
- **禁止**把任何具体视频的产物写入 `out/` 根目录

冲突时以 AGENTS.md 为准；本文件中的命令示例已按此约定写出。

## Four-Step Workflow

### Step 0 — 初始化 Workspace（必做）

```bash
# 从 URL 解析 videoId，先抓取 metadata-only，再据标题生成 slug
URL="<YOUTUBE_URL>"
VID=$(python3 -c "import re,sys; m=re.search(r'(?:v=|youtu\.be/)([\w-]{11})', sys.argv[1]); print(m.group(1))" "$URL")

mkdir -p out/_tmp
yt-dlp --skip-download --write-info-json \
  -o "out/_tmp/%(id)s.%(ext)s" "$URL"

TITLE=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['title'])" "out/_tmp/$VID.info.json")
SLUG=$(python3 -c "import re,sys; s=sys.argv[1]; s=re.sub(r'[\s\W]+','',s); print(s[:24])" "$TITLE")
WS="out/${VID}__${SLUG}"

mkdir -p "$WS/raw" "$WS/transcript" "$WS/logs" "$WS/scratch"
mv "out/_tmp/$VID.info.json" "$WS/raw/"
rmdir out/_tmp 2>/dev/null
echo "Workspace ready: $WS"
```

**所有后续命令的输出路径都必须指向 `$WS/...`，绝不允许写入 `out/` 根。**

### Step 1 — 提取字幕（Extract）

**优先级**：官方/自动字幕 > Whisper 转写

```bash
# $WS 来自 Step 0
yt-dlp \
  --write-auto-subs --sub-lang "zh-CN,zh-Hans,zh,en" --skip-download \
  --write-info-json -o "$WS/raw/%(id)s.%(ext)s" \
  "$URL" \
  2> "$WS/logs/$VID.dl.log"
```

产物（均在 workspace 内）：
- `$WS/raw/<videoId>.<lang>.vtt` — 原始字幕
- `$WS/raw/<videoId>.info.json` — 标题/频道/时长/观看量等元数据（Step 0 已写入）
- `$WS/logs/<videoId>.dl.log` — 抓取日志

**清洗 VTT → 纯文本**（脚本固定为以下 25 行；可复用 [vtt2txt.py](file:///Users/apple/Documents/Github/video-srt/out/vtt2txt.py#L1-L25)，输出落到 `$WS/transcript/`）：

```python
import re, sys, pathlib
p = pathlib.Path(sys.argv[1])
raw = p.read_text(encoding='utf-8')
lines = []
for ln in raw.splitlines():
    if not ln.strip(): continue
    if ln.startswith('WEBVTT') or ln.startswith('Kind:') or ln.startswith('Language:'): continue
    if '-->' in ln: continue
    if re.match(r'^\d+$', ln.strip()): continue
    ln = re.sub(r'<[^>]+>', '', ln)
    ln = re.sub(r'&nbsp;', ' ', ln)
    lines.append(ln.strip())
seen, prev = [], None
for ln in lines:
    if ln != prev and ln:
        seen.append(ln); prev = ln
text = ''.join(seen)
text = re.sub(r'\s+', '', text)
out = p.with_suffix('.txt')
out.write_text(text, encoding='utf-8')
print(f'chars={len(text)} -> {out}')
```

**Whisper 兜底**（仅当 yt-dlp 拿不到任何字幕时启用，所有产物落 workspace）：
```bash
yt-dlp -x --audio-format mp3 -o "$WS/raw/%(id)s.%(ext)s" "$URL" \
  2>> "$WS/logs/$VID.dl.log"
whisper "$WS/raw/$VID.mp3" --language zh --model medium \
  --output_dir "$WS/transcript" --output_format txt \
  2> "$WS/logs/$VID.whisper.log"
```

### Step 2 — 结构化总结（Summarize）

读入清洗后的 `$WS/transcript/*.txt`，按以下四元结构提炼：

| 字段 | 要求 |
|---|---|
| **是什么（What）** | 一句话讲清视频题材、叙事弧线、性质（新闻/评论/教学/八卦） |
| **为什么（Why）** | 作者的核心主张 / 想让观众相信什么 |
| **核心逻辑（How）** | 论证链路 L1→L2→...→Ln，每环写清"证据 → 结论" |
| **主要论据** | 列出 **15-25 条** 可被独立检验的事实性主张，按"商业事实 / 因果叙事 / 时间口径"分类 |

**关键纪律**：**事实主张** 与 **作者推论** 必须分行写、分别打标，绝不混淆。

### Step 3 — 构建校验能力（Verify Skill）

对 Step 2 输出的每条事实性主张，逐条 `WebSearch` 核查，打四档标签：

| 标签 | 含义 | 处置 |
|---|---|---|
| ✅ 属实 | 多个独立来源印证 | 保留 |
| 🟡 部分属实 | 核心为真但数字/时间有夸张 | 标注差异 |
| ⚠️ 无法核实 | 仅有匿名/转引/单一来源 | 明确标"二手转引" |
| ❌ 与事实不符 | 公开信息矛盾 | 在报告中直接驳正 |

**搜索策略**：
1. 先用关键词组合（人名+事件+年份）
2. 失败则降级为更通用关键词
3. 对敏感人物指控类主张，**至少要求两个独立来源**才能打 ✅
4. 找不到来源**不要编造 URL**，诚实标 ⚠️

**核查覆盖目标**：至少 20 条主张，至少 10 次独立检索。

### Step 4 — 深度梳理报告（Synthesize）

按以下固定结构输出中文报告（即"分析报告"，区别于后续可能归档的"知识笔记"）：

```
1. TL;DR（3 行结论）
2. 视频在讲什么（What）
3. 核心论证链（带证据强度评级表）
4. 事实核查证据表（按 5.1 商业事实 / 5.2 因果叙事 / 5.3 时间口径 分组）
5. 合理与不合理判断
   - 6.1 ✅ 合理且值得吸收
   - 6.2 ⚠️ 不合理或过激（必须与 6.1 颗粒度对等！）
   - 6.3 🎯 启发性的部分（中性第三栏）
6. 可迁移的思维模型与方法论
7. 适用边界与读者警示
```

**关键反例检查（输出前自检）**：
- 是否落入 **post hoc ergo propter hoc**（时间相邻当因果相邻）？
- 是否落入 **Mono-causal Fallacy**（单因解释多变量崩塌）？
- "合理"与"不合理"两侧字数/证据量是否对等？（避免偏袒）

**落盘位置**：若用户要求保存报告，**必须**写入 `$WS/report.md`（不带 videoId 前缀，因为目录已隔离），禁止写到 `out/` 根。

## Output Contract

- **语言**：默认中文；用户明示英文时切换。
- **不虚构**：拿不到的来源标 ⚠️，不编 URL。
- **不具名传谣**：对在世人物的指控类主张，隐去具名细节，仅记录"属无法独立核实层"。
- **可点击路径**：所有本地文件用 `[name](file:///abs/path)` 格式，且**必须指向当前 workspace 内**的文件。
- **交付物形态**：默认 inline Markdown 直出；用户要求落盘则写到 `$WS/report.md`。
- **目录隔离**：严格遵守 [AGENTS.md](file:///Users/apple/Documents/Github/video-srt/AGENTS.md) §1，禁止跨 workspace 污染。

## Handoff to Next Skill

本 skill 产出"分析报告"（位于 `$WS/report.md` 或 inline）。如果用户进一步要求**归档**，请调用姊妹 skill：
`research-to-knowledge-note` — 它会读取同一 workspace 的 `report.md` 与 `raw/` `transcript/` 素材，把结果整合为 `$WS/note.md`。

## Reference Implementation

本 skill 抽象自一次真实执行：
- 视频：[WSXOa7Edkrc.info.json](file:///Users/apple/Documents/Github/video-srt/out/WSXOa7Edkrc.info.json)（《首富的黄昏：王健林是怎么得罪习近平的？》）
- 清洗后字幕：[WSXOa7Edkrc.zh-CN.txt](file:///Users/apple/Documents/Github/video-srt/out/WSXOa7Edkrc.zh-CN.txt)（34,637 字符）
- 复用脚本：[vtt2txt.py](file:///Users/apple/Documents/Github/video-srt/out/vtt2txt.py#L1-L25)
