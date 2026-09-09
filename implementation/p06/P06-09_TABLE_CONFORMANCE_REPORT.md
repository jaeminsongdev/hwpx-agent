# P06-09 current-PC table conformance report

- Generated: 2026-09-09
- Target: licensed Hancom Hangul 2020 `11.0.0.9136`, `ko-KR`, x86 on this PC
- Matrix schema: `hwpx-agent.table-conformance-report/v1`
- Matrix state: `non_green`
- Task state: `in_progress`
- Recommended reasoning: `max`

## Result

The deterministic report contains every `TABLE-001` through `TABLE-061` capability exactly once.
Current green coverage is **0/61**. This does not erase the completed P06 components; it shows that
the roadmap's release row requires more than component or one-fixture evidence.

| Dimension | Current evidence |
|---|---:|
| direct `oracle_verified` | 15 |
| direct `integration_passed` | 40 |
| direct `unit_passed` | 6 |
| direct `cataloged` only | 0 |
| automation `candidate_unverified` | 6 |
| automation `unavailable_with_reason` | 55 |
| automation runtime verified | 0 |
| differential exact match | 0 |
| green rows | 0/61 |

The machine-readable authority is
`implementation/p06/evidence/conformance/p06-table-conformance.current-2020.v1.json`.

## Existing evidence admitted conservatively

- P06-02 contributes the exact blank unmerged grid creation contract. A template-based preserving
  HWPX adapter now creates arbitrary bounded rectangular dimensions with caller-bound logical IDs
  and explicit physical tracks at an exact empty paragraph. It inherits only a reviewed blank 2x2
  template's table/cell/page-split and six uniform edge-band semantics, then reopens exact zero
  payload/formula state in a closed package. This is static integration, not a licensed application
  or renderer oracle. P06-02's row/column edits are now superseded by the exact structure model's
  stronger static preserving HWPX integration. P06-03's exact
  merge/split model also has static preserving HWPX integration, but no licensed target oracle.
- P06-04 contributes exact-target oracle evidence for cell margin, alignment, direction,
  protection, border and fill.
- P06-05 contributes exact-target width/height evidence. That oracle still covers only its absolute
  automatic-column plan; it is not reused as a fixed-column or autofit application oracle.
- P06-06 contributes exact-target formula, horizontal sum, relative-reference and cache evidence;
  number-format support remains component-only. TABLE-060 now has separate static direct-HWPX
  integration for complete canonical AST anchor upgrades, without a target-build claim.
- P06-07 contributes exact current-PC Hangul 2020 target evidence for repeat header, cell-content
  splitting, row-boundary splitting, before/exact/after whole-table boundaries and top/bottom
  captions. TABLE-042/043/044/055 are now `oracle_verified`; their automation and formula-readback
  requirements remain open, so none is release-green.
- P06-08 contributes bounded nested-table inspection evidence, not nested-table mutation/lowering.
- The first P06-09 implementation slice contributes bounded pure unit and static direct-HWPX
  integration evidence for equal row height, equal column width and row minimum height. A closed
  disposable package now proves formula/cache and pagination-policy readback plus exact preservation
  of every non-section part across all three operations. It does not include a licensed Hangul 2020
  target-build oracle.
- The table-layout mode slice contributes operation-specific static direct-HWPX integration for
  TABLE-051/052/053. A mixed plan keeps its fixed column exact, fit-content stops at verified
  preferred widths, and fit-page fills the exact body width. All three reopen through the closed
  package fixture with exact formula/cache, pagination-policy and non-section-part preservation;
  no licensed Hangul target-build or render result is inferred.
- The aggregate planner and preserving HWPX adapter cover all block, horizontal and vertical
  `SUM`/`AVG`/`PRODUCT` combinations. Eight rows now have static integration evidence through one
  exact formula-free/unmerged source profile and empty destination, with full state/grid/flow,
  payload/property/edge, pagination/caption and closed-package preservation. TABLE-025 runs as a
  regression while its already stronger target oracle remains unchanged. No formula evaluation,
  verified cache, licensed Hangul execution or render result is inferred.
- The thousands-format planner changes only the grouping flag on an exact selection of existing
  numeric formula-cell formats. TABLE-032/033 move to unit evidence while decimal places, formula
  AST and cache remain exact; unsupported formats fail closed. Exact Hangul 2020 source tooling is
  static-ready, but baseline SaveAs access was not approved, so no HWPX mapping or promotion exists.
- The text conversion component adds bounded UTF-8 tab/comma/semicolon parsing and deterministic
  writing for TABLE-004/005. TABLE-004 converts a complete admitted plain-text paragraph to an exact
  template-derived table. TABLE-005 converts every cell of an arbitrary-size admitted plain unmerged
  table to exact LF/CRLF bytes and a typed HWPX paragraph while binding the removed state/grid,
  properties, payloads and pagination. Both preserve closed-package non-target bytes. Fields, opaque
  content, and unreviewed merged/formula flattening fail closed; no Hangul/render result is inferred.
