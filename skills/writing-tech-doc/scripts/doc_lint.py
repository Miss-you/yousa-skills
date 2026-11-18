#!/usr/bin/env python3
"""中文技术文档自检：文风红线 + 结构完整性。

用法: python3 doc_lint.py <file.md> [--strict]

退出码: 0=无 error, 1=有 error。--strict 时 warn 也计入。
"""
import re
import sys
from pathlib import Path

# 评价性措辞：替读者下判断，技术文档应改为摆数据
HEDGE = ["值得注意", "值得一提", "不可否认", "毫无疑问", "不可能是巧合", "众所周知",
         "非常", "极其", "极大", "惊人", "显然", "其实", "可以说", "有意思的是",
         "最有价值", "最重要的是", "令人", "遗憾的是", "好消息是", "坏消息是",
         "简单来说", "换句话说", "总而言之", "综上所述", "不难看出", "由此可见"]

# 明确禁用的句式，见 references/style.md
BANNED = [
    (r"不是.{1,20}而是", "「不是A而是B」句式"),
    (r"(?<![一二三四五六七八九十])主要(?=[是有为的用来在])", "「主要」作强调副词"),
    (r"^\s*即[：:]", "「即：」开头的补充句"),
    (r"^\s*注[：:]", "「注：」开头的补充句"),
]

# 标题在讲故事而不是命名内容
NARRATIVE = [r"[？?]", r"^为什么", r"^怎么", r"^如何看", r"了吗", r"变了", r"来了",
             r"其实", r"真相", r"背后", r"[，,]", r"[。！!]$"]

FENCE = re.compile(r"^```")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
ROW = re.compile(r"^\s*\|.*\|\s*$")
SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def code_mask(lines):
    """每行是否在围栏代码块内（围栏行本身也算）。"""
    mask, inside = [], False
    for ln in lines:
        if FENCE.match(ln.strip()):
            inside = not inside
            mask.append(True)
        else:
            mask.append(inside)
    return mask


def check_style(lines, mask):
    out = []
    for i, ln in enumerate(lines, 1):
        if mask[i - 1]:
            continue
        for w in HEDGE:
            if w in ln:
                out.append(("warn", i, f"评价性措辞「{w}」，改为直接给数据或删除"))
        for pat, why in BANNED:
            if re.search(pat, ln):
                out.append(("error", i, f"{why}：{ln.strip()[:50]}"))
        if "——" in ln:
            out.append(("warn", i, "破折号铺陈，拆成两句或改用冒号"))
        if not ROW.match(ln) and re.search(r"\S\s*→\s*\S", ln):
            out.append(("warn", i, "正文用箭头串联，改成文字、表格或流程图"))
    return out


def check_bold(lines, mask):
    """正文加粗（表格行、标题行不计）。"""
    out = []
    for i, ln in enumerate(lines, 1):
        if mask[i - 1] or ROW.match(ln) or HEADING.match(ln):
            continue
        n = len(re.findall(r"\*\*[^*]+\*\*", ln))
        if n:
            out.append(("warn", i, f"正文加粗 {n} 处，技术文档靠层级和表格分主次"))
    return out


def check_headings(lines, mask):
    out, seen, numbered = [], [], 0
    for i, ln in enumerate(lines, 1):
        if mask[i - 1]:
            continue
        m = HEADING.match(ln)
        if not m:
            continue
        level, text = len(m.group(1)), m.group(2).strip()
        seen.append((i, level, text))
        if level < 2:
            continue
        is_appendix = bool(re.match(r"^(附录|Appendix)", text))
        if re.match(r"^\d+\.", text) or is_appendix:
            numbered += 1
        for pat in NARRATIVE:
            if re.search(pat, text):
                out.append(("warn", i, f"叙事性标题「{text}」，改为名词短语"))
                break
        # 「附录 A：xxx」是标准写法，冒号不算复合标题
        if not is_appendix and ("：" in text or ":" in text):
            out.append(("warn", i, f"复合标题「{text}」，冒号后的解释移入正文"))
        if len(text) > 24:
            out.append(("warn", i, f"标题过长（{len(text)} 字）：{text}"))
    h2 = [s for s in seen if s[1] == 2]
    if h2 and numbered < len(h2) * 0.6:
        out.append(("error", h2[0][0],
                    f"二级标题未使用编号（{numbered}/{len(h2)}），改为「1. xxx」层级"))
    for k in range(1, len(seen)):
        if seen[k][1] - seen[k - 1][1] > 1:
            out.append(("warn", seen[k][0], f"标题层级跳跃 H{seen[k-1][1]}→H{seen[k][1]}"))
    return out


def check_tables(lines, mask):
    out, i, n = [], 0, len(lines)
    while i < n:
        if mask[i] or not ROW.match(lines[i]):
            i += 1
            continue
        start, block = i, []
        while i < n and not mask[i] and ROW.match(lines[i]):
            block.append(lines[i])
            i += 1
        if len(block) < 2:
            out.append(("warn", start + 1, "疑似单行表格"))
        elif not SEP.match(block[1]):
            out.append(("error", start + 2, "表格缺少表头分隔行 |---|---|"))
        else:
            # 单元格内 \| 是转义竖线，不是列分隔
            widths = {len(re.sub(r"\\\|", "", r).strip().strip("|").split("|"))
                      for r in block}
            if len(widths) > 1:
                out.append(("error", start + 1, f"表格列数不一致：{sorted(widths)}"))
    return out


