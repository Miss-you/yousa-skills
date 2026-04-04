#!/usr/bin/env python3
"""Fetch a web page via Chrome CDP and print its text content to stdout.

Usage:
    python fetch_page.py <url> [--port 9222] [--wait 6] [--scrolls 3]

Requires:
    - Chrome running with --remote-debugging-port (default 9222)
    - pip install playwright
"""

import argparse
import asyncio
import json
import subprocess
import sys


def get_ws_url(port: int) -> str:
    """Get WebSocket debugger URL from CDP endpoint."""
    try:
        raw = subprocess.check_output(
            ["curl", "-s", f"http://localhost:{port}/json/version"],
            timeout=5,
        )
        return json.loads(raw)["webSocketDebuggerUrl"]
    except Exception:
        print(
            f"ERROR: Cannot reach Chrome CDP on port {port}.\n"
            f"Start Chrome with: bash ~/.claude/skills/cdp-page-to-md/references/start_chrome_cdp.sh",
            file=sys.stderr,
        )
        sys.exit(1)


async def fetch(url: str, port: int, wait_sec: int, scrolls: int) -> None:
    from playwright.async_api import async_playwright

    ws_url = get_ws_url(port)

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]

        # Reuse tab if already open
        page = None
        for pg in context.pages:
            if url in pg.url:
                page = pg
                break

        if page is None:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(wait_sec * 1000)

        # Scroll to trigger lazy loading
        for _ in range(scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

        # Extract metadata
        title = await page.title()
        final_url = page.url

        # Extract text content
        content = await page.evaluate(
            """() => {
                const el = document.querySelector('main') || document.body;
                return el.innerText;
            }"""
        )

        await page.close()

        # Output as simple structured format
        print(f"TITLE: {title}")
        print(f"URL: {final_url}")
        print(f"LENGTH: {len(content)}")
        print("---CONTENT---")
        print(content)


def main():
    parser = argparse.ArgumentParser(description="Fetch page via Chrome CDP")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--port", type=int, default=9222, help="CDP port (default 9222)")
    parser.add_argument("--wait", type=int, default=6, help="Seconds to wait after navigation (default 6)")
    parser.add_argument("--scrolls", type=int, default=3, help="Number of scroll-to-bottom passes (default 3)")
    args = parser.parse_args()

    asyncio.run(fetch(args.url, args.port, args.wait, args.scrolls))


if __name__ == "__main__":
    main()
