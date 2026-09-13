# P06-09 TABLE-006 direct HWPX chart policy

- Scope: `direct_hwpx / integration_passed`
- Target: licensed Hangul 2020 `11.0.0.9136` x86 ko-KR on the current PC
- Domain schema: `hwpx-agent.table-chart/v1`
- HWPX schema: `hwpx-agent.table-chart-hwpx/v1`
- HWPX profile: `hwpx-agent.table-chart-hwpx.hancom-2020/1`
- Capability: `table.chart_from_table`

## Admitted native profile

The input is one complete native 3-by-3 table contained directly by an `hp:run`. The top-left cell
is empty, the remaining first row contains the two series labels, the remaining first column
contains the two category labels, and the four body cells contain finite decimal values. The source
worker proves that selecting the complete cell block in the exact Hangul 2020 build creates a 3D
vertical bar chart whose chart cache contains those labels and values.

The native source has a table-height inconsistency: the table height is 3846 HWPUNIT while the three
cell heights total 846 HWPUNIT. The product builder never edits that source. It creates a distinct
derived fixture, sets the three cell heights to 1282 HWPUNIT, and removes only the stale
`hp:linesegarray` renderer caches. The normalized row lattice therefore sums exactly to the native
table height. This normalization is specific to the locked fixture and is not arbitrary repair.

## Exact binding and lowering

Inspection binds the selected section, direct `hp:run` parent, complete table bytes, the nine native
cell spans, complete `TableGrid`, typed source values, source-state SHA-256, grid SHA-256 and semantic
document-flow SHA-256. Literal and formula-display-cache provenance use the domain model without
collapsing their origins. Request construction and lowering recheck every binding and ID allocation.

Lowering adds exactly one `hp:chart` anchor and one closed `Chart/chart1.xml` part, updates the OPF
manifest, and allocates distinct table, chart, chart-resource and z-order identities. The chart uses
`c:bar3DChart` with `c:barDir val="col"`; its two series contain the exact series names, category
names and row-major numeric values. The source table remains present and unchanged within the
derived package. The preservation engine uses
`hwpx-agent.preservation/hancom-2020-preview-text-v2`, including through writer build, staged reopen,
atomic publication and published reopen.

## Current-target lifecycle

Attempt `20260913-01` opens the hash-bound product HWPX through x86 STA COM, verifies the exact
Hangul executable identity, saves to a new HWPX, closes it, reopens that saved file, verifies the
visible source-text digest is unchanged, and exports a new PDF. The watchdog accepts only its exact
same-session automation process and records no document text or chart payload.

Independent package readback confirms that both the product and the Hangul-saved output contain one
table, nine cells, one chart anchor, one chart part, the 3D vertical-bar type and all source labels.
The native-source chart and saved product chart have the same ordered ten chart-cache values. The
one-page A4 PDF identifies `Hwp 2020 11.0.0.9136` as creator. Its rendered page was reviewed at
150 DPI: the table, two categories, two series and four bars are visible without clipping.

## Bounds, privacy and failures

The adapter and request JSON are bounded and duplicate/unknown keys fail closed. Invalid source
parentage, grid/cell/value/provenance drift, relationship or ID drift, output overflow and writer
preservation drift return no partial artifact. The target worker accepts only the exact input digest,
creates new outputs, rejects pre-existing Hwp processes, and has a bounded watchdog.

The target trace contains hashes, sizes and finite state only. It does not contain raw document text,
raw chart XML, secrets or arbitrary paths. No user document, module registration, UI input, network,
registry write or system-setting mutation is allowed. Access approval remains a user click.

## Gate boundary

TABLE-006 advances from `component_only / unit_passed` to
`direct_hwpx / integration_passed`. Actual product HWPX open/save/reopen and PDF export pass on the
exact current target, and the rendered page has been inspected. This checkpoint does not mark
`render_diff` complete because a separately exported native-reference PDF has not yet been compared
for geometry, text and object differences. Rollback/retry, verified product automation binding and
runtime, release exact differential, merged-cell sources, arbitrary documents, another PC or
version, P06-09/P06 completion, production and product completion remain unclaimed.
