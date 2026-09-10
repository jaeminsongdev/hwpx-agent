# P17 remote TLS license admission v1 migration

## Change

`deny.toml` keeps ISC out of the global license allowlist and admits it only for the three exact
locked packages introduced by the certificate-pinned rustls transport:

- `ring@0.17.14`
- `rustls-webpki@0.103.15`
- `untrusted@0.9.0`

The validator binds each Cargo.lock checksum, Cargo metadata license expression and current-PC
package license-file digest. A name-only exception, another version, another license, a global ISC
allowance or any additional exception fails closed.

## Compatibility

No runtime protocol, persisted record, credential or network behavior changes. The migration only
admits the exact locked dependency graph to the existing cargo-deny license policy. Cargo advisory,
ban and source checks remain enabled and `cargo deny --frozen check all` must pass as one command.

## Rollback and upgrade

Remove an exception when its exact package leaves Cargo.lock. Any version upgrade requires a new
review of the resolved license expression and package license file, a new exact-version exception,
and a successor contract. Do not replace the exceptions with a global `ISC` allowance.

This component decision does not verify an external endpoint, real certificate or credential,
issuance/rotation, production, P17-06 completion or product completion.
