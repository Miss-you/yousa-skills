import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import pr_ai_review_monitor as monitor

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "monitoring-pr-ai-reviews"
    / "scripts"
    / "pr_ai_review_monitor.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


canonical_monitor = load_module("canonical_pr_ai_review_monitor", CANONICAL_SCRIPT)


class PrAiReviewMonitorTest(unittest.TestCase):
    def test_collect_findings_treats_codex_bot_as_ai_reviewer_by_default(self):
        pull_requests = [
            {
                "number": 9,
                "title": "Monitor PR AI reviews",
                "url": "https://example.test/pr/9",
                "reviewThreads": {
                    "nodes": [
                        {
                            "id": "thread-1",
                            "isResolved": False,
                            "isOutdated": False,
                            "path": "scripts/pr_ai_review_monitor.py",
                            "line": 109,
                            "comments": {
                                "nodes": [
                                    {
                                        "body": "Please paginate review threads.",
                                        "author": {"login": "chatgpt-codex-connector"},
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        findings = monitor.collect_findings(
            pull_requests,
            monitor.resolve_ai_review_logins([]),
        )

        self.assertEqual(1, len(findings))

    def test_root_wrapper_delegates_to_skill_local_script(self):
        pull_requests = [
            {
                "number": 9,
                "title": "Monitor PR AI reviews",
                "url": "https://example.test/pr/9",
                "reviewThreads": {
                    "nodes": [
                        {
                            "id": "thread-1",
                            "isResolved": False,
                            "isOutdated": False,
                            "path": "skills/monitoring-pr-ai-reviews/scripts/pr_ai_review_monitor.py",
                            "line": 42,
                            "comments": {
                                "nodes": [
                                    {
                                        "body": "Please keep this script self-contained.",
                                        "author": {"login": "Copilot"},
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        findings = canonical_monitor.collect_findings(
            pull_requests,
            canonical_monitor.resolve_ai_review_logins([]),
        )

        self.assertEqual(str(CANONICAL_SCRIPT), monitor.collect_findings.__code__.co_filename)
        self.assertEqual(1, len(findings))

    def test_collect_findings_uses_first_ai_comment_for_summary(self):
        pull_requests = [
            {
                "number": 9,
                "title": "Monitor PR AI reviews",
                "url": "https://example.test/pr/9",
                "reviewThreads": {
                    "nodes": [
                        {
                            "id": "thread-1",
                            "isResolved": False,
                            "isOutdated": False,
                            "path": "scripts/pr_ai_review_monitor.py",
                            "line": 180,
                            "comments": {
                                "nodes": [
                                    {
                                        "body": "human follow-up",
                                        "author": {"login": "maintainer"},
                                    },
                                    {
                                        "body": "Prefer the first AI comment for the summary.",
                                        "author": {"login": "Copilot"},
                                    },
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        findings = monitor.collect_findings(
            pull_requests,
            monitor.resolve_ai_review_logins([]),
        )

        self.assertEqual(
            "Prefer the first AI comment for the summary.",
            findings[0]["threads"][0]["summary"],
        )

    def test_load_review_threads_fetches_all_pages_for_one_pr(self):
        first_page = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "id": "thread-1",
                                    "isResolved": False,
                                    "isOutdated": False,
                                    "path": "a.py",
                                    "line": 10,
                                    "comments": {"nodes": [{"body": "one", "author": {"login": "Copilot"}}]},
                                }
                            ],
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
                        }
                    }
                }
            }
        }
        second_page = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "id": "thread-2",
                                    "isResolved": False,
                                    "isOutdated": False,
                                    "path": "b.py",
                                    "line": 20,
                                    "comments": {"nodes": [{"body": "two", "author": {"login": "Copilot"}}]},
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }

        with patch.object(monitor, "gh_graphql", side_effect=[first_page, second_page]) as gh_graphql:
            threads = monitor.load_review_threads("owner", "repo", 7)

        self.assertEqual(["thread-1", "thread-2"], [thread["id"] for thread in threads])
        self.assertEqual(2, gh_graphql.call_count)

    def test_load_pull_requests_hydrates_paginated_threads_for_open_prs(self):
        pull_requests_page = {
            "data": {
                "repository": {
                    "pullRequests": {
                        "nodes": [
                            {
                                "number": 5,
                                "title": "Add monitor",
                                "url": "https://example.test/pr/5",
                            }
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            }
        }
        hydrated_threads = [
            {
                "id": "thread-1",
                "isResolved": False,
                "isOutdated": False,
                "path": "scripts/pr_ai_review_monitor.py",
                "line": 42,
                "comments": {"nodes": [{"body": "paginate this", "author": {"login": "Copilot"}}]},
            }
        ]

        with patch.object(monitor, "gh_graphql", return_value=pull_requests_page):
            with patch.object(monitor, "load_review_threads", return_value=hydrated_threads) as load_review_threads:
                pull_requests = monitor.load_pull_requests("owner/repo", None)

        self.assertEqual(1, len(pull_requests))
        self.assertEqual(
            hydrated_threads,
            pull_requests[0]["reviewThreads"]["nodes"],
        )
        load_review_threads.assert_called_once_with("owner", "repo", 5)


if __name__ == "__main__":
    unittest.main()
