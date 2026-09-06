# P17-06 loopback TCP transport v10

Date: 2026-09-06

Scope: current PC, checkpoint-only authenticated transport increment

Decision: **bounded loopback TCP component implemented; durable process/service evidence remains open**

## Implemented boundary

- `remote-sync-wire` owns one binary request/response framing contract with fixed magic, explicit
  status, big-endian lengths and exact authorization/request/response size ceilings.
- `LoopbackTcpTransport` connects only to an exact `127.0.0.1` or `::1` endpoint with a nonzero
  port and a 1 ms through 60 second connect/read/write deadline.
- `LoopbackCheckpointServer` binds only to loopback, accepts one connection at a time, verifies the
  peer is loopback, derives the request ID at the host, and receives the observed time from the
  trusted server caller rather than the public frame.
- Request and response framing reject trailing bytes, malformed status/payload combinations,
  oversized fields and incomplete reads. Uncertain I/O maps to unavailable; definitive framing or
  host denial maps to rejected.
- `SingleUseCredentialProvider` consumes one pre-issued bearer exactly once. Authorization values
  are redacted from `Debug` and zeroized on both accepted and rejected construction paths.

## Verification

- `cargo test -p remote-sync-wire -p local-sync -p remote-sync-host`: PASS.
  - `remote-sync-wire`: 3/3.
  - `local-sync`: 45/45 across unit and integration targets.
  - `remote-sync-host`: 10/10.
- The host suite includes a real OS loopback TCP connection crossing the strict frame, single-use
  credential, authentication, exact mirror/head admission and checkpoint dispatcher. It also proves
  that trailing request bytes are rejected before dispatch.
- `cargo clippy -p remote-sync-wire -p local-sync -p remote-sync-host --all-targets --all-features -- -D warnings`: PASS.
- `cargo fmt --all -- --check` and `git diff --check`: required again with the final successor.

## Evidence boundary

The passing TCP test is process-local component evidence using a test thread, an ephemeral local
HMAC issuer and in-memory service repositories. It does not prove a separately launched daemon,
durable PostgreSQL checkpoint state, persistent credential custody, cross-machine transport, TLS,
pull/push service handling, production readiness, or P17-06 completion. The next increment is a
PostgreSQL-backed checkpoint repository and a separately launched current-PC host/client acceptance
run; credential issuance remains external and must not be replaced by a plaintext token file.
