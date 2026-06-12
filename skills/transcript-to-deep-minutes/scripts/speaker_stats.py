#!/usr/bin/env python3
"""转录说话人统计与核心嘉宾线索分析（阶段 0 辅助）。

用法: python3 speaker_stats.py <转录.md> [--honorific 老师,总,哥]

输入格式假设: 每段以"说话人 N <时间戳>"单独成行开头，时间戳兼容 MM:SS 与 H:MM:SS 双格式。
输出: ① 按字数排序的说话人分布 ② 称呼-接答配对表 ③ 混人嫌疑（矛盾检测）
      ④ 时间戳→行号映射（每 10 分钟一个锚点，供切 chunk 用）
本脚本只产出证据，嘉宾判定结论由主流程按 SKILL.md 阶段 0 交叉确认并呈报用户。
"""
import re
import sys
from collections import Counter, defaultdict

TURN_RE = re.compile(r"^(说话人\s*\d+)\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*$")


def ts_to_sec(ts: str) -> int:
    parts = [int(x) for x in ts.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def parse(path: str):
    """返回 [(speaker, ts, line_no, content)]。"""
    turns = []
    cur = None
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        m = TURN_RE.match(line.strip())
        if m:
            if cur:
                turns.append(cur)
            cur = [m.group(1), m.group(2), i, ""]
        elif cur:
            cur[3] += line
    if cur:
        turns.append(cur)
    return turns


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    honorifics = ["老师", "总", "哥"]
    if "--honorific" in args:
        idx = args.index("--honorific")
        honorifics = args[idx + 1].split(",")
        args = args[:idx] + args[idx + 2:]
    turns = parse(args[0])
    if not turns:
        print("未解析到任何发言段——检查转录格式是否为每段以'说话人 N 时间戳'开头", file=sys.stderr)
        return 1

    # ① 字数分布
    chars = Counter()
    for sp, _, _, c in turns:
        chars[sp] += len(c.strip())
    print(f"== ① 说话人分布（共 {len(chars)} 个标签 / {len(turns)} 段）==")
    for sp, n in chars.most_common(10):
        print(f"  {n:7d} 字  {sp}")

    # ② 称呼-接答配对：含"<称呼词>"且像提问的段，看下一段谁接
    print("\n== ② 称呼-接答配对（嘉宾线索：被频繁称呼且由同一标签接答）==")
    addr_re = re.compile(r"([一-鿿A-Za-z]{1,6}(?:" + "|".join(map(re.escape, honorifics)) + r"))")
    follow = defaultdict(Counter)
    for k, (sp, ts, ln, c) in enumerate(turns[:-1]):
        m = addr_re.search(c)
        if m and ("问" in c or "请教" in c or "？" in c or "?" in c):
            follow[m.group(1)][turns[k + 1][0]] += 1
    for addr, ctr in sorted(follow.items(), key=lambda x: -sum(x[1].values()))[:8]:
        total = sum(ctr.values())
        top, n = ctr.most_common(1)[0]
        if total >= 2:
            print(f"  称呼「{addr}」后接答: {top} {n}/{total} 次  {'⭐ 强信号' if n/total >= 0.6 else ''}")

    # ③ 混人嫌疑（矛盾检测）：先取字数第一为嘉宾候选，再找"既向候选提问、又有候选式自述"的标签
    guest = chars.most_common(1)[0][0]
    print(f"\n== ③ 混人嫌疑（以字数第一 {guest} 为嘉宾候选做矛盾检测）==")
    main_addrs = [a for a in follow if follow[a].most_common(1)[0][0] == guest]
    suspects = defaultdict(list)
    for sp, ts, ln, c in turns:
        if sp == guest:
            continue
        asked = any(a in c for a in main_addrs) and ("问" in c or "请教" in c)
        selfclaim = re.search(r"我(是|在|们公司|们机构|加入了)", c) and len(c.strip()) > 60
        if asked:
            suspects[sp].append(("问嘉宾", ts))
        elif selfclaim:
            suspects[sp].append(("自述", ts))
    for sp, evs in suspects.items():
        kinds = {k for k, _ in evs}
        if len(kinds) > 1 and len(evs) >= 3:
            print(f"  ⚠️ {sp}: 同标签下既有提问又有多段自述（{len(evs)} 条线索）——疑似多人混合，样例时间戳 {[t for _, t in evs[:4]]}")

    # ④ 时间锚点 → 行号（切 chunk 用）
    print("\n== ④ 时间锚点 → 行号（每 ~10 分钟）==")
    last = -600
    for sp, ts, ln, _ in turns:
        sec = ts_to_sec(ts)
        if sec - last >= 600:
            print(f"  {ts:>8}  L{ln}")
            last = sec
    return 0


if __name__ == "__main__":
    sys.exit(main())
