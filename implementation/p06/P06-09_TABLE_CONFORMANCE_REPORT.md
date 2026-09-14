# P06-09 current-PC table conformance report

- Generated: 2026-09-13
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
| direct `oracle_verified` | 39 |
| direct `integration_passed` | 22 |
| direct `unit_passed` | 0 |
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
- TABLE-001 now additionally passes an exact current-PC Hangul 2020 create-only target oracle. The
  deterministic 3x4 nonuniform and 1x1 boundary inputs completed save/close/reopen/PDF lifecycles;
  independent typed readback preserved the pre-existing formula table and every admitted exterior
  byte after validating renderer caches. Both one-page PDFs passed original-detail review, and a
  fresh retry over identical inputs completed after the failed attempts remained immutable. This
  advances only direct TABLE-001 to `oracle_verified`; automation and differential stay `not_run`.
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
- P06-08 contributes bounded nested-table inspection evidence. TABLE-054 now also has a separate
  static direct-HWPX mutation adapter: it inserts one exact caption-free inline template at a bound
  master-cell paragraph, reopens complete parent and child state, and isolates formula ownership by
  nearest table. This is not licensed Hangul or render evidence.
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
  `SUM`/`AVG`/`PRODUCT` combinations. TABLE-022/023/024/026/027/028/029/030 now pass one exact
  licensed Hangul 2020 create-only batch: all eight save/reopen/text/PDF lifecycles, 133 progress
  events, complete typed state/grid/formula/cache/layout/preview oracles and original-detail A4 PDF
  review passed. After validating renderer caches, the exact 564-to-2564 table-height rewrite and
  one positive matching field-identity pair, every normalized section is byte-identical. Attempt 01
  remains failed timeout evidence. These rows are `oracle_verified`; formula evaluation, verified
  cache refresh, automation and differential remain unclaimed. TABLE-025 retains its independent
  stronger target oracle.
- The thousands-format planner and preserving HWPX adapter cover TABLE-032/033. Exact licensed
  Hangul 2020 attempt 11 passed all three native saves and 22 ordered progress events. Offline
  comparison proves the add/remove thousands-separator actions change only the selected formula
  field's visible result text; native formula metadata, AST, numeric cache, complete grid and
  document flow remain exact. Direct remove/add output sections are byte-identical to the
  corresponding native sections, so both rows are now `integration_passed`. Attempts 01-10 remain
  failed or interrupted evidence; attempt 10 specifically remains failed because the old watchdog
  omitted a valid phase from its allowlist. Direct-output package save/reopen, PDF/render,
  rollback/retry and product automation-route runtime remain not run.
- The number-format planner and preserving HWPX adapter cover TABLE-049 for the exact native
  general and fixed zero-through-four-decimal tokens with independent grouping. Licensed attempt 05
  passed 50 ordered progress events, six formula actions, six user-authored dialog choices and both
  grouping directions. Five direct plans match the grouped native section; after one separately
  qualified TABLE-033 grouping edit, five direct plans match the ungrouped native section. Formula
  AST/cache, grid, semantic document flow and unowned bytes remain exact. Direct-output package
  save/reopen, PDF/render, rollback/retry and automation runtime remain not run.
- The text conversion component adds bounded UTF-8 tab/comma/semicolon parsing and deterministic
  writing for TABLE-004/005. The exact current-PC target batch covers quoted delimiters, Korean,
  multiline content, empty cells and the 1x1 boundary in both directions. All four Hangul 2020
  save/close/reopen/read/PDF lifecycles, 69 progress events, independent typed state/grid/text-flow
  oracles and original-detail A4 render reviews passed. Attempts 01-05 remain failed or superseded
  evidence and are not promoted. TABLE-004/005 are therefore `oracle_verified`; fields, opaque
  content, unreviewed merged/formula flattening, automation and differential remain unclaimed.
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
  sibling table's formula/cache and pagination plus all non-target parts. TABLE-007 now additionally
  passes a deterministic exact-target two-operation build, licensed Hangul 2020 save/reopen/PDF
  lifecycle, independent typed property/formula/cache oracle, original-detail render review and
  create-new retry boundary. The combined table-and-cell single-request development probe remains
  unqualified. TABLE-008/009/047 now also pass one deterministic three-target batch, three licensed
  Hangul 2020 save/reopen/PDF lifecycles, independent per-cell/unified-border/fill/diagonal typed
  oracles, exact native inert-hatch normalization, original-detail render review and create-new
  retry. Automation runtime and differential evidence remain `not_run`.
