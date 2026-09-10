# P17 durable Git mirror push current-PC qualification v15

Date: 2026-09-10
Source base: `2b0a74e68107931fce9a2a2f6985f5b081ad078f`
Decision: **current-PC durable push/recovery component PASS; P17-06 remains open**

The qualification binds the exact 27-check receipt from run
`9b3ff9b352ec402aab20f1c5a387a8ec` to migration 16, the authenticated loopback
host/client, the PostgreSQL coordinator, the local bare-Git effect host, the fixture, the harness,
the private contract, the current PostgreSQL image digest and every admitted migration digest.
The runtime and guard source lists are complete, bounded and digest-locked to the source base or
this qualification snapshot as appropriate.

The earned evidence is limited to this PC: PostgreSQL 18.4 in a disposable loopback container,
one generated local SHA-1 bare repository and authenticated loopback processes. It covers verified
artifact ACL admission, durable plan-before-effect, lease/fencing recovery, exact replay, branch
reservation, committed-effect recovery, divergence preservation, rollback safety, metadata and
privilege drift rejection, and owned resource cleanup. No secret or authorization value is retained.

The evidence does not cover a remote Git service or network, durable pull, persistent credential
custody, registered application lifecycle, Hangul execution or production. It does not close
P17-06 or the product. Those fields remain false in both qualification projections and validators.
