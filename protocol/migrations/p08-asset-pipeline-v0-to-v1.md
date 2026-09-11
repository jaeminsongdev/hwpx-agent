# P08 asset pipeline v0 to v1 migration

There is no stored v0 asset plan or receipt. V1 introduces the finite
`hwpx-agent.asset-pipeline.hwp-image-v1` profile, complete package-graph binding, exact declared and
sniffed media agreement, full-payload SHA-256 identity, deterministic reuse/add disposition and a
private sidecar plan that deliberately excludes payload bytes.

No earlier generic `AddedPart`, package-preservation result, artifact-service media descriptor or
table-chart resource is an asset-pipeline v1 plan. Those records MUST NOT be relabeled or promoted.
Callers must build a new plan from the exact payload and current closed `PackageGraph`.

The v1 private plan has no defaultable fields. Missing, duplicate, unknown or extra fields fail
deserialization; wrong schema/profile labels fail version admission; stored values are compared to
a fully recomputed canonical plan. Future media-profile expansion requires a new profile or schema,
new malformed-media tests and explicit migration policy.
