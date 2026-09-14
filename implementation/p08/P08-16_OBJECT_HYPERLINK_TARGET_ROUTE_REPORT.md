# P08-16 object hyperlink target route report

## Result

Result: `target_scope_qualified / fail_closed_route_pass / row_unit_only / target_mutation_not_run`.

The exact current-target chart fallback question is closed as unavailable, not approximated. The
new typed route admits the five P08-15 direct-HWPX IR kinds only after direct preflight. Chart and
every direct-preflight rejection return `CAPABILITY_UNAVAILABLE_FOR_TARGET` without attempting the
dialog-mediated desktop surface. Form object and paragraph band remain outside the catalogued
`OBJ-048` IR.

## Verified evidence

- Official HWPML review confirms the common root `href` inheritance for the five admitted IR kinds
  and its absence from the chart inheritance branch.
- Official help lists supported object hyperlink categories without chart, while official
  automation material establishes only the general hyperlink parameter surface.
- On the exact Hangul 2020 `11.0.0.9136` x86 ko-KR executable, a disposable generic shape was a
  positive control: the semantic hyperlink action was available and invoking it opened a dialog.
- The disposable chart was located by its anchor and tested by front selection, reverse selection
  and document-end reverse selection. Selection succeeded in all three paths, but the semantic
  hyperlink action remained unavailable in all three.
- The chart action was not executed. No external file was opened, no document was saved, no
  successful hyperlink mutation was claimed, and the owned Hangul process count returned to zero.
- Rust route tests pass 5/5: five-kind direct routing, chart rejection, no fallback after direct
  rejection, exact-target drift rejection, out-of-scope rejection and redacted diagnostics.

## Evidence boundary

The target observation was captured during this task but no raw private trace file was retained.
Accordingly it qualifies the conservative route decision only; it is not a verified automation
binding or a mutation receipt. `OBJ-048` remains `unit_passed` and non-green until a complete HWPX
package, licensed open/save/reopen/readback, resource-integrity, bounds/render, differential and
rollback/retry campaign passes for the admitted direct profile.

`chart_unavailable_with_reason=true`, `route_unit_tests=true`, `no_desktop_fallback=true`;
`raw_target_trace_persisted=false`, `object_hyperlink_mutation=false`, `save_reopen=false`,
`render=false`, `automation_runtime_binding=false`, `differential=false`,
`obj_048_complete=false`, `p08_complete=false`, `production_ready=false`, and
`product_complete=false`.

## Next exact task

Implement the remaining P08-10 native object-property adapters as one source-qualified batch, then
run one combined licensed-target campaign rather than one UI case at a time.