- The placement component and preserving HWPX adapter cover TABLE-034/036/037/038. Position tests
  span every reference and alignment value, signed offsets and the three flags; attachment changes
  preserve inactive native fields; all 16 table wrap/side-flow pairs and four margins read back
  exactly. Closed synthetic packages preserve grid/cell content, formulas/caches, pagination,
  merged siblings and all non-section parts. No licensed Hangul result is claimed.
- The table-sort component and preserving HWPX adapter cover TABLE-056 for an exact plain,
  unmerged and formula-free native profile. Ordered row/column keys, blank placement, binary or
  ASCII-insensitive text collation and exact numeric classification drive stable whole-cell moves.
  Payloads and complete non-ruling properties move inside the selected region while the physical
  grid, edges, unselected cells, pagination and caption remain fixed. Request/build/lower bind and
  recheck source and target state/grid/text/pagination/flow, and strict reopen proves the target.
  Formula-bearing, rich or merged native sorting, licensed Hangul and rendering remain unclaimed.
- The table-auto-fill components and preserving HWPX adapter cover TABLE-057/058. Explicit cycles,
  exact-number and date-day series fill any admitted merge-free rectangle in row/column order while
  editing only selected run content. Complete state/grid/scalar/style/formula/payload/pagination and
  flow bindings are rebuilt before lowering and reopened afterward. Selected formulas are rejected
  or explicitly replaced; a changed dependency of an unselected formula fails closed instead of
  preserving a stale cache. Rich/merged content, native UI series mapping, licensed Hangul and
  rendering remain unclaimed.
- The absolute-reference adapter covers TABLE-060 across the complete bounded `FormulaAst` grammar.
  It selects one owner among zero or more other formula fields, preserves formula meaning and
  coordinates, and permits only independent relative-to-absolute row/column anchor upgrades.
  Preserve, explicit unverified update and clear cache policies reopen exactly; recalculation and
  non-General formats fail closed. Other formulas, table content outside the selected native text
  slots, pagination, caption and package parts remain exact. This is synthetic static integration,
  not licensed Hangul execution or verified cache evidence.
- The table-style component and preserving HWPX adapter cover TABLE-020. Fixed-precedence,
  merged-cell-aware regions resolve to a complete typed visual identity spanning non-border cell
  properties, four borders, backgrounds and visible diagonals. The lowerer binds exact source,
  grid, flow, definition, request and plan state, preserves truthful unified diagonal provenance and
  normalizes a broken group to exact each-cell intent. Closed-package reopen preserves payload,
  formula/cache, pagination and unrelated parts; no licensed Hangul or renderer result is inferred.
- The transpose component keeps complete grid/span/formula-axis semantics, while the preserving
  HWPX adapter moves TABLE-021 to static integration for its exact formula-free, zero-repeat-header
  native profile. Arbitrary rectangular merged grids, nonuniform physical axes, complete edges,
  payload/properties/diagonals, page-split policy and caption reopen exactly; double transpose
  restores the source grid/state. Formula-bearing native transpose, licensed Hangul and rendering
  remain unclaimed.
- The table-properties model and preserving HWPX adapter cover TABLE-007/008/009/047. The strict
  reader binds complete grid/state, typed table and cell semantics, four independent border sides,
  backgrounds, payload/formula identities and explicit each-cell or unified diagonal intent.
  Lowering accepts only a fully prevalidated typed value catalog, relifts parts/state/grid before
  mutation, verifies current document flow, interns exact border fills and reopens target semantics.
  Native cell spacing remains geometry-bound and preserved. Closed synthetic packages preserve the
  sibling table's formula/cache and pagination plus all non-target parts; no licensed Hangul or
  renderer result is inferred.
- The whole-table partition component adds TABLE-010/011 cursor-row split and whitespace-only join
  plans. Split inherits exact table width, column tracks and table properties while rebasing rows;
  join retains the leading table identity/properties, chooses the larger source width and maps both
  source grids onto a reduced-rational common lattice. Cross-boundary merges, unsupported separators,
  collapsed tracks and unsafe formula crossings fail closed. Formula moves use the shared AST rebase
  engine and clear caches, but no HWPX lowering or licensed Hangul result is claimed.
- The preserving whole-table split HWPX adapter moves only TABLE-010 to static integration. Its
  exact top-level wrapper profile slices and rebases row geometry, carries every complete cell,
  payload, property and edge to one of two authoritative grids, inserts a distinct empty paragraph,
  and reopens both results. Selected-table formulas, repeat-header rows and captions fail closed;
  sibling formula/cache, supported page-split state and non-target package parts remain exact.
  No saved real HWPX, licensed Hangul or render result is inferred.
