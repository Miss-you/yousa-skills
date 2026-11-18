# Skill usage stats

`scripts/skill_usage_stats.py` counts how often skills are used in local Claude Code and Codex session logs. It uses only the Python standard library; compressed Codex archives need the `zstd` CLI.

```bash
# public, aggregate-only file used by the README "Activity" column
python3 scripts/skill_usage_stats.py --emit-repo-usage docs/readme/usage.json
python3 scripts/render_readmes.py

# private per-event output for your own analysis (contains local paths; do not commit)
python3 scripts/skill_usage_stats.py --out-dir skill-usage-out
```

## `usage.json`

Only skills under `skills/` are included. Each one has:

| Field | Meaning |
|---|---|
| `monthly` | Uses per calendar month for the last 6 months (UTC+8); the current month is partial |
| `recent_3m` | Uses in the current month plus the two before it |
| `last_used_month` | Latest month in the 6-month window with a use, or `null` |
| `status` | `active` if `recent_3m` ≥ 5, `low` if 1–4, `inactive` if 0 |

The file also has `generated_at`, `window`, `status_rule` and `coverage_note`. It contains no session ids, project paths or event timestamps.

## What counts as a use

Claude Code (`~/.claude/projects/**/*.jsonl`, including subagent transcripts):

- An assistant `Skill` tool call, unless its result is an error.
- A user slash command that loads a skill or expands a custom command. Built-in CLI commands do not count.
- A "Base directory for this skill" injection that cannot be linked to either of the above (fallback only).
- Records replayed into resumed or forked transcripts are deduplicated by tool_use id or message uuid.

Codex (`~/.codex/sessions`, `~/.codex/archived_sessions`, plus `~/.codex/thread_history_1.sqlite` for threads whose rollout file was deleted):

- The user's own message mentions `$skill-name`, matched against the session's skill catalog or installed skills.
- A `<skill>` injection in a user-role message.
- The model runs a read command (`cat`, `sed`, `head`, `rg`, …) on `…/skills/<name>/SKILL.md` under an installed skill root. Reads of repo copies (skill authoring) and commands touching more than 8 skills do not count.
- Guardian sessions and parent history replayed into sub-agent rollouts are skipped. One use per (session, turn, skill).

Never counted: skill catalogs and generic skill instructions in system prompts, tool output, and assistant prose. Plugin skills are merged by base name, so `superpowers:brainstorming` and `brainstorming` count together.

## Known gaps

- Counts reflect one maintainer's usage, not installs or other users.
- Claude Code transcripts on disk start in 2026-08, and most older Codex rollout files were pruned, so months outside the last three are undercounted.
- Reading a SKILL.md with Claude's Read tool, or typing a skill name that the model never loads, is not counted.
- Some Codex skills are triggered automatically by other instructions or scheduled automations, which inflates their counts.
- A skill used several times in one turn counts once.
- 0 means no recorded use, not proof that the skill was never used.
