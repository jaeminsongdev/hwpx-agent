# P09-04 comment-model policy

## Decision

P09-04 is `five_capability_typed_component_pass / official_structure_partially_qualified /
native_author_time_visibility_resolution_unverified / direct_hwpx_not_run / target_not_run /
task_incomplete`. The component covers `REF-026` through `REF-030`: hidden-explanation state,
comment insertion, memo-style replacement, show/hide state, and resolution state. Comment deletion is
not a P09 capability: `review.comment_delete` is P11-owned and is deliberately absent.

The component does not lower or mutate an HWPX package, invoke installed Hangul, claim that author,
time, visibility or resolution fields have an exact native binding, or prove semantic reopen,
field/reference readback, render, automation, differential, production, P09, or product completion.

## Qualified official surface

The official Hancom `hwpx-owpml-model` source is pinned at commit
`1453388472c703a4b299a0834f425cdac16644b9`. The qualified structural surface is:

- a `hiddenComment` run control containing `subList`;
- paired `fieldBegin` and `fieldEnd` controls where the field type catalog contains `MEMO`;
- `fieldBegin` attributes `id`, `type`, `name`, `editable`, `dirty`, `zorder`, `fieldid` and children
  `parameters`, `subList`, `metaTag`; `fieldEnd` attributes `beginIDRef` and `fieldid`;
- header mapping-table `memoProperties` containing `memoPr` records with `id`, `width`, `lineWidth`,
  `lineType`, `lineColor`, `fillColor`, `activeColor`, and `memoType`;
- section `memoShapeIDRef`, all 18 `LineType2` values, all 16 line widths, and the four official
  memo-type tokens `NOMAL`, `USER_INSERT`, `USER_DELETE`, `USER_UPDATE`. The model maps the official
  `NOMAL` spelling to semantic `Normal` without rewriting source evidence.

The pinned model does not expose a proven exact native author/time, show/hide, or resolved-status
field for comments. Those values are therefore retained as typed component state under
`UnverifiedMemoParameters`; they are not represented as qualified HWPX attributes.

## Complete state and exact transitions

The ordered document state binds every section, author, memo style, hidden explanation and comment.
It preserves logical identity, begin-control/field pairing, exact ordered anchors, native field
shape, author and original-offset timestamps, body/plain-text/parameters/sublist digests, style and
section references, visibility/resolution, opaque native payload/properties, protection and all
unrelated document inventory digests.

Insert accepts only a fresh shown and unresolved comment and adds it at one exact slot. Style
replacement changes one exact style record while preserving all references. Show/hide and
resolve/unresolve change only the chosen comment field. Hidden-explanation toggle changes only the
chosen enabled bit. Document, section, style, explanation and comment locks fail closed; no
operation exposes a delete path or raw XML.

## Determinism and failure policy

Requests and builds independently recheck exact source-state and document-flow SHA-256. Plans seal
the operation, capability, request, full source/result state and both flow digests. Duplicate or
unknown JSON fields, oversized input/output, missing or colliding identities, invalid ordered
anchors, broken section/author/style references, invalid colors/timestamps/resolution tuples,
unqualified native shapes, invalid insertion indexes, protected/no-op changes, drift, and plan
tampering fail without a partial result. Debug output redacts identities, anchors, author metadata,
timestamps, comment bodies, opaque values and state digests.

## Evidence boundary

Focused Rust tests passed 11/11: ten public happy/boundary/negative/preservation tests and one
private sealed-plan tamper test. Private contract tests passed 5/5. These tests prove typed component
state and pinned official-source metadata only.

`unit_model_implemented=true`, `five_capabilities_unit_passed=true`,
`official_structure_source_qualified=true`, `complete_bound_state_preserved=true`,
`author_time_component_fixtures=true`, `style_visibility_resolution_fixtures=true`,
`protection_fixtures=true`, `request_and_build_drift_rejected=true`, and
`p11_comment_delete_excluded=true`. `native_author_time_binding_verified=false`,
`native_visibility_binding_verified=false`, `native_resolution_binding_verified=false`,
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `semantic_reopen=false`,
`field_readback=false`, `reference_update=false`, `hancom_open=false`, `save_reopen=false`,
`render=false`, `automation=false`, `differential=false`, `p09_04_green=false`,
`p09_complete=false`, `production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. Exact native author/time/visibility/resolution qualification and HWPX
lowering/readback remain `max`.
