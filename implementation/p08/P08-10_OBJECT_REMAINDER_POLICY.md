# P08-10 remaining direct object capability policy

## Decision

This checkpoint admits the fourteen previously cataloged P08-owned object capabilities at the
`unit_passed` stage only. It implements complete typed state transitions and fail-closed bindings;
it does not claim HWPX lowering, installed Hangul behavior, save/reopen, rendering, automation,
differential equivalence, production readiness, or a green P08 row.

The exact capability set is `obj.drawing_gallery`, `obj.form_object_insert`,
`obj.caption_insert`, `obj.paragraph_band_object`, `obj.margin_caption`,
`obj.textbox_properties`, `obj.image_properties`, `obj.freeform`,
`obj.shape_edit_points`, `obj.aspect_lock`, `obj.object_protect`, `obj.printable`,
`obj.alt_text`, and `obj.object_hyperlink`. A generic shape or generic property claim cannot
substitute for one of these capability IDs.

## State and transition model

`hwpx-agent.object-properties/v1` binds the exact object identity and kind, complete common
geometry, appearance, payload, resource, embedded-content and opaque-property state. It applies
typed margin/caption, text-box, image, aspect-lock, protection, printability, alternative-text and
hyperlink transitions. Text-box and image operations require the corresponding object kind.
Hyperlinks admit only bounded `https`, `mailto`, or intra-document bookmark targets; local file
and executable-style targets fail closed.

`hwpx-agent.shape-points/v1` edits only an existing freeform polygon or curve. The complete
freeform topology and common geometry are reused from the basic-shape and object-geometry models.
A topology-kind mismatch, degenerate geometry, no-op replacement, or unrelated state change is
rejected. New freeform insertion is routed by the exact `obj.freeform` capability rather than the
generic `obj.shape_insert` capability.

`hwpx-agent.object-special/v1` models drawing-gallery insertion, inert form insertion, caption
binding and paragraph-band insertion against a complete document inventory. It binds document
order, external and special object identities, captions, paragraph IDs, all resource and
relationship IDs, and document payload/property/resource/paragraph/opaque digests. The resource
inventory digest is recomputed from the complete sorted resource and relationship sets. Active
form content is denied.

## Exactness and preservation

Every request validates exact source-state SHA-256 and document-flow SHA-256. Planning rebuilds
the result from the source and seals the operation, source, result and flow digests. Building
rechecks the current source state and current flow before rebuilding the same result. Identity,
kind, payload, properties, formulas/caches where represented by bound digests, resources,
embedded content and opaque state not named by the operation must remain exact.

All JSON inputs are bounded, duplicate-key and unknown-field rejecting, and deterministic on
output. Identifiers, paths, text, links, resource names and digests are redacted from `Debug`.
Invalid limits, malformed state, collisions, unsupported kinds, unsafe links, active forms,
missing targets, stale state/flow, plan tampering and no-op operations return a typed failure with
no partial result or fallback.

## Evidence boundary

Focused Rust tests passed 27/27: six existing basic-shape regression tests, eight object-property
tests, six shape-point tests and seven special-object tests. These are component/unit tests only.

`unit_model_implemented=true`, `fourteen_capabilities_unit_passed=true`,
`complete_bound_state_preserved=true`, and `request_and_build_drift_rejected=true`.
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`property_readback=false`, `render=false`, `automation=false`, `differential=false`,
`p08_10_green=false`, `p08_complete=false`, `production_ready=false`, and
`product_complete=false`.

Reasoning level: max. The next exact task is direct HWPX lowering for the eight P08-owned
component rows already identified by the authoritative ledger, followed by the combined licensed
Hangul 2020 validation campaign.
