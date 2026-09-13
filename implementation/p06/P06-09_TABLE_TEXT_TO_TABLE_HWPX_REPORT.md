# P06-09 TABLE-004 text-to-table HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-text-to-table-hwpx.hancom-2020-template/1`
- Model profile: `hwpx-agent.table-text-conversion/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-004 now has preserving direct-HWPX integration evidence for the complete admitted plain-text
conversion profile. A comma fixture converts quoted delimiters, Korean text, multiline content and an
empty trailing cell into an exact 3x2 table with nonuniform explicit physical tracks and six distinct
row-major master identities. Five nonempty cells receive five distinct payload identities; the empty
cell remains the exact semantic empty scaffold. A semicolon 1x1 boundary also reopens exactly.

The request, builder and lowerer bind or independently recheck destination header/section, exact source
paragraph bytes/context, delimiter and parsed grid, template section plus typed state/grid, current flow,
target flow, logical identities and physical tracks. The domain create receipt is rebuilt before mutation.
Output is returned only after strict semantic text/grid/state/pagination/formula/table-count readback.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-004 adapter tests | 8/8 PASS |
| Quoted delimiter, Korean, multiline and empty cells | exact 3x2 static readback PASS |
| Semicolon 1x1 boundary | exact static readback PASS |
| Source/template/grid/context/flow/identity/track/plan drift | fail closed |
| Ragged, opaque/dynamic text and nonblank template | fail closed |
| Duplicate/unknown/oversized JSON and Debug privacy | fail closed / redacted |
| Closed package graph and opaque non-target part | exact preservation PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved real
HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 11 to 10
- direct `integration_passed`: 35 to 36
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

This section records the original static transition. The later exact-target qualification is recorded
in `P06-09_TABLE_TEXT_CONVERSION_TARGET_READBACK_REPORT.md`; the current matrix must be read from
`P06-09_TABLE_CONFORMANCE_REPORT.md`.

TABLE-004 initially gained static `semantic_reopen`, formula-free `formula_readback` and `page_split`
evidence. The exact-target qualification later adds render, target-build, and retry evidence without
claiming automation runtime or differential equality.

## Preserved boundaries

The adapter converts the entire admitted paragraph/grid, not a fixed-size or ASCII-only sample. It
rejects fields and opaque elements rather than silently flattening them, and it never invents native
styles, IDs or physical dimensions. The output is blank-template-derived, formula-free and unmerged;
TABLE-005, merged/formula semantics and arbitrary templates are not claimed. Synthetic XML/package
evidence is not licensed Hangul or render evidence. P06-09, P06, production and the product remain in
progress. Recommended reasoning remains `max`.
