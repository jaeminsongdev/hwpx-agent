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
| direct `integration_passed` | 12 |
| direct `unit_passed` | 34 |
| direct `cataloged` only | 0 |
| automation `candidate_unverified` | 6 |
| automation `unavailable_with_reason` | 55 |
| automation runtime verified | 0 |
| differential exact match | 0 |
| green rows | 0/61 |

The machine-readable authority is
`implementation/p06/evidence/conformance/p06-table-conformance.current-2020.v1.json`.

## Existing evidence admitted conservatively

- P06-02 and P06-03 contribute bounded pure unit evidence for create/row-column edits and
  merge/split; they are not represented as HWPX bindings.
- P06-04 contributes exact-target oracle evidence for cell margin, alignment, direction,
  protection, border and fill.
- P06-05 contributes exact-target width/height evidence. That oracle still covers only its absolute
  automatic-column plan; it is not reused as a fixed-column or autofit application oracle.
- P06-06 contributes exact-target formula, horizontal sum, relative-reference and cache evidence;
  number-format and absolute-reference support remain component-only.
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
- The aggregate planner adds bounded selection-to-formula unit evidence for block, horizontal and
  vertical `SUM`/`AVG`/`PRODUCT`. Eight previously catalog-only rows move to unit evidence while
  the already stronger horizontal-sum oracle remains unchanged.
- The thousands-format planner changes only the grouping flag on an exact selection of existing
  numeric formula-cell formats. TABLE-032/033 move to unit evidence while decimal places, formula
  AST and cache remain exact; unsupported formats fail closed.
- The text conversion component adds bounded UTF-8 tab/comma/semicolon parsing and deterministic
  writing for TABLE-004/005. Quoting, Unicode, multiline and empty cells roundtrip semantically;
  malformed or ragged input fails closed.
- The placement component and preserving HWPX adapter cover TABLE-034/036/037/038. Position tests
  span every reference and alignment value, signed offsets and the three flags; attachment changes
  preserve inactive native fields; all 16 table wrap/side-flow pairs and four margins read back
  exactly. Closed synthetic packages preserve grid/cell content, formulas/caches, pagination,
  merged siblings and all non-section parts. No licensed Hangul result is claimed.
- The table-sort component adds a stable, bounded whole-cell relocation plan for TABLE-056. It
  supports ordered row/column keys, explicit blank and text-collation policies, exact fixed-decimal
  comparison, merge rejection and formula-movement policy binding without claiming HWPX execution.
- The table-auto-fill components add reusable explicit, exact-number and date-day series plus an
  exact-region scalar mutation plan for TABLE-057/058. Traversal, start index, existing formula
  replacement and style preservation are digest-bound; rich-content/formula generation, native
  series-index mapping and HWPX execution remain unclaimed.
- The table-style and transpose components add fixed-precedence, merged-cell-aware style resolution
  for TABLE-020 and complete grid/span/formula-axis transposition for TABLE-021. Payload/style or
  formula state outside each operation is digest-bound, but neither component is an HWPX adapter.
- The table-properties component adds complete grid/state binding for TABLE-007/008/009/047, strict
  exact logical-slot selection with a rectangle required for unified border or diagonal application,
  full merged-cell containment, per-cell/unified border topology and explicit two-direction slash,
  center-line and line-tuple diagonal semantics. Untargeted cells, properties, payload and formula
  identities remain bound. It is not yet an HWPX adapter.
- The whole-table partition component adds TABLE-010/011 cursor-row split and whitespace-only join
  plans. Split inherits exact table width, column tracks and table properties while rebasing rows;
  join retains the leading table identity/properties, chooses the larger source width and maps both
  source grids onto a reduced-rational common lattice. Cross-boundary merges, unsupported separators,
  collapsed tracks and unsafe formula crossings fail closed. Formula moves use the shared AST rebase
  engine and clear caches, but no HWPX lowering or licensed Hangul result is claimed.
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
170 missing validation instances, 61 unverified automation runtime rows and 61 missing
differentials. A row can carry multiple blockers, so blocker counts are not intended to sum to 61.

## Decision and next implementation order

P06-09's matrix engine and current snapshot are implemented, but the roadmap completion criterion
`required matrix green` is not satisfied. The next current-PC sequence is:

1. lower the 34 unit-only rows through preserving HWPX adapters;
2. close the twelve integration-only target oracles;
3. supply remaining feature-specific validations, including formula readback where required;
4. qualify exact current-target automation bindings and run safe disposable differentials; and
5. regenerate until all 61 rows are green, then run the P06 hard Gate.

P06-09 and P06 remain in progress. No production, other-PC/version or whole-product completion is
claimed.
