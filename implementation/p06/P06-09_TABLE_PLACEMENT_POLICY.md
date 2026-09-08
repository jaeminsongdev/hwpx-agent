# P06-09 table placement component policy v1

Status: pure bounded component implemented; no HWPX or Hangul 2020 oracle claim

## Scope

This policy covers the logical state and mutation boundary for four P06 table capabilities:

- `TABLE-034` / `table.position`
- `TABLE-036` / `table.inline_floating`
- `TABLE-037` / `table.wrap`
- `TABLE-038` / `table.outer_margin`

The component binds one validated logical table ID to attachment mode, floating position, text
wrap/flow and four outer margins. It does not locate a table in a package, lower native XML,
automate Hangul, or predict renderer output.

## Placement semantics

Attachment is either inline with an explicit line-spacing effect flag, or floating with exact
horizontal/vertical reference frames, alignments, signed offsets and three flow/anchor flags.
Switching attachment mode changes only the mode payload. Wrap/flow and outer margins are preserved
so inactive native attributes are not silently discarded.

`table.position` replaces only the complete floating-position payload. `table.wrap` replaces the
wrap and side-flow pair together. Both reject inline tables because their values are inactive in
that mode; callers must explicitly request `table.inline_floating` first. `table.outer_margin`
changes only four nonnegative margins and is valid in either attachment mode.

The logical enumerations retain the exact native value space needed by a later adapter: paper,
page, column and paragraph reference frames; left/center/right/inside/outside or
top/center/bottom/inside/outside alignment; square/top-and-bottom/behind/in-front wrapping; and
both/left/right/largest side flow. This is a model boundary, not evidence that every combination
has already passed Hangul 2020.

## Safety and determinism

- State JSON is exactly `hwpx-agent.table-placement/v1`; empty, oversized, malformed, duplicate
  and unknown-field input fails closed.
- Signed offsets and nonnegative margins are checked against separate finite micrometer limits.
- Operations clone the validated source and fully validate the candidate before returning a state
  and receipt. Errors publish no partial state.
- State and receipt serialization are deterministic, compact and bounded. Receipts bind logical
  table ID, exact operation, capability ID, source/output SHA-256 and whether state changed.
- Reapplying the same operation is idempotent. Debug output redacts identifiers, offsets, margins
  and state hashes.

## Evidence promotion rule

Passing Rust and contract/tamper tests promotes only TABLE-034, TABLE-036, TABLE-037 and TABLE-038
to `component_only / unit_passed` with `schema` evidence. It cannot promote direct HWPX
integration, semantic reopen, formula/page preservation, render diff, licensed Hangul 2020
target-build, automation, differential exact match, release-enabled, P06-09/P06 PASS, production
or product completion.

The next boundary is an exact preserving HWPX adapter for `hp:tbl`, `hp:pos` and `hp:outMargin`,
followed by a separate licensed Hangul 2020 save/reopen and PDF oracle. Recommended reasoning
remains `max`.
