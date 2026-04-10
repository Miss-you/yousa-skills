#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_AI_REVIEW_LOGINS = {
    "copilot-pull-request-reviewer",
    "Copilot",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report unresolved AI review threads for one PR or all open PRs."
    )
    parser.add_argument("--repo", required=True, help="Repository in owner/name form.")
    parser.add_argument("--pr", type=int, help="Optional pull request number to scan.")
    parser.add_argument("--output", help="Optional markdown output path.")
    parser.add_argument(
        "--ai-login",
        action="append",
        default=[],
        help="Additional GitHub login to treat as an AI reviewer. May be repeated.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit non-zero when unresolved AI review threads are found.",
    )
    return parser.parse_args()


def resolve_ai_review_logins(extra_logins: list[str]) -> set[str]:
    logins = set(DEFAULT_AI_REVIEW_LOGINS)
    env_value = os.environ.get("PR_AI_REVIEW_LOGINS", "")
    if env_value:
        logins.update(login.strip() for login in env_value.split(",") if login.strip())
    if extra_logins:
        logins.update(login.strip() for login in extra_logins if login.strip())
    return logins


def gh_graphql(query: str, variables: dict[str, str | int | None]) -> dict:
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        cmd.extend(["-F", f"{key}={value}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)

    return json.loads(result.stdout)


def load_pull_requests(repo: str, pr_number: int | None) -> list[dict]:
    owner, name = repo.split("/", 1)
    if pr_number is not None:
        query = """
query($owner:String!, $name:String!, $prNumber:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$prNumber) {
      number
      title
      url
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first:20) {
            nodes {
              body
              author {
                login
              }
            }
          }
        }
      }
    }
  }
}
"""
        payload = gh_graphql(query, {"owner": owner, "name": name, "prNumber": pr_number})
        pr = payload["data"]["repository"]["pullRequest"]
        return [pr] if pr else []

    query = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequests(first:50, after:$cursor, states:OPEN, orderBy:{field:UPDATED_AT, direction:DESC}) {
      nodes {
        number
        title
        url
        reviewThreads(first:100) {
          nodes {
            id
            isResolved
            isOutdated
            path
            line
            comments(first:20) {
              nodes {
                body
                author {
                  login
                }
              }
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""
    cursor = None
    pull_requests: list[dict] = []
    while True:
        payload = gh_graphql(query, {"owner": owner, "name": name, "cursor": cursor})
        connection = payload["data"]["repository"]["pullRequests"]
        pull_requests.extend(connection["nodes"])
        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return pull_requests


def is_ai_thread(thread: dict, ai_review_logins: set[str]) -> bool:
    for comment in thread["comments"]["nodes"]:
        author = comment.get("author")
        if author and author.get("login") in ai_review_logins:
            return True
    return False


def summarize_comment(body: str) -> str:
    compact = " ".join(line.strip() for line in body.splitlines() if line.strip())
    if not compact:
        return "(empty comment body)"
    return textwrap.shorten(compact, width=160, placeholder="...")


def collect_findings(pull_requests: list[dict], ai_review_logins: set[str]) -> list[dict]:
    findings: list[dict] = []
    for pr in pull_requests:
        threads = []
        for thread in pr["reviewThreads"]["nodes"]:
            if (
                thread["isResolved"]
                or thread["isOutdated"]
                or not is_ai_thread(thread, ai_review_logins)
            ):
                continue
            first_comment = thread["comments"]["nodes"][0]
            threads.append(
                {
                    "id": thread["id"],
                    "path": thread.get("path") or "(unknown path)",
                    "line": thread.get("line"),
                    "summary": summarize_comment(first_comment.get("body", "")),
                }
            )
        if threads:
            findings.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["url"],
                    "threads": threads,
                }
            )
    return findings


def render_report(
    repo: str, scanned_count: int, findings: list[dict], ai_review_logins: set[str]
) -> str:
    lines = [
        "# PR AI Review Monitor",
        "",
        f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- Repo: {repo}",
        f"- PRs scanned: {scanned_count}",
        f"- PRs with unresolved AI review threads: {len(findings)}",
        f"- AI reviewer logins: {', '.join(sorted(ai_review_logins))}",
        "",
    ]

    if not findings:
        lines.append("No unresolved AI review threads found.")
        return "\n".join(lines) + "\n"

    for pr in findings:
        lines.extend(
            [
                f"## PR #{pr['number']} {pr['title']}",
                f"- URL: {pr['url']}",
                f"- Unresolved AI review threads: {len(pr['threads'])}",
                "",
            ]
        )
        for index, thread in enumerate(pr["threads"], start=1):
            location = thread["path"]
            if thread["line"] is not None:
                location = f"{location}:{thread['line']}"
            lines.append(
                f"{index}. `{thread['id']}` [{location}] {thread['summary']}"
            )
        lines.append("")

    return "\n".join(lines)


def write_output(path: str, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    ai_review_logins = resolve_ai_review_logins(args.ai_login)
    pull_requests = load_pull_requests(args.repo, args.pr)
    findings = collect_findings(pull_requests, ai_review_logins)
    report = render_report(args.repo, len(pull_requests), findings, ai_review_logins)

    if args.output:
        write_output(args.output, report)
    else:
        sys.stdout.write(report)

    if args.fail_on_findings and findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
