# DEV-01 validation throughput policy

## Scope and authority

DEV-01 shortens local analysis, build and validation feedback. It is development
infrastructure, not a P06/P17/P18 product or release Gate. A fast-profile PASS
MUST NOT replace a complete phase closure run or be promoted to actual HWPX,
Hangul, render, automation, differential, production or performance-SLO evidence.

Historical frozen validators and their source locks are immutable. DEV-01 may
provide a source-lockable implementation for a future successor, but MUST NOT
rewrite, monkey-patch or silently cache around a historical tamper test.

## Validation tiers

- `component`: focused code and contract feedback only.
- `development_feedback_only`: current P17 checks/contracts with qualification,
  frozen-authority and source-successor replay excluded by an explicit plan.
- `closure_validation`: the existing complete discovery/workspace command. No
  test count, assertion or evidence requirement is removed.

Every profile exposes its authority before executing. An unknown profile fails
closed. The current full P17 command remains
`python -m unittest discover -s tools/p17/tests -p "test_*.py"`.

## Live run journal

- Commands execute as argument arrays without a shell.
- stdout and stderr stream to the console while an elapsed-time heartbeat is
  emitted at a bounded interval.
- Ignored `tmp/dev-runs/` contains bounded JSONL events and an atomic summary.
- The initial summary is `running`; only an observed zero exit becomes `passed`.
- Persisted output redacts the workspace path, URI credentials, bearer values
  and common secret assignments. Raw command arguments and environment values
  are never persisted.
- Names, arguments, queued stream chunks, events and total log bytes are bounded.
- `sccache` is opt-in. When selected, the runner uses it only for Cargo, honors
  an existing `RUSTC_WRAPPER`, and disables incompatible incremental calls.

## Git object batch reader

The reader SHALL preserve exact 40-hex revision and relative-path validation,
repository-selection environment removal, no prompts, no lazy fetch, no replace
objects, blob-type and size checks, exact-length reads and bounded memory. One
reader may reuse one `git cat-file --batch` process and cache at most 4,096
entries or 64 MiB.
Missing, malformed, non-blob, oversized and truncated responses fail closed with
content-free codes.

## Product hot-path change

Preserving-patch conflict detection SHALL retain the existing range semantics:
duplicate insert positions conflict; insertions on either replacement boundary
conflict; overlapping replacements conflict; adjacent replacements do not.
After deterministic sorting, validation MUST use a single sweep rather than a
quadratic scan. Exhaustive small-range equivalence and at least 50,000 distinct
insertions are required regression cases.

## Acceptance

- Developer-tool unit, boundary, redaction and plan tests pass.
- A real runner smoke test contains heartbeat, redacted output and terminal state.
- Batched and direct Git reads return identical bytes and a repeat-read benchmark
  records process/query/cache counts without becoming production evidence.
- P17 fast profile reports its excluded file count and passes its admitted tests.
- Patch conflict tests prove semantic equivalence and the large insertion case.
- Focused, workspace, Clippy, format/diff and strict self-audit remain required
  before checkpoint; interrupted or incomplete full runs are reported as such.
