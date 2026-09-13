# P06-09 TABLE-005 table-to-text HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-table-to-text-hwpx.hancom-2020-plain-grid/1`
- Model profile: `hwpx-agent.table-text-conversion/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-005 now has preserving direct-HWPX integration evidence for the complete admitted plain,
unmerged table profile. A 3x2 table containing a delimiter, Korean text, a multiline cell and an
embedded quote serializes to exact CRLF CSV and reopens as one typed HWPX text paragraph. The source
has nonuniform tracks, complete cell properties, six distinct master/payload identities, `TABLE`
page split and a valid repeat-header row. A fully empty 1x1 table also converts to exact empty LF/tab
output and an empty scaffold paragraph.

The request, builder and lowerer bind or independently recheck header/section, exact wrapper/table,
source paragraph and table ordinals, complete state/grid/text/pagination, serialized bytes, target
paragraph, current/target flow, source table count and a distinct output identity. Output is returned
only after exact paragraph bytes, typed flow, visible NFC text and one-table decrement reopen.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-005 adapter tests | 8/8 PASS |
| Comma, Korean, CRLF, multiline and embedded quote | exact static readback PASS |
| Empty 1x1 tab/LF boundary | exact static readback PASS |
| Source/state/grid/text/wrapper/count/flow/identity/plan drift | fail closed |
| Merged, formula, multi-paragraph, opaque and nonempty wrapper | fail closed |
| Duplicate/unknown/oversized JSON and Debug privacy | fail closed / redacted |
| Closed package, unrelated table and relationship parts | exact preservation PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved real
HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 10 to 9
- direct `integration_passed`: 36 to 37
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

This section records the original static transition. The later exact-target qualification is recorded
in `P06-09_TABLE_TEXT_CONVERSION_TARGET_READBACK_REPORT.md`; the current matrix must be read from
`P06-09_TABLE_CONFORMANCE_REPORT.md`.

TABLE-005 initially gained static `semantic_reopen`, formula-free `formula_readback` and source
`page_split` classification evidence. The exact-target qualification later adds render, target-build,
and retry evidence without claiming automation runtime or differential equality.

## Preserved boundaries

The adapter converts every cell in the admitted arbitrary-size rectangular grid, not a fixed sample.
It returns exact LF/CRLF bytes and uses typed HWPX line breaks without embedding carriage-return text.
It binds all removed table state rather than pretending that cell styles, rulings or pagination exist
after conversion. Merged cells, formulas/caches, multiple paragraphs, fields, opaque content,
captions, nested tables and arbitrary wrappers are rejected rather than flattened. Synthetic
XML/package evidence is not licensed Hangul or render evidence. P06-09, P06, production and the
product remain in progress. Recommended reasoning remains `max`.
