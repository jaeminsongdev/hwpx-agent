# P02-09 Registry Signing and Drift Report

- Completed: 2026-09-02
- Audited source commit: `7b63d0ede07ea116e64d084fa00015a0fefb4ec3`
- Task state: `pass_current_pc_local`
- Review: `STRICT / max`, blocker/major/minor `0/0/0`

## Delivered

- Ed25519 key generation, deterministic signing, trusted-public-key verification and private no-overwrite publication CLIs.
- A self-contained private signed envelope that covers the exact original registry bytes plus a separately structured qualification overlay.
- Independent reconstruction of the overlay from the locked P02-08 request, trace and receipt before signature acceptance.
- Target/profile/build/architecture/executable identity binding, explicit current-PC local scope and hard-disabled production/provider/routing policy.
- Monotonic registry sequence and parent-payload lineage checks that reject signed rollback and wrong-parent comparisons.
- A safe drift report that exposes only capability IDs, change classes, hashes and support demotion; raw Action/ParameterSet identifiers remain in the private signed artifact.
- An additive migration note, four Draft 2020-12 schemas and exact `cryptography==50.0.1` toolchain preflight.
- A public local-development trust policy and public key. The private key remains local, Git-ignored and was never printed.

## Actual signed registry

- Signing implementation/source commit: `7b63d0ede07ea116e64d084fa00015a0fefb4ec3`.
- Algorithm: Ed25519.
- Key ID: `ed25519-sha256-2df5b9452e4e49827de3d4716bc9add34a11dbad69dfbc9fd9882e66053daa64`.
- Public key SHA-256: `838f7ce354cb2e284ca8b1e108c4234481b66fdfc0c9d415de43dc7cd3da57f5`.
- Source registry SHA-256: `986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48`.
- Signed payload SHA-256: `3958ccc564be09d0f40889287fa4f2db36584596001a7a2b9e8df0ca57a9450f`.
- Signed envelope: 963,624 bytes, SHA-256 `97c86645a4bf0696474cb6815699a2e4b012f650ae09ef81c582b672580b85e4`.
- Independent verification receipt: 929 bytes, SHA-256 `c11c2e2555877ea4d4f3973ae6b3e739ddecbbf80150b99ce66be966b54d48f7`, errors `0`.
- First registry sequence: `1`; parent payload: none.
- State: `partially_qualified_scoped_current_target`.

The authoritative envelope, verification receipt, reproducibility copy and drift report remain local under Git-ignored `implementation/p02/evidence/signing-runs/7b63d0ede07ea116e64d084fa00015a0fefb4ec3/`.

## Signed qualification coverage

| State | Count |
|---|---:|
| source bindings | 536 |
| source candidates | 32 |
| source unavailable | 504 |
| `verified_current_target` | 2 |
| `failed_current_target` | 1 |
| `blocked_by_policy` | 17 |
| `unverified_not_run` | 12 |
| routing enabled | 0 |

Only the exact P02-08 undo/redo canaries were promoted. The default-read failure, risk-blocked candidates and not-run candidates were not promoted. Signing does not convert unavailable or unexecuted bindings into product support.

## Drift and rollback

- Actual drift report: 974 bytes, SHA-256 `28c8efba8f64d101cb5e7345b3d8589e011a1466da9c5bed69b906855926df4b`.
- Actual baseline state: `baseline_unavailable`; compared capability count `0`.
- No actual cross-build comparison is claimed because no second exact-build signed registry exists on this PC.
- Synthetic signed-registry tests proved `added`, `removed`, binding, ParameterSet and behavior change classification without exposing raw identifiers.
- A changed capability becomes `unverified_for_build`; no change is auto-promoted.
- Validly signed rollback sequence and wrong-parent lineage are rejected.
- Payload, embedded-registry, signature, trust-anchor and no-overwrite tamper cases fail closed.

## Validation

- Windows combined P02 suite: `61/61` passed.
- Official Python 3.13.13 Linux image `sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286`, read-only source: `61/61` passed.
- Current repository FULL bootstrap: `5/5` lanes passed.
- Clean clone at the audited commit: FULL bootstrap `5/5`, post-run Git status changes `0`.
- Ten P02 schemas passed Draft 2020-12 meta-schema validation; new JSON matched Prettier formatting.
- Signed envelope regeneration with the same key and locked inputs was byte-identical twice.
- Existing-envelope publication was rejected with exit `2`; the original envelope hash remained unchanged.
- Secret findings, Rust/Node/.NET vulnerabilities and forbidden licenses: `0`; CycloneDX components: `148`.

The first Linux read-only attempt mounted native dependencies on a non-executable tmpfs and failed before tests. Re-running the identical read-only source lane with executable tmpfs produced the authoritative `61/61 PASS`. The infrastructure failure is not represented as a code-test pass.

## Preserved boundaries

- The source registry and runtime evidence were read and hash-locked; none was rewritten in place.
- Private key, signed registry and raw identifiers remain outside Git. The public key and explicit non-production trust policy are the only trust material committed.
- Routing, production, provider, hosted/VM, redistribution and other Hancom versions remain disabled or deferred.
- This signature is a local-development integrity boundary, not a public release or legal-document signature.

## Next exact task

Start `P03-01 Bounded ZIP reader`: implement a Rust HWPX package reader with archive/entry/uncompressed-size/compression-ratio/name/path/nesting limits and a synthetic malicious-ZIP corpus. Use reasoning effort `max`; no Hancom UI or user document is required.
