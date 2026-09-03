# Foundation worker v1 to Windows bridge v1

P10-01 adds `hwpx_agent.windows_bridge.v1` without changing the P01
`hwpx_agent.foundation.v1` package, descriptor, tags, generated models or wire bytes. The foundation
`ArtifactRef` and `ValidationState` types are imported by the new package; the legacy
`WorkerRequestContext` and `WorkerReceipt` remain valid only for their existing P01 semantic-boundary
tests.

This is an additive protocol, not an automatic conversion. A P01 request cannot be treated as an
authenticated lease or an STA command because it has no protocol version, target identity, lease,
fencing token, deadline, security policy, typed command union or staged sandbox handle. Consumers
must opt into the new v1 package and pass its validators. Missing or incompatible authority fails
closed; no fallback to a raw action, generic parameter map, filesystem path or document bytes exists.

Within `windows_bridge.v1`, field numbers, wire types, enum numbers, oneof members, RPC names and
security meaning are immutable. Compatible additions require new field numbers and a protocol-minor
policy update. Removing a field, reusing a tag, weakening validation or changing an existing meaning
requires a new protobuf package version and another explicit migration. Unknown major versions are
rejected before staging or worker creation.

Rollback disables P10 consumers while leaving the immutable v1 artifacts and baseline lock in place.
It never rewrites an already recorded lease, command, receipt or evidence artifact.
