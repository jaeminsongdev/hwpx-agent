# P06 table layout HWPX v0 to v1

P06-05 introduces private profile `hwpx-agent.table-layout-hwpx.hancom-2020/1`. There was no
accepted v0 HWPX table-layout adapter payload, so no legacy document shape or receipt is migrated
automatically.

The v1 lowerer accepts only a verified `hwpx-agent.table-layout/v1` plan whose canonical grid digest
matches the exact requested `TableGrid`. It admits a narrow current-Hangul-2020 table shape with
absolute table sizing, zero cell spacing, bounded positive dimensions, and one gap-free,
nonoverlapping cell coverage identical to the requested grid. Unknown, relative, malformed,
ambiguous, overlapping, incomplete, unverified, or digest-drifted inputs fail closed.

Each logical column and row is converted from micrometers to HWPUNIT with checked domain conversion.
Table size is the exact sum of the quantized logical dimensions, and each merged cell size is the
exact sum across its span. Only existing `hp:sz` width/height and `hp:cellSz` width/height value spans
are changed. The result must fully reparse with exact layout readback and unchanged content digest
before it is returned.

Relative sizing, nonzero cell spacing, shape repair, installed-font measurement, renderer equality,
row constraints, equalization, compatibility aliases, and silent normalization are not migrated.
Any expansion requires a new contract version, migration, and negative tests.
