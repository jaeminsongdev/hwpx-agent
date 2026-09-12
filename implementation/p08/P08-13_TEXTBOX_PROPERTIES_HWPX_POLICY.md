# P08-13 text-box properties HWPX policy

## Decision

P08-13 is `direct_hwpx_integration_pass / target_not_run / task_incomplete`. It advances only
`OBJ-025 obj.textbox_properties` from typed component evidence to preserving synthetic section-HWPX
integration. It does not prove licensed Hangul, visual equivalence, automation, production, P08, or
product completion.

## Exact native profile

The profile `hwpx-agent.textbox-properties-hwpx.hwpml-2011-attribute-spans/v1` admits exactly one
run-level `hp:rect` at the requested object ordinal. The rectangle must have one direct `hp:drawText`;
that element must contain exactly one empty `hp:textMargin` followed by exactly one `hp:subList`.
Nested, missing, duplicate, wrong-order, wrong-root, qualified-target-attribute and ambiguous forms
fail closed.

The reviewed one-to-one field map is:

- `textMargin.left/right/top/bottom` to the four typed HWP-unit margins;
- `subList.textDirection` values `HORIZONTAL`, `VERTICAL`, and `VERTICALALL` to all three typed text
  directions; and
- `subList.vertAlign` values `TOP`, `CENTER`, and `BOTTOM` to all three typed vertical alignments.

Numbers must be canonical unsigned decimal within the domain extent bound. Native object `id` and
`instid` must be canonical, nonzero, and equal the complete typed source state. No other attribute,
child, text, reference, object, comment, or section byte is rewritten.

## Planning, preservation, and limits

Request planning and lowering independently execute `ObjectPropertiesBuilder::build`, bind the
complete source and target `ObjectPropertiesState`, and check source and target document-flow SHA.
The HWPX plan additionally seals the exact section, rectangle, `drawText`, `textMargin`, `subList`,
domain plan, and plan SHA values. Lowering changes at least one and at most six reviewed attribute
value spans, proves every byte outside those spans is exact, and requires typed target readback.

Section, element, object, edit, output, and plan sizes have finite configurable limits below hard
ceilings. Plans are deterministic bounded JSON. Debug output redacts identities, document content,
properties, and all binding digests.

## Evidence boundary

`static_section_hwpx=true`, `typed_semantic_reopen=true`, `outside_attribute_spans_preserved=true`,
and `all_direction_alignment_variants=true` refer only to generated test XML. There was no complete
target package and no licensed target execution.

`actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`, `object_bounds=false`,
`render=false`, `automation=false`, `differential=false`, `p08_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. The remaining exact native adapters and the later combined licensed Hangul
2020 campaign remain `max`.
