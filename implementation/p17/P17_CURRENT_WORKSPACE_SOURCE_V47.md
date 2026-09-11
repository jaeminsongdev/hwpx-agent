# P17 current workspace source qualification v47

Date: 2026-09-11

Decision: **exact committed credential broker source qualification PASS; P17-06 remains open**

Base commit `27406fa409c99ecb5435d4373ae49ee4bae7d5ae` contains the distinct issuer wire,
recoverable credential broker, lifecycle validation extension, pinned TLS 1.3 issuer transport,
Windows Credential Manager vault, private contract, migration, validators, tests and preserved v1/v2
current-PC evidence. The clean source runner passed eleven checks and emitted receipt run
`c5cf7a8fe7414221a625c79e50cb0228` with 28 exact successor records, 30 Cargo workspace members and
the new locked/offline Cargo metadata projection.

The v47 contract composes immutable frozen v46, 22 exact implementation sources, five runtime
qualification sources and three qualification guards. Runtime verification rechecks all four pure
lifecycle operations, ordered append-only pending/prepared/stable recovery, canonical request-bound
issuer responses, no-overwrite publication, exact vault reconciliation, TLS identity/pin failures,
Windows issue/write/read/revoke/delete and every explicit nonclaim. The v2 execution preserves and
SHA-binds v1 and was rerun after the final store-history hardening.

The actual issuer remains synthetic, ephemeral and loopback-only. Client-assertion
signature/freshness, an independently controlled external issuer, external network, real service
credential, cross-system atomicity, Windows power-loss durability, actual Windows refresh/rotate,
registered host, production, P17-06 completion, Hangul, different PC/version and product completion
remain unverified and false. A following immutable verifier must bind the exact qualification commit
before these mutable qualification files stop being authoritative.
