#!/usr/bin/env python3
"""按文件统计注释密度、定位长注释块、发现失效引用。

用法：
    comment_audit.py                 # 审 git diff + 未跟踪文件
    comment_audit.py FILE [FILE...]  # 审指定文件

输出三块：密度对照、函数体内的长注释块、注释里已不存在的标识符。
三者都只是**线索**，不是判决——取舍由 SKILL.md 的判据决定。
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

LINE_COMMENT = {
    ".go": "//", ".java": "//", ".ts": "//", ".tsx": "//", ".js": "//", ".jsx": "//",
    ".c": "//", ".h": "//", ".cc": "//", ".cpp": "//", ".rs": "//", ".kt": "//", ".swift": "//",
    ".py": "#", ".rb": "#", ".sh": "#",
}
# 函数体内连续 N 行以上的注释，多半是设计论证而非「改这里要小心什么」
LONG_BLOCK = 4


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout.split()


def changed_files():
    out = set(sh("git", "diff", "--name-only"))
    out |= set(sh("git", "diff", "--cached", "--name-only"))
    out |= set(sh("git", "ls-files", "-o", "--exclude-standard"))
    return sorted(f for f in out if os.path.splitext(f)[1] in LINE_COMMENT and os.path.exists(f))


def scan(path):
    """返回 (注释行数, 代码行数, [(起始行, 块行数, 是否缩进)])."""
    marker = LINE_COMMENT[os.path.splitext(path)[1]]
    comment = code = 0
    blocks, run_start, run_len, run_indented = [], 0, 0, False
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError):
        return 0, 0, []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s:
            continue
        if s.startswith(marker):
            comment += 1
            if run_len == 0:
                run_start, run_indented = i, raw[:1] in (" ", "\t")
            run_len += 1
        else:
            code += 1
            if run_len >= LONG_BLOCK:
                blocks.append((run_start, run_len, run_indented))
            run_len = 0
    if run_len >= LONG_BLOCK:
        blocks.append((run_start, run_len, run_indented))
    return comment, code, blocks


def is_test(path):
    n = os.path.basename(path)
    return "_test." in n or n.startswith("test_") or ".test." in n or "/tests/" in path


def baseline(exts, exclude):
    """仓内同后缀、不在本次改动内的文件的密度基线。

    测试与非测试分开统计——测试天然注释更多（每个用例要说清它防的是什么事故），
    拿测试去比非测试基线会得出「哪都超标」的假结论。
    """
    per = defaultdict(lambda: [0, 0])
    for f in sh("git", "ls-files"):
        ext = os.path.splitext(f)[1]
        if ext not in exts or f in exclude or not os.path.exists(f):
            continue
        key = (ext, is_test(f))
        c, x, _ = scan(f)
        per[key][0] += c
        per[key][1] += x
    return {k: (c / (c + x) * 100 if c + x else 0.0) for k, (c, x) in per.items()}


IDENT = re.compile(r"[`\s(（]([A-Za-z_][A-Za-z0-9_]{5,})[`\s,.)）:：]")


def stale_refs(paths):
    """注释里提到、但仓内代码中已不存在的标识符。删了代码没删注释的信号。"""
    found = defaultdict(set)
    for p in paths:
        marker = LINE_COMMENT[os.path.splitext(p)[1]]
        try:
            lines = open(p, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, raw in enumerate(lines, 1):
            s = raw.strip()
            if not s.startswith(marker):
                continue
            for m in IDENT.finditer(" " + s[len(marker):] + " "):
                w = m.group(1)
                if w.islower() and "_" not in w:
                    continue  # 普通英文词
                found[w].add(f"{p}:{i}")
    stale = {}
    for w, locs in found.items():
        hits = subprocess.run(["git", "grep", "-lw", w], capture_output=True, text=True).stdout.split()
        cited_in = {l.rsplit(":", 1)[0] for l in locs}
        if any(h not in cited_in for h in hits):
            continue  # 别处代码里有，不算失效
        if any(_in_code(w, f) for f in cited_in):
            continue  # 就在本文件的代码里
        stale[w] = sorted(locs)
    return stale


def _in_code(word, path):
    """该标识符是否出现在 path 的**非注释**行里。"""
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    marker = LINE_COMMENT[os.path.splitext(path)[1]]
    pat = re.compile(r"\b" + re.escape(word) + r"\b")
    return any(pat.search(l) for l in lines if not l.strip().startswith(marker))


def main():
    files = [f for f in (sys.argv[1:] or changed_files()) if os.path.exists(f)]
    if not files:
        print("没有可审的文件")
        return
    base = baseline({os.path.splitext(f)[1] for f in files}, set(files))

    rows, tc, tx = [], 0, 0
    for f in files:
        c, x, blocks = scan(f)
        if c + x == 0:
            continue
        tc, tx = tc + c, tx + x
        ratio = c / (c + x) * 100
        b = base.get((os.path.splitext(f)[1], is_test(f)), 0.0)
        rows.append((ratio, f, c, x, b, blocks))

    print("== 注释密度（对照仓内同类文件基线）==")
    for ratio, f, c, x, b, _ in sorted(rows, reverse=True):
        flag = "  ← 显著偏高" if b and ratio > b * 1.5 else ""
        print(f"  {ratio:5.1f}%  注释{c:4d} 代码{x:4d}  基线{b:5.1f}%  {f}{flag}")
    if tc + tx:
        print(f"  合计 {tc / (tc + tx) * 100:.1f}%（注释 {tc} / 代码 {tx}）")

    print(f"\n== 函数体内 >= {LONG_BLOCK} 行的注释块（最可能该搬进设计文档）==")
    hit = False
    for _, f, _, _, _, blocks in rows:
        for start, length, indented in blocks:
            if indented:
                hit = True
                print(f"  {f}:{start}  {length} 行")
    if not hit:
        print("  无")

    print("\n== 注释提到、但代码里已不存在的标识符（注释烂在原地）==")
    stale = stale_refs(files)
    if not stale:
        print("  无")
    for w, locs in sorted(stale.items()):
        print(f"  {w:<28} {', '.join(locs[:3])}")


if __name__ == "__main__":
    main()
