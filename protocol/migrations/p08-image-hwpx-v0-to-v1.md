# P08 image HWPX v0 to v1 migration

There is no stored v0 image-HWPX request, source binding, readback or lowering receipt. V1 adds the
private `hwpx-agent.image-hwpx/v1` request and the deliberately narrow
`hwpx-agent.image-hwpx.hwpml-2011-static-embed/v1` profile.

No earlier P08-01 asset plan, generic `AddedPart`, arbitrary drawing XML, table-chart resource,
synthetic package reopen or manually edited HWPX is a v1 image request or result. These records
MUST NOT be relabeled or promoted. A caller must inspect the exact current empty-run target, build
the P08-01 asset plan from the exact bytes and current graph, then construct a fresh request with
complete source, flow, geometry, crop, DPI, alternate-text and ID bindings.

V1 has no defaultable fields. Missing, duplicate, unknown, malformed or extra JSON fields fail.
`link` and `package_relationship` enum values are parseable solely to return a typed unsupported
mode error; they do not imply capability. Future linked-image support, floating anchors, effects or
target-qualified serialization require a new profile/schema and an explicit migration policy.
