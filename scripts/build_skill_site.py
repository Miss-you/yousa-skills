"""Build the public registry from the repository's bilingual inventory."""
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

if __package__:
    from .render_readmes import load_manifest, repo_root, validate_manifest
else:
    from render_readmes import load_manifest, repo_root, validate_manifest

ORIGIN = "https://skills.yousali.com"
REPO = "https://github.com/Miss-you/yousa-skills"
ASSETS = ("registry.css", "registry.js")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def copy_button(text: str, label: str, name: str, *, primary: bool = False) -> str:
    kind = "button primary" if primary else "button"
    return (
        f'<button type="button" class="{kind}" data-copy="{html.escape(text)}" '
        f'aria-label="{label} · {name}" hidden>{label}</button>'
    )


def install_prompt(name: str) -> str:
    source = f"{REPO}/tree/main/skills/{name}"
    return (
        f"Install the {name} skill from {source} into this workspace. "
        "Start from AGENTS.md and follow any WORKSPACE.md routing rules. Clone or vendor the repository "
        "under the appropriate project directory. Keep this skill's directory and its companion files "
        "together. Expose its single SKILL.md through the workspace's skill-discovery chain and register "
        "it in the local index if present. Keep private aliases, paths, and credentials in a local overlay."
    )


def download_link(name: str, label: str) -> str:
    return f'<a class="button" href="/downloads/{name}.zip" download aria-label="{label} · {name}">{label}</a>'


def layout(title: str, description: str, path: str, alternate: str, zh: bool, body: str) -> str:
    lang = "zh-CN" if zh else "en"
    home = "/" if zh else "/en/"
    catalog = "技能目录" if zh else "Catalog"
    homepage = "个人主页" if zh else "About Yousa"
    switch = "English" if zh else "简体中文"
    switch_lang = "en" if zh else "zh-CN"
    theme = "切换明暗主题" if zh else "Toggle light/dark theme"
    copied = "已复制" if zh else "Copied"
    manual = "手动复制" if zh else "Copy manually"
    failed = "剪贴板不可用，请复制下方已选中的文本。" if zh else "Clipboard unavailable. Copy the selected text."
    close = "关闭" if zh else "Close"
    main_nav = "主导航" if zh else "Main navigation"
    skip = "跳到主要内容" if zh else "Skip to main content"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{ORIGIN}{path}">
  <link rel="canonical" href="{ORIGIN}{path}">
  <link rel="alternate" hreflang="{switch_lang}" href="{ORIGIN}{alternate}">
  <link rel="stylesheet" href="/assets/registry.css">
  <script src="/assets/registry.js" defer></script>
  <title>{html.escape(title)}</title>
</head>
<body data-copied="{copied}">
  <a class="skip-link" href="#main-content">{skip}</a>
  <header class="site-header">
    <div class="site-header-inner">
      <div class="site-brand-row">
        <a class="site-brand" href="https://yousali.com/">Yousa Driven Development | YDD</a>
        <div class="site-controls">
          <button id="theme-toggle" type="button" aria-pressed="false" aria-label="{theme}" hidden><span aria-hidden="true"></span></button>
          <a href="{alternate}" hreflang="{switch_lang}" lang="{switch_lang}" aria-label="{switch}">{"En" if zh else "中文"}</a>
        </div>
      </div>
      <nav class="site-menu" aria-label="{main_nav}">
        <a href="https://yousali.com/">{homepage}</a>
        <a href="{home}" aria-current="{'page' if path == home else 'location'}">{catalog}</a>
        <a href="{REPO}">GitHub</a>
      </nav>
    </div>
  </header>
  <main id="main-content">{body}</main>
  <div id="copy-status" class="visually-hidden" role="status"></div>
  <dialog id="copy-fallback" aria-labelledby="copy-heading">
    <form method="dialog">
      <h2 id="copy-heading">{manual}</h2>
      <p id="copy-instruction">{failed}</p>
      <textarea readonly rows="7" aria-labelledby="copy-heading" aria-describedby="copy-instruction"></textarea>
      <button class="button" type="submit">{close}</button>
    </form>
  </dialog>
  <footer><a href="https://yousali.com/">{homepage}</a> <span aria-hidden="true">·</span>
    <a href="{REPO}">Miss-you / yousa-skills</a></footer>
