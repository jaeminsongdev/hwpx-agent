# P17-06 remote TLS dependency license admission v20

Date: 2026-09-11

Decision: **exact locked dependency license-policy component PASS; P17-06 remains open**

The certificate-pinned TLS transport added an ISC-licensed portion to three transitive packages.
The project-wide license allowlist was not widened. `deny.toml` instead admits `ISC` only for
`ring@0.17.14`, `rustls-webpki@0.103.15` and `untrusted@0.9.0`. Package name and version must both
match, so a dependency upgrade does not inherit this decision.

The private contract and validator bind the exact exception set, unchanged global allowlist,
Cargo.lock versions, registry sources and checksums, Cargo metadata license expressions, and the
current-PC package LICENSE file names, byte lengths and SHA-256 digests. They also require advisory,
ban, license and source checks to pass together through `cargo deny --frozen check all`. Tamper tests
reject global ISC admission, name-only or different-version exceptions, additional exceptions,
package/checksum/license-file drift and any product or production claim promotion.

Current-PC evidence records all four cargo-deny checks passing. The reviewed package license files
remain in Cargo's local registry cache; their absolute local paths and contents are not copied into
the repository or evidence. This is a narrowly scoped dependency-policy qualification, not legal
advice and not a remote-service runtime qualification.

No external endpoint, real service certificate, real service credential, issuance/refresh/rotation,
registered-host lifecycle, production network, P17-06 completion or product completion is claimed.
