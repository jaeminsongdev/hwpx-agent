# P06-08 table inspection and selection policy v1

Date: 2026-09-08

Decision: **pure, bounded table inspector implemented; no backend selection claim**

## Purpose

P06-08 builds an immutable metadata snapshot from one already validated `DocumentGraph` revision.
It indexes every top-level and nested `TableNode`, restores each table's logical `TableGrid`, and
creates stable table/cell selectors for later read or edit plans. It does not move a Hangul cursor,
call COM, or alter HWPX bytes.

## Stable table selector

A `TableSelector` always carries all three anchors below:

- globally unique logical table ID;
- exact section/note, flow-child, parent-cell structural path;
- SHA-256 fingerprint of the complete logical `TableNode`.

Resolution first checks the caller's revision ID and canonical graph SHA-256, then requires the ID,
path, and fingerprint to identify the same indexed table. There is no index-only fallback and no
"first match" behavior. Missing IDs report not-found; drift in a previously valid anchor reports
stale.

## Stable cell selector and merged coordinates

A `TableCellSelector` binds the stable table selector, requested pre-merge logical coordinate,
canonical master-cell ID, and master-cell fingerprint. Covered coordinates in a rectangular merged
span resolve to the same master cell while preserving the exact requested coordinate in the result.
Out-of-range coordinates, a changed master mapping, or fingerprint drift fail closed.

Master-cell selection by logical ID is also supported. Covered slots do not invent independent cell
IDs. The result returns only table/cell identity, coordinates, span, fingerprints, and directly
nested table IDs; it never returns or logs cell content.

## Nested tables

Nested tables are indexed recursively through table-cell flows and drawing child flows. Their
structural path contains the parent table flow child and the parent master-cell coordinate before
the nested table flow child. Multiple nested tables in one cell retain distinct logical IDs and
paths and are selected exactly; the inspector never treats sibling order alone as identity.

`direct_nested_table_ids` lists only the immediate table roots contained by a cell. Descendant
tables inside one of those nested tables belong to that nested table's own cells.

## Snapshot and bounds

Schema `hwpx-agent.table-inspection/v1` serializes metadata only, in stable table-ID and canonical
master-cell order. It binds revision ID, graph SHA-256, table path/fingerprint, logical-grid SHA-256,
cell spans/fingerprints, and direct nested table IDs. Cell body text, equations, and private
properties are represented only through fingerprints.

Defaults cap the snapshot at 100,000 tables, 1,000,000 master cells, 64 structural path steps,
64 nested-table levels, and 32 MiB of serialized metadata. Hard ceilings remain finite. The
underlying `TableGrid` applies its existing dimension, slot, identifier, and serialization bounds.

## Evidence

The Rust boundary suite covers merged-slot-to-master resolution, nested and sibling table paths,
drawing-contained and note-root tables, direct-nested ownership, revision/graph/table/cell drift,
invalid restored selectors, zero-match and out-of-range errors, table/cell/depth/path/output limits,
deterministic metadata-only snapshots, redacted debug surfaces, and stable public error codes.

## Not claimed

- No HWPX table/cell selector lift or lower is implemented by this pure component.
- No Hangul 2020 cursor/selection, save/reopen, rendering, or automation result is claimed.
- No arbitrary user-document compatibility, other PC/version, P06 phase completion, production,
  or product completion is claimed.
