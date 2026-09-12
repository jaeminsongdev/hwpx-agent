# P09-05 Link/reference policy

Status: `typed_component_pass / official_structure_partially_qualified /
native_hyperlink_parameters_unverified / direct_hwpx_not_run / target_not_run / p09_05_non_green`.

## Scope and ownership

P09-05 owns REF-031 `ref.bookmark_insert`, REF-032 `ref.bookmark_delete`, REF-033
`ref.hyperlink_insert`, and REF-034 `ref.hyperlink_edit`. P09-06 owns cross references. This card
does not claim direct HWPX lowering, semantic reopen, field/reference readback, installed-Hangul
execution, save/reopen, render, automation, differential, production, P09, or product completion.

## Qualified native boundary

The pinned Hancom OWPML model at commit `1453388472c703a4b299a0834f425cdac16644b9`
defines `bookmark` with the exact `name` attribute. It also defines `fieldBegin`/`fieldEnd`, the
`HYPERLINK` field-type token, begin attributes `id/type/name/editable/dirty/zorder/fieldid`, begin
children `parameters/subList/metaTag`, and end attributes `beginIDRef/fieldid`. The generic model
does not define the semantic keys or serialization rules inside hyperlink parameters. Therefore
`UnverifiedFieldParameters` is the only admitted semantic binding and no lowering claim is made.

## Complete typed state

`hwpx-agent.link-reference/v1` binds ordered section, bookmark and hyperlink inventories. Sections
bind paragraph count plus run/inline topology digests. Bookmarks bind logical identity, NFC exact
name, ordered anchor, native tag, opaque payload/properties and protection. Hyperlinks bind logical,
begin-control and field identity; ordered anchor; target; display digest; the complete native pair;
opaque state/properties and protection. Sorted occupied non-hyperlink control/field ID inventories
prevent native collisions. Document state additionally binds unrelated-field, style, object,
relationship, resource, protection, non-reference-content and opaque-document digests.

## Target and security rules

Internal targets use a live logical bookmark ID. External targets are limited to syntactically safe
ASCII HTTPS, plain email address, or path-free managed-artifact identity with an optional NFC
bookmark name. Every external target requires an exact kind-and-target SHA-256 entry in the bound
policy revision. HTTP, file/local paths, credentials in HTTPS authorities, whitespace, backslashes,
query-bearing email addresses, malformed names and unapproved targets fail closed. Debug output
never exposes names, URIs, email addresses, artifact IDs, anchors, digests or opaque payloads.

## Transition and preservation rules

Bookmark insertion requires one fresh logical ID, exact name and valid insertion index. Deletion
rejects protected bookmarks and any live internal hyperlink instead of creating a dangling target.
Hyperlink insertion requires fresh logical/native identities and a unique exact anchor. Editing may
change only target and display-text digest; identity, anchor, native pair, opaque state and every
unrelated inventory remain byte-for-byte equal. Document/section/entry locks and no-ops fail before
returning any output.

Request creation, plan construction and build independently recheck canonical source-state and
document-flow SHA-256. The sealed plan covers capability, request, source/target state, source/target
flow and operation. Strict JSON rejects duplicate or unknown keys and all inputs/outputs/collections
are bounded without truncation.

## Evidence boundary

`unit_model_implemented=true`, `four_capabilities_unit_passed=true`,
`official_structure_source_qualified=true`, `external_policy_fixtures=true`,
`dangling_reference_fixtures=true`, `complete_bound_state_preserved=true`, and
`request_and_build_drift_rejected=true`. `native_hyperlink_parameters_verified=false`,
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `semantic_reopen=false`,
`field_readback=false`, `reference_update=false`, `hancom_open=false`, `save_reopen=false`,
`render=false`, `automation=false`, `differential=false`, `p09_05_green=false`,
`p09_complete=false`, `production_ready=false`, and `product_complete=false`.

Authority: `protocol/private/p09-link-reference-v1.json` and
`implementation/p09/evidence/p09-05-link-reference-source-qualification.v1.json`.
