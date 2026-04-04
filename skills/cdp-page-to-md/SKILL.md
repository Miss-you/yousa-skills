---
name: cdp-page-to-md
description: "Fetch authenticated or JS-rendered web pages via Chrome CDP (DevTools Protocol) and convert them to clean Markdown files. Use when: (1) user provides a URL that requires authentication (e.g. claude.ai, chatgpt.com, Google Docs, Notion, Confluence, Jira), (2) user wants to save/archive a web page as Markdown, (3) WebFetch fails with 403/401 or returns empty content, (4) the page is a JS-rendered SPA that needs a real browser. Trigger words: 'fetch page', 'grab page', 'save as markdown', 'convert to md', 'pull down this page', 'CDP', 'archive this URL'."
---

# CDP Page to Markdown

Fetch web pages through a local Chrome browser with CDP, extract content, and convert to structured Markdown.

## Workflow

### Step 1: Ensure Chrome CDP is running

```bash
curl -s http://localhost:9222/json/version
```

If this fails, start Chrome with CDP:

```bash
bash ~/.claude/skills/cdp-page-to-md/references/start_chrome_cdp.sh
```

Close all Chrome windows first (Cmd+Q), then run the script.

### Step 2: Fetch page content

Run the extraction script — it handles CDP connection, navigation, scrolling, and text extraction:

```bash
python3 ~/.claude/skills/cdp-page-to-md/scripts/fetch_page.py "<URL>"
```

Options: `--port 9222` (CDP port), `--wait 6` (seconds after navigation), `--scrolls 3` (lazy-load scroll passes).

Output format:
```
TITLE: <page title>
URL: <final URL>
LENGTH: <text length>
---CONTENT---
<raw page text>
```

Set Bash timeout to 60s+.

### Step 3: Convert raw text to Markdown

This is the only step requiring intelligence. Take the raw text output and:

1. Use `TITLE` as `# heading`
2. Add `> Source: <URL>` metadata
3. For **chat pages** (claude.ai, chatgpt.com): separate user/assistant turns with `---` and `## User` / `## Assistant` headers
4. For **general pages**: infer heading hierarchy, lists, code blocks, bold/italic from content structure
5. Remove navigation chrome, footers, cookie banners, "Report" links
6. Write `.md` file to user-specified path

## Site-Specific Notes

| Site | User turn marker | Assistant turn marker | Notes |
|------|------------------|-----------------------|-------|
| claude.ai/share/* | Raw user text blocks | Prose blocks after date | Title in page title before `\| Claude` |
| chatgpt.com/share/* | "你说：" / "You said:" | "ChatGPT 说：" / "ChatGPT said:" | May include "Reasoned for Xm Ys" |

## References

- `scripts/fetch_page.py` — CDP extraction script. Run directly, no need to read into context.
- `references/start_chrome_cdp.sh` — Launch Chrome with CDP enabled (port configurable, default 9222).
