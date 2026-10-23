# P09 field auto-number HWPX v0 to v1

There is no accepted v0 wire or adapter profile to migrate.

v1 introduces the closed `hwpx-agent.field-auto-number-hwpx.hwpml-2011-digit/v1` static-section
profile. Producers must emit only the admitted PAGE, PICTURE, TABLE or EQUATION `autoNum` shape and
must bind the complete source state, flow, section, paragraph map, projection and plans. Consumers
must reject every unrecognized format, attribute, child, identity assumption or transition.

No compatibility fallback is permitted. Unsupported or ambiguous input must fail closed with no
partial output; no rejected state may be silently normalized into the admitted profile.
