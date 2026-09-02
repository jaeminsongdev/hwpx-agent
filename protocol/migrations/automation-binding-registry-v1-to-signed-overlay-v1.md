# Automation binding registry v1 → signed qualification overlay v1

This migration is additive. `hwpx-agent.automation-binding-registry/v1` remains the immutable, restricted source registry and is not rewritten in place.

`hwpx-agent.signed-automation-registry-envelope/v1` carries the exact original registry bytes as Base64 plus a separately structured qualification overlay. The Ed25519 signature covers the canonical payload containing both items. The registry state is `partially_qualified_scoped_current_target`: only individually verified bindings receive that target-scoped state. Consumers MUST verify the signature against an explicitly trusted public key before decoding or resolving a binding.

State mapping is fail-closed:

| Source/runtime state | Signed overlay state | Routing |
|---|---|---|
| unavailable binding | `unavailable` | disabled |
| verified runtime canary | `verified_current_target` | disabled in P02 |
| typed runtime failure | `failed_current_target` | disabled |
| policy-blocked probe | `blocked_by_policy` | disabled |
| probe not run | `unverified_not_run` | disabled |

An envelope is target-scoped to its exact profile/build/architecture/executable identity. It MUST NOT be reused for another build. Lineage starts at `registry_sequence=1`; a successor MUST increment the sequence and bind `parent_payload_sha256` to the directly preceding signed payload. A later build comparison rejects rollback and wrong-parent input, emits only capability IDs, change classes and hashes, and keeps raw Action/ParameterSet identifiers confined to the signed private registry. Changed or unknown bindings become `unverified_for_build` and are never auto-promoted.

The current P02 key is a local-development trust anchor only. Production, provider, hosted, VM and redistribution trust require a separately approved key-custody and release process.
