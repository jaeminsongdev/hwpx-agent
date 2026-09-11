# P08-11 object HWPX integration policy

## Decision

P08-11 is `static_section_hwpx_integration_pass / target_not_run / task_incomplete`. It lowers the
six P08-06 composition operations and the P08-08 canvas-insert/crop operations into one bounded
HWPML 2011 section island, then requires exact semantic reopen and byte preservation outside that
island. This advances eight P08 rows from component to integration evidence only.

## Admitted native profiles

- `hwpx-agent.object-composition-hwpx.hwpml-2011-static/v1` admits exactly one closed run-contained
  object island. Logical IDs bind distinct native `id`/`instid`, parent containers, contiguous
  `zOrder`, `groupLevel`, offset and current size. Existing fragments retain their complete opaque
  payload. Group/ungroup, four z-order moves, six alignments, two distribution axes and all nine
  connector kinds lower to native container/shape/connectLine structure.
- `hwpx-agent.drawing-canvas-hwpx.hwpml-2011-static/v1` admits one nonempty closed canvas island.
  Existing containers, pictures and passive shapes retain opaque content. Crop changes only native
  `imgClip` plus the domain payload binding. Insert appends one reserved container/rectangle tree.
  The picture relationship and original dimensions are checked, but package payload bytes are not.
- Visibility and printability have no admitted native delta in these profiles and therefore must be
  true. Newly generated groups, connectors, containers and rectangles require the standardized
  empty binding: five SHA-256 values of the empty byte string, zero opaque bytes and no resources.
  Other generated object kinds, linked/OLE content, picture effects and nonempty generated payloads
  fail closed instead of being approximated.

## Planning, preservation and limits

Both adapters recheck complete domain source state and document-flow SHA at request planning and
again at lowering. Plans seal source/target section SHA, state SHA, flow SHA and a deterministic
plan SHA. Lowering regenerates the exact target, verifies the sealed target section digest, compares
all bytes before and after the selected island, and performs a strict native semantic reopen.

Inputs, outputs, element counts and object/node counts have finite limits and hard ceilings. XML is
parsed by the preserving tokenizer; malformed, duplicate, missing or ambiguous native structure is
rejected. Debug views expose counts and booleans only and redact bindings/digests.

## Evidence boundary

The source is synthetic static section HWPML and is not a complete HWPX package. Therefore
`static_section_hwpx=true` and `semantic_reopen=true`, while `full_package=false`,
`resource_integrity=false`, `actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`object_bounds=false`, `render=false`, `automation=false`, `differential=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false`.

Reasoning level: `max`; extension to the remaining P08-10 models and target evidence remains
`max`.
