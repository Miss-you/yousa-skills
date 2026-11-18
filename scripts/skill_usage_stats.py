#!/usr/bin/env python3
"""Count skill usages across Claude Code and Codex sessions (stdlib only).

Usage:
    python3 scripts/skill_usage_stats.py [--since YYYY-MM-DD] [--until YYYY-MM-DD]
                                         [--out-dir DIR] [--no-claude] [--no-codex]
    python3 scripts/skill_usage_stats.py --emit-repo-usage docs/readme/usage.json

--emit-repo-usage writes a public, aggregate-only file for this repo's README:
monthly counts for the last 6 calendar months, recent_3m (current month plus the
two before it), last_used_month and status (>=5 active, 1-4 low, 0 inactive),
only for skills under skills/. It contains no session ids, paths or timestamps.
Private outputs are skipped in this mode unless --out-dir is given.

Dates are interpreted in Beijing time (UTC+8); the window is [since, until).
Defaults: the last ~6 months up to the end of today.

Outputs written to --out-dir:
    usage_events.jsonl   one line per usage (may contain local paths; keep private)
    usage_summary.json   aggregated by base_name, plus scan coverage stats
    usage_by_month.csv   rows = base_name, columns = months

Claude Code sources: ~/.claude/projects/**/*.jsonl (+ desktop-app session
metadata for the archived flag). Signals: Skill tool_use, user slash commands
that load a skill / custom command, orphan "Base directory for this skill"
injections. Codex sources: ~/.codex/sessions, ~/.codex/archived_sessions
(*.jsonl[.zst], decompressed via the zstd CLI), ~/.codex/thread_history_1.sqlite
for threads whose rollout file was pruned. Signals: user `$skill` mentions,
`<skill>` injections, shell commands that read .../skills/<name>/SKILL.md.
Skill catalogs / generic skill instructions in system prompts are never counted.
Plugin skills are aggregated by base name (the part after the last ':').
Dedup: Claude by tool_use id / message uuid across resumed or forked files;
Codex by (session, turn, skill). See docs/skill-usage-stats.md for the rules
and known limitations.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional


# ==========================================================================
# Claude Code parser
# ==========================================================================

BJ = timezone(timedelta(hours=8))
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
DESKTOP_META_DIR = os.path.expanduser("~/Library/Application Support/Claude/claude-code-sessions")
SKILL_DIR_GLOBS = [
    "~/.claude/skills/*/SKILL.md",
    "~/.claude/plugins/**/skills/*/SKILL.md",
    "~/.codex/skills/**/SKILL.md",
    "~/.agents/skills/**/SKILL.md",
]
COMMAND_GLOBS = ["~/.claude/commands/**/*.md", "~/.claude/plugins/**/commands/*.md"]

INJECTION_PREFIX = "Base directory for this skill"
CMD_NAME_RX = re.compile(r"<command-name>\s*(.*?)\s*</command-name>", re.S)
INJ_RX = re.compile(r"Base directory for this skill:\s*(\S+)")

# Built-in CLI commands: never counted unless a "Base directory" injection follows.
BUILTIN_COMMANDS = frozenset("""
add-dir agents autocompact auto-mode-setup bashes btw bug clear compact config context
cost doctor exit export fast feedback goal help hooks ide init install-github-app
keybindings login logout mcp memory migrate-installer model output-style output-style:new
permissions plugin plugins pr-comments privacy-settings quit release-notes reload-plugins
remote-control resume review rewind sandbox settings stats status statusline terminal-setup
theme todos upgrade usage vim tasks color copy effort rename extra-usage
""".split())

PREFILTER = (b'"name":"Skill"', b"<command-name>", INJECTION_PREFIX.encode())
PENDING_SLASH_WINDOW = 6  # lines to look ahead for a slash command's injection


def _load_archive_map() -> dict:
    out = {}
    for p in glob.glob(os.path.join(DESKTOP_META_DIR, "**", "*.json"), recursive=True):
        try:
            with open(p, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        if isinstance(d, dict) and d.get("cliSessionId"):
            out[d["cliSessionId"]] = bool(d.get("isArchived"))
    return out


def _known_skill_names() -> set:
    names = set()
    for g in SKILL_DIR_GLOBS:
        for p in glob.glob(os.path.expanduser(g), recursive=True):
            names.add(os.path.basename(os.path.dirname(p)))
    for g in COMMAND_GLOBS:
        for p in glob.glob(os.path.expanduser(g), recursive=True):
            names.add(os.path.splitext(os.path.basename(p))[0])
    return names


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _claude_parse_ts(ts, fallback: datetime) -> datetime:
    if isinstance(ts, str) and ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
    return fallback


def iter_claude_events(since: datetime, until: datetime, stats: dict) -> Iterator[dict]:
    limit_files = stats.pop("_limit_files", None)  # test hook used by __main__
    for k in ("files_scanned", "files_failed", "files_skipped_mtime", "lines_failed",
              "bytes_scanned", "lines_parsed", "dup_skipped", "skill_tool_errors",
              "linked_injections", "out_of_range"):
        stats.setdefault(k, 0)
    stats.setdefault("slash_ignored", Counter())
    stats.setdefault("by_signal", Counter())

    archived = _load_archive_map()
    known = _known_skill_names()
    since_ts = since.timestamp()

    files = []
    for p in glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True):
        try:
            mt = os.path.getmtime(p)
        except OSError:
            stats["files_failed"] += 1
            continue
        if mt < since_ts:
            stats["files_skipped_mtime"] += 1
            continue
        files.append((mt, p))
    files.sort()
    if limit_files:
        files = files[-limit_files:]

    seen_keys: set = set()       # counted / suppressed invocation keys (global)
    skill_tool_ids: set = set()  # every Skill tool_use id seen
    slash_uuids: set = set()     # every non-meta slash-command uuid seen

    for mtime, path in files:
        rel = os.path.relpath(path, PROJECTS_DIR)
        proj_subdir = rel.split(os.sep, 1)[0]
        is_sub = f"{os.sep}subagents{os.sep}" in path
        fallback_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        file_events = []          # buffered so errored Skill calls can be dropped
        pending_tools = {}        # tool_use id -> event index in file_events
        pending_slash = None      # dict while waiting for the command's injection

        def make_event(skill, signal, d, lineno):
            skill = skill.strip().lstrip("/")
            dt = _claude_parse_ts(d.get("timestamp"), fallback_dt)
            sid = d.get("sessionId") or os.path.basename(path)[:-6]
            local = dt.astimezone(BJ)
            return {
                "skill": skill,
                "base_name": skill.rsplit(":", 1)[-1],
                "source": "claude",
                "signal": signal,
                "timestamp": local.isoformat(),
                "month": local.strftime("%Y-%m"),
                "session_id": sid,
                "archived": archived.get(sid),
                "project_dir": d.get("cwd") or proj_subdir,
                "is_subagent": is_sub,
                "file": rel,
                "line": lineno,
                "_dt": dt,
            }

        def resolve_slash(ps, child_kind):
            name = ps["name"].lstrip("/")
            if child_kind == "inject":
                ok = True
            elif name in BUILTIN_COMMANDS:
                ok = False
            else:
                ok = child_kind == "meta" or name in known
            if ok:
                file_events.append(ps["event"])
            else:
                stats["slash_ignored"][name] += 1

        try:
            fh = open(path, "rb")
        except OSError:
            stats["files_failed"] += 1
            continue
        stats["files_scanned"] += 1
        try:
            with fh:
                for lineno, raw in enumerate(fh, 1):
                    stats["bytes_scanned"] += len(raw)
                    s = raw.strip()
                    if not s:
                        continue
                    if not (s[:1] == b"{" and s[-1:] == b"}"):
                        stats["lines_failed"] += 1
                        continue
                    want = any(p in raw for p in PREFILTER)
                    if pending_slash is not None:
                        want = True
                    if pending_tools and b'"is_error":true' in raw:
                        want = True
                    if not want:
                        continue
                    try:
                        d = json.loads(raw)
                    except ValueError:
                        stats["lines_failed"] += 1
                        continue
                    stats["lines_parsed"] += 1
                    if not isinstance(d, dict):
                        continue
                    rtype = d.get("type")
                    if rtype not in ("user", "assistant"):
                        continue
                    msg = d.get("message") if isinstance(d.get("message"), dict) else {}
                    content = msg.get("content")
                    uuid = d.get("uuid")

                    # --- resolve a pending slash command by its child record
                    if pending_slash is not None:
                        if rtype == "user" and d.get("isMeta") and d.get("parentUuid") == pending_slash["uuid"]:
                            kind = "inject" if _text_of(content).lstrip().startswith(INJECTION_PREFIX) else "meta"
                            resolve_slash(pending_slash, kind)
                            pending_slash = None
                        elif lineno - pending_slash["line"] > PENDING_SLASH_WINDOW:
                            resolve_slash(pending_slash, None)
                            pending_slash = None

                    if rtype == "assistant" and isinstance(content, list):
                        for b in content:
                            if not (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill"):
                                continue
                            tid = b.get("id")
                            name = (b.get("input") or {}).get("skill") if isinstance(b.get("input"), dict) else None
                            if tid:
                                skill_tool_ids.add(tid)
                            key = ("tool", tid or uuid)
                            if key in seen_keys:
                                stats["dup_skipped"] += 1
                                continue
                            seen_keys.add(key)
                            if not isinstance(name, str) or not name.strip():
                                continue
                            known.add(name.strip().lstrip("/"))
                            pending_tools[tid] = len(file_events)
                            file_events.append(make_event(name, "skill_tool", d, lineno))
                        continue

                    if rtype != "user":
                        continue

                    # --- tool_result errors for buffered Skill calls
                    if pending_tools and isinstance(content, list):
                        for b in content:
                            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in pending_tools:
                                idx = pending_tools.pop(b["tool_use_id"])
                                if b.get("is_error"):
                                    file_events[idx] = None
                                    stats["skill_tool_errors"] += 1

                    text = _text_of(content)
                    head = text.lstrip()

                    # --- slash command
                    if not d.get("isMeta") and head.startswith("<command-") and "<command-name>" in head:
                        m = CMD_NAME_RX.search(head)
                        if not m or not m.group(1):
                            continue
                        if uuid:
                            slash_uuids.add(uuid)
                        key = ("msg", uuid)
                        if key in seen_keys:
                            stats["dup_skipped"] += 1
                            continue
                        seen_keys.add(key)
                        if pending_slash is not None:
                            resolve_slash(pending_slash, None)
                        pending_slash = {"uuid": uuid, "name": m.group(1), "line": lineno,
                                         "event": make_event(m.group(1), "slash_command", d, lineno)}
                        continue

                    # --- skill injection (counted only when orphaned)
                    if d.get("isMeta") and head.startswith(INJECTION_PREFIX):
                        src = d.get("sourceToolUseID")
                        if (src and src in skill_tool_ids) or d.get("parentUuid") in slash_uuids:
                            stats["linked_injections"] += 1
                            continue
                        key = ("msg", uuid)
                        if key in seen_keys:
                            stats["dup_skipped"] += 1
                            continue
                        seen_keys.add(key)
                        m = INJ_RX.search(head)
                        if m:
                            name = os.path.basename(m.group(1).rstrip("/"))
                            file_events.append(make_event(name, "skill_injection", d, lineno))
                if pending_slash is not None:
                    resolve_slash(pending_slash, None)
        except OSError:
            stats["files_failed"] += 1
            continue

        for ev in file_events:
            if ev is None:
                continue
            dt = ev.pop("_dt")
            if not (since <= dt < until):
                stats["out_of_range"] += 1
                continue
            stats["by_signal"][ev["signal"]] += 1
            yield ev


# ==========================================================================
# Codex parser
# ==========================================================================

BJT = timezone(timedelta(hours=8))
CODEX_HOME = os.path.expanduser("~/.codex")
SESSIONS_DIR = os.path.join(CODEX_HOME, "sessions")
ARCHIVED_DIR = os.path.join(CODEX_HOME, "archived_sessions")
STATE_DB = os.path.join(CODEX_HOME, "state_5.sqlite")
HISTORY_DB = os.path.join(CODEX_HOME, "thread_history_1.sqlite")
INCLUDE_HISTORY_DB = True

UUID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
FILE_TS_RE = re.compile(r"rollout-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})")

# catalog line inside developer instructions: "- name: description (file: path)"
CATALOG_RE = re.compile(r"(?m)^- ([A-Za-z0-9][\w.\-]*(?::[\w.\-]+)?): .*?\(file: ([^)\n]+)\)")
ROOT_ALIAS_RE = re.compile(r"(?m)^- `(r\d+)` = `([^`]+)`")
INJECT_RE = re.compile(r"<skill>\s*<name>([^<]+)</name>")
MENTION_RE = re.compile(r"(?<![\w$\\])\$([A-Za-z][\w.\-]*(?::[A-Za-z0-9][\w.\-]*)?)")
SKILL_TOKEN_RE = re.compile(r"[^\s'\"`=(),;|&<>\[\]{}]*SKILL\.md")
SHELL_WRAP_RE = re.compile(r"^\s*(?:\S*/)?(?:ba|z|da)?sh\s+-l?c\s+")
VERSION_DIR_RE = re.compile(r"^(v?\d[\w.\-]*|[0-9a-f]{7,40})$")
READ_VERBS = {"cat", "sed", "head", "tail", "nl", "less", "more", "bat", "awk",
              "rg", "grep", "egrep", "view", "type", "get-content"}
WRITE_BEFORE_RE = re.compile(r"(>>?|\btee(\s+-a)?|\*\*\* (Update|Add|Delete) File:|writeFile\w*\(|"
                             r"\bcp\b|\bmv\b|\bln\b|\brm\b|\binstall\b|\bdiff\b|\bgit\b)[^\n]*$")
SKILL_ROOT_MARKERS = ("/.codex/skills/", "/.agents/skills/", "/.claude/skills/", "/plugins/")
# a single command touching more skills than this is a survey, not a use
MAX_SKILLS_PER_COMMAND = 8
NON_USER_PREFIXES = ("<", "# AGENTS.md", "The following is the Codex agent history")


# --------------------------------------------------------------------------- helpers

def _codex_parse_ts(s) -> Optional[datetime]:
    if not s or not isinstance(s, str):
        return None
    s = s.replace("Z", "+00:00")
    m = re.match(r"^(.*T\d\d:\d\d:\d\d)(?:\.(\d+))?(.*)$", s)
    if m:  # py3.9 fromisoformat only takes 3 or 6 fractional digits
        frac = ((m.group(2) or "") + "000000")[:6]
        s = f"{m.group(1)}.{frac}{m.group(3)}"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(BJT)
    except ValueError:
        return None


def _base(name: str) -> str:
    return name.rsplit(":", 1)[-1]


def _disk_skill_names() -> set:
    """Installed skill names on disk. Standalone skills by dir name; plugin
    skills as `plugin:skill` (plus bare name only when skill == plugin)."""
    names = set()
    for p in ["~/.codex/skills/*/SKILL.md", "~/.codex/skills/.system/*/SKILL.md",
              "~/.agents/skills/*/SKILL.md", "~/.claude/skills/*/SKILL.md"]:
        for f in glob.glob(os.path.expanduser(p)):
            names.add(os.path.basename(os.path.dirname(f)))
    for p in ["~/.codex/plugins/cache/*/*/*/skills/*/SKILL.md",
              "~/.claude/plugins/cache/*/*/*/skills/*/SKILL.md",
              "~/.claude/plugins/marketplaces/*/plugins/*/skills/*/SKILL.md"]:
        for f in glob.glob(os.path.expanduser(p)):
            full = _name_from_path(f)
            if full:
                names.add(full)
                plugin, _, skill = full.rpartition(":")
                if plugin == skill:
                    names.add(skill)
    return names


def _name_from_path(path: str) -> Optional[str]:
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2 or parts[-1] != "SKILL.md":
        return None
    name = parts[-2]
    if "*" in name or "$" in name or "{" in name or name in (".", ".."):
        return None
    # plugin cache layout: .../plugins/cache/<marketplace>/<plugin>/<version>/skills/<skill>/SKILL.md
    if "plugins" in parts and len(parts) >= 4 and parts[-3] == "skills":
        i = len(parts) - 4
        cand = parts[i]
        if VERSION_DIR_RE.match(cand) and i - 1 >= 0:
            cand = parts[i - 1]
        if cand not in ("plugins", "cache", ".codex", ".claude", ".agents"):
            return f"{cand}:{name}"
    return name


class _Session:
    def __init__(self, sid, archived, fallback_ts, file_label):
        self.sid = sid
        self.archived = archived
        self.cwd = ""
        self.fallback_ts = fallback_ts
        self.file = file_label
        self.catalog = {}          # normalized path -> name
        self.names = set()         # catalog skill names (full)
        self.base_to_full = {}
        self.aliases = {}
        self.is_guardian = False
        self.is_subagent = False
        self.skip_before_ordinal = None
        self.turn = None
        self.has_turn_ids = False
        self.synthetic_turn = 0
        self.last_ts = None

    def add_catalog(self, text):
        for a, root in ROOT_ALIAS_RE.findall(text):
            self.aliases[a] = root.rstrip("/")
        for name, path in CATALOG_RE.findall(text):
            path = path.strip()
            m = re.match(r"^(r\d+)/(.*)$", path)
            if m and m.group(1) in self.aliases:
                path = self.aliases[m.group(1)] + "/" + m.group(2)
            self.names.add(name)
            self.base_to_full.setdefault(_base(name), set()).add(name)
            np = os.path.normpath(os.path.expanduser(path))
            self.catalog[np] = name
            try:
                rp = os.path.realpath(np)
                if rp != np:
                    self.catalog.setdefault(rp, name)
            except OSError:
                pass


# --------------------------------------------------------------------------- read detection

def _split_segments(cmd: str) -> list:
    """Split a shell string on ; | && || newlines that are outside quotes."""
    segs, cur, q, i = [], [], None, 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            if ch == "\\" and q == '"' and i + 1 < len(cmd):
                cur.append(cmd[i:i + 2]); i += 2; continue
            if ch == q:
                q = None
            cur.append(ch)
        elif ch in "'\"":
            q = ch; cur.append(ch)
        elif ch in ";|\n&":
            segs.append("".join(cur)); cur = []
            if cmd[i:i + 2] in ("&&", "||"):
                i += 1
        else:
            cur.append(ch)
        i += 1
    segs.append("".join(cur))
    return segs


def _unwrap_shell(cmd: str) -> str:
    m = SHELL_WRAP_RE.match(cmd)
    if not m:
        return cmd
    rest = cmd[m.end():].strip()
    if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in "'\"":
        rest = rest[1:-1]
        if cmd[m.end():].strip()[0] == '"':
            rest = rest.replace('\\"', '"').replace("\\$", "$").replace("\\`", "`")
        else:
            rest = rest.replace("'\"'\"'", "'")
    return rest


def _segment_reads(cmd: str) -> list:
    """Return SKILL.md path tokens that a shell command string reads."""
    out = []
    if not cmd or "SKILL.md" not in cmd:
        return out
    for seg in _split_segments(_unwrap_shell(cmd)):
        if "SKILL.md" not in seg:
            continue
        toks = seg.strip().split()
        # skip env assignments / sudo / command wrappers
        while toks and ("=" in toks[0] and not toks[0].startswith("-") or toks[0] in ("sudo", "command", "env", "time", "(", "{", "then", "do")):
            toks = toks[1:]
        if not toks:
            continue
        verb = os.path.basename(toks[0].strip("\"'(")).lower()
        if verb not in READ_VERBS:
            continue
        for m in SKILL_TOKEN_RE.finditer(seg):
            before = seg[:m.start()]
            if re.search(r">>?\s*$", before) or re.search(r"\btee(\s+-a)?\s+$", before):
                continue
            out.append(m.group(0))
    return out


def _js_reads(code: str) -> list:
    """Paths read by a Codex code-mode `exec` JS cell."""
    if "SKILL.md" not in code or "exec_command" not in code:
        return []
    out = []
    # literal shell commands inside the JS
    for m in re.finditer(r"cmd\s*:\s*(`(?:[^`\\]|\\.)*`|\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')", code):
        lit = m.group(1)[1:-1]
        try:
            lit_dec = json.loads('"' + lit.replace('"', '\\"') + '"') if m.group(1)[0] == '"' else lit
        except ValueError:
            lit_dec = lit
        out.extend(_segment_reads(lit_dec.replace("\\n", "\n")))
    # templated reads: cmd: `sed -n '1,400p' '${path}'` over a literal path list
    if re.search(r"cmd\s*:\s*`[^`]*\b(" + "|".join(READ_VERBS) + r")\b[^`]*\$\{", code):
        for m in re.finditer(r"[\"'`]([^\"'`\n]*SKILL\.md)[\"'`]", code):
            line_start = code.rfind("\n", 0, m.start()) + 1
            if WRITE_BEFORE_RE.search(code[line_start:m.start()]):
                continue
            out.append(m.group(1))
    return out


def _resolve(tok: str, cwd: str) -> str:
    tok = tok.strip("\"'`")
    tok = os.path.expanduser(tok.replace("$HOME", "~").replace("${HOME}", "~"))
    if not tok.startswith("/") and cwd:
        cwd = cwd[7:] if cwd.startswith("file://") else cwd
        tok = os.path.join(cwd, tok)
    return os.path.normpath(tok)


def _skills_from_tokens(sess: _Session, toks, stats) -> list:
    if sess.is_guardian:  # approval-review sessions are automated, never a use
        return []
    names = []
    for tok in toks:
        path = _resolve(tok, sess.cwd)
        name = sess.catalog.get(path)
        if name is None:
            if not any(mk in path for mk in SKILL_ROOT_MARKERS):
                stats["reads_outside_skill_roots"] = stats.get("reads_outside_skill_roots", 0) + 1
                samples = stats.setdefault("_outside_root_samples", [])
                if len(samples) < 500:
                    samples.append((sess.sid, path))
                continue
            name = _name_from_path(path)
            if name and ":" not in name and name not in sess.names:
                full = sess.base_to_full.get(name)
                if full and len(full) == 1:
                    name = next(iter(full))
        if name and name not in names:
            names.append(name)
    if len(names) > MAX_SKILLS_PER_COMMAND:
        stats["survey_commands_skipped"] = stats.get("survey_commands_skipped", 0) + 1
        return []
    return names


def _mentions(sess: _Session, text: str, disk_names: set) -> list:
    out = []
    for m in MENTION_RE.finditer(text):
        raw = m.group(1).rstrip(".-")
        prev = text[m.start() - 1] if m.start() else " "
        nxt = text[m.end():m.end() + 2]
        # code-ish contexts: x=$var, "$var", {$var}, $var[..], $var->, $var(
        if prev in "=\"'{:/." or (nxt[:1] and nxt[:1] in "[(=") or nxt == "->":
            continue
        name = None
        if raw in sess.names:
            name = raw
        elif raw in sess.base_to_full and len(sess.base_to_full[raw]) == 1:
            name = next(iter(sess.base_to_full[raw]))
        elif raw in disk_names:
            name = raw
        if name and name not in out:
            out.append(name)
    return out


def _all_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _all_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _all_strings(v)


def _user_texts(content) -> list:
    out = []
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and isinstance(c.get("text"), str):
                out.append(c["text"])
    elif isinstance(content, str):
        out.append(content)
    return out


# --------------------------------------------------------------------------- file iteration

def _open_lines(path, stats):
    if path.endswith(".zst"):
        zstd = shutil.which("zstd") or "/opt/homebrew/bin/zstd"
        proc = subprocess.Popen([zstd, "-dc", path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            for raw in proc.stdout:
                stats["bytes_scanned"] += len(raw)
                yield raw.decode("utf-8", "replace")
        finally:
            proc.stdout.close()
            rc = proc.wait()
            if rc != 0:
                raise IOError(f"zstd exit {rc}")
    else:
        with open(path, "rb") as fh:
            for raw in fh:
                stats["bytes_scanned"] += len(raw)
                yield raw.decode("utf-8", "replace")


def _list_files():
    files = []
    for p in glob.glob(os.path.join(SESSIONS_DIR, "*", "*", "*", "*.jsonl")):
        files.append((p, False))
    for p in glob.glob(os.path.join(ARCHIVED_DIR, "*.jsonl")) + glob.glob(os.path.join(ARCHIVED_DIR, "*.jsonl.zst")):
        files.append((p, True))
    files.sort()
    return files


def _ro_connect(path, stats=None):
    """Open a live (WAL) sqlite DB read-only; fall back to immutable mode, which
    ignores not-yet-checkpointed WAL pages, when the -shm file cannot be used."""
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.execute("select 1 from sqlite_master limit 1").fetchall()
        return con
    except sqlite3.Error:
        if stats is not None:
            stats["sqlite_immutable_fallback"] = stats.get("sqlite_immutable_fallback", 0) + 1
        return sqlite3.connect(f"file:{path}?immutable=1", uri=True)


def _state_threads(stats=None):
    info = {}
    if not os.path.exists(STATE_DB):
        return info
    try:
        con = _ro_connect(STATE_DB, stats)
        for tid, archived, cwd, src, tsrc, path in con.execute(
                "select id, archived, cwd, source, thread_source, rollout_path from threads"):
            info[tid] = {"archived": bool(archived), "cwd": cwd or "", "source": src or "",
                         "thread_source": tsrc or "", "rollout_path": path}
        con.close()
    except sqlite3.Error:
        pass
    return info


def _file_start(path) -> Optional[datetime]:
    m = FILE_TS_RE.search(os.path.basename(path))
    if not m:
        return None
    # rollout file names use local wall time of the machine (Beijing here)
    try:
        return datetime.strptime(f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4)}",
                                 "%Y-%m-%dT%H:%M:%S").replace(tzinfo=BJT)
    except ValueError:
        return None


def _scan_file(path, archived, since, until, stats, disk_names, emitted, seen_ids, state):
    m = UUID_RE.findall(os.path.basename(path))
    sid = m[-1] if m else os.path.basename(path)
    st = state.get(sid)
    if st:
        archived = st["archived"] or archived
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(path), BJT)
    except OSError:
        mtime = None
    fallback = _file_start(path) or mtime
    sess = _Session(sid, archived, fallback, path)
    if st:
        sess.cwd = st["cwd"]
        sess.is_guardian = "guardian" in st["source"] or st["thread_source"] == "guardian_review"
        sess.is_subagent = "thread_spawn" in st["source"] or st["thread_source"] == "subagent"
    meta_seen = False

    def emit(names, signal, ts, lineno, turn_hint=None):
        turn = turn_hint or sess.turn or f"syn{sess.synthetic_turn}"
        ts = ts or sess.last_ts or sess.fallback_ts
        for name in names:
            stats["raw_hits_" + signal] = stats.get("raw_hits_" + signal, 0) + 1
            key = (sess.sid, turn, name)
            if key in emitted:
                stats["dedup_merged"] = stats.get("dedup_merged", 0) + 1
                continue
            emitted.add(key)
            if ts is None or not (since <= ts < until):
                continue
            yield {
                "skill": name, "base_name": _base(name), "source": "codex", "signal": signal,
                "timestamp": ts.isoformat(timespec="seconds"), "month": ts.strftime("%Y-%m"),
                "session_id": sess.sid, "archived": sess.archived, "project_dir": sess.cwd,
                "file": path, "line": lineno,
            }

    for lineno, line in enumerate(_open_lines(path, stats), 1):
        head = line[:400]
        has_skill = "SKILL.md" in line or "<skill>" in line
        is_meta = '"session_meta"' in head or (lineno == 1 and head.startswith('{"id"'))
        is_turn = '"type":"turn_context"' in head or '"type":"task_started"' in head
        is_user = '"role":"user"' in head  # every user message advances synthetic turns
        if not (has_skill or is_meta or is_turn or is_user or "(file: " in line):
            # still track timestamps cheaply
            tm = re.search(r'"timestamp":"([^"]+)"', head)
            if tm:
                sess.last_ts = _codex_parse_ts(tm.group(1)) or sess.last_ts
            continue
        try:
            d = json.loads(line)
        except ValueError:
            stats["lines_failed"] += 1
            continue
        if not isinstance(d, dict):
            continue
        ts = _codex_parse_ts(d.get("timestamp"))
        if ts:
            sess.last_ts = ts
        rtype = d.get("type")
        p = d.get("payload") if isinstance(d.get("payload"), dict) else d
        ordinal = d.get("ordinal")

        if rtype == "session_meta" or (lineno == 1 and "id" in d and "type" not in d):
            if not meta_seen:
                meta_seen = True
                sess.cwd = p.get("cwd") or sess.cwd
                src = json.dumps(p.get("source")) if p.get("source") is not None else ""
                if "guardian" in src or p.get("thread_source") == "guardian_review":
                    sess.is_guardian = True
                if "thread_spawn" in src or p.get("thread_source") == "subagent":
                    sess.is_subagent = True
                if p.get("forked_from_id") and isinstance(p.get("subagent_history_start_ordinal"), int):
                    sess.skip_before_ordinal = p["subagent_history_start_ordinal"]
                if ts is None and not sess.fallback_ts:
                    sess.fallback_ts = _codex_parse_ts(p.get("timestamp"))
            bi = p.get("base_instructions")
            if isinstance(bi, dict):
                bi = bi.get("text")
            if isinstance(bi, str) and "(file: " in bi:
                sess.add_catalog(bi)
            continue

        # replayed parent history in forked sub-agent rollouts
        if sess.skip_before_ordinal is not None and isinstance(ordinal, int) and ordinal < sess.skip_before_ordinal:
            stats["replayed_records_skipped"] = stats.get("replayed_records_skipped", 0) + 1
            continue
        if rtype == "compacted":
            continue

        tid = p.get("turn_id") if isinstance(p, dict) else None
        if rtype in ("turn_context", "event_msg") and tid and p.get("type") in (None, "task_started"):
            sess.turn = tid
            sess.has_turn_ids = True
        if rtype == "turn_context":
            sess.cwd = p.get("cwd") or sess.cwd
            continue
        if rtype == "event_msg" and p.get("type") == "task_started":
            continue

        ptype = p.get("type")
        meta = p.get("internal_chat_message_metadata_passthrough") or {}
        turn_hint = tid or (meta.get("turn_id") if isinstance(meta, dict) else None)

        # catalog from developer instructions / world_state
        if "(file: " in line and (p.get("role") == "developer" or rtype == "world_state"):
            for t in _all_strings(p):
                if "(file: " in t:
                    sess.add_catalog(t)
            continue

        # user messages: mentions + injections
        if ptype == "message" and p.get("role") == "user":
            mid = p.get("id")
            if mid:
                if (sess.sid, mid) in seen_ids:
                    continue
                seen_ids.add((sess.sid, mid))
            texts = _user_texts(p.get("content"))
            if sess.is_guardian:
                continue
            for t in texts:
                s = t.lstrip()
                if s.startswith("<skill>"):
                    names = [n.strip() for n in INJECT_RE.findall(s)]
                    yield from emit(names, "skill_injection", ts, lineno, turn_hint)
                    continue
                if s.startswith(NON_USER_PREFIXES):
                    continue
                if not sess.has_turn_ids:
                    sess.synthetic_turn += 1
                if sess.is_subagent:
                    continue  # the "user" of a spawned sub-agent is the parent model
                names = _mentions(sess, t, disk_names)
                if names:
                    yield from emit(names, "user_mention", ts, lineno, turn_hint)
            continue

        if "SKILL.md" not in line:
            continue
        toks = []
        item_id = None
        if rtype == "event_msg" and ptype == "item_completed":
            it = p.get("item") or {}
            if it.get("type") != "CommandExecution":
                continue
            item_id = it.get("id")
            for pc in it.get("parsed_cmd") or []:
                if pc.get("type") in ("read", "search") and str(pc.get("path") or "").endswith("SKILL.md"):
                    toks.append(pc["path"])
            cmd = it.get("command")
            if isinstance(cmd, list):
                cmd = cmd[-1] if cmd else ""
            toks.extend(_segment_reads(cmd or ""))
            if it.get("cwd"):
                c = it["cwd"]
                sess.cwd = c[7:] if c.startswith("file://") else c
        elif ptype in ("function_call", "local_shell_call", "custom_tool_call"):
            name = p.get("name") or ""
            item_id = p.get("call_id") or p.get("id")
            if ptype == "custom_tool_call" and name == "exec":
                toks.extend(_js_reads(p.get("input") or ""))
            elif name in ("shell", "exec_command", "container.exec", "shell_command") or ptype == "local_shell_call":
                args = p.get("arguments") or p.get("action") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {"cmd": args}
                cmd = args.get("command") or args.get("cmd") or ""
                if isinstance(cmd, list):
                    cmd = cmd[-1] if cmd else ""
                if args.get("workdir"):
                    sess.cwd = args["workdir"]
                toks.extend(_segment_reads(cmd))
            else:
                continue
        else:
            continue
        if item_id:
            if (sess.sid, item_id) in seen_ids:
                continue
            seen_ids.add((sess.sid, item_id))
        names = _skills_from_tokens(sess, toks, stats)
        if names:
            yield from emit(names, "skill_read", ts, lineno, turn_hint)


def _scan_history_db(since, until, stats, disk_names, emitted, skip_ids, state):
    if not (INCLUDE_HISTORY_DB and os.path.exists(HISTORY_DB)):
        return
    try:
        con = _ro_connect(HISTORY_DB, stats)
    except sqlite3.Error:
        stats["files_failed"] += 1
        return
    lo = int(since.timestamp() * 1000)
    hi = int(until.timestamp() * 1000)
    q = ("select thread_id, turn_id, item_id, rollout_ordinal, created_at_ms, item_type, item_json "
         "from thread_items where item_type in ('commandExecution','userMessage') "
         "and created_at_ms >= ? and created_at_ms < ? "
         "and (item_json like '%SKILL.md%' or (item_type='userMessage' and item_json like '%$%')) "
         "order by thread_id, rollout_ordinal")
    sessions = {}
    stats["history_threads_scanned"] = 0
    for tid, turn, item_id, ordn, cms, itype, ij in con.execute(q, (lo, hi)):
        if tid in skip_ids:
            continue
        sess = sessions.get(tid)
        if sess is None:
            st = state.get(tid, {})
            sess = _Session(tid, st.get("archived", False), None, HISTORY_DB)
            sess.cwd = st.get("cwd", "")
            sess.is_guardian = "guardian" in st.get("source", "") or st.get("thread_source") == "guardian_review"
            sess.is_subagent = "thread_spawn" in st.get("source", "") or st.get("thread_source") == "subagent"
            sessions[tid] = sess
            stats["history_threads_scanned"] += 1
        stats["history_items_scanned"] = stats.get("history_items_scanned", 0) + 1
        try:
            it = json.loads(ij)
        except ValueError:
            stats["lines_failed"] += 1
            continue
        ts = datetime.fromtimestamp(cms / 1000, BJT)
        names, signal = [], None
        if itype == "userMessage":
            if sess.is_guardian:
                continue
            for t in _user_texts(it.get("content")):
                s = t.lstrip()
                if s.startswith("<skill>"):
                    names += [n.strip() for n in INJECT_RE.findall(s)]
                    signal = signal or "skill_injection"
                elif not s.startswith(NON_USER_PREFIXES) and not sess.is_subagent:
                    for n in _mentions(sess, t, disk_names):
                        if n not in names:
                            names.append(n)
                            signal = signal or "user_mention"
        else:
            if it.get("cwd"):
                sess.cwd = it["cwd"]
            toks = [a["path"] for a in it.get("commandActions") or []
                    if a.get("type") in ("read", "search") and str(a.get("path") or "").endswith("SKILL.md")]
            toks += _segment_reads(it.get("command") or "")
            names = _skills_from_tokens(sess, toks, stats)
            signal = "skill_read"
        for name in names:
            stats["raw_hits_" + signal] = stats.get("raw_hits_" + signal, 0) + 1
            key = (tid, turn, name)
            if key in emitted:
                stats["dedup_merged"] = stats.get("dedup_merged", 0) + 1
                continue
            emitted.add(key)
            yield {
                "skill": name, "base_name": _base(name), "source": "codex", "signal": signal,
                "timestamp": ts.isoformat(timespec="seconds"), "month": ts.strftime("%Y-%m"),
                "session_id": tid, "archived": sess.archived, "project_dir": sess.cwd,
                "file": HISTORY_DB, "line": ordn,
            }
    con.close()


LIMIT_FILES: Optional[int] = None  # set by __main__ --limit-files; None = everything


def iter_codex_events(since: datetime, until: datetime, stats: dict) -> Iterator[dict]:
    _limit_files = LIMIT_FILES
    for k in ("files_scanned", "files_failed", "files_skipped_by_date", "lines_failed", "bytes_scanned"):
        stats.setdefault(k, 0)
    disk_names = _disk_skill_names()
    state = _state_threads(stats)
    stats["state_threads_known"] = len(state)
    emitted: set = set()
    seen_ids: set = set()
    files = _list_files()
    file_ids = set()
    for path, _ in files:
        m = UUID_RE.findall(os.path.basename(path))
        if m:
            file_ids.add(m[-1])
    if _limit_files is not None:
        files = files[-_limit_files:] if _limit_files >= 0 else files
    for path, archived in files:
        start = _file_start(path)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path), BJT)
        except OSError:
            mtime = None
        # no event can be newer than the last write, nor older than the file start
        if (mtime and mtime < since) or (start and start >= until):
            stats["files_skipped_by_date"] += 1
            continue
        stats["files_scanned"] += 1
        try:
            yield from _scan_file(path, archived, since, until, stats, disk_names, emitted, seen_ids, state)
        except (OSError, IOError) as e:
            stats["files_failed"] += 1
            stats.setdefault("failed_files", []).append(f"{os.path.basename(path)}: {e}")
    if _limit_files is None:
        yield from _scan_history_db(since, until, stats, disk_names, emitted, file_ids, state)


# ==========================================================================
# Aggregation / CLI
# ==========================================================================

EVENT_FIELDS = ("skill", "base_name", "source", "signal", "timestamp", "month",
                "session_id", "archived", "project_dir")


def _parse_day(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=BJ)


def _jsonable_stats(st: dict) -> dict:
    out = {}
    for k, v in st.items():
        if k.startswith("_") or k == "failed_files":
            continue
        if isinstance(v, Counter):
            v = dict(v.most_common())
        elif isinstance(v, set):
            v = len(v)
        try:
            json.dumps(v)
        except TypeError:
            v = str(v)
        out[k] = v
    return out


REPO_SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
COVERAGE_NOTE = (
    "Counts come from the maintainer's local Claude Code and Codex session logs, "
    "so they reflect one person's usage, not installs. Claude Code transcripts exist "
    "only from 2026-08 and most older Codex logs were pruned, so months before the "
    "recent_3m window are undercounted. Reading a SKILL.md with Claude's Read tool, "
    "or a skill typed but never loaded, is not counted. A skill used several times "
    "in one turn counts once. 0 means no recorded use, not proof of no use."
)


def _last_months(today: datetime, n: int) -> list:
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out[::-1]


def _status(n: int) -> str:
    return "active" if n >= 5 else "low" if n >= 1 else "inactive"


def repo_usage(events: list, today: datetime, months6: list) -> dict:
    """Aggregate events for skills under this repo's skills/ directory only."""
    repo_skills = sorted(d for d in os.listdir(REPO_SKILLS_DIR)
                         if os.path.isfile(os.path.join(REPO_SKILLS_DIR, d, "SKILL.md")))
    counts = {s: Counter() for s in repo_skills}
    for e in events:
        if e["base_name"] in counts and e["month"] in months6:
            counts[e["base_name"]][e["month"]] += 1
    months3 = months6[-3:]
    skills = {}
    for s in repo_skills:
        c = counts[s]
        used = [m for m in months6 if c[m]]
        r3 = sum(c[m] for m in months3)
        skills[s] = {
            "monthly": {m: c[m] for m in months6},
            "recent_3m": r3,
            "last_used_month": used[-1] if used else None,
            "status": _status(r3),
        }
    return {
        "generated_at": today.strftime("%Y-%m-%d"),
        "window": {
            "monthly": f"{months6[0]} to {months6[-1]}",
            "recent_3m": f"{months3[0]} to {months3[-1]}",
            "note": f"Calendar months in UTC+8; {months6[-1]} is partial, up to {today.strftime('%Y-%m-%d')}.",
        },
        "status_rule": "recent_3m >= 5: active; 1-4: low; 0: inactive",
        "coverage_note": COVERAGE_NOTE,
        "skills": skills,
    }


