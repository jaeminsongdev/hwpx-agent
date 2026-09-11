# P08 object appearance v0 to v1 migration

There is no stored v0 appearance request, plan, source binding or lowering receipt. V1 adds the
private `hwpx-agent.object-appearance/v1` state schema and the bounded
`hwpx-agent.object-appearance-hwpx.hwpml-2011-static/v1` section profile.

Earlier shape defaults, arbitrary XML fragments, screenshots, image rectangles, visual examples
and manual Hangul saves are not v1 appearance plans or evidence. They MUST NOT be relabeled. A
caller must construct a fresh complete source/target appearance transition, bind exact before/after
document flow, then bind that domain plan to the current section and direct-run object.

V1 has no defaultable request fields. Missing, duplicate, unknown, malformed or extra JSON fields
fail. Basic-shape fill/shadow and picture effects/image adjustment are different native families and
cannot migrate through fallback conversion. Scheme/system/preset effect colors, grouped/nested
objects, package-level image-fill resource proof, target-created HWPX, licensed-Hangul save/reopen,
rendering and visual diff require a new profile or later task with an explicit migration policy.
