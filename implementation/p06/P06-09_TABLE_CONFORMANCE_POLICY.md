# P06-09 current-PC table conformance policy v1

Date: 2026-09-14

Decision: **fail-closed 61-row matrix implemented; required matrix remains non-green**.

## Authority and target

The matrix joins exactly `TABLE-001` through `TABLE-061` from the canonical feature catalog and
generated capability contracts with two target-scoped inputs:

- a redacted projection of the exact current-PC Hangul 2020 automation registry; and
- hash-bound direct/component evidence from completed P06 work.

The only admitted target is licensed Hancom Hangul 2020 `11.0.0.9136`, `ko-KR`, x86 on this PC for
personal local development. Other PCs and Hangul 2022/2024 require separate projections, evidence,
and reports. Evidence is never inherited across targets.

The three public P06 schemas are published only through additive `schema-catalog-v5.json`; immutable
catalogs v2 through v4 remain byte-identical.

## Row states and green rule

Direct evidence stages are `cataloged`, `unit_passed`, `integration_passed`, and
`oracle_verified`. Missing evidence stays `cataloged`. A pure component cannot claim a stage above
`unit_passed`, and an HWPX adapter without actual Hangul readback cannot claim
`oracle_verified`.

An individual row is `green` only when all of the following are true:

1. the direct route is an exact `direct_hwpx` binding at `oracle_verified`;
2. every validation named by that feature's generated contract passes;
3. every required fixture class passes, including `security` when the contract requires it;
4. negative and rollback-or-retry evidence passes;
5. the current-target automation binding and runtime support are verified; and
6. a target-bound direct/automation differential is an `exact_match`.

Component evidence, a candidate Action mapping, an unrelated automation canary, or a successful
save/reopen by itself cannot promote a row. P06-09 passes only when all 61 rows are green.

## Redacted automation projection

The immutable private P02 registry and the P06 exact ActionTable overlay contain restricted Action
and ParameterSet identifiers. The projection
retains only feature ID, semantic capability ID, binding disposition, runtime support state and the
routing Boolean. It binds the selected source registry/overlay SHA-256 and exact target but contains no raw action,
ParameterSet, default, probe value, document content or absolute private path.

Projection creation is create-only. The public report consumes the committed redacted projection,
so clean-checkout validation does not require copying the Git-ignored private evidence. When the
private evidence is present, validation reconstructs and byte-compares the review contract, overlay
and projection.

## Evidence and deterministic report

Every positive direct/component record lists sorted feature IDs, backend, stage, passed validation
and fixture subsets, negative/rollback state, differential state, and one or more repository-relative
evidence files with exact SHA-256. Contract source locks hash bounded UTF-8 text after the sole
cross-platform normalization CRLF to LF; bare CR and content drift reject. Missing records and
missing fields fail closed. Evidence paths reject traversal, symlink/junction escape, empty files,
oversized files, duplicate keys and digest drift.

The report is canonical UTF-8 JSON with stable row order and source digests. It exposes row blockers
and aggregate counts but no private automation identifiers. Publication is create-only; a changed
input requires a new output path or an explicitly reviewed successor update.

## Current result

- Required rows: 61; green: 0; non-green: 61.
- Direct stages: 0 cataloged, 0 unit-passed, 22 integration-passed, 39 oracle-verified.
- The 22 integration rows have deterministic exact-target inputs and typed oracles. Their remaining
  direct validation is the successful licensed lifecycle and original-detail `render_diff` from the
  single-session pending-22 batch; failed attempts 01 through 07 and the control diagnostic remain
  failed evidence. The runner now opens an exact previously verified Hangul-saved TABLE-012 control
  before any pending row, so access-admission failure cannot be attributed to TABLE-016.
- The other 39 rows retain their exact current-target direct oracles. This includes TABLE-006's
  fresh native/product pair, semantic relift, frozen render differential and distinct retry.
- Cross-property static integration closed 25 missing formula/page-split validation instances across
  18 rows. The only remaining validation-missing instances are the 22 render checks above.
- Exact unique official ActionTable review yields 32 candidate-unverified and 29
  unavailable-with-reason bindings; all 61 runtime
  states are unverified and all 61 direct/automation differentials are not-run.
- Only the original six candidate Actions have isolated exact-target effect plus Undo component
  canaries. The other 26 have exact-source mapping evidence only. Neither evidence class proves
  product runtime routing or a direct/automation differential.

The current matrix is a truthful implementation backlog, not a P06-09 PASS. Detailed current
feature evidence and blocker counts are authoritative in `P06-09_TABLE_CONFORMANCE_REPORT.md` and
the canonical machine report. No binding is manufactured from a menu label or binary string.

## Not claimed

- No table capability is release-enabled by this matrix.
- P06-07 is complete only for its exact current-PC target; P06-09, P06, production and the product
  are not complete.
- No arbitrary user document, other PC, Hangul 2022/2024, provider or redistribution claim exists.