- The preserving whole-table join HWPX adapter moves TABLE-011 to static integration. It binds both
  top-level wrappers and the exact whitespace-only paragraph sequence, projects unequal widths and
  column counts onto the reduced-rational common lattice, retains the leading table identity and
  removes only the separator plus trailing wrapper. Both projected sources and the final joined
  table reopen exactly. A differing shared junction edge, selected formula, repeat header, caption
  or page-split policy fails closed; sibling formula/cache and non-target package parts remain exact.
- The exact row/column structure model and preserving HWPX adapter move TABLE-012/013/014/015 to
  static integration as one four-operation profile. Insertions create only explicit empty 1x1
  masters at whole-grid boundaries and duplicate the source boundary around the new band. Deletions
  remove only fully contained masters and collapse only identical survivor edges. Every surviving
  identity, span, track geometry, payload, complete property, formula/cache and document-flow state
  remains bound. Formula owners and references rebase through the same grid edit, including a merged
  formula-span reopen regression; owner deletion is explicit. Page-split, caption, repeat-header
  prefix and native wrapper/table IDs reopen exactly, while a repeat-header zero/nonzero transition,
  insertion through a merged span and partial-span deletion fail closed. This is synthetic static
  integration, not a saved HWPX, licensed Hangul target build or render oracle.
- The table-chart component adds TABLE-006 exact rectangular cell-block projection. It ignores the
  documented top-left corner, maps first-row series labels and first-column category labels, keeps
  exact numeric/blank data points and formula-display-cache origins, and binds source state plus
  document flow. Cursor-only default-data creation, merged source cells and body text fail closed;
  no chart XML, package mutation, linked save/reopen or licensed Hangul result is claimed.
- The table-ruling model and preserving HWPX adapter cover TABLE-002/003 as one exact
  physical-lattice and topology model.
  Drawing covers a new outer rectangle, full row/column strokes, rectangular local cell splits,
  existing-line style changes and two cell-local diagonal directions. Erasing a shared edge merges
  only rectangular compatible cells, while outer or same-master edges become explicitly
  transparent. Complete normalized edges, ordered payload blocks, properties, formulas, caches,
  table state, grid and document flow are bound. Static lowering relifts source state/grid, updates
  coordinated section/header XML, reopens exact semantics and preserves sibling formula/cache plus
  pagination in a closed package. Outer creation uses a digest-bound empty paragraph and reviewed
  1x1 native wrapper. Structural formula topology changes remain native fail-closed; no licensed
  Hangul execution or renderer result is claimed.
- The merge/split preserving HWPX adapter covers TABLE-016/017 with the complete domain content
  policies. Merge preserves the top-left master and removes only newly internal edges; split uses
  exact row-major identities and a source-catalog-bound edge line. Paragraph blocks remain exact,
  `First` receipts intentional discards, and request/build/lower all recheck source state, grid,
  content and flow. Selected formulas, diagonals or unequal complete merge-cell properties fail
  closed, while an unselected same-table formula/cache survives topology change and strict reopen.
  This is static integration evidence, not licensed Hangul or render evidence.

No evidence is promoted merely because a neighboring feature used the same table fixture.

## Automation boundary

The exact P02 registry contains only six table candidates and 55 rows with
`no_reviewed_action_mapping`; all 61 table runtime states are unverified and routing-disabled. The
redacted projection does not disclose the six private Action/ParameterSet identifiers. P02's two
verified undo/redo canaries are unrelated to the table domain and are not reused here.

## Validation and blockers

The generator verifies 61-row identity across catalog, contract and projection; exact target;
operation schema presence; required validation/fixture subsets; evidence file digests; canonical
ordering; duplicate JSON keys; finite files; path containment; privacy; and create-only publication.
Protocol code generation publishes the three P06 schemas through additive catalog v5 while baseline
locks prove catalogs v2 through v4 remain unchanged.

Current aggregate blockers include 0 missing direct evidence rows, 46 rows below direct oracle,
83 missing validation instances, 61 unverified automation runtime rows and 61 missing
differentials. A row can carry multiple blockers, so blocker counts are not intended to sum to 61.

## Decision and next implementation order

P06-09's matrix engine and current snapshot are implemented, but the roadmap completion criterion
`required matrix green` is not satisfied. The next current-PC sequence is:

1. lower the remaining 5 unit-only rows through preserving HWPX adapters;
2. close the 41 integration-only target oracles;
3. supply remaining feature-specific validations, exact current-target automation bindings and safe
   disposable differentials; and
4. regenerate until all 61 rows are green, then run the P06 hard Gate.

P06-09 and P06 remain in progress. No production, other-PC/version or whole-product completion is
claimed.
