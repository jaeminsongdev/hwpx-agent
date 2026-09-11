# P08-07 chart automation policy

## Decision

P08-07 is `exact_chart_automation_component_pass / installed_target_not_run / task_incomplete`.
The v1 checkpoint implements all nine chart rows as one complete chart-state and target-binding
model. It deliberately does not guess `chartN.xml`, expose raw `HAction` names, or claim that the
licensed Hangul 2020 target executed, reopened, read back or exported any chart.

## Exact target profile and state

The schema is `hwpx-agent.chart-automation/v1`. An admitted target profile binds the exact product,
version, architecture, locale and executable/catalog/readback-adapter digests. It must contain
exactly these sorted capability mappings: `obj.chart_insert`, `obj.chart_type`, `obj.chart_data`,
`obj.chart_series`, `obj.chart_axis`, `obj.chart_legend`, `obj.chart_labels`, `obj.chart_title` and
`obj.chart_style`. Each mapping carries an opaque binding ID plus parameter-schema and
readback-schema SHA-256; public requests never contain action identifiers or unchecked parameter
bags. Chart-type and style choices must resolve through separately digest-bound target mappings.

Every chart binds distinct logical chart/data-resource/chart-part IDs, nonzero distinct native
object and instance IDs, complete row and column labels, a row-major numeric-or-blank grid,
orientation and embedded/linked-table/editor provenance. Series order and labels are derived from
the chosen data orientation and each complete series preserves visibility, exclusion, primary or
secondary axis, stacking relation, line, marker and style state. Axes preserve kind, visibility,
order, logarithmic flag, automatic or exact-decimal scale, title, number format, gridlines and
style. Legend, labels, title, selected target style, geometry, composition, appearance and opaque
unmodelled chart semantics are all explicit.

The document projection also binds a digest of every non-chart object identity. Insert requires a
five-part identity reservation plus before/after external-inventory and allocator-proof digests;
the digest is evidence that an allocator ran, not independent proof of collision freedom. State
validation proves collision freedom inside the chart projection; collision freedom against the
non-chart inventory still requires independent allocator-proof verification and target readback.

## Operations and preservation

- `obj.chart_insert` inserts one fully specified chart with no cursor-default fallback.
- `obj.chart_type` changes the mapped family, dimension and stacking tuple.
- `obj.chart_data` replaces the complete grid, labels, orientation, provenance and complete series
  array together.
- `obj.chart_series` updates exactly one existing ordered series. A secondary series requires an
  existing secondary axis; an unused secondary axis may exist so the two exact operations do not
  deadlock.
- `obj.chart_axis` upserts one exact typed axis; category and primary-value axes remain mandatory.
- `obj.chart_legend`, `obj.chart_labels`, `obj.chart_title` and `obj.chart_style` replace only their
  complete named component.

Every operation rejects no-op output. All untargeted charts and every untargeted component remain
byte-for-byte equal in the canonical state. Data dimensions, series labels/order, linked-table
digests, manual axis scale, presentation consistency, target type/style support, identity and
opaque preservation are revalidated after the transition.

## Request, plan, build and observation

Requests bind profile SHA, source-state SHA and before/after document-flow SHA. Admission, planning
and build independently recheck the profile, current source and current flow. A sealed plan binds
the exact capability binding, parameter/readback schemas, operation, target chart, complete target
state, request and all digests; build recomputes the target and rejects private-field tampering.

An execution observation is admitted only when exactly one attempt opened, saved and reopened the
document, performed full property readback, reproduced the exact target-state SHA and produced a
nonempty bounded export with SHA-256. This only proves receipt coherence. A separate provenance
campaign must prove the values came from the licensed target rather than a synthetic fixture.

All profile/state/request/observation JSON inputs are finite, duplicate-key-free, unknown-field
strict and NFC canonical. Counts, text, decimals, opaque state and export size have independent
limits. Debug output redacts target identity, labels, values, titles, object/resource IDs,
bindings and digests.

## Evidence boundary

The static vocabulary is grounded in the archived KS X 6101 source, Hancom's OWPML model at pinned
commit `1453388472c703a4b299a0834f425cdac16644b9`, and Hancom's chart help for families, row/column
data, series, axes, legend, labels, title and style. The model's `ChartType` only exposes a chart
reference while its serializer copies the chart part opaquely; therefore this checkpoint preserves
opaque chart semantics and uses target automation/readback bindings instead of inventing XML.

`exact_chart_state_component_pass=true`, `all_nine_chart_rows_modelled=true`,
`automation_plan_and_observation_contract=true`. `actual_target_profile=false`,
`direct_hwpx=false`, `resource_integrity=false`, `semantic_reopen=false`, `actual_hangul=false`,
`save_reopen=false`, `full_property_readback=false`, `export=false`, `render_diff=false`,
`direct_automation_differential=false`, `p08_07_complete=false`, `p08_complete=false`,
`production_ready=false` and `product_complete=false` remain explicit.

Reasoning level: `max`; P08-08 and the later combined target campaign also remain `max`.
