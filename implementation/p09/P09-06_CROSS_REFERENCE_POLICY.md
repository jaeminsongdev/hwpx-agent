# P09-06 Cross-reference policy

Status: `typed_component_pass / official_structure_partially_qualified /
native_crossref_parameters_unverified / direct_hwpx_not_run / target_not_run / p09_06_non_green`.

## Scope and ownership

P09-06 owns REF-035 `ref.crossref_insert`. REF-036 `ref.crossref_update` remains P11-owned
automation. This card does not claim native parameter lowering, direct HWPX write/readback,
installed-Hangul execution, save/reopen, render, automation, differential, production, P09, or
product completion.

## Qualified native boundary

The pinned Hancom OWPML model at commit `1453388472c703a4b299a0834f425cdac16644b9`
defines the `CROSSREF` field-type token and the generic `fieldBegin`/`fieldEnd` envelope. It proves
begin attributes `id/type/name/editable/dirty/zorder/fieldid`, begin children
`parameters/subList/metaTag`, and end attributes `beginIDRef/fieldid`. It does not define the
semantic parameter keys, target-kind encoding, display-kind encoding, anchor binding, cached-value
encoding, or update rules. Therefore `UnverifiedFieldParameters` is the only admitted native
binding and no direct lowering is exposed.

## Complete typed state

`hwpx-agent.cross-reference/v1` binds ordered complete section, target and cross-reference
inventories. A target has a logical identity, one of bookmark/heading/numbered-paragraph/caption/
footnote/endnote kinds, an exact anchor, semantic-name/source-text/label/number/page-assignment
digests, sorted dependency IDs, opaque state/properties and protection. Target source text excludes
the display text of contained cross-reference controls so inserting a reference cannot mutate the
target projection that authorizes that insertion.

A reference binds logical, begin-control and field identity; exact anchor and optional containing
target; live target identity; display kind; update policy; cached display and exact target-projection
digest; native pair; opaque state/properties and protection. Sorted complete occupied non-crossref
begin-control, field-ID and field-name-digest inventories prevent global native collisions. Document state also binds
run/inline topology, non-crossref content, unrelated fields, bookmarks, notes, objects, numbering,
styles, relationships, resources, protection and opaque document state.

## Target graph and cache rules

All target dependencies and containment-derived reference edges form one complete directed graph.
Missing, duplicate, self-referential or cyclic targets fail closed. `TargetText`, `TargetName`,
`PageNumber` and `RelativePosition` are available for every target; `NumberOnly` requires numbering;
`LabelAndNumber` requires a caption with both label and numbering. Each display kind hashes only its
exact semantic projection. A cache is `Current` exactly when its target-projection digest matches;
otherwise it must be `Stale`. REF-035 accepts only a current cache. Reclassification of hypothetical
read state is modeled, but recalculating display content is not an implemented operation.

## Transition and preservation rules

Insertion requires an exact index, valid section/anchor, live compatible target, fresh logical and
native IDs, a non-colliding field name, unique anchor, current cache and a valid non-cyclic target graph. Document and section
locks reject mutation. A newly inserted entry may itself be locked; that lock governs later mutation,
which is outside REF-035. Only the ordered cross-reference inventory may change. Every target,
section, occupied-ID inventory, unrelated digest and opaque value remains byte-for-byte equal.

Request creation, plan construction and build independently recheck canonical source-state and
document-flow SHA-256. The sealed plan covers capability, request, source/target state, source/target
flow and operation. Strict JSON rejects duplicate or unknown keys and every input, output and
collection is bounded without truncation. Debug output redacts identities, anchors, digests, cached
values and opaque payloads.

## Evidence boundary

`unit_model_implemented=true`, `ref_035_unit_passed=true`, `target_graph_fixtures=true`,
`cache_projection_fixtures=true`, `cycle_and_dangling_fixtures=true`,
`complete_bound_state_preserved=true`, and `request_and_build_drift_rejected=true`.
`native_crossref_parameters_verified=false`, `ref_036_update_implemented=false`,
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `semantic_reopen=false`,
`field_readback=false`, `reference_update=false`, `hancom_open=false`, `save_reopen=false`,
`render=false`, `automation=false`, `differential=false`, `p09_06_green=false`,
`p09_complete=false`, `production_ready=false`, and `product_complete=false`.

Authority: `protocol/private/p09-cross-reference-v1.json` and
`implementation/p09/evidence/p09-06-cross-reference-source-qualification.v1.json`.
