# P17 current workspace source qualification v46

Date: 2026-09-11

Decision: **exact committed remote credential lifecycle source qualification PASS; P17-06 remains open**

Base commit `a13ec5ca0e21c64f4d84ac734ad601252fb21074` contains the complete pure lifecycle
crate, private contract, migration, validator, six contract/tamper tests, fifteen Rust tests, direct
current-PC component evidence and bounded PLANS entry. The clean source runner passed eleven checks
and emitted receipt run `bc1bdc271d4b464db1c9cbc0a1da0d46` with 28 exact successor records,
28 Cargo workspace members and the new locked/offline Cargo metadata projection.

The v46 contract composes immutable frozen v45, ten exact implementation sources, two runtime
qualification sources and three qualification guards. Runtime verification rechecks issue, refresh,
rotation and signed terminal revocation; canonical request/pending/JWS handling; complete policy and
prior-state binding; exact claim, generation, time, retry and replay rules; zeroizing secret custody;
and all explicit component nonclaims.

The ephemeral test issuer and generated signing keys are synthetic. No external issuer or network,
real service credential, atomic Windows vault/state broker, registered host, production, P17-06
completion, Hangul, different PC/version or product completion is established. A following
immutable verifier must bind the exact qualification commit before mutable files stop being
authoritative.
