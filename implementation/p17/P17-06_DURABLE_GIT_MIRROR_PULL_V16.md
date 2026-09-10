# P17-06 durable Git mirror pull v16

Date: 2026-09-11
Decision: **current-PC durable pull/replay component PASS; P17-06 remains open**

The private pull request is now `hwpx-agent.remote-sync-request/v4`; only pull changes. It binds the
client's exact `observed_snapshot_sha256` beside the observed revision and generation. Push and
checkpoint remain v3. The host authenticates one `mirror.sync` service credential, requires
canonical bytes, derives the observation identity, reads one derived reference from an explicit
local bare repository without mutation, and reconciles through PostgreSQL migration 17.

Migration 17 stores the observed snapshot independently from local ahead/conflict payload, verifies
the remote revision's available/verified result artifact and current ACL, requires an exact revision
chain and Git/database observation, and records one immutable terminal observation. Clean advance,
ahead conflict, unchanged state and exact replay are separate results. Conflict preserves the local
snapshot and pending plan. Git/database drift returns unavailable without another observation or
local state mutation. The application role has only the reconciliation function, not direct table
mutation; RLS, immutable triggers, fixed search path and revoked public execute are admission checks.

The authoritative local run is `4162580f49da402983be6a8527e9721e`, receipt SHA-256
`059ec3ebbf1f871af86b7df84fc38a878bb2ca52fb68f3074b6b419668f390a5`. All 20 checks passed against
the pinned PostgreSQL 18.4 image and an owned local SHA-1 bare repository. The receipt was written
only after owned container/volume cleanup and binds the harness, pinned-image contract, migrations,
Rust sources, probes and fixtures. It records three immutable observations, one durable conflict,
exact updated/conflict replay, local conflict preservation and a bounded final-state digest without
retaining passwords, authorization headers or local paths.

Earlier no-receipt run directories and earlier successful receipts remain preserved and are not
rewritten or promoted as this qualification. One post-hardening run exposed a three-second seed
push lease boundary; pull's seed-only push now uses a bounded 30-second lease, and two subsequent
hardened runs passed before the final self-bound run.

This is current-PC component evidence only. It does not exercise a remote Git network or service,
persistent credential custody, a registered host, production authentication, Hangul, P17-06
completion or product completion. Those claims remain false in the contract, receipt and validator.