- The whole-table partition component and preserving HWPX adapters cover TABLE-010/011 cursor-row
  split and whitespace-only join. Split carries every complete cell into two authoritative grids;
  join projects both source grids onto a reduced-rational common lattice and keeps the leading
  identity. Cross-boundary merges, unsupported separators, collapsed tracks and unsafe formula
  crossings fail closed. One deterministic formula-free 4x2 state chain now passes both exact
  target operations: TABLE-010 visibly reopens as two 2x2 tables and TABLE-011 rejoins them to one
  4x2 table. Both licensed Hangul 2020 save/reopen/PDF lifecycles, independent typed/cache oracles,
  original-detail render reviews and a byte-identical retry pass. The target's native canonical
  serialization additionally qualified trailing empty table text and its self-closing empty-run
  separator. Formula, repeat-header and caption split/join profiles, automation runtime and the
  direct/automation differential remain unclaimed.
- The exact row/column structure model and preserving HWPX adapter now move TABLE-012/013/014/015
  to `oracle_verified` as one four-operation target batch. Insertions create only explicit empty 1x1
  masters at whole-grid boundaries and duplicate the source boundary around the new band. Deletions
  remove only fully contained masters and collapse only identical survivor edges. All four licensed
  save/reopen/PDF lifecycles, independent typed/cache oracle, original-detail render review and a
  byte-identical retry passed. The target probe fixed Hangul's native empty-cell scaffold and a
  deletion-receipt payload overcount. Every surviving identity, span, track geometry, payload,
  complete property and document-flow state remains bound. Existing static tests retain formula,
  page-split, caption, repeat-header-prefix and native-wrapper failure boundaries, while the promoted
  target batch is deliberately formula-free with no repeat header or caption; those broader target
  profiles remain unclaimed.
- The table-chart component adds TABLE-006 exact rectangular cell-block projection. It ignores the
  documented top-left corner, maps first-row series labels and first-column category labels, keeps
  exact numeric/blank data points and formula-display-cache origins, and binds source state plus
  document flow. Cursor-only default-data creation, merged source cells and body text fail closed;
  no default chart is synthesized. The direct HWPX adapter inserts one closed chart relationship and
  OOXML resource while preserving the complete source table and unrelated package bytes. Its exact
  product opens, saves, reopens and exports a one-page A4 PDF on licensed Hangul 2020. After the
  calibration-only profile was frozen, one fresh native/product pair and one distinct retry pair
  each passed exact lifecycle traces, 48 total ordered progress events, full HWPX semantic relift and
  the frozen word/page/raster/ink comparison. The only native/product raster difference remains
  inside the frozen default-title region, and original-detail review finds no clipping, overlap or
  broken glyphs. Direct `render_diff` and rollback/retry are therefore proven and TABLE-006 is
  `oracle_verified`. Product automation runtime and the direct/automation release differential
  remain `not_run`, so the row is not green.
