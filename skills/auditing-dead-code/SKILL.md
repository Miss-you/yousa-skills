---
name: auditing-dead-code
description: Use when identifying unused functions, dead code, deletion candidates, or "safe to remove" symbols, especially with RPC, config, generated code, scripts, or exported APIs
---

# Auditing Dead Code

## Overview

Dead-code audits are evidence classification, not grep counting. A symbol is removable only when static analysis, reference classification, entrypoint checks, and API-boundary risks agree.

## When to Use

Use for "find unused functions", "safe to delete", "dead code scan", or "unreferenced symbols".

## Core Pattern

1. Define scope: target dirs, tests, scripts, config, generated/proto/RPC surfaces, build tags, external caller risk.
2. Run static tools first. If packages do not load or no unused/deadcode tool succeeds, mark degraded; never claim "safe" from text search alone.
3. Enumerate symbols, including exported symbols missed by private-unused tools.
4. Search exact names and variants across production, tests, generated, scripts, docs, proto, config, CI, and cron.
5. Block false positives: RPC handlers, proto aliases, generated service interfaces, `Register...Service`, main registration, route maps, config keys, reflection, `map[string]func`, init/plugin registries, interface dispatch, build tags, scripts.
6. For medium/high risk, split agents into static-tool scan, text-reference classification, and entrypoint/config/interface review. Reconcile disagreements.
7. Classify evidence; unresolved entrypoint, interface, exported API, or dynamic dispatch risk overrides hit counts.
8. If deleting, rerun static tools, exact/variant searches, affected tests, service build, broader tests when feasible, and proto/generated checks if relevant.

## Quick Reference

| Category | Evidence | Action |
|---|---|---|
| Safe-looking internal | Unexported; static tool hit; no refs except definition/comments | Remove after tests/build |
| Cascading candidate | Only called by another dead candidate | Remove as a group |
| Exported symbol | No repo refs; no entrypoint/config evidence | Unknown until org-wide search or owner signoff |
| Not a candidate | RPC/API surface, interface method, config/route/reflection target, script caller | Keep |
| Degraded audit | Tooling failed or dynamic usage unclear | Do not call safe |

## Implementation

For Go services, start with:

```bash
go list ./target/...
staticcheck -checks=U1000 ./target/...
golangci-lint run --no-config --enable-only=unused ./target/...
rg -n '\bSymbolName\b|symbol_name|/service/path|trpc\.alias' .
```

Classify refs as production, test-only, generated, config, docs, scripts, CI/cron. Docs alone do not prove liveness. Operational scripts block deletion. A method is removable only if not required by any interface, or the interface plus implementers and callers are dead.

Example: `oldRank` is unexported, `U1000`, no exact/variant refs, no interface/RPC/config/script hits: safe-looking internal. `OldRank` with the same evidence is exported: unknown until cross-repo search by module path or owner signoff.

## Output Template

Report: SOP, commands, candidate table, easy-to-misread non-candidates, and exported/cross-repo limits.

## Common Mistakes

| Mistake | Fix |
|---|---|
| `rg` hit counting | Separate definition, production calls, tests, docs, logs, generated code |
| Green tests only | Tests do not prove no external caller or config route |
| Exported equals safe | Require cross-repo search or owner signoff |
| Ignoring RPC/generated | Check proto aliases, generated registration, main registration |
| Missing scripts | Search CLI/offline operational scripts |