def main(argv=None) -> int:
    today = datetime.now(BJ).replace(hour=0, minute=0, second=0, microsecond=0)
    ap = argparse.ArgumentParser(description="Count skill usages in Claude Code and Codex sessions")
    ap.add_argument("--since", default=(today - timedelta(days=184)).strftime("%Y-%m-%d"),
                    help="inclusive start date, Beijing time (default: ~6 months ago)")
    ap.add_argument("--until", default=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
                    help="exclusive end date, Beijing time (default: tomorrow)")
    ap.add_argument("--out-dir", default=None,
                    help="directory for private outputs (default: skill-usage-out)")
    ap.add_argument("--no-claude", action="store_true", help="skip Claude Code sessions")
    ap.add_argument("--no-codex", action="store_true", help="skip Codex sessions")
    ap.add_argument("--emit-repo-usage", metavar="PATH",
                    help="write aggregate usage of this repo's skills (e.g. docs/readme/usage.json)")
    a = ap.parse_args(argv)
    months6 = _last_months(today, 6)
    if a.emit_repo_usage:
        # the repo file always covers the last 6 calendar months up to today
        a.since = months6[0] + "-01"
        a.until = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    since, until = _parse_day(a.since), _parse_day(a.until)
    out_dir = None
    if a.out_dir or not a.emit_repo_usage:
        out_dir = os.path.expanduser(a.out_dir or "skill-usage-out")
        os.makedirs(out_dir, exist_ok=True)

    events: list = []
    coverage: dict = {}
    sources = []
    if not a.no_claude:
        sources.append(("claude", iter_claude_events))
    if not a.no_codex:
        sources.append(("codex", iter_codex_events))
    for name, fn in sources:
        st: dict = {}
        t0 = time.time()
        n0 = len(events)
        events.extend(fn(since, until, st))
        st["elapsed_s"] = round(time.time() - t0, 1)
        st["events"] = len(events) - n0
        coverage[name] = _jsonable_stats(st)
        print(f"[{name}] events={st['events']} files_scanned={st.get('files_scanned')} "
              f"files_failed={st.get('files_failed')} lines_failed={st.get('lines_failed')} "
              f"elapsed={st['elapsed_s']}s", file=sys.stderr)

    events.sort(key=lambda e: e["timestamp"])
    if a.emit_repo_usage:
        path = os.path.expanduser(a.emit_repo_usage)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(repo_usage(events, today, months6), fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"wrote repo usage to {path}", file=sys.stderr)
    if out_dir is None:
        return 0
    with open(os.path.join(out_dir, "usage_events.jsonl"), "w", encoding="utf-8") as fh:
        for e in events:
            row = {k: e.get(k) for k in EVENT_FIELDS}
            for k in ("is_subagent", "file", "line"):
                if k in e:
                    row[k] = e[k]
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    agg: dict = {}
    for e in events:
        b = e["base_name"]
        s = agg.setdefault(b, {"total": 0, "by_source": Counter(), "monthly": Counter(),
                               "_sessions": set(), "names": Counter(),
                               "first_used": e["timestamp"], "last_used": e["timestamp"]})
        s["total"] += 1
        s["by_source"][e["source"]] += 1
        s["monthly"][e["month"]] += 1
        s["_sessions"].add((e["source"], e["session_id"]))
        s["names"][e["skill"]] += 1
        s["first_used"] = min(s["first_used"], e["timestamp"])
        s["last_used"] = max(s["last_used"], e["timestamp"])
    skills = {}
    for b, s in sorted(agg.items(), key=lambda kv: (-kv[1]["total"], kv[0])):
        skills[b] = {
            "total": s["total"],
            "by_source": dict(s["by_source"]),
            "monthly": dict(sorted(s["monthly"].items())),
            "distinct_sessions": len(s["_sessions"]),
            "first_used": s["first_used"],
            "last_used": s["last_used"],
            "raw_names": dict(s["names"].most_common()),
        }
    months = sorted({e["month"] for e in events})
    summary = {
        "generated_at": datetime.now(BJ).isoformat(timespec="seconds"),
        "window": {"since": since.isoformat(), "until": until.isoformat()},
        "months": months,
        "total_events": len(events),
        "coverage": coverage,
        "skills": skills,
    }
    with open(os.path.join(out_dir, "usage_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, "usage_by_month.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["base_name", "total", "claude", "codex"] + months)
        for b, s in skills.items():
            w.writerow([b, s["total"], s["by_source"].get("claude", 0), s["by_source"].get("codex", 0)]
                       + [s["monthly"].get(m, 0) for m in months])
    print(f"wrote {len(events)} events, {len(skills)} skills to {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
