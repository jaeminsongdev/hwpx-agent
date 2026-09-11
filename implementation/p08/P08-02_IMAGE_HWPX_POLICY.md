# P08-02 static image HWPX policy

## Decision

P08-02 is `static_component_pass / target_not_run / task_incomplete`. The v1 checkpoint admits one
embedded raster asset and one inline HWPML 2011 `pic` control, with exact crop, resolution,
display extent, alternate text, object identity, anchor and document-flow binding. Linked images,
licensed-Hangul behavior and rendering remain outside this checkpoint, so P08-02 is not complete.

## Source and request admission

The source builder accepts exactly one caller-selected spine part, paragraph and run. The run must
contain only an empty `t` anchor. It binds the ordered package graph, full section bytes, paragraph,
run, all supported package object IDs, all picture instance IDs and the picture insertion ordinal.
The request also binds the P08-01 asset plan, source and target document-flow SHA-256 values,
distinct nonzero object/instance IDs, display extent, independent X/Y DPI, a nonempty pixel crop
rectangle and nonempty XML-safe alternate text.

Only `embed` is admitted. `link` and `package_relationship` fail closed; no URI resolution, network
fetch or external file access occurs. The asset binding must equal a plan rebuilt from the exact
private payload and complete current graph. Both request construction and final lowering recheck
source state and document flow.

## Static lowering and preservation

The lowerer combines the P08-01 part/manifest relationship intents and one `pic` insertion in the
same preserving patch transaction. New content changes exactly the section and package manifest and
adds exactly one opaque `BinData` part. Deduplicated content changes only the section. Relationship,
media type, target part, full content digest and byte length must close exactly.

The static profile emits the HWPML picture/component fields required by the qualified model:
component offset/original/current size, flip, rotation and matrices; image resource reference;
image rectangle, pixel crop converted to HWPUNIT with deterministic half-up rounding, source image
dimension, margins/effects, absolute size, inline position and `shapeComment` alternate text. A
strict reader requires the exact v1 attribute/child set and values. Removing the inserted picture
and, for new assets, the inserted manifest item must restore the original bytes exactly; every other
part must remain byte-identical.

## Limits and diagnostics

Section bytes, XML elements, picture inventory, JSON, display extent, identifiers, DPI and alternate
text are finite and hard-ceiling checked. Asset/package/graph/ID/patch limits remain independently
enforced. Strict JSON rejects duplicate, unknown, missing or malformed fields. Public `Debug`
redacts paths, text, IDs, asset identity and all digests. Errors are typed and no failed operation
returns a partial artifact.

## Evidence boundary

The static vocabulary is grounded in the local official KS X 6101 archive and Hancom's public
OWPML model at pinned commit `1453388472c703a4b299a0834f425cdac16644b9`; neither proves how the
installed Hangul 2020 target serializes or renders this object. Synthetic package writer reopen is
component evidence only.

`linked_image=false`, `actual_hwpx_image=false`, `actual_hangul=false`, `save_reopen=false`,
`render=false`, `automation=false`, `differential=false`, `p08_02_complete=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false` remain explicit.

Reasoning level: `max`; the next P08 task and later exact-target qualification remain `max`.
