# P06-09 current-PC table conformance policy v1

Date: 2026-09-09

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

The private P02 registry contains restricted Action and ParameterSet identifiers. The projection
retains only feature ID, semantic capability ID, binding disposition, runtime support state and the
routing Boolean. It binds the source registry SHA-256 and exact target but contains no raw action,
ParameterSet, default, probe value, document content or absolute private path.

Projection creation is create-only. The public report consumes the committed redacted projection,
so clean-checkout validation does not require copying the Git-ignored private registry. When the
private registry is present, validation may independently rebuild and byte-compare the projection.

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
- Direct stages: 0 cataloged, 0 unit-passed, 36 integration-passed, 25 oracle-verified.
- Automation bindings: 6 candidate-unverified, 55 unavailable-with-reason.
- Automation runtime support: 61 unverified.
- Direct/automation differential: 61 not-run.

The current matrix is a truthful implementation backlog, not a P06-09 PASS. P06-07 contributes
four exact-target oracle rows. TABLE-001 also has exact current-PC target-build, typed save/reopen,
PDF render-review and retry evidence for its deterministic blank unmerged 3x4 nonuniform and 1x1
profiles, so only that direct row is `oracle_verified`. The fixed-column, fit-content and fit-page
layout modes; the
  position/attachment/wrap/outside-margin group; complete table styles; exact table transpose;
  exact cell merge/split;
  exact admitted whole-table split; exact admitted text-to-table/table-to-text conversion;
  and other admitted operations have operation-specific static direct-HWPX integration evidence,
  but no licensed application oracle. The remaining direct operations and exact automation
  bindings/probes have not been manufactured from menu names.

The complete TABLE-022/023/024/026/027/028/029/030 block/horizontal/vertical aggregate-formula
group now has exact current-PC Hangul 2020 create-only save/reopen, typed whole-section oracle,
one-page PDF visual review and retry evidence. Those eight rows are `oracle_verified`; their visible
results remain explicit unverified caches, not proof of formula evaluation. Automation runtime and
direct/automation differential remain `not_run`, so none is green.

TABLE-060 additionally has selected-cell canonical-formula integration: only relative reference
axes may become absolute, other formula fields remain opaque unowned bytes, and preserve/update/
clear cache policies reopen statically. No formula engine or target application result is inferred.

TABLE-054 additionally has exact master-cell nested-table insertion integration. A caption-free
inline template retains its complete typed child state, while the complete parent state reopens with
only one ordered payload insertion. Nested formulas use nearest-table ownership and cannot leak into
the parent formula state. No licensed application or renderer result is inferred.

TABLE-032/033 additionally have a current-target native-source-backed HWPX integration. The exact
Hangul 2020 actions change only the selected formula field's visible result; formula metadata, AST,
numeric cache, grid and document flow remain exact. Direct remove/add sections match the native
sections byte-for-byte. Direct-output package save/reopen, render, rollback/retry and product
automation runtime remain not run, so the rows are `integration_passed`, not oracle-verified.

TABLE-049 additionally has a current-target native-source-backed HWPX integration. The exact six
Hangul 2020 result-format tokens and independent grouping states lower through a preserving adapter;
five grouped and five ungrouped plans match the native sections byte-for-byte. Formula AST/cache,
grid, semantic document flow and every unowned section byte remain exact. Direct-output package
save/reopen, render, rollback/retry and automation runtime remain not run, so the row is
`integration_passed`, not oracle-verified.

TABLE-006 additionally has a current-target native-source-backed linked-chart HWPX integration.
The exact 3x3 rectangular source lowers to a closed chart relationship/resource, preserves the
source table and unrelated package bytes, and passes product HWPX open/save/reopen plus one-page PDF
export and render review on Hangul 2020. Native-reference PDF `render_diff`, rollback/retry, product
automation runtime and release differential remain not run, so the row is `integration_passed`, not
oracle-verified.

## Not claimed

- No table capability is release-enabled by this matrix.
- P06-07 is complete only for its exact current-PC target; P06-09, P06, production and the product
  are not complete.
- No arbitrary user document, other PC, Hangul 2022/2024, provider or redistribution claim exists.
