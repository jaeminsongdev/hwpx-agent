# P17 current workspace source qualification v45

Date: 2026-09-11

Decision: **exact committed TLS dependency license-admission source qualification PASS; P17-06 remains open**

Base commit `f7020352482115270c466ce4c228265daad39784` contains the exact-version ISC
exceptions, private contract, migration, validator, five tamper/current tests, current-PC package
license-file evidence and bounded PLANS entry. The source runner passed eleven checks against that
clean commit and emitted receipt run `4f667761e3a1460585ed4329f6b1354e` with 28 exact successor
records and the unchanged 27-member Cargo workspace projection.

The v45 contract composes immutable frozen v44, eight implementation sources, two runtime-policy
sources and three qualification guards. Its runtime check revalidates Cargo.lock checksums, Cargo
metadata license expressions, local registry LICENSE file digests and all cargo-deny checks. ISC is
not in the global allowlist and no dependency version other than the three reviewed versions is
admitted.

This source qualification does not establish an external remote network, real certificate or
credential, issuance/refresh/rotation, registered host, production, P17-06 completion, Hangul, a
different PC/version or product completion. A following immutable verifier must bind the exact
qualification commit before mutable worktree files stop being authoritative.
