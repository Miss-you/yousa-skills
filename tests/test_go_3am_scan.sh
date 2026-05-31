#!/usr/bin/env bash
# Acceptance checks for the go-3am-debuggable heuristic scanner.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCAN="$REPO_ROOT/skills/go-3am-debuggable/scripts/scan.sh"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cat > "$TMP/sample.go" <<'GO'
package sample

import (
	"context"
	"time"
)

var (
	reportFunc = realReport
)

func realReport(table string, args ...interface{}) {}

func lowercaseCallback(ctx context.Context, build func() []string) {
	trpc.Go(ctx, time.Second, func(ctx context.Context) {
		consume(func() string { return "nested" })
		_ = build()
	})
}

func detachContext(ctx context.Context) {
	trpc.Go(context.Background(), time.Second, func(ctx context.Context) {
		report(ctx)
	})
}

func closureChain(items []string) []string {
	seen := map[string]bool{}
	ensure := func(name string) bool {
		if name == "" {
			return false
		}
		seen[name] = true
		return true
	}
	appendName := func(out []string, name string) []string {
		if !ensure(name) {
			return out
		}
		return append(out, name)
	}
	var out []string
	for _, item := range items {
		out = appendName(out, item)
	}
	return out
}

func legalAsync(ctx context.Context) {
	trpc.Go(ctx, time.Second, func(ctx context.Context) {
		report(ctx)
	})
}

func consume(fn func() string) { _ = fn() }
func report(ctx context.Context) {}
GO

output="$(bash "$SCAN" "$TMP")"

assert_contains() {
  local needle="$1"
  if [[ "$output" != *"$needle"* ]]; then
    printf 'expected scanner output to contain %q\n\noutput:\n%s\n' "$needle" "$output" >&2
    exit 1
  fi
}

assert_contains "A. "
assert_contains "reportFunc"
assert_contains "B. "
assert_contains "lowercaseCallback"
assert_contains "C. "
assert_contains "consume(func() string"
assert_contains "E. "
assert_contains "ensure := func"
assert_contains "appendName := func"
assert_contains "F. 异步边界检查点"
assert_contains "trpc.Go"
assert_contains "G. context.Background/TODO near async"
assert_contains "context.Background"

printf 'go-3am scan acceptance checks passed\n'
