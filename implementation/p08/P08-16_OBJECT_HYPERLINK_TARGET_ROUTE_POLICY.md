# P08-16 object hyperlink target route policy

## Decision

P08-16 is `target_scope_qualified / fail_closed_route_pass / row_unit_only / target_mutation_not_run`.
It closes the chart fallback question for the exact licensed Hangul 2020 target without claiming
that `OBJ-048` is release-green.

The product route is now explicit:

- picture, basic shape, text box, drawing canvas and embedded object may use the P08-15 preserving
  direct-HWPX profile when its complete preflight admits the selected object;
- chart returns `CAPABILITY_UNAVAILABLE_FOR_TARGET` before effect;
- a direct-HWPX rejection never falls through to desktop automation;
- form object and paragraph band are outside the catalogued `OBJ-048` IR and fail closed.

## Source and target basis

The pinned HWPML 2011 model places the common root `href` field on
`AbstractShapeComponentType`. The reviewed chart model inherits from `AbstractShapeObjectType`
instead and has no corresponding common root field. The official object-hyperlink help enumerates
picture, table, drawing object, text box and equation targets, but does not enumerate chart. The
official automation tables document a hyperlink parameter set and a shape-object flag, but do not
establish an unattended chart mutation route.

One disposable, unsaved exact-target observation used a generic drawing shape as a positive
control and a newly created chart as the negative target. The generic shape reported the semantic
hyperlink action available, while the chart reported it unavailable after all three reviewed
selection paths. Executing the positive-control surface opened a dialog, as the user attested; no
mutation result was claimed. The chart command was never executed. No external file was opened,
no document was saved, and the owned Hangul process count returned to zero.

The observation did not persist a raw private trace, so it is target-scope evidence only. It is not
runtime binding, mutation, save/reopen, render, differential or production evidence.

## Route and failure rules

The router first qualifies build `11.0.0.9136`, x86, ko-KR and the pinned executable SHA-256.
It exposes no target identity in Debug output. The five admitted IR kinds route only to
`DirectHwpx` when direct preflight is eligible. Chart and a rejected direct preflight return the
public API error `CAPABILITY_UNAVAILABLE_FOR_TARGET`. Target drift and out-of-scope kinds remain
distinguishable internally while mapping to the same non-disclosing public capability error.

The target-scope policy never executes an Action, never opens or saves a document, and never
switches backend after a partial mutation.

## Evidence boundary

`official_source_review=true`, `exact_target_surface_observed=true`,
`generic_shape_positive_control=true`, `chart_three_selection_paths=true`,
`chart_unavailable_with_reason=true`, `route_unit_tests=true`, and
`no_desktop_fallback=true`.

`raw_target_trace_persisted=false`, `object_hyperlink_mutation=false`, `actual_target_hwpx=false`,
`save_reopen=false`, `resource_integrity=false`, `object_bounds=false`, `render=false`,
`automation_runtime_binding=false`, `differential=false`, `obj_048_complete=false`,
`p08_complete=false`, `production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. The combined target campaign remains `max`.