</body>
</html>
"""


def description_for(entry: dict, zh: bool) -> str:
    return entry["description_zh" if zh else "description_en"]


def catalog_page(entries: list[dict], zh: bool) -> str:
    prefix = "" if zh else "/en"
    title = "Skills 目录" if zh else "Skills catalog"
    intro = (
        "浏览公开 Skill，把安装提示发给你的编程助手，或下载 ZIP 手动安装。"
        if zh else "Browse public skills. Send an install prompt to your coding agent or download a ZIP."
    )
    search_label = "搜索 Skill" if zh else "Search skills"
    placeholder = "名称或简介，例如「代码」" if zh else "Name or description, e.g. code review"
    count = f"全部 {len(entries)} 项" if zh else f"All {len(entries)} skills"
    no_results = "没有匹配的 Skill。" if zh else "No matching skills."
    clear = "清除搜索" if zh else "Clear search"
    copy = "复制安装提示" if zh else "Copy install prompt"
    download = "下载 ZIP" if zh else "Download ZIP"
    rows = []
    for entry in sorted(entries, key=lambda item: item["name"]):
        name = entry["name"]
        desc = html.escape(description_for(entry, zh))
        search_text = html.escape(" ".join((name, name.replace("-", " "), entry["description_en"], entry["description_zh"])))
        rows.append(f"""
        <li class="skill-row" data-search="{search_text}">
          <div class="skill-info">
            <h2><a href="{prefix}/skills/{name}/">{name}</a></h2>
            <p>{desc}</p>
          </div>
          <div class="row-actions">
            {copy_button(install_prompt(name), copy, name, primary=True)}
            {download_link(name, download)}
          </div>
        </li>""")
    body = f"""
    <section class="intro">
      <h1>{title}</h1>
      <p>{intro}</p>
    </section>
    <section aria-label="{title}">
      <div class="catalog-tools">
        <form class="search" role="search" hidden>
          <label class="visually-hidden" for="skill-search">{search_label}</label>
          <input id="skill-search" type="search" autocomplete="off" placeholder="{placeholder}">
          <button class="button clear-search" type="reset" hidden>{clear}</button>
        </form>
        <p class="count" id="skill-count" role="status">{count}</p>
      </div>
      <p class="empty" id="no-results" hidden>{no_results}</p>
      <ul class="catalog">{''.join(rows)}</ul>
    </section>"""
    return layout(f"{title} · YDD", intro, f"{prefix}/", "/en/" if zh else "/", zh, body)


def detail_page(entry: dict, zh: bool) -> str:
    name = entry["name"]
    desc = description_for(entry, zh)
    prefix = "" if zh else "/en"
    route = f"/skills/{name}/"
    source = f"{REPO}/tree/main/skills/{name}"
    source_label = "查看源码 ↗" if zh else "View source ↗"
    back = "← 全部 Skills" if zh else "← All skills"
    kind = "分享的 Skill · GitHub 仓库" if zh else "Shared skill · GitHub repository"
    copy = "复制安装提示" if zh else "Copy install prompt"
    copy_link = "复制链接" if zh else "Copy link"
    install = "安装这个 Skill" if zh else "Install this skill"
    cli = "手动安装" if zh else "Manual installation"
    scope = (
        "默认安装到 Claude Code、Codex 和 Trae，并备份同名版本。"
        "添加 --claude-only、--codex-only 或 --trae-only 可只安装到一个客户端。"
        if zh else
        "Installs to Claude Code, Codex, and Trae with backups of existing copies. "
        "Add --claude-only, --codex-only, or --trae-only to select one client."
    )
    prompt = install_prompt(name)
    download = "下载 ZIP" if zh else "Download ZIP"
    zip_help = (
        "解压后将整个 Skill 文件夹放入客户端的技能目录，保留其中的子目录和文件。"
        if zh else "Unzip and place the entire skill folder in your client's skill directory."
    )
    command = f"git clone {REPO}.git\ncd yousa-skills\n./install.sh --backup {name}"
    windows = f"git clone {REPO}.git\ncd yousa-skills\n.\\install.ps1 --backup {name}"
    body = f"""
    <a class="back" href="{prefix}/">{back}</a>
    <article class="share-card">
      <p class="kind">{kind}</p>
      <h1>{name}</h1>
      <p class="description">{html.escape(desc)}</p>
      <div class="actions">
        {copy_button(prompt, copy, name, primary=True)}
        {download_link(name, download)}
        <a class="button" href="{source}">{source_label}</a>
        {copy_button(ORIGIN + prefix + route, copy_link, name)}
      </div>
    </article>
    <section class="install-panel" aria-labelledby="install-heading">
      <h2 id="install-heading">{install}</h2>
      <p>{"将这段提示发给你的编程助手。" if zh else "Send this prompt to your coding agent."}</p>
      <pre id="install-prompt">{html.escape(prompt)}</pre>
      <details><summary>{cli}</summary>
        <p>{zip_help}</p>
        <p>{scope}</p>
        <p>macOS / Linux</p><pre>{html.escape(command)}</pre>
        <p>Windows PowerShell</p><pre>{html.escape(windows)}</pre>
      </details>
    </section>"""
    return layout(f"{name} · Yousa Skills", desc, prefix + route, ("/en" if zh else "") + route, zh, body)


def missing_page(zh: bool) -> str:
    title = "找不到这个 Skill" if zh else "Skill not found"
    back = "返回技能目录" if zh else "Browse all skills"
    home = "/" if zh else "/en/"
    body = f'<section class="intro"><h1>{title}</h1><p><a href="{home}">{back}</a></p></section>'
    prefix, alternate = ("", "/en") if zh else ("/en", "")
    return layout(title, title, f"{prefix}/404.html", f"{alternate}/404.html", zh, body)


def archive_skills(root: Path, output: Path, entries: list[dict]) -> None:
    tree = subprocess.check_output(["git", "ls-tree", "-rz", "HEAD", "--", "skills/"], cwd=root)
    committed = set()
    for record in tree.split(b"\0"):
        if not record:
            continue
        metadata, filename = record.split(b"\t", 1)
        if metadata.split()[0] not in (b"100644", b"100755"):
            raise ValueError(f"Skill archive requires committed regular files: {os.fsdecode(filename)}")
        committed.add(os.fsdecode(filename))

    output.mkdir()
    for entry in entries:
        name, path = entry["name"], entry["path"]
        if f"{path}/SKILL.md" not in committed:
            raise ValueError(f"Commit {path}/SKILL.md before building its download")
        with (output / f"{name}.zip").open("wb") as archive:
            subprocess.run(
                ["git", "archive", "--format=zip", f"--prefix={name}/", f"HEAD:{path}"],
                cwd=root, stdout=archive, check=True,
            )


def build(output: Path) -> int:
    root = repo_root()
    entries = load_manifest(root)
    validate_manifest(entries, root)
    for entry in entries:
        name = entry["name"]
        if not SLUG.fullmatch(name) or entry["path"] != f"skills/{name}":
            raise ValueError(f"Skill must use a matching kebab-case directory: {name!r}")
        skill_dir = root / entry["path"]
        if skill_dir.is_symlink() or (skill_dir / "SKILL.md").is_symlink():
            raise ValueError(f"Skill must use checked-in files: {name!r}")

    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError(f"Build output must be empty: {output}")
    assets = output / "assets"
    assets.mkdir()
    for filename in ASSETS:
        source = root / "site" / filename
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Public asset must be a regular file: {source}")
        shutil.copyfile(source, assets / filename)
    archive_skills(root, output / "downloads", entries)
    for zh in (True, False):
        locale_dir = output if zh else output / "en"
        locale_dir.mkdir(exist_ok=True)
        (locale_dir / "index.html").write_text(catalog_page(entries, zh), encoding="utf-8")
        (locale_dir / "404.html").write_text(missing_page(zh), encoding="utf-8")
        for entry in entries:
            page = locale_dir / "skills" / entry["name"] / "index.html"
            page.parent.mkdir(parents=True)
            page.write_text(detail_page(entry, zh), encoding="utf-8")
    return len(entries)


def publish(destination: Path) -> int:
    """Build into a fresh release and switch the live symlink in one operation."""
    release_root = destination / "releases"
    release_root.mkdir(parents=True, exist_ok=True)
    release = Path(tempfile.mkdtemp(prefix="site-", dir=release_root))
    pending = destination / f".{release.name}.next"
    try:
        count = build(release)
        pending.symlink_to(release.relative_to(destination))
        os.replace(pending, destination / "current")
    except Exception:
        pending.unlink(missing_ok=True)
        shutil.rmtree(release)
        raise
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="Build into an empty directory.")
    mode.add_argument("--publish-to", type=Path, help="Build and switch the current release in this directory.")
    args = parser.parse_args()
    count = build(args.output) if args.output else publish(args.publish_to)
    print(f"Built {count} skills in Chinese and English.")
