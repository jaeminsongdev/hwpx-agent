# P08-06 object composition report

## Result

Result: `pure_object_graph_component_pass / successor_static_hwpx_integration_pass /
target_not_run / task_incomplete`.

This checkpoint implements all six P08-06 composition rows in one shared exact graph model rather
than closing a group-only or z-order-only subset.

## Implemented evidence

- Complete object nodes bind logical/native identity, containment, z-order, group depth, world
  bounds, visibility, printability and content-addressed payload/property/resource state.
- Group/ungroup preserve child identity and non-composition state, recompute levels and exact union
  bounds, and reject non-sibling or connector-open selections.
- All four z-order moves preserve a contiguous sibling order and reject no-op edges.
- All six alignment modes and both distribution axes have explicit deterministic integer rules;
  group moves translate descendants and ancestor group bounds are recomputed bottom-up.
- Connector create/update covers all nine public model kinds, attached/detached endpoints, ordered
  control points, same-parent closure and derived bounds.
- Request, plan and build recheck source-state SHA, document-flow SHA, exact target recomputation and
  sealed-plan integrity. Strict bounded graph/request JSON and redacted Debug are enforced.

Focused Rust tests: 10/10 PASS (graph invariant tests 9/9 plus private-plan tamper 1/1). They cover
group/ungroup roundtrip, all four z-order moves, all six alignments, horizontal/vertical balanced
distribution, connector create/update and closed grouping, invalid z-order/selection/open connector
edges, strict/duplicate/unknown/limited JSON, geometry/content boundaries, source drift, flow drift,
non-composition preservation and redacted Debug.

P08-11 adds a separate preserving static-section HWPX adapter: focused lowering tests pass 6/6 for
all six rows, strict semantic reopen and outside-island preservation. That successor evidence moves
the rows to `integration_passed`; it does not alter this domain contract or prove a full package.

## Evidence boundary

No full-package output or licensed-target execution exists for this graph model. No output was
opened, saved, reopened, bounds-read or rendered by licensed Hangul 2020. The P08-11 synthetic
section reopen and pinned Hancom model are not runtime oracles.

`pure_object_graph_component_pass=true`, `graph_invariant_tests=true`,
`static_section_hwpx=true`, `semantic_reopen=true`, while `resource_integrity=false`,
`actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`, `object_bounds=false`,
`render_diff=false`, `direct_automation_differential=false`, `p08_06_complete=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false`.

## Next exact task

Continue lowering the remaining P08 typed models at `max`. The later P08 target campaign must add
full-package integrity, installed-target bounds and render-diff evidence before any registry row
becomes green.
