---
name: build-hancom-tables
description: Create and edit advanced Hancom tables: row/column operations, merge/split, sizing, borders, fills, alignment, formulas, repeating headers, page split, captions, and nested tables.
---

# Build Hancom Tables

## Use this when

The request centers on a table or structured form.

## Workflow

1. Define the logical grid, cell spans, content, widths/heights, style, page behavior, formula AST, and number formats.
2. Validate merge rectangles, nested table policy, nonempty-cell merge behavior, and formula reference movement.
3. Call `capability_check` and compile table operations into an atomic plan.
4. Dry-run with a grid diff and expected layout width.
5. Execute and inspect the table snapshot; validate formulas, merged cells, borders/fills, repeat headers, and page splits.
6. Render boundary pages and use Hancom save/reopen for release-grade output.

## Guardrails

Never infer destructive merge content behavior. When multiple source cells contain data, require a declared concatenate/first/distribute/reject policy.
