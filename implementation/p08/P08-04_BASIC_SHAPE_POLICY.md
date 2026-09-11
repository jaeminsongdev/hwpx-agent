# P08-04 basic-shape construction policy

## Decision

P08-04 is `static_shape_component_pass / target_not_run / task_incomplete`. The v1 checkpoint
implements the complete reviewed static construction boundary for line, rectangle, ellipse, text
box and freeform polygon/curve shapes. It emits a preserving synthetic HWPX package and performs
strict semantic readback, but licensed Hangul 2020 serialization and rendering have not run.
P08-04 and P08 therefore remain incomplete.

## Admitted shape model

The domain schema is `hwpx-agent.basic-shape/v1`. `obj.shape_insert` admits line, rectangle and
ellipse payloads; `obj.textbox_insert` admits a rectangle plus drawing-text state; and
`obj.freeform` admits polygon and curve payloads. Every operation carries the complete P08-03 common geometry state, distinct nonzero native
object and instance IDs, and exact before/after document-flow SHA-256 bindings.

Line state includes reversal and two distinct signed points. Rectangle and text-box state includes
ratio and four distinct nonzero-area corners. Ellipse state includes interval-dirty, arc-property
presence, NORMAL/PIE/CHORD semantics and all seven center/axis/start/end points; its two axes must
be nonzero and non-collinear. Polygon state requires at least three unique nonzero-area points.
Curve state requires one or more nonzero LINE/CURVE segments. Coordinates are signed bounded
HWPUNIT integers.

Text boxes bind last width, name, editability, four text margins, distinct sub-list and paragraph
IDs, paragraph/style/character-property references, text width/height, vertical alignment and
XML-valid Unicode text. The lowerer emits `drawText`, `textMargin`, `subList`, paragraph, run and
text nodes as one typed object. Line/fill/shadow appearance is deliberately owned by P08-05; it is
not silently defaulted into this profile.

## Exact package planning and lowering

Request construction and domain build both revalidate the complete geometry, shape payload and
document flow. HWPX planning then binds the exact package-state digest, selected section,
paragraph, empty run, object-ID set, instance-ID set, paragraph-ID set and sub-list-ID set. Final
lowering repeats every inspection and rejects any source, plan, flow or ID drift.

The output is one static HWPML 2011 run-level `line`, `rect`, `ellipse`, `polygon` or `curve`
fragment. It contains the complete P08-03 common geometry plus all admitted shape-specific state.
The patch changes exactly one spine part, adds no part or relationship, and inserts immediately
before the one selected empty text node. The v6 ID profile types every shape object/instance ID and
inherits all prior table, formula, equation and picture rules.

Before returning, the lowerer strictly reparses the emitted object, reuses the P08-03 common
geometry reader, compares the full shape payload, checks object/instance/shape/paragraph/sub-list
count deltas and removes the inserted byte span to prove byte-exact source restoration. The
synthetic package writer then reopens the complete ZIP through the package graph and v6 ID index.
No failure returns a partial artifact.

## Limits and diagnostics

JSON input/output, points, segments, text, names, coordinate magnitudes, section bytes, XML
elements, native identifiers and fragment size have independent finite ceilings. Duplicate,
unknown, missing, malformed and oversized JSON fields fail closed. Native integers and booleans
are canonical; element namespaces, child order and attribute sets are exact. Public Debug output
redacts request IDs, native IDs, paths, digests, text-box names/text and shape payloads.

## Evidence boundary

The vocabulary is grounded in the local archived KS X 6101 material and Hancom's public OWPML
model at pinned commit `1453388472c703a4b299a0834f425cdac16644b9`. Those are static type
references, not the installed target's runtime serialization oracle. All current packages are
synthetic fixtures.

`synthetic_full_package_reopen=true`, while `actual_target_hwpx=false`,
`exact_current_2020_serialization=false`, `actual_hangul=false`, `save_reopen=false`,
`render=false`, `automation=false`, `differential=false`, `p08_04_complete=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false` remain explicit.

Reasoning level: `max`; P08-05 appearance semantics and the later combined target campaign also
remain `max`.
