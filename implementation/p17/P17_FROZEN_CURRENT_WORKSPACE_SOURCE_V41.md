# P17 frozen current workspace source qualification v41

Date: 2026-09-10

Decision: **immutable durable-push source/runtime chain PASS; P17-06 remains open**

The v41 verifier first verifies frozen v40 and the independent frozen v15 durable-push runtime
qualification. It then reads the exact v41 contract, current projection and current-source receipt
from qualification commit `162c143d6942a8d648dc25e8986122a61813b8d4`, validates twenty
implementation sources against commit `2b0a74e68107931fce9a2a2f6985f5b081ad078f`, and validates
six runtime-qualification plus three guard sources against the qualification commit.

All twenty-eight successor blobs are checked at the base commit; the sole intentional overlap is
the artifact PostgreSQL repository. The committed source receipt is verified byte-for-byte. No
mutable qualification generator or working-tree product source is authoritative in this path.

This chain earns only the current-PC PostgreSQL 18.4, disposable local bare-Git push,
authenticated-loopback, recovery and divergence-preservation claims already established by the
frozen runtime verifier. Durable pull, a remote Git network, persistent credential custody,
registered host, production, P17-06 and product completion remain false.
