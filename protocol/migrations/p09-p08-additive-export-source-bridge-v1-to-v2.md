# Additive-export dependency-source bridge v1 -> v2

Store a separate v2 receipt. Preserve v1's original raw receipt, code, policy,
migration, shared-lib baseline and original test bytes. Live v1 must fail on the
new current lib; v2 records that actual failure and independently verifies the
exact two-span successor projection and unchanged predecessor implementation.

The current bridge test becomes an explicit v1/v2 lineage test, with old pure
projection cases executed on the pinned archived v1 lib rather than a fabricated
current source. No old source/target receipt is updated, normalized or relabeled.
Every claim field is explicit. Missing prerequisites, extra errors, weakened
checks, code/contract drift, duplicate spans or unknown byte changes fail closed.
No schema default implies target, routing, render, green or product success.
