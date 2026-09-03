# P02 signed registry to P10 execution bundle v1

`hwpx-agent.signed-automation-registry-envelope/v1` remains a restricted evidence artifact with
`routing_enabled=false`. P10 MUST NOT reinterpret that value, mutate the P02 artifact or treat a
source/documentation candidate as executable authority.

P10 introduces a separate private promotion boundary:

1. A trusted offline builder verifies the P02 Ed25519 envelope, exact current-PC target identity and
   per-binding runtime-probe evidence.
2. Only individually verified bindings are projected into
   `hwpx-agent.p10-06-binding-bundle/v1`. Every projected binding carries its probe-evidence digest,
   exact target identity and finite typed argument map.
3. The exact decoded payload bytes are signed and transported in
   `hwpx-agent.p10-06-signed-binding-envelope/v1`. The worker verifies the pinned public-key file,
   DER-derived key ID, payload/envelope digests and Ed25519 signature before parsing a raw private
   identifier.
4. The Agent copies the operation plan, envelope and public key into fixed read-only sandbox files
   and binds their identities into `hwpx-agent.p10-06-security-lease/v2`.
5. Public protobuf commands contain only the semantic bundle ID, hashes and opaque staged-artifact
   handles. Raw Action, ParameterSet and item identifiers remain inside the signed private payload.

The v1 executor supports only `document_global` bindings. A future target-positioning mode requires
a new schema version, target-resolution evidence and negative migration tests. Unknown fields,
duplicate JSON properties, unknown capability/argument, raw public automation tokens, invalid
enum/range/scale, wrong target/key/hash/signature and lease replay all fail before COM dispatch.
Once COM dispatch starts, false/exceptional completion is `UNKNOWN_OUTCOME` and requires worker
cleanup; it is never silently retried in the same session.
