# P06-09 TABLE-006 table-backed chart policy

- Scope: `component_only / unit_passed`
- Target context: licensed Hangul 2020 `11.0.0.9136` x86 on the current PC
- Model schema: `hwpx-agent.table-chart/v1`
- Capability: `table.chart_from_table`
- Reasoning level: `max`

## Source semantics

Hancom's chart help distinguishes two materially different paths. Invoking chart creation with only
a table/cursor context creates a chart from initial values. Selecting the entire table or part of it
as a cell block creates a chart linked to those table values. This capability models only the latter,
because `chart_from_table` must prove an exact table-data source instead of silently accepting default
sample data.

The selected block uses the top-left cell as the axes-intersection corner and ignores its value. The
remaining first row supplies series labels, the remaining first column supplies category labels, and
the rectangular body supplies series values. The initial object is explicitly a three-dimensional
vertical bar chart, matching the documented creation behavior.

Official reference:

- <https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/chart/chart(createchart).htm>

## Exact source state

`TableChartSourceState` binds all master cells in one `TableGrid`, not only the selected subset. Every
master-cell ID and top-left coordinate must occur exactly once, and the state carries exact grid and
table-state SHA-256 bindings. Each typed display value is `blank`, exact fixed decimal, or NFC text,
with a source digest and either literal or formula-display-cache provenance. Digests and finite
limits are validated before any plan is returned.

The selected source is an inclusive rectangle of at least two rows by two columns. Merged cells in
that rectangle fail closed because duplicating or collapsing a merged value into a chart series is
not yet proven against Hangul 2020. Cursor-only creation is also rejected rather than substituted
with initial sample values.

## Projection and preservation

The planner produces a deterministic, lowering-ready linked-data projection:

- ignored corner coordinate;
- category labels with exact source coordinates and digests;
- series labels with exact source coordinates and digests;
- numeric or blank data points with exact source coordinates, digests, and value origins;
- distinct table, chart, and chart-data-resource identities;
- exact selected-cell-block insertion context and the documented initial chart type;
- source-state and current document-flow bindings.

Text in the numeric body fails closed. Blank data points remain explicit missing values. Decimal
labels are rendered from the exact base-10 representation without binary floating-point conversion.
Request construction and plan building both revalidate source-state, grid, table identity, and
document-flow SHA-256 values. Planning never mutates the source table, and no partial plan or receipt
is returned after an error.

## Bounds and privacy

Default bounds are 32 MiB input, 1,000,000 cells, 1 MiB per label, 256-byte identifiers, 128 MiB
serialized output, and decimal scale 18. Hard ceilings are enforced. Canonical JSON is bounded and
row-major deterministic. Debug output redacts table/chart/resource IDs, labels, values, provenance,
and content digests.

## Exact Hangul 2020 source qualification

Direct HWPX lowering is intentionally blocked on a native package profile instead of guessing an
anchor, chart-part path, manifest rule or chart XML dialect. The private source worker creates only
a new disposable 3-by-3 table. Its top-left cell stays blank; the first row carries two series
labels, the first column carries two category labels, and the four body cells carry exact integers.
It saves a baseline, returns to the first cell, invokes the documented whole-table cell-block
sequence, asks Hangul to create the chart through the official action/ParameterSet pair, proves the
visible source text did not change, and saves a distinct chart HWPX.

The worker and watchdog pin x86 COM to build `11.0.0.9136`, the locked executable digest, creation
time, session and automation command line; reject pre-existing Hwp processes and path collisions;
bound runtime and artifact size; preserve the inner trace and progress journal; and may stop only an
exact same-session automation process.
Receipts contain hashes and finite counts, never document text or chart payload. There is no user
document open, module registration, UI input, network access or registry/system-setting write.

Static preparation is not native evidence. A run is admissible only when both HWPX artifacts,
terminal progress, exact process cleanup and later offline package inspection all pass. Every access
approval remains a user click; Computer Use does not perform it.

## Gate boundary

TABLE-006 advances only from `cataloged` to `unit_passed`. This policy does not prove a direct HWPX
adapter, chart XML, package mutation/preservation, linked-data save/reopen, formula-cache readback,
rendering, licensed Hangul 2020 execution, automation, differential parity, arbitrary user documents,
other PCs or versions, P06-09 completion, production readiness, or product completion. Each remains
a separate evidence Gate. The source worker, watchdog and static tests merely prepare the next
qualification run and do not change that decision.