def check_mermaid(lines):
    """mermaid 常见渲染故障。节点标签含括号/冒号/斜杠不加引号会解析失败。"""
    out, i, n = [], 0, len(lines)
    while i < n:
        if not re.match(r"^```\s*mermaid", lines[i].strip()):
            i += 1
            continue
        start, i, body = i + 1, i + 1, []
        while i < n and not FENCE.match(lines[i].strip()):
            body.append((i + 1, lines[i]))
            i += 1
        if i >= n:
            out.append(("error", start, "mermaid 代码块未闭合"))
            break
        i += 1
        if not body:
            out.append(("error", start, "mermaid 块为空"))
            continue
        kind = body[0][1].strip()
        if kind.startswith("%%{"):
            kind = body[1][1].strip() if len(body) > 1 else ""
        if not re.match(r"^(flowchart|graph|sequenceDiagram|stateDiagram|erDiagram"
                        r"|gantt|classDiagram|journey|pie)", kind):
            out.append(("error", start, f"mermaid 首行不是图类型声明：{kind[:40]}"))
        for lno, ln in body:
            # 只有括号会真的让 flowchart 节点标签解析失败；: / <br/> 都是合法的
            for lb in re.findall(r"\[([^\]]*)\]", ln):
                if lb and not lb.startswith('"') and re.search(r"[()（）{}]", lb):
                    out.append(("error", lno, f'节点标签含括号需加引号："{lb[:30]}"'))
            if re.search(r"\|[^|]*[()（）][^|]*\|", ln):
                out.append(("warn", lno, "mermaid 边标签含括号，建议去掉"))
    return out


def check_provenance(lines, mask):
    """有统计数字就必须能复核。"""
    text = "\n".join(l for l, m in zip(lines, mask) if not m)
    stats = re.search(r"\d+(\.\d+)?%|\d{3,} ?条|样本|抽样|统计", text)
    scope = re.search(r"口径|统计范围|数据窗口|时间窗口|数据来源", text)
    if stats and not scope:
        return [("error", 1, "含统计数据但未声明口径/数据窗口，读者无法复核")]
    return []


def check_density(lines, mask):
    """连续长散文多半该改成表格。"""
    out, run, start = [], 0, 0
    for i, ln in enumerate(lines, 1):
        if mask[i - 1] or HEADING.match(ln) or ROW.match(ln) or not ln.strip():
            run = 0
            continue
        if run == 0:
            start = i
        run += len(ln.strip())
        if run > 320:
            out.append(("warn", start, f"连续散文 {run} 字，考虑拆成表格或列表"))
            run = 0
    return out


DISABLE = re.compile(r"<!--\s*doc-lint:disable\s+([^>]+?)\s*-->")


def disabled_groups(lines):
    """文件任意位置的 <!-- doc-lint:disable 文风,标题 --> 关闭对应检查组。

    用于列举反面例句的元文档（如规范本身），否则示例会被当成违规。
    """
    off = set()
    for ln in lines:
        m = DISABLE.search(ln)
        if m:
            off.update(g.strip() for g in re.split(r"[,，\s]+", m.group(1)) if g.strip())
    return off


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    strict = "--strict" in sys.argv
    path = args[0]
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    mask = code_mask(lines)
    off = disabled_groups(lines)

    groups = [
        ("文风", check_style(lines, mask) + check_bold(lines, mask)),
        ("标题", check_headings(lines, mask)),
        ("表格", check_tables(lines, mask)),
        ("Mermaid", check_mermaid(lines)),
        ("数据口径", check_provenance(lines, mask)),
        ("段落密度", check_density(lines, mask)),
    ]
    groups = [(n, [] if n in off else it) for n, it in groups]
    if off:
        print(f"（已按 doc-lint:disable 跳过：{'、'.join(sorted(off))}）")

    n_err = n_warn = 0
    for name, items in groups:
        if name in off:
            print(f"[skip] {name}")
            continue
        if not items:
            print(f"[ok]   {name}")
            continue
        errs = [x for x in items if x[0] == "error"]
        n_err += len(errs)
        n_warn += len(items) - len(errs)
        print(f"[{name}] {len(errs)} error / {len(items) - len(errs)} warn")
        for lvl, ln, msg in sorted(items, key=lambda x: x[1])[:20]:
            print(f"  {'E' if lvl == 'error' else 'W'} {path}:{ln}  {msg}")
        if len(items) > 20:
            print(f"  ... 另有 {len(items) - 20} 条")

    print(f"\n合计 {n_err} error / {n_warn} warn")
    return 1 if (n_err or (strict and n_warn)) else 0


if __name__ == "__main__":
    sys.exit(main())
