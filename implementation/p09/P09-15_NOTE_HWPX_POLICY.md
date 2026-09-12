# P09-15 note HWPX policy

## Decision

P09-15 is `REF-021/022 closed plain-text note static-section integration pass / target not run /
p09 incomplete`. It advances only footnote and endnote insertion from the typed note component to
an exact preserving HWPML section profile. It does not prove arbitrary rich-note bodies, a complete
HWPX package, licensed Hangul behavior, save/reopen, reference update, rendering, automation,
differential behavior, P09, production, or product completion.

## Closed native profile

The profile `hwpx-agent.note-hwpx.hwpml-2011-inline-note-payload/v1` admits one section with a
complete ordered logical-ID map for every top-level paragraph. Every existing note is exactly one
`footNote` or `endNote` inside an attribute-free direct `ctrl` child of a direct top-level paragraph
run. The note admits only `flag`, 16-bit `number`, BMP one-UTF-16-code-unit `userChar`, `prefixChar`,
`suffixChar`, positive `instId`, and exactly one `subList` child. Foreign-namespace or nested notes,
extra attributes/children and opaque or locked typed notes fail closed.

The inserted body is a separately supplied, self-contained `subList` payload. Its closed graph is
one or more fully attributed `p` elements, each with one or more fully attributed `run` elements,
and only plain `t` children with an optional numeric `charStyleIDRef`. `subList` requires the
official ID, direction, wrap, alignment, link-list, size and reference flags; this v1 profile admits
`HORIZONTAL`, `BREAK`, `TOP`. Tables, objects, fields, change tracking, line-segment caches,
special-character children, arbitrary XML and incomplete attributes are not silently accepted.

The complete payload byte SHA-256 is the body-graph binding. Decoded ordered text has a separate
SHA-256. A length-framed exact start-tag projection across `subList/p/run/t` binds all admitted body
style and structural attributes. The marker-style digest is the exact enclosing source-run start
tag. Native `instId`, semantic/native kind, all marker values, logical note identity, section,
paragraph, run and non-note inline anchor must match the complete typed target state.

## Planning, preservation and limits

Domain request/plan/build and HWPX plan/lower independently recheck the complete source state and
document flow. The HWPX plan additionally seals the exact section, every existing note wrapper,
the complete paragraph logical-ID map, raw payload SHA/length, domain plan and bounded plan digest.
Raw note text/XML is not embedded in plan JSON or Debug output.

Lowering performs one insertion byte edit and compares every byte outside it with the source. It
then reparses the complete target note inventory and checks every typed binding. Section, payload,
element, paragraph, run, inline, note, decoded-text, plan and output limits have finite hard
ceilings; allocation failures are typed. No fallback or partial output is returned.

## Evidence boundary

`static_section_hwpx=true`, `typed_target_projection_readback=true`,
`outside_delta_byte_preserved=true`, and `REF-021/022=integration_passed` refer only to generated
test section XML and the closed plain-text body profile. They are not licensed-Hangul or complete
package evidence and do not cover rich body objects.

`arbitrary_rich_note_body=false`, `complete_package_hwpx=false`, `actual_hwpx=false`,
`actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`, `reference_update=false`,
`hancom_open=false`, `save_reopen=false`, `render=false`, `automation=false`,
`differential=false`, `green_rows=0`, `p09_complete=false`, `production_ready=false`, and
`product_complete=false`.

Reasoning level: `max`. Rich-body expansion and the later combined licensed Hangul 2020 campaign
remain `max`.
