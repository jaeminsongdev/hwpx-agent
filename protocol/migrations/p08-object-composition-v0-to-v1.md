# P08 object composition v0 to v1 migration

There is no stored v0 object-composition graph, request, plan or receipt. V1 introduces the
private `hwpx-agent.object-composition/v1` graph and exact transition contract.

Earlier flat object lists, raw `zOrder` attributes, screenshots, synthetic grouped XML and manual
Hangul edits are not v1 graphs or target evidence and MUST NOT be relabeled. A caller must build a
fresh complete graph whose sibling orders, containment depths, group bounds, connector closure and
content-addressed non-composition bindings all validate, then issue a fresh source/flow-bound v1
request.

V1 has no defaultable request or graph fields. Missing, duplicate, unknown, malformed, dangling,
cross-parent, cyclic, non-contiguous or over-limit input fails. HWPX lowering, package relationship
closure, installed-Hangul behavior, semantic reopen, bounds readback and render comparison require
a later explicit profile and cannot migrate from this pure model by assertion.
