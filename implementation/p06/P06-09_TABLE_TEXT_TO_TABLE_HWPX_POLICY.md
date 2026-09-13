# P06-09 TABLE-004 text-to-table HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and exact native profile

This profile converts the complete semantic text of one explicitly bound top-level `hp:p` into one
blank-template-derived table. The source paragraph may contain any bounded combination of supported
text spans, tabs and line breaks across runs. Fields and opaque elements fail closed because replacing
them with static cell text would lose dynamic or unknown semantics. Visible text is normalized to NFC
and parsed by the complete `TableTextGrid` tab/comma/semicolon grammar, including quoted delimiters,
doubled quotes, multiline fields and empty cells.

Every nonzero bounded rectangular result is admitted. The caller supplies a distinct table ID, every
row-major 1x1 master ID, one payload ID for each nonempty cell, `None` for every empty cell, and every
nonzero physical row/column track. Cursor defaults, inferred IDs and guessed dimensions are forbidden.

Native table structure comes from the separately bound exact blank unmerged 2x2 native run-direct
template defined by the TABLE-001 profile. A legacy `hp:ctrl`-wrapped table is rejected. The template
has four empty formula-free masters, identical complete non-ruling cell
properties, no diagonal, caption or repeat header, and six uniform outer/inner edge bands. Generated
cell paragraphs use the deterministic current-2020 paragraph/run/text profile and represent tabs and
line breaks as typed `hp:tab` and `hp:lineBreak` atoms.

## Exact binding, lowering and reopen

The request binds destination header/section, source paragraph bytes and context, parsed text-grid
state, template section plus exact typed state/grid, delimiter, paragraph/template ordinals, current
and target document-flow SHA-256, every logical identity and every physical track. Request admission
and build independently recheck all of them. The builder calls the authoritative domain unmerged
create operation and constructs the complete target grid, ruling/cell/property/payload state and
bounded deterministic plan.

Immediately before mutation the lowerer rereads the source paragraph and template, reparses the full
text grammar, rechecks current flow and rebuilds the plan. It renders a blank target from the template,
patches every nonempty cell with its exact generated paragraph, rejects native table-ID collision and
replaces only the bound source paragraph. Output is returned only after exact target binding regeneration
and strict header/section reopen prove the complete grid/state, text grid, payload count, zero formulas,
page-split policy, zero repeat headers/caption and exact table-count increment.

Closed-package tests preserve every opaque non-target part and relationship. Source/template/package
inputs are borrowed and never mutated. XML, allocation, text, grid, ruling, formula, pagination and JSON
work is finite. Duplicate/unknown JSON fails closed. Debug omits text, hashes, IDs and raw XML.

## Evidence promotion rule

Passing the eight adapter tests and private contract tamper suite promotes only TABLE-004 from
`component_only / unit_passed` to `direct_hwpx / integration_passed` with `schema`, static
`semantic_reopen`, formula-free `formula_readback` and `page_split` preservation.

It does not prove TABLE-005, render equivalence, a saved real HWPX, licensed Hangul 2020 execution,
target-build, rollback/retry, automation, differential exact match, merged/formula-bearing output,
dynamic/opaque source conversion, arbitrary native templates or user documents, another PC/version,
P06-09/P06 completion, production or product completion.
