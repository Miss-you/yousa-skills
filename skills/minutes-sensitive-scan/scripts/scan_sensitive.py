#!/usr/bin/env python3
"""会议纪要敏感信息扫描器。

用法: python3 scan_sensitive.py <file.md> [--names "名字1,名字2,机构A"]

按九类风险输出命中清单（类别/行号/原文片段）。只负责"找嫌疑"，
删改决定由人/agent 按 SKILL.md 第 2 步逐项判断。
退出码: 0=无命中, 1=有命中, 2=用法错误。
"""
import re
import sys

CATEGORIES = {
    "1-直接身份(需--names提供)": [],  # 由 --names 注入本场景的人名/机构名及变体
    "2-职级暗示": [
        r"总裁", r"掌门人", r"董事长", r"创始人兼", r"一把手",
        r"CEO", r"CTO", r"CFO", r"COO", r"CIO",
        r"VP", r"副总裁", r"首席[^\s，。,\.]{1,4}官",
        r"合伙人", r"联合创始人", r"联创",
        r"教授", r"院长", r"主任医师", r"总监",
    ],
    "3-玩笑话与人事信号": [
        r"摸鱼", r"监控", r"放个豆豆", r"全景监狱",
        r"headcount", r"不用\s*fill", r"裁员", r"裁人", r"不用补", r"编制冻结",
    ],
    "5-口语化敏感词": [
        r"坐牢", r"裸奔", r"老登", r"翻墙", r"金句", r"吃灰", r"死穴",
        r"刀法", r"诛心", r"ICU", r"彩蛋", r"拷问", r"杀手锏", r"爆款文",
    ],
    "6-结构性风险": [r"^#+\s*.*(金句|TOP\s*\d|故事集|名场面)", r"语录"],
    "7-外链(逐条人工核对是否击穿匿名)": [r"https?://[^\s)\]]+"],
    "8-指纹细节(精确数字需人工判断)": [
        r"\d+(\.\d+)?\s*(亿|万)?\s*(美金|美元|元|人民币)/?(周|月|年)?",
        r"\d+\s*个团队", r"\d+\s*人(团队|公司|的公司)", r"[七八九]成",
        r"[近上]?[百千万][余多]?个(团队|人)",  # 中文数词指纹
        r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}",  # 精确日期
    ],
    "9-第三方未公开信息": [r"内测", r"未发布", r"内部数据", r"还没对外"],
    "10-编辑残留": [
        r"[一-鿿]\s{1,}[一-鿿]",  # 中文间异常空格（删词痕迹）
        r"终稿撰写人", r"占位", r"TODO", r"XXX",
    ],
}

# 7 类外链中点开即可能实名的高风险域名（命中时单独标注）
RISKY_LINK_HINT = re.compile(r"ithome|qcc\.com|tianyancha|linkedin|zhipin|maimai|baike", re.I)
# 8 类中允许的相对模糊表达，不报
FUZZY_OK = re.compile(r"(数十|数百|数千|大量|多个|若干|几十|上百|近年)")
# 8 类豁免：带 URL 的行是对公开资料的引用，数字属于第三方公开数据而非主体指纹
# （该行的链接风险仍由第 7 类单独覆盖）
CITATION_LINE = re.compile(r"https?://")


def scan(path: str, names: list[str]) -> int:
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError as e:
        print(f"无法读取 {path}: {e}", file=sys.stderr)
        return 2

    cats = dict(CATEGORIES)
    if names:
        cats["1-直接身份(需--names提供)"] = [re.escape(n.strip()) for n in names if n.strip()]
    else:
        print("⚠️ 警告：未传 --names，第 1 类（直接身份）未启用——这是最危险的类别，"
              "请传入本场景人名/机构名及全部变体后重跑", file=sys.stderr)

    total = 0
    for cat, pats in cats.items():
        if not pats:
            continue
        hits = []
        for i, line in enumerate(lines, 1):
            for p in pats:
                for m in re.finditer(p, line, re.M):
                    frag = line.strip()
                    if cat.startswith("8-") and (FUZZY_OK.search(frag) or CITATION_LINE.search(frag)):
                        continue
                    tag = ""
                    if cat.startswith("7-") and RISKY_LINK_HINT.search(m.group(0)):
                        tag = "  ⚠️ 高风险域名(可能击穿匿名)"
                    hits.append(f"  L{i}: {frag[:90]}{tag}")
                    break
        if hits:
            # 同一行多模式只报一次，去重保序
            uniq = list(dict.fromkeys(hits))
            print(f"\n【{cat}】{len(uniq)} 处")
            print("\n".join(uniq))
            total += len(uniq)

    print(f"\n==== 合计 {total} 处嫌疑（含需人工判断项，非全是违规）====")
    print("注：第 4 类（点评同行）为语义级风险，机器不扫描，必须按 SKILL.md 第 2 步人工覆盖")
    return 1 if total else 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    names = []
    if "--names" in args:
        idx = args.index("--names")
        try:
            names = args[idx + 1].split(",")
        except IndexError:
            print("--names 需要参数，如 --names '张三,某某公司'", file=sys.stderr)
            return 2
        args = args[:idx] + args[idx + 2:]
    return scan(args[0], names)


if __name__ == "__main__":
    sys.exit(main())
