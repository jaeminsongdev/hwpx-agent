# P09-29 complete native-form package binding policy

Date: 2026-10-02. Advance full package observation and plan binding without
changing the frozen P09-28 public exports or P09-27 production implementation.

Implement a separate production package reader/binder, compiled by an explicit
pending-export integration target. Read every integrity-checked ZIP entry and
the closed package graph, all ordered spine sections, actual header catalogs,
all non-form reference attributes and binary resources. Bind every complete
section/component map; reject missing/extra/duplicate sections, paragraph IDs,
component reservations and observed native IDs across sections. Empty-form
sections still participate. Derive fingerprints from bytes, never caller hashes.

The old shape ID-index profile genuinely rejects the actual native capture's
`edit@borderTypeIDRef` and `formCharPr@charPrIDRef` as unknown. Preserve that
failure. Add only a closed, location/namespace-exact form-reference overlay:
each reported issue must be an unknown ID-like attribute on an already fully
observed form root/native character child, independently catalog/identity checked.
Any other issue/code/location fails. Never report the legacy index itself PASS.
Native borderType zero is observed; the official model only declares a UINT,
not its target catalog semantics. Do not equate nonzero borderTypeIDRef with
borderFill IDs without evidence. Nonzero form border types remain unsupported
in this binding profile pending actual/reference qualification, not removed
from the full P09 goal. Fingerprint the real border catalog without inventing
that relationship.

Use the actual native section reader and existing typed domain engine. Require
full ordered explicit payload/default/validation policy bindings; native values
must match actual observations. Do not infer application/default policy from
saved XML. Reconstruct the complete global domain state from independent package
bindings and compare every field, not only control values. Plan binding rereads
the exact package/map, validates actual source flow and refuses observed metadata
protection/signature signals. Protection fingerprint/marker observation is not
a general claim of unlocked-document qualification.

Exercise the original missing-ID native capture, derived multi-section fixtures,
cross-section global tab plans, tampered metadata/state/maps/resources/references,
protection markers, finite limits and redaction. Derived fixtures and memory
plans are not actual native outputs. No package lowering/output, new exports,
production route, native/render/comparator or Gate claim is allowed in this step.
Those are still required subsequent product work, not removed from the goal.

Preserve all original files, capsules and failures. Pin current public source
successor and capture before/after tests. Publish a distinct deterministic source
capsule only after final tests and quality checks, with NOT_RUN claims retained.
Collect all ready native cases before later batch dispatch; no permission input,
new native session, original overwrite, deletion/move, staging, commit or push.