- The table-ruling model and preserving HWPX adapter cover TABLE-002/003 as one exact
  physical-lattice and topology model.
  Drawing covers a new outer rectangle, full row/column strokes, rectangular local cell splits,
  existing-line style changes and two cell-local diagonal directions. Erasing a shared edge merges
  only rectangular compatible cells, while outer or same-master edges become explicitly
  transparent. Complete normalized edges, ordered payload blocks, properties, formulas, caches,
  table state, grid and document flow are bound. Static lowering relifts source state/grid, updates
  coordinated section/header XML, reopens exact semantics and preserves sibling formula/cache plus
  pagination in a closed package. Outer creation uses a digest-bound empty paragraph and reviewed
  1x1 native wrapper. Structural formula topology changes remain native fail-closed. Deterministic
  manifest `8296cf40...da543` drives five candidates and all nine ruling actions. Exact
  licensed-target attempt 08 completed 5/5 save-close/reopen/PDF cases and 85/85 progress events on
  Hangul 2020 `11.0.0.9136`, x86, `ko-KR`. The independent oracle relifted the complete selected
  table before admitting only renderer caches, empty-run serialization and the exact outer-anchor
  zero-default paragraph attributes; unknown exterior drift still fails closed. All five one-page
  A4 PDFs passed original-detail visual review. TABLE-002/003 are therefore `oracle_verified` with
  target-build, render and retry evidence. Attempts 01-07 remain immutable failed/interrupted
  evidence. Automation runtime and direct/automation differential are still `not_run`, so neither
  row is green.
- The merge/split preserving HWPX adapter covers TABLE-016/017 with the complete domain content
  policies. Merge preserves the top-left master and removes only newly internal edges; split uses
  exact row-major identities and a source-catalog-bound edge line. Paragraph blocks remain exact,
  `First` receipts intentional discards, and request/build/lower all recheck source state, grid,
  content and flow. Selected formulas, diagonals or unequal complete merge-cell properties fail
  closed, while an unselected same-table formula/cache survives topology change and strict reopen.
  This is static integration evidence, not licensed Hangul or render evidence.
- The remaining 22 target candidates now share one exact single-HWP-session lifecycle runner, so one
  user-owned `allow all` decision can cover one access control plus the 2/10/10 prepared groups
  without 22 separate prompts. Attempts 01 through 04 timed out at TABLE-016 `open_input`; attempts
  05 and 06 returned `Open=false` after prompt resolution. A same-session diagnostic then returned
  `Open=false` for a previously verified Hangul-saved TABLE-012 control before testing TABLE-016,
  isolating the current failure to file-access admission. Every run kept all inputs exact, published
  no HWPX/PDF output and left zero HWP processes. The runner now hash-binds and opens that exact
  TABLE-012 control before any pending case; the Rust oracle and renderer require its open, close and
  immutability states to pass. Integrated attempts 07 and 08 returned `Open=false` on that control
  with 0/22 cases, unchanged control bytes, no HWPX/PDF output and zero remaining HWP processes.
  Attempt 08 followed the user's attestation that the instructed second button was selected, while
  the automation trace still cannot independently attest the click. Attempt 08 trace SHA-256 is
  `ed27da43ad209485af8dfc8e85a943af8b0fd408c59ad3521c6162a271c7275c` and progress SHA-256 is
  `4b0056befd11152226e7ee053eea4a1ba5caf6e472636378473c1881bfcb347a`.
  The exact installed `Hnc.Office.String.ko-KR.dll` (`11.0.0.10677`, SHA-256
  `528b0b7f881f3648fd9bc8be5722e5f275fd53809a3f93159005c77737ad0867`) binds the four
  dialog choices in order as `접근 허용`, `모두 허용`, `허용 안 함`, and `모두 안 함`.
  The current `HKCU\Software\HNC\HwpAutomation\Modules` key has no named module registration,
  so the prompt is expected; no registry value or system setting was changed. Attempt 05 waited
  about 509 seconds, attempt 06 about 13 seconds and attempt 07 about 5.8 seconds between
  `open/running` and `open/failed`, which is consistent with prompt resolution rather than an
  immediate file, ACL or package rejection. The runner now permits one bounded second `Open` of the
  same control on the same document/session after the first false result, then fails closed if that
  retry is also false. It records the attempt count and first result; both the Rust oracle and the
  renderer reject inconsistent values. Configuration-only validation, 29/29 readback checks, 28/28
  wrapper checks, 11/11 renderer tests and 4/4 Rust oracle unit tests pass without invoking HWP.
  Attempt 03 trace SHA-256 is
  `577771fdbde65e572b0bfc59697d1a5334101927764b5afaeba6f8f721071356`. A combined offline oracle now admits only a
  complete 22-case success trace, then reuses all three existing typed semantic readers directly;
  every failed attempt is rejected before any oracle receipt is created. A single end-to-end wrapper
  now creates a new attempt directory, runs that one HWP session, hashes the resulting trace and
  invokes the combined oracle automatically; configuration-only and pre-existing-attempt paths are
  proven side-effect free. After the oracle passes, the same command uses pinned Poppler 26.07.0
  tools to render all 22 one-page A4 PDFs at 144 DPI into bounded PNG review candidates and writes a
  hash-bound manifest whose visual-review state remains `not_run`. A separate fail-closed finalizer
  accepts only all 22 original-detail assistant findings in exact feature order, rehashes every PNG
  and PDF plus the source manifest/observation files, and creates one promotion-ready receipt while
  keeping automation, differential, P06-09 and P06 completion unclaimed. Unreviewed preparation
  still promotes no row.

