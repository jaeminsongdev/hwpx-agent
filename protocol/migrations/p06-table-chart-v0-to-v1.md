# P06 table-chart v0 to v1 migration

`hwpx-agent.table-chart/v1` replaces the catalog-generated generic TABLE-006 argument shape with a
private, bounded semantic contract for linked table-cell-block chart creation.

Existing documents are unchanged. Existing public capability catalogs are unchanged. The new model
is an internal component boundary and does not expose raw HWPX XML, COM action names, parameter-set
identifiers, or arbitrary file paths.

Callers must now provide a complete exact-grid `TableChartSourceState`, typed display values and
origins, an inclusive cell-block rectangle of at least 2x2, distinct table/chart/data-resource IDs,
the expected source-state SHA-256, and the current document-flow SHA-256. Cursor-only chart creation
is not migrated because it creates default sample values instead of a table-linked chart. Merged
source blocks and text inside the numeric data body fail closed.

The v1 plan ignores the block's top-left corner, projects first-row series labels, first-column
category labels and numeric/blank body values, and fixes the documented initial chart to a
three-dimensional vertical bar. Source table state is preserved by the pure plan. Errors return no
partial plan or receipt.

Direct HWPX lowering, package preservation, save/reopen linkage, licensed Hangul 2020 execution,
automation and differential parity remain separate Gates and require independent migration evidence.
