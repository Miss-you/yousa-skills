---
name: secret-scan
description: Use when about to git commit, git push, or create PRs. Scans staged/changed files for leaked secrets (API keys, tokens, passwords, credentials). MUST run before any git commit or push operation.
---

# Secret Scan

Scan files for accidentally included secrets before git operations. Prevents credential leaks.

## When to Use

- Before `git commit`
- Before `git push`
- Before creating PRs
- When reviewing staged changes

## Scan Patterns

Check staged/changed files for these patterns:

| Type | Pattern | Example |
|------|---------|---------|
| API Key | `sk-[a-zA-Z0-9]{20,}` | `sk-jDDxHo4CtzRau4...` |
| Kimi Key | `sk-kimi-[a-zA-Z0-9]+` | `sk-kimi-jzAmMPO...` |
| Bearer Token | `Bearer [a-zA-Z0-9_\-\.]{20,}` | `Bearer eyJhbGci...` |
| AWS Key | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| Password in URL | `://[^:]+:[^@]+@` | `mysql://root:pass@host` |
| Private Key | `-----BEGIN.*PRIVATE KEY-----` | PEM private keys |
| Generic Secret | `(secret\|password\|passwd\|token\|api_key)\s*[=:]\s*["'][^"']{8,}` | `password = "abc123xyz"` |
| Base64 long blob | Inline base64 > 200 chars in source code | Data URI with actual image data |
| .env values | `^[A-Z_]+=.{20,}` in `.env` files | `DATABASE_URL=postgres://...` |

## Procedure

```dot
digraph scan {
    "Get changed files" [shape=box];
    "Grep patterns" [shape=box];
    "Secrets found?" [shape=diamond];
    "Report & BLOCK commit" [shape=box, style=filled, fillcolor=red, fontcolor=white];
    "Safe to proceed" [shape=box, style=filled, fillcolor=green];

    "Get changed files" -> "Grep patterns";
    "Grep patterns" -> "Secrets found?";
    "Secrets found?" -> "Report & BLOCK commit" [label="yes"];
    "Secrets found?" -> "Safe to proceed" [label="no"];
}
```

**Step 1:** Get files to scan

```bash
# Staged files
git diff --cached --name-only
# Or all changed files (staged + unstaged)
git diff --name-only HEAD
# Or specific files about to be committed
git status --porcelain | awk '{print $2}'
```

**Step 2:** Run scan (exclude binary files, known safe patterns)

```bash
# Core scan command
grep -rn -E "(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN.*PRIVATE KEY|Bearer [a-zA-Z0-9_\-\.]{20,})" <files>
```

**Step 3:** Review results
- Ignore matches inside: `token.yaml`, `.env`, `.env.*`, `*.example`, test mocks with `"sk-test-key"`
- Flag matches in: `.py`, `.js`, `.ts`, `.yaml`, `.yml`, `.json`, `.md`, `.sh` source files
- BLOCK if real credentials found in committed files

## Safe Patterns (Do NOT Flag)

- `os.environ.get("MOONSHOT_API_KEY")` - reading env var, not a secret
- `"sk-test-key"` or `"sk-xxx"` - obvious placeholders
- `token.yaml` in `.gitignore` - already excluded
- Test files with `MagicMock` / placeholder values
- Documentation describing key formats (like this skill)

## If Secrets Found

1. **Do NOT commit.** Report the file, line number, and pattern match.
2. Move secret to environment variable or `token.yaml` (which should be in `.gitignore`).
3. If secret was already committed: rotate the credential immediately, then `git filter-branch` or `git-filter-repo` to remove from history.