No evidence is promoted merely because a neighboring feature used the same table fixture.

## Automation boundary

The immutable P02 registry contains six table candidates. A P06-specific exact official ActionTable
review preserves those six and admits 26 additional exact, unique, single-action mappings, producing
32 candidate-unverified and 29 unavailable-with-reason rows. Ambiguous, partial, generic-dialog and
composed behaviors remain unavailable; all 61 table runtime states are unverified and
routing-disabled. The redacted projection discloses no private Action/ParameterSet identifiers.
P02's two
verified undo/redo canaries are unrelated to the table domain and are not reused here. A bounded
planner now binds TABLE-010/015/016/017/046/048 to the exact private registry and redacted P06
projection, preserving the order in one create-new request. Planned attempt 01 was not executed and
is superseded because its single-table session label did not match the isolated per-candidate
runner. Attempt 02 binds one HWP session to six independently generated disposable 3x3 documents,
so the user access decision remains one batch while selection state cannot leak between candidates.
It allows only `IsActionEnable` and documented default-ParameterSet surface reads; candidate Action
execution, user-document access, runtime qualification, routing and differential promotion remain
forbidden and not run. The create-new attempt-02 request digest is
`d9588469b901ec31136e15f657b772f93872943c0411ac7b4794ba4feca31355`.
The exact current-PC attempt completed all six isolated documents in one HWP session: all six
Action surfaces were created, TABLE-010/015/016/046/048 were enabled in their bounded contexts,
TABLE-017 was present but disabled in the attempted adjacent-cell context, and all four documented
default ParameterSet reads passed. Candidate execution remained 0, no user document was opened,
no raw Action/ParameterSet identifier entered public evidence, and the HWP process exited cleanly.
This is a component-level non-executing surface result only: runtime support remains unverified,
routing stays disabled, and differential/P06 promotion remains not run.

A create-new attempt-03 disposable execution canary then reused the same six-case order in one HWP
session with a fresh generated 3x3 document per case. A preceding format probe showed that
`GetTextFile` returned `null` for every tested in-memory-document format on this exact target, while
the documented `InitScan`/`GetText` by-reference path produced a bounded whole-document sequence.
The canary therefore hashes scan status plus text per chunk for TABLE-010/015/016/017 and combines
that scan with the selected style ParameterSet hash for TABLE-046/048. TABLE-017 required an initial
cell block followed by two extension transitions; that corrected context remained enabled
before and after the baseline snapshot. All six candidates executed exactly once, all six produced
a channel-appropriate state change, and all six returned to their exact composite baseline after
one Undo. Request SHA-256 is
`8dcf8c678c68f5a001609502694c74bf5dd2b255e8d93c6a5bda2408cc5d9df2`; trace SHA-256 is
`614a3ba3768a36864e3136b12723638b7e3cc8334b537f5adc3de3f894319f51`. No user document was
opened, no file open/save, network, registry/system-setting or Computer Use input was invoked, and
the HWP remainder was zero. This advances only an exact-target disposable component canary. It does
not qualify the production automation binding, enable routing, run an exact product differential or
change the 0/61 release-green matrix.

