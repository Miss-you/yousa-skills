---
name: checking-upstream-before-work
description: Use when starting implementation, bugfix, refactor, docs, or investigation work in a repository where upstream pull requests may already cover or conflict with the task.
---

# Checking Upstream Before Work

## Overview

Before edits, check upstream for related open PRs and PRs merged in the last 5 days.

## When to Use

Use in any repo with an `upstream` or shared `origin` remote, except throwaway experiments or work the user says should ignore upstream.

## Workflow

1. Resolve the upstream repo and remote name:
   ```bash
   if git remote get-url upstream >/dev/null 2>&1; then
     REMOTE_NAME=upstream
   else
     REMOTE_NAME=origin
   fi
   REMOTE=$(git remote get-url "$REMOTE_NAME")
   REPO=$(printf '%s\n' "$REMOTE" | sed -E 's#^(git@github.com:|https://github.com/)##; s#\.git$##')
   printf '%s\n' "$REPO"
   ```
   If this prints a fork, set `REPO=OWNER/REPO` manually.

2. Generate 3-6 task terms: issue/error, command, subsystem, file/function/config names, symptom, and synonyms.

3. Fetch if local base state matters (use the remote resolved in step 1):
   ```bash
   git fetch "$REMOTE_NAME" --prune
   ```

4. Compute the exact 5-day UTC window and run broad checks:

   ```bash
   SINCE=$(date -u -v-5d +%F 2>/dev/null || date -u -d '5 days ago' +%F)

   gh pr list --repo "$REPO" --state open --limit 100 \
     --json number,title,headRefName,author,updatedAt,url

   gh pr list --repo "$REPO" --state merged --search "merged:>=$SINCE" --limit 100 \
     --json number,title,author,mergedAt,url
   ```

5. Run targeted searches:
   ```bash
   gh pr list --repo "$REPO" --state all --search "TERM1 TERM2" --limit 20 \
     --json number,title,state,mergedAt,updatedAt,url
   ```
   If `gh` is unavailable, use the GitHub connector or web search with the same evidence.

## Decision Table

| Finding | Action |
| --- | --- |
| Open PR solves the same problem | Pause, inspect it, and tell the user. |
| Open PR touches likely files/subsystems | Inspect diff, adjust plan, state risk. |
| Recent merged PR clearly solves it | Fetch/rebase, verify if already done. |
| Recent merged PR overlaps likely files | Rebase or inspect before editing. |
| No credible matches | Proceed and record the queries used. |

## Verification Gate

Do not edit files until the preflight has a decision:

- `pause`: exact open PR or recent merged PR already covers the task.
- `inspect first`: likely file/subsystem overlap; inspect diff or rebase first.
- `proceed`: broad and targeted checks produced no credible match.

Invalid without repo, 5-day window, search terms, matches, and action.

## Example

```bash
gh pr list --repo "$REPO" --state open --search "MCP configs subagents" \
  --limit 10 --json number,title,state,updatedAt,url
```

If a PR has the same fix, stop and report it.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Checking only local `main` | Query GitHub too. |
| Searching only exact title | Add symptoms/files/synonyms. |
| Ignoring recent merges | They may solve it or change base. |
| Continuing after exact match | Pause unless user wants competing work. |
| Saying "no conflict" without evidence | Include repo/window/queries/matches. |

## Required Report

```text
Upstream preflight: OWNER/REPO, merged since YYYY-MM-DD.
Open PR matches: ...
Recent merged matches: ...
Decision: proceed | inspect first | pause for user.
```
