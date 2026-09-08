# P06 table geometry HWPX adapter v0 to v1

Date: 2026-09-08

`v0` had the pure `hwpx-agent.table-geometry/v1` state but no reviewed bridge to Hancom 2020 HWPX
table size attributes. Callers could not publish its logical row/column tracks into a preserving
section-part edit with exact readback evidence.

`hwpx-agent.table-geometry-hwpx.hancom-2020/1` is additive and strict. The adapter requires an
exact state/grid binding and a supported absolute-size table. It converts logical tracks with the
official integer HWP-unit conversion, writes only table and master-cell size attributes, reparses
the result, and returns bytes only when structure, sizes, content digest and inner margins match
the expected state. Section selection is explicit and zero-based; missing ordinals are not coerced.

Legacy table indexes without state/grid identity, arbitrary namespaces/shapes, partial grids,
nonzero cell spacing, relative table sizes and zero/over-limit dimensions are rejected. Static
adapter PASS may not promote licensed Hangul 2020, renderer, automation, differential,
release-enabled, P06-09/P06, production, other-PC/version, or product claims.
