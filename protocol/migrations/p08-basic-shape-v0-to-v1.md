# P08 basic shape v0 to v1 migration

There is no stored v0 basic-shape request, plan, package binding or lowering receipt. V1 adds the
private `hwpx-agent.basic-shape/v1` schema and the bounded
`hwpx-agent.basic-shape-hwpx.hwpml-2011-static/v1` profile.

Earlier image rectangles, common-geometry edits, arbitrary XML fragments, screenshots, synthetic
shape examples and manual Hangul saves are not v1 shape plans or evidence. They MUST NOT be
relabeled. A caller must construct a fresh complete shape payload with P08-03 geometry, bind exact
before/after document flow, then bind that domain plan to the current package, anchor and every
native ID set.

V1 has no defaultable fields. Missing, duplicate, unknown, malformed or extra JSON fields fail.
Line, rectangle, ellipse, polygon, curve and drawing-text payloads are distinct and cannot migrate
through fallback conversion. Appearance properties, grouped/nested shapes, connectors, arcs,
containers, OLE/video/text-art, target-created HWPX, licensed-Hangul save/reopen and rendering
require a new profile or later task with an explicit migration policy.
