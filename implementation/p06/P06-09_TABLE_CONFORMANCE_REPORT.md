# P06-09 current-PC table conformance report

- Generated: 2026-09-08
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
| direct `oracle_verified` | 11 |
| direct `integration_passed` | 7 |
| direct `unit_passed` | 25 |
| direct `cataloged` only | 18 |
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
- P06-05 contributes exact-target width/height evidence, while fixed-column and autofit modes remain
  component-only because the successful target used an absolute automatic-column plan.
- P06-06 contributes exact-target formula, horizontal sum, relative-reference and cache evidence;
  number-format and absolute-reference support remain component-only.
- P06-07 contributes static HWPX integration evidence for repeat header, page split, row policy and
  caption, but its corrected renderer target remains `NOT_RUN`.
- P06-08 contributes bounded nested-table inspection evidence, not nested-table mutation/lowering.
- The first P06-09 implementation slice contributes bounded pure unit and static direct-HWPX
  integration evidence for equal row height, equal column width and row minimum height. A closed
  disposable package now proves formula/cache and pagination-policy readback plus exact preservation
  of every non-section part across all three operations. It does not include a licensed Hangul 2020
  target-build oracle.
- The aggregate planner adds bounded selection-to-formula unit evidence for block, horizontal and
  vertical `SUM`/`AVG`/`PRODUCT`. Eight previously catalog-only rows move to unit evidence while
  the already stronger horizontal-sum oracle remains unchanged.
- The thousands-format planner changes only the grouping flag on an exact selection of existing
  numeric formula-cell formats. TABLE-032/033 move to unit evidence while decimal places, formula
  AST and cache remain exact; unsupported formats fail closed.
- The text conversion component adds bounded UTF-8 tab/comma/semicolon parsing and deterministic
  writing for TABLE-004/005. Quoting, Unicode, multiline and empty cells roundtrip semantically;
  malformed or ragged input fails closed.

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

Current aggregate blockers include 18 missing direct evidence rows, 50 rows below direct oracle,
223 missing validation instances, 61 unverified automation runtime rows and 61 missing
differentials. A row can carry multiple blockers, so blocker counts are not intended to sum to 61.

## Decision and next implementation order

P06-09's matrix engine and current snapshot are implemented, but the roadmap completion criterion
`required matrix green` is not satisfied. The next current-PC sequence is:

1. complete P06-07 corrected-target renderer evidence;
2. implement the 18 remaining catalog-only direct operations in bounded semantic groups;
3. lower the 25 component-only rows and close the seven static-only target oracles;
4. qualify exact current-target automation bindings and run safe disposable differentials; and
5. regenerate until all 61 rows are green, then run the P06 hard Gate.

P06-09 and P06 remain in progress. No production, other-PC/version or whole-product completion is
claimed.
