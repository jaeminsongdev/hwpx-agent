# P09-13 bookmark HWPX policy

## Decision

P09-13 is `two_rows_static_section_integration_pass / target_not_run / p09_incomplete`.
It advances only REF-031 `ref.bookmark_insert` and REF-032 `ref.bookmark_delete` from the typed
link/reference model to exact preserving static-section HWPML integration. It does not prove a
complete HWPX package, licensed Hangul behavior, save/reopen, reference update, rendering,
automation, differential behavior, P09, production, or product completion.

## Closed native profile

The profile `hwpx-agent.bookmark-hwpx.hwpml-2011-point-marker/v1` admits one exact `hp:sec` and an
ordered complete inventory of empty `hp:bookmark` markers. Each marker has only the required
unqualified `name` attribute, is the only element inside its direct `hp:ctrl` wrapper, and that
wrapper is a direct child of one `hp:run` inside a known `hp:p`. Only whitespace may surround the
marker inside the wrapper.

The typed anchor must be a point. Its paragraph ordinal, direct-run ordinal and non-bookmark inline
element ordinal must match the complete native projection. Logical bookmark identity and lock or
opaque state are not inferred from XML: the complete typed source state is bound, and only an
unlocked `Bookmark` entry with empty opaque payload/properties is representable. Same-boundary
markers retain their complete typed inventory order.

REF-031 inserts exactly one escaped marker wrapper at the bound point. REF-032 removes exactly the
bound whole wrapper. Ranged anchors, unsupported native tags, locked or opaque bookmarks, malformed
or duplicate attributes, ambiguous transitions, out-of-range anchors, and unmodeled bookmark
wrappers fail closed.

## Planning, preservation, and limits

Domain request/plan/build and HWPX plan/lower independently recheck the complete source state and
document flow. The HWPX plan additionally seals the section SHA-256, every source bookmark-wrapper
SHA-256, the domain plan, and its own deterministic bounded JSON digest.

Lowering performs exactly one byte edit. Every byte before and after that edit is compared against
the source, followed by complete typed target-projection readback. Section, element, paragraph,
run, inline-element, bookmark, name, output, and plan sizes have finite hard ceilings. Public Debug
and errors redact names, identities, paths, state, and digests.

## Evidence boundary

`static_section_hwpx=true`, `typed_target_projection_readback=true`,
`outside_delta_byte_preserved=true`, and `REF-031/032=integration_passed` refer only to generated
test section XML. The readback verifies the expected typed state against the full admitted native
projection; it is not a licensed-Hangul or independent package reconstruction oracle.

`complete_package_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`field_readback=false`, `reference_update=false`, `hancom_open=false`, `render=false`,
`automation=false`, `differential=false`, `green_rows=0`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. The remaining exact lowering and later combined licensed Hangul 2020
campaign remain `max`.
