# P06-09 TABLE-022/023/024/026/027/028/029/030 aggregate HWPX policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## One complete aggregate adapter

The eight unit-only aggregate rows share the existing `hwpx-agent.table-aggregate/v1` domain model
and the new `hwpx-agent.table-aggregate-hwpx.hancom-2020-wrapper/1` preserving adapter. TABLE-025
`table.horizontal_sum` is exercised by the same adapter as a regression, but its stronger licensed
target oracle remains authoritative and is neither duplicated nor downgraded.

Every request binds the exact header and section bytes, complete ruling state, logical grid, current
document flow, intended target flow, axis/function/range/destination and an explicit unverified
decimal display cache. Request admission and build independently recompute the source part, state,
grid and flow bindings. The builder deterministically derives the relative A1 `SUM`, `AVG` or
`PRODUCT` range and the complete target ruling state; callers cannot substitute an alternate target
formula or silently label a cache as verified.

## Exact native profile and preservation

The source table must be formula-free, unmerged and fully admitted by the ruling and pagination
readers. The destination must be its own master cell with empty logical payload and, at lowering,
exactly one empty paragraph/run/text node. This is one complete profile for all nine axis/function
combinations, not a function-by-function easy subset. Existing formulas, merged topology, nonempty
destinations, alternate field envelopes, non-General formats, non-decimal caches and multiple
formula fields fail closed.

The lowerer emits exactly one native formula field whose `Command`, `Formula`, `ResultFormat`,
`LastResult` and visible result agree. New field identifiers are allocated above every existing
field identifier in the section. It then reopens the explicit A1 formula AST, owner, unverified
cache and number format through the aggregate-only reader. The public legacy formula reader remains
restricted to the already proven `SUM(LEFT)` profile.

The grid, frame, physical boundaries, every edge identity, every cell identity, ordered payload,
complete cell properties and table-property digest remain exact. Page-split, repeat-header and the
raw-bound caption semantics are compared after reopening. The header and binding remain unchanged;
sibling content and every non-target closed-package part remain byte exact. A failure returns no
partial parts or receipt.

JSON is deterministic and bounded and rejects malformed, unknown or recursively duplicated keys.
Debug omits part/state/grid/flow hashes, logical identifiers, payloads, formulas, caches, caption
content and raw XML. Receipts bind source/output parts, complete state/grid, formula, request, plan
and before/after flow plus exact preservation and insertion counts.

## Evidence boundary

Eight existing domain tests, four adapter tests covering all nine mappings, and four private
contract/tamper tests promote only TABLE-022/023/024/026/027/028/029/030 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`. Static `schema`,
`semantic_reopen`, `formula_readback` and `page_split` validations are admitted. The matrix moves
`unit_passed` from 21 to 13 and `integration_passed` from 25 to 33; `cataloged` remains 0,
`oracle_verified` remains 15 and green remains 0/61.

The exact-target fixture may be exercised only through a bounded runner that validates the complete
eight-case manifest and every input digest in both the watchdog parent and x86 STA worker. One
licensed `HWPFrame.HwpObject.2` session processes the cases in fixed feature order; every case has an
independent open, text-digest, create-only save, close, reopen, second text-digest, PDF export and
close lifecycle. The first error stops later cases, while already-created outputs and the progress
journal remain failed evidence. The parent has a finite timeout, validates every returned HWPX/PDF
digest and PDF signature, cleans only a same-session, post-start, exact-executable automation process,
and writes a bounded redacted trace. It never registers a module or sends UI input.

Neither a successful lifecycle trace nor a PDF alone promotes a row. Each saved HWPX must pass the
feature-specific aggregate oracle checker, and each render claim must receive bounded visual review.
Any access-approval timeout or partial batch remains failed evidence and is not restarted merely
because observation ended.

This evidence does not prove formula evaluation, a verified cache, a saved real HWPX, licensed
Hangul 2020 execution, render identity, target build, rollback/retry, automation runtime,
differential exact match, arbitrary user documents, merged or pre-formula tables, another PC or
version, release, P06-09/P06 completion, production or product completion.
