# P17 current workspace source v47 to frozen v1

The mutable v47 source qualification is retired in favor of
`hwpx-agent.p17-frozen-current-source-v47-verification/v1`. The replacement accepts only the exact
implementation and qualification commits, frozen v46 predecessor, credential broker contract,
preserved current-PC Windows evidence and receipts, and bounded Git blobs with pinned byte lengths
and SHA-256 digests.

No phase or product claim is added. The issuer and signing keys remain synthetic; client-assertion
signature/freshness, an external issuer/network, real credential, cross-system atomicity, Windows
power-loss durability, actual Windows refresh/rotate, registered-host operation, production, Hangul,
other PC/version, `P17-06`, and product completion remain false.
