# P06-09 table cross-property preservation batch report

- Generated: 2026-09-14
- Scope: current repository, static Hancom 2020 HWPX integration
- Result: `PASS`
- Release effect: validation-only; no automation/runtime/differential promotion

## Result

One Cargo invocation ran eight table integration binaries and passed 77/77 tests. Five new
operation-bound checks close the previously missing cross-property evidence without treating a
static package test as a licensed-target or product-runtime result:

| Feature rows | Newly proved validation | Exact preserving path |
|---|---|---|
| TABLE-039/040/041/045 | `formula_readback`, `page_split` | complete cell-style batch on a formula-bearing paginated table |
| TABLE-046/048 | `formula_readback`, `page_split` | typed border/fill formula round trip plus closed-package pagination preservation |
| TABLE-035 | `formula_readback`, `page_split` | shared table-layout HWPX lowerer with full-package semantic reopen |
| TABLE-025 | `page_split` | nine aggregate mappings with exact pagination readback |
| TABLE-031/059/061 | `page_split` | formula/cache lowering with independent pagination readback |
| TABLE-032/033 | `page_split` | add/remove grouping with independent pagination readback |
| TABLE-049 | `page_split` | all admitted number formats with independent pagination readback |
| TABLE-042/043/044/055 | `formula_readback` | all page-split transitions, repeated-header change and caption change with formula readback after every transition |

The operation result semantics for the oracle-stage rows remain bound to their existing exact
current-PC Hangul reports. This batch proves only the missing preservation dimension through the
same typed lowerers. The integration-only rows retain their existing stages and still need their
licensed-target lifecycle where applicable.

## Verification

```text
cargo test -p hwpx-package --test table_cell_style --test table_formula \
  --test table_thousands_hwpx --test table_number_format_hwpx \
  --test table_pagination --test table_aggregate_hwpx \
  --test table_layout_modes_hwpx --test table_properties_hwpx
```

Result: eight binaries, 77 passed, 0 failed, 0 ignored.

The batch includes strict formula AST/cache readback, page-split/repeated-header/caption readback,
grid dimensions, selected style state, package preservation, negative inputs and bounded failure
paths. Formula or pagination equality is checked semantically; a changed table-content digest is
not mistaken for a pagination failure when the requested formula payload changes.

## Gate boundary

This evidence does not open Hangul, execute a private Action, enable routing, qualify an automation
binding, run a direct/automation differential, prove arbitrary user documents or change any
`not_run` differential. P06-09, P06, production and whole-product completion remain in progress.
