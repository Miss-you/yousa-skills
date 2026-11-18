#!/usr/bin/env python3
"""改动清点：逐文件列出「新增 / 改了既有行 / 仅格式」、归属和风险提示，供范围审计逐块分类。

只做清点，不下结论。结论由 SKILL.md 的分类表给出。

用法:
  scope_inventory.py                      # 当前目录：git（含未跟踪文件）或 svn 工作区
  scope_inventory.py --diff-file X.diff   # 读取 unified diff（diff -ruN / git diff / svn diff）
  scope_inventory.py --root DIR           # 指定仓库根，用于查找 OWNERS / CODEOWNERS
  scope_inventory.py --me NAME            # 用户在 OWNERS 里的名字（默认取 git user.name / email 前缀）
"""
import argparse
import os
import re
import subprocess
import sys

CONFIG_EXT = (".yaml", ".yml", ".json", ".toml", ".ini", ".conf", ".properties", ".env")
DEP_FILES = ("go.mod", "go.sum", "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
             "requirements.txt", "poetry.lock", "Cargo.toml", "Cargo.lock", "pom.xml", "build.gradle")
HUNK_RE = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
OWNER_FILES = ("OWNERS", "CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS", "MAINTAINERS")


def run(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace").stdout
    except OSError:
        return ""


def collect_diff(root):
    """返回 (diff 文本, 未跟踪文件列表, vcs 名)。"""
    if os.path.isdir(os.path.join(root, ".svn")):
        return run(["svn", "diff"], root), [
            line[8:].strip() for line in run(["svn", "status"], root).splitlines() if line.startswith("?")
        ], "svn"
    top = run(["git", "rev-parse", "--show-toplevel"], root).strip()
    if not top:
        sys.exit("不是 git / svn 工作区，请用 --diff-file 传入补丁")
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], root).split()
    return run(["git", "diff", "HEAD"], root), untracked, "git"


def strip_prefix(path):
    """去掉 a/ b/ 以及 diff -ruN 的顶层目录（before/ after/）。"""
    path = path.split("\t")[0].strip()
    if path in ("/dev/null", ""):
        return None
    if path[:2] in ("a/", "b/"):
        return path[2:]
    return path


def parse(diff_text, strip_levels):
    files, cur = [], None
    for line in diff_text.splitlines():
        if line.startswith("--- "):
            cur = {"old": strip_prefix(line[4:]), "new": None, "add": [], "del": [], "hunks": 0, "mod_hunks": 0}
            files.append(cur)
        elif line.startswith("+++ ") and cur is not None and cur["new"] is None:
            cur["new"] = strip_prefix(line[4:])
        elif line.startswith("@@") and cur is not None:
            m = HUNK_RE.match(line)
            if m and cur["hunks"] == 0:
                cur["old_empty"] = m.group(1) == "0" and m.group(2) == "0"
                cur["new_empty"] = m.group(3) == "0" and m.group(4) == "0"
            cur["hunks"] += 1
            cur["_hunk_has_del"] = False
        elif cur is not None and cur["new"] is not None:
            if line.startswith("+"):
                cur["add"].append(line[1:])
            elif line.startswith("-"):
                cur["del"].append(line[1:])
                if not cur.get("_hunk_has_del"):
                    cur["mod_hunks"] += 1
                    cur["_hunk_has_del"] = True
    for f in files:
        for key in ("old", "new"):
            if f[key] and strip_levels:
                f[key] = "/".join(f[key].split("/")[strip_levels:])
    return files


def owners_for(root, rel_path):
    """自文件所在目录向上找 OWNERS 类文件，返回 (文件相对路径, 内容)。"""
    d = os.path.dirname(os.path.join(root, rel_path))
    root = os.path.abspath(root)
    while True:
        for name in OWNER_FILES:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    return os.path.relpath(p, root), open(p, errors="replace").read()
                except OSError:
                    pass
        if os.path.abspath(d) == root or os.path.dirname(d) == d:
            return None, ""
        d = os.path.dirname(d)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diff-file")
    ap.add_argument("--root", default=".")
    ap.add_argument("--me", default="")
    ap.add_argument("--strip", type=int, default=0, help="路径去掉前 N 层目录（diff -ruN before after 用 1）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    untracked, vcs = [], "diff-file"
    if args.diff_file:
        text = open(args.diff_file, errors="replace").read()
    else:
        text, untracked, vcs = collect_diff(root)

    me = [args.me] if args.me else []
    if not me:
        for key in ("user.name", "user.email"):
            v = run(["git", "config", key], root).strip()
            if v:
                me.append(v.split("@")[0])

    rows = []
    for f in parse(text, args.strip):
        path = f["new"] or f["old"]
        if not path:
            continue
        if f["new"] is None or f.get("new_empty"):
            kind = "删除文件"
        elif f["old"] is None or f.get("old_empty"):
            kind = "新增文件"
        elif f["mod_hunks"] == 0:
            kind = "修改·纯追加"
        else:
            squash = lambda ls: sorted(re.sub(r"\s+", "", x) for x in ls if x.strip())
            kind = "修改·仅格式" if squash(f["add"]) == squash(f["del"]) else "修改·改了既有行"
        rows.append((path, kind, len(f["add"]), len(f["del"]), f["mod_hunks"], f["hunks"]))
    for p in untracked:
        rows.append((p, "新增文件(未跟踪)", 0, 0, 0, 0))

    print(f"== 改动清点（来源: {vcs}，共 {len(rows)} 个文件）==")
    print(f"当前用户标识: {', '.join(me) or '未知（用 --me 指定）'}\n")
    for path, kind, add, dele, mod_h, hunks in sorted(rows, key=lambda r: (r[1].startswith("新增"), r[0])):
        flags = []
        base = os.path.basename(path)
        if base in DEP_FILES:
            flags.append("依赖清单")
        elif path.endswith(CONFIG_EXT):
            flags.append("配置文件")
        owner_file, owner_text = owners_for(root, path)
        if owner_file:
            mine = any(m and re.search(r"\b" + re.escape(m) + r"\b", owner_text) for m in me)
            flags.append(f"归属 {owner_file}: {'含当前用户' if mine else '不含当前用户'}")
        else:
            flags.append("未找到 OWNERS")
        detail = f"+{add}/-{dele}" + (f"，{mod_h}/{hunks} 个块动了既有行" if mod_h else "")
        print(f"- [{kind}] {path}  ({detail})  {'；'.join(flags)}")

    touched = [r for r in rows if "改了既有行" in r[1] or r[1] in ("删除文件", "修改·仅格式")]
    print(f"\n需要逐块说明授权来源的文件: {len(touched)} 个（动了既有行 / 删除 / 仅格式）")
    print("纯新增与纯追加也要能指到用户原话，但不改变既有行为。")


if __name__ == "__main__":
    main()
