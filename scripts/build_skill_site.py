"""Build the public registry from the repository's bilingual inventory."""
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re
import shutil
import tempfile

if __package__:
    from .render_readmes import load_manifest, repo_root, validate_manifest
else:
    from render_readmes import load_manifest, repo_root, validate_manifest

ORIGIN = "https://skills.yousali.com"
REPO = "https://github.com/Miss-you/yousa-skills"
ASSETS = ("registry.css", "registry.js")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def copy_button(target: str, label: str) -> str:
    return f'<button type="button" data-copy="{target}" hidden>{label}</button>'


def layout(title: str, description: str, path: str, alternate: str, zh: bool, body: str) -> str:
    lang = "zh-CN" if zh else "en"
    home = "/" if zh else "/en/"
    catalog = "技能目录" if zh else "Catalog"
    homepage = "个人主页" if zh else "About Yousa"
    switch = "English" if zh else "简体中文"
    switch_lang = "en" if zh else "zh-CN"
    theme = "切换深色模式" if zh else "Toggle dark mode"
    copied = "已复制" if zh else "Copied"
    failed = "复制失败，请手动选中复制" if zh else "Copy unavailable. Select the text to copy it."
    link_failed = "请从地址栏复制链接" if zh else "Copy the link from the address bar."
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
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&amp;family=Noto+Serif+SC:wght@600;700&amp;family=Noto+Sans+SC:wght@400;500;700&amp;display=swap">
  <link rel="stylesheet" href="/assets/registry.css">
  <script src="/assets/registry.js" defer></script>
  <title>{html.escape(title)}</title>
</head>
<body data-copied="{copied}" data-copy-failed="{failed}" data-link-failed="{link_failed}">
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="https://yousali.com/">Yousa Driven Development <span>| YDD</span></a>
      <nav aria-label="{catalog}">
        <a href="{home}" aria-current="{'page' if path == home else 'true'}">{catalog}</a>
        <a href="{REPO}">GitHub</a>
        <a href="{alternate}" hreflang="{switch_lang}" lang="{switch_lang}">{switch}</a>
        <button id="theme-toggle" class="theme-toggle" type="button" aria-pressed="false" aria-label="{theme}" hidden>◐</button>
      </nav>
    </div>
  </header>
  <main>{body}</main>
  <footer><a href="https://yousali.com/">{homepage}</a> <span aria-hidden="true">·</span>
    <a href="{REPO}">Miss-you / yousa-skills</a></footer>
</body>
</html>
"""


def description_for(entry: dict, zh: bool) -> str:
    return entry["description_zh" if zh else "description_en"]


def catalog_page(entries: list[dict], zh: bool) -> str:
    prefix = "" if zh else "/en"
    title = "Yousa Skills"
    intro = ("面向 AI 协作的可复用工作流，从源码阅读、写作到代码审查。"
             if zh else "Reusable workflows for working with AI, from reading source code and writing to reviewing changes.")
    search_label = "搜索名称或说明" if zh else "Search by name or description"
    count = f"{len(entries)} 项 Skills" if zh else f"{len(entries)} skills"
    no_results = "没有匹配的 Skill。" if zh else "No matching skills."
    cards = []
    for entry in sorted(entries, key=lambda item: item["name"]):
        name = entry["name"]
        desc = html.escape(description_for(entry, zh))
        cards.append(
            f'<li class="skill-card"><a href="{prefix}/skills/{name}/">'
            f'<h2>{name}</h2><p>{desc}</p><span class="arrow" aria-hidden="true">↗</span></a></li>'
        )
    body = f"""
    <section class="intro">
      <h1>{title}</h1>
      <p>{intro}</p>
    </section>
    <section aria-label="{title}">
      <div class="catalog-tools">
        <label class="search" hidden>{search_label}
          <input id="skill-search" type="search" autocomplete="off">
        </label>
        <p class="count" id="skill-count" aria-live="polite">{count}</p>
      </div>
      <p id="no-results" hidden>{no_results}</p>
      <ul class="catalog">{''.join(cards)}</ul>
    </section>"""
    return layout(title, intro, f"{prefix}/", "/en/" if zh else "/", zh, body)


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
    prompt = (
        f"Install the {name} skill from {source} into this workspace. "
        "Start from AGENTS.md and follow any WORKSPACE.md routing rules. Clone or vendor the repository under the appropriate project directory. "
        "Keep this skill's directory and its companion files together. Expose its single SKILL.md "
        "through the workspace's skill-discovery chain and register it in the local index if present. "
        "Keep private aliases, paths, and credentials in a local overlay."
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
        {copy_button("install-prompt", copy)}
        <a class="action" href="{source}">{source_label}</a>
        {copy_button("share-url", copy_link)}
      </div>
      <span id="copy-status" class="status" role="status"></span>
    </article>
    <section class="install-panel" aria-labelledby="install-heading">
      <h2 id="install-heading">{install}</h2>
      <p>{"将这段提示发给你的编程助手。" if zh else "Send this prompt to your coding agent."}</p>
      <pre id="install-prompt">{html.escape(prompt)}</pre>
      <span id="share-url" hidden>{ORIGIN}{prefix}{route}</span>
      <details><summary>{cli}</summary>
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
