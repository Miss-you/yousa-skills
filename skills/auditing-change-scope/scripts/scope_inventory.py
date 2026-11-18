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
    untracked = [p for p in run(["git", "ls-files", "-z", "--others", "--exclude-standard"], root).split("\0") if p]
    return run(["git", "-c", "core.quotePath=false", "diff", "HEAD"], root), untracked, "git"


def strip_prefix(path):
    """去掉 a/ b/ 以及 diff -ruN 的顶层目录（before/ after/）。"""
    path = path.split("\t")[0].strip().strip('"')
    if path in ("/dev/null", ""):
        return None
    if path[:2] in ("a/", "b/"):
        return path[2:]
    return path


def git_header_paths(rest):
    """解析 `diff --git a/X b/Y` 的 X、Y；路径含空格且两侧相同时按对半切。"""
    half = (len(rest) - 1) // 2
    if rest[half:half + 1] == " " and rest[2:half] == rest[half + 3:]:
        return strip_prefix(rest[:half]), strip_prefix(rest[half + 1:])
    m = re.match(r'("?a/.+?"?) ("?b/.+"?)$', rest)
    return (strip_prefix(m.group(1)), strip_prefix(m.group(2))) if m else (None, None)


def new_entry(old, new, git_header=False):
    return {"old": old, "new": new, "add": [], "del": [], "sides": [], "hunks": 0, "mod_hunks": 0,
            "git_header": git_header, "headers_done": False}


def parse(diff_text, strip_levels):
    """按 hunk 头声明的行数消费 hunk 内容，避免把 `--- xxx` 这样的删除行当成文件头。

    git 格式的 `diff --git` 头单独建条目，所以二进制、仅权限、纯重命名这类没有 ---/+++ 的改动也会被清点。
    """
    files, cur = [], None
    old_rem = new_rem = 0
    for line in diff_text.splitlines():
        if old_rem > 0 or new_rem > 0:
            if line.startswith("\\"):
                continue
            tag, body = line[:1], line[1:]
            old_side, new_side = cur["sides"][-1]
            if tag == "+":
                cur["add"].append(body)
                new_side.append(body)
                new_rem -= 1
            elif tag == "-":
                cur["del"].append(body)
                old_side.append(body)
                old_rem -= 1
                if not cur["_hunk_has_del"]:
                    cur["mod_hunks"] += 1
                    cur["_hunk_has_del"] = True
            else:
                old_side.append(body)
                new_side.append(body)
                old_rem -= 1
                new_rem -= 1
            continue
        if line.startswith("diff --git "):
            old, new = git_header_paths(line[len("diff --git "):])
            cur = new_entry(old, new, git_header=True)
            files.append(cur)
        elif cur is not None and cur["git_header"] and cur["hunks"] == 0 and not cur["headers_done"] \
                and line.startswith(("new file mode", "deleted file mode", "rename from ", "rename to ",
                                     "old mode", "new mode", "Binary files", "GIT binary patch")):
            if line.startswith("new file mode"):
                cur["old"] = None
            elif line.startswith("deleted file mode"):
                cur["new"] = None
            elif line.startswith("rename from "):
                cur["old"], cur["renamed"] = line[len("rename from "):], True
            elif line.startswith("rename to "):
                cur["new"], cur["renamed"] = line[len("rename to "):], True
            elif line.startswith(("Binary files", "GIT binary patch")):
                cur["binary"] = True
            else:
                cur["mode"] = True
        elif line.startswith("--- "):
            old = strip_prefix(line[4:])
            if cur is not None and cur["git_header"] and cur["hunks"] == 0 and not cur["headers_done"]:
                cur["old"] = old
            else:
                cur = new_entry(old, None)
                files.append(cur)
        elif line.startswith("+++ ") and cur is not None and not cur["headers_done"]:
            cur["new"] = strip_prefix(line[4:])
            cur["headers_done"] = True
        elif line.startswith("@@") and cur is not None:
            m = HUNK_RE.match(line)
            if not m:
                continue
            if cur["hunks"] == 0:
                cur["old_empty"] = m.group(1) == "0" and m.group(2) == "0"
                cur["new_empty"] = m.group(3) == "0" and m.group(4) == "0"
            old_rem = int(m.group(2)) if m.group(2) is not None else 1
            new_rem = int(m.group(4)) if m.group(4) is not None else 1
            cur["hunks"] += 1
            cur["sides"].append(([], []))
            cur["headers_done"] = True
            cur["_hunk_has_del"] = False
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


def codeowners_regex(pattern):
    """把一条 CODEOWNERS 模式（gitignore 语法子集）转成匹配仓库相对路径的正则。"""
    dir_only = pattern.endswith("/")
    anchored = pattern.startswith("/") or "/" in pattern.rstrip("/")
    p = pattern.strip("/")
    out, i = [], 0
    while i < len(p):
        if p.startswith("**/", i):
            out.append("(?:.*/)?"); i += 3
        elif p.startswith("**", i):
            out.append(".*"); i += 2
        elif p[i] == "*":
            out.append("[^/]*"); i += 1
        elif p[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(p[i])); i += 1
    body = "".join(out)
    return re.compile(("^" if anchored else "^(?:.*/)?") + body + ("/.*$" if dir_only else "(?:/.*)?$"))


def owners_of(owner_file, owner_text, rel_path):
    """返回适用于 rel_path 的归属文本；CODEOWNERS 取最后一条匹配规则，无匹配返回 None。

    OWNERS / MAINTAINERS 是按目录生效的，整份文件就是该目录的归属。
    """
    if os.path.basename(owner_file) != "CODEOWNERS":
        return owner_text
    owners = None
    for raw in owner_text.splitlines():
        parts = raw.split("#", 1)[0].split()
        if parts and codeowners_regex(parts[0]).match(rel_path):
            owners = " ".join(parts[1:])
    return owners


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
        elif f["hunks"] == 0:
            what = [w for k, w in (("renamed", "重命名"), ("mode", "权限"), ("binary", "二进制")) if f.get(k)]
            kind = f"修改·无文本差异（{'/'.join(what) or '元数据'}）"
        elif f["mod_hunks"] == 0:
            kind = "修改·纯追加"
        else:
            # 逐块比较含上下文的新旧两侧，只忽略首尾空白和空行、保留行序；换行重排等情况保守地算作改了既有行
            norm = lambda ls: [x.strip() for x in ls if x.strip()]
            same = all(norm(old) == norm(new) for old, new in f["sides"])
            kind = "修改·仅格式" if same else "修改·改了既有行"
            if f.get("renamed"):
                kind += "+重命名"
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
            owners = owners_of(owner_file, owner_text, path)
            if owners is None:
                flags.append(f"归属 {owner_file}: 无匹配规则")
            else:
                mine = any(m and re.search(r"\b" + re.escape(m) + r"\b", owners) for m in me)
                flags.append(f"归属 {owner_file}: {'含当前用户' if mine else '不含当前用户'}")
        else:
            flags.append("未找到 OWNERS")
        detail = f"+{add}/-{dele}" + (f"，{mod_h}/{hunks} 个块动了既有行" if mod_h else "")
        print(f"- [{kind}] {path}  ({detail})  {'；'.join(flags)}")

    touched = [r for r in rows if "改了既有行" in r[1] or "无文本差异" in r[1] or r[1] in ("删除文件", "修改·仅格式")]
    print(f"\n需要逐块说明授权来源的文件: {len(touched)} 个（动了既有行 / 删除 / 仅格式 / 无文本差异）")
    print("纯新增与纯追加也要能指到用户原话，但不改变既有行为。")


if __name__ == "__main__":
    main()