The canary wire chain now also has a tracked independent verifier. It rehashes the private request
and trace, rejects duplicate keys and boundary escapes, recomputes every composite scan/style
snapshot, requires channel-specific change plus exact Undo restoration, checks the redacted public
projection, and rejects raw private Action identifiers. Its seven tamper/non-promotion tests pass,
and the actual attempt-03 request/trace/public-evidence chain passes with 6 cases, 4 scan effects,
2 style effects, 6 exact Undo results and zero Action-identifier leaks. The verifier deliberately
returns runtime support `unverified` and differential `not_run`.

The P06 binding overlay is a restricted derivative and does not mutate the P02 registry. Its tracked
contract SHA-locks the parent registry, official ActionTable records, candidate graph, canonical
matrix and private review, then stores only hashes for each admitted mapping. A fail-closed builder
reconstructs the 61-row private overlay and public projection, rejecting duplicate source Actions,
non-unique graph nodes, capability/source drift, existing-candidate demotion, runtime promotion or
enabled routing. Four synthetic tamper/boundary tests, the actual 32/29 reconstruction and the
private overlay/contract/projection cross-check pass. The 26 new candidates have source mapping
evidence only; the six-case canary is not generalized to them. Authority:
`P06-09_TABLE_AUTOMATION_BINDING_OVERLAY_REPORT.md` and
`protocol/private/p06-table-automation-binding-overlay-v1.json`.

The cross-property preservation batch now closes the previously missing formula/pagination
validation combinations for 18 rows. One Cargo invocation passed eight integration binaries and
77/77 tests. Five new checks exercise a formula-bearing paginated table through cell-style,
formula/cache, thousands, number-format and pagination lowerers; existing aggregate, layout-mode
and property package tests supply the other operation-bound preservation paths. This reduces
missing validation instances from 47 to 22 without changing any direct stage, automation binding,
runtime state, differential state or release decision. Authority:
`implementation/p06/P06-09_TABLE_CROSS_PROPERTY_BATCH_REPORT.md` and
`implementation/p06/evidence/target/p06-table-cross-property-preservation.current-2020.v1.json`.

## Validation and blockers

The generator verifies 61-row identity across catalog, contract and projection; exact target;
operation schema presence; required validation/fixture subsets; evidence file digests; canonical
ordering; duplicate JSON keys; finite files; path containment; privacy; and create-only publication.
Protocol code generation publishes the three P06 schemas through additive catalog v5 while baseline
locks prove catalogs v2 through v4 remain unchanged.

Current aggregate blockers include 0 missing direct evidence rows, 22 rows below direct oracle,
22 rows with one missing render validation, 29 rows without an admitted automation candidate, 61
unverified automation runtime rows and 61 missing
differentials. A row can carry multiple blockers, so blocker counts are not intended to sum to 61.

## Decision and next implementation order

P06-09's matrix engine and current snapshot are implemented, but the roadmap completion criterion
`required matrix green` is not satisfied. The next current-PC sequence is:

1. close the remaining 22 integration-only target oracles in the existing one-session batch;
2. runtime-qualify the 32 exact-source candidates, resolve the other 29 bindings and run safe
   disposable differentials; and
3. regenerate until all 61 rows are green, then run the P06 hard Gate.

P06-09 and P06 remain in progress. No production, other-PC/version or whole-product completion is
claimed.
