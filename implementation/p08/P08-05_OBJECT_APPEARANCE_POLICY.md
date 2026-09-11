# P08-05 object appearance policy

## Decision

P08-05 is `static_appearance_component_pass / visual_target_not_run / task_incomplete`. The v1
checkpoint implements the complete reviewed static appearance boundary for direct-run basic shapes
and pictures. It performs exact section-level HWPML readback and preserving lowering, but no output
has been opened, saved, reopened or rendered by licensed Hangul 2020. The required visual diff has
not run, so P08-05 and P08 remain incomplete.

## Admitted appearance model

The domain schema is `hwpx-agent.object-appearance/v1`. It covers all eleven P08 appearance
capabilities: line style, solid/gradient/pattern/image fill, shape or picture shadow, reflection,
glow, soft edge, transparency and image color adjustment. Basic shapes and pictures are separate
families; cross-family fields fail closed.

Line state includes RGB color, positive HWPUNIT width, all public-model line patterns, end cap,
head/tail arrow shape, fill, size, outline placement and alpha. Shape fill is exactly one of solid,
pattern, gradient or image. Gradients bind type, angle, center, step, ordered colors and alpha;
patterns bind face/hatch colors and hatch type; image fills bind placement mode, lexical manifest
relationship ID, brightness, contrast, effect and alpha. Classic shape shadow binds the public
model's exact legacy enum spelling, RGB color, signed offsets and alpha.

Picture effects cover outside/inside shadow, glow, soft edge and reflection, including align,
radius, direction, distance, rotation, skew, scale, fade, alpha/position ranges and ordered RGB
color transforms. V1 admits exact RGB effect colors with the public model's `-1` inactive index
sentinels only; scheme/system/preset color sources are rejected rather than guessed. Solid fill
similarly admits the public model's inactive black hatch default only. Picture image adjustment binds brightness, contrast, effect and
alpha. A transparency request may change only the named alpha channel; color adjustment may not
silently change image alpha.

## Exact planning and preserving lowering

Every request binds distinct nonzero logical/native identity, complete source and target appearance,
one exact operation and before/after document-flow SHA-256. Request construction, domain planning
and domain build all repeat family, range, resource syntax, single-delta and flow checks. Canonical
request and plan JSON is bounded and duplicate/unknown-field strict.

The HWPX profile is `hwpx-agent.object-appearance-hwpx.hwpml-2011-static/v1`. Planning selects one
direct-run `line`, `rect`, `ellipse`, `polygon`, `curve` or `pic` by document order and binds the
exact section, object bytes, native IDs, source appearance and domain plan. Final lowering repeats
all checks. Basic-shape appearance children are regenerated canonically after `renderingInfo`;
picture line/effects are regenerated and only the four reviewed image-adjustment attributes may
change. Unknown attributes, duplicate components, unmodelled content, noncanonical numbers,
unsupported namespaces and unsupported effect colors fail closed.

Strict readback must equal the complete target state. Replacing the resulting object span with the
original object bytes must reconstruct the original section byte for byte, proving that paragraphs,
runs, geometry, payload, text and all bytes outside the selected object were preserved. The v1
lowerer is deliberately section-level: it validates an image-fill relationship ID lexically but
does not yet prove that it resolves to a package manifest image. P08-01/P08-02 package integration
must bind that resource before image-fill target evidence can pass.

## Limits and diagnostics

JSON bytes, section bytes, output bytes, XML elements, direct-run objects, fragment bytes, numeric
lexemes, gradient colors, color transforms, identifiers, line width, offsets and effect scalars
have independent finite ceilings. No failure returns partial bytes. Public Debug output exposes
only profile, capability, family, ordinal, counts and booleans; identities, paths, relationship IDs,
appearance values and digests remain redacted.

## Evidence boundary

The vocabulary is grounded in the local archived KS X 6101 material and Hancom's public OWPML
model at pinned commit `1453388472c703a4b299a0834f425cdac16644b9`. That source establishes
static vocabulary and types only, not installed-target serialization or rendering behavior. All
current XML is synthetic.

`synthetic_section_roundtrip=true`, while `package_image_fill_resource_integrity=false`,
`actual_target_hwpx=false`, `exact_current_2020_serialization=false`, `actual_hangul=false`,
`save_reopen=false`, `visual_diff=false`, `render=false`, `automation=false`,
`differential=false`, `p08_05_complete=false`, `p08_complete=false`,
`production_ready=false` and `product_complete=false` remain explicit.

Reasoning level: `max`; P08-06 composition and the later combined target campaign also remain
`max`.
