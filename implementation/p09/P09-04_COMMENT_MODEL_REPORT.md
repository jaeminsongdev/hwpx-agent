# P09-04 comment-model report

## Result

Result: `five_capability_typed_component_pass / official_structure_partially_qualified /
unverified_native_semantic_bindings_preserved / direct_hwpx_not_run / p09_04_non_green`.

P09 now has a bounded comment-state component for `REF-026` through `REF-030`. Comment deletion
remains P11-owned. No component result is promoted to an actual HWPX, installed-Hangul, semantic
reopen, field/reference readback, save/reopen, render, automation, differential, production, P09,
or product PASS.

## Implemented evidence

- `comment_model.rs` implements hidden-explanation toggle, exact ordered comment insertion, exact
  memo-style replacement, show/hide, and resolve/unresolve under
  `hwpx-agent.comment-model/v1`.
- The complete ordered state binds section memo-style references, authors, styles, explanations,
  comments, native field identity, ordered anchors, original-offset timestamps, body and native
  payload digests, protection and unrelated document inventory digests.
- Insert admits only fresh shown/unresolved comments. Each other mutation changes one exact target;
  document, section, style, explanation and comment locks and no-op requests fail closed.
- Requests and builds independently reject exact source-state and document-flow drift. The plan
  binding, strict bounded JSON, duplicate/unknown-field rejection, finite limits, typed stable
  errors and redacted diagnostics are covered.
- The pinned official model qualifies `hiddenComment/subList`, `fieldBegin`/`fieldEnd` with `MEMO`,
  the memo-style table and section reference, 18 line types, 16 widths, and four memo-type tokens.
  It does not qualify exact native author/time, show/hide or resolved-status fields; the component
  preserves those values under the explicit `UnverifiedMemoParameters` boundary.

Focused Rust: public comment-model tests 10/10 PASS; private sealed-plan tamper test 1/1 PASS; total
11/11 PASS. Private contract/qualification/tamper tests: 5/5 PASS.

## Evidence boundary

No section/header XML or HWPX package was created, mutated or reopened. No licensed Hangul process
was used. No native author/time, show/hide or resolution mapping was inferred from UI behavior or a
generic parameter container.

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

## Next exact task

Implement P09-05 bookmark/hyperlink/reference operations as a complete typed component with exact
identity, anchors, targets, display text, protection, preservation and drift checks. Exact native
comment semantic bindings and comment HWPX lowering/readback remain separate target work.
