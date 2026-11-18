# Acceptance Blindspots Checklist

## Shared dispatch context

Every role receives: task/spec paths; exact base and target state; included changed paths/hunks and requirement mapping; related unchanged code; exclusions with reasons; fingerprints; accepted tradeoffs; commands already run. Review read-only. Report a missing scope dependency to the orchestrator before silently expanding the target.

## Role prompts

- **Vertical:** Run the relevant test/build commands on the declared state, with project-required flags. Record commands, exit codes and log paths. Verify tests assert behavior across real boundaries rather than only mocked function calls. Separate environment blocks, confirmed baseline failures, regressions and untested paths. Do not claim a staged snapshot passed tests run against different working-tree content.
- **Horizontal:** Map every in-scope requirement to implementation and test evidence. Compare with the nearest reference implementation or architecture layers: definition, routes/RPC, validation, producer, consumer, runtime configuration, generated artifacts, tests. Include necessary unchanged code. Record missing touchpoints with impact; task checkboxes are not proof.
- **Chain:** Trace every new/changed field and option through define → serialize → transport → deserialize → consume. Check both languages, old/new rollout combinations, defaults, loss/duplication, nil/empty inputs, errors, cancellation, concurrency and rollback where relevant. A field existing in a proto does not prove it reaches its use site.
- **Fact:** Verify only material, unstable external claims against primary/official sources, cite URLs and dates. Distinguish documented vendor behavior from repository policy or an unverified environment assumption. Do not browse just to fill this role when no external claim needs verification.
- **Judge:** After receiving specialist evidence, challenge each suspected finding against the actual target, requirements and accepted tradeoffs. Reproduce or inspect evidence, remove duplicates and unsupported claims, and distinguish “no findings” from “not tested.” Report in the skill's required order. Do not repair product code during review.

## Scope traps

| Trap | Required response |
|---|---|
| Empty index while spec implementation is unstaged/untracked | Review working-tree candidates by default; empty index is not empty task scope |
| Spec names only handler, but producer is in a sibling directory | Include producer when supported by diff/call-chain evidence |
| Unrelated README edit in the same workspace | Record exclusion; don't review it as part of the feature |
| Staged bug is fixed only in working tree | Test isolated index snapshot or report the gap |
| Spec's implementation was already committed | Resolve relevant history/base; don't invent HEAD~1 |
| Same file contains unrelated hunks | Include only justified hunks; read other hunks as context if needed |
| Deleted/renamed file or generated binding | Keep in candidate scope and inspect consumers/registration |
| Test package is skipped or cannot be listed | Explicit coverage gap, never “all passed” |
| Workspace changed during review | Recollect scope and re-review affected evidence |

## Finding template

- Severity: high/P1, medium/P2, low/P3
- Requirement / regression:
- Trigger and production impact:
- Evidence: exact target-state path:line, chain or reproduction
- Suggested fix:

Accepted risks still need accurate reporting. A proven violation of the stated safety boundary remains a finding even if a broader risk was accepted. Live operational conditions that were not checked remain unverified.

## Helper migration

`collect_review_scope.py` emits JSON candidates and fingerprints from any repository subdirectory. Use `--mode staged` for index-only or `--mode range --base <commit> --head <commit>` for an exact committed range. It does not infer spec relevance or run tests. Exit 0 means collection succeeded, not acceptance.

The legacy `run_staged_acceptance.sh` now delegates collection to this helper. Its old `--run-tests` mode is intentionally rejected: automatic Go-only tests against the working tree could misrepresent index/commit evidence and skip other languages. Choose explicit repository test commands through the Vertical role.
