# P16-06 dedicated plan-review staging host v14

Date: 2026-09-06
Scope: current-PC local staging, licensed Hangul 2020 target profile only

## Boundary

`web/plan-review-staging` exposes one HTTPS MCP endpoint on an ephemeral loopback port. It registers
only `render_plan_review_widget` and `ui://hwpx-agent/plan-review/v1.html`. The immutable P15
18-tool catalog remains outside this server and is checked by its locked SHA-256 before full-stack
acceptance.

The Rust driver is read-only at this boundary. On startup it admits three independent
least-privilege PostgreSQL roles, then a render request performs all of these checks again through
the product repositories:

1. authenticate the bearer for `project.read` and bind its tenant and subject;
2. load the active project head and verified source graph from `LocalPostgresPlanSourceRepository`;
3. load and decrypt the exact unexpired compiled plan from `LocalPostgresStoredPlanRegistry`;
4. load and decrypt the receipt-bound route, semantic diff, dry-run, signature and execution policy
   from `LocalPostgresPlanReviewEvidenceRepository`;
5. let `PlanReviewRenderer` return only the bounded public snapshot.

No document is opened, written or executed by this endpoint. It does not grant a mutation permit.

## Configuration contract

The Node host requires `HWPX_AGENT_ROOT`, an absolute
`HWPX_AGENT_PLAN_REVIEW_DRIVER`, a bounded lifetime, and these driver values:

- identity: `HWPX_AGENT_PLAN_REVIEW_HMAC_KEY_B64`, `..._TENANT_ID`, `..._PROJECT_ID`,
  `..._SUBJECT`;
- database: `..._PG_PORT`, `..._PG_DATABASE` plus distinct `..._SOURCE_PG_*`, `..._PLAN_PG_*`
  and `..._EVIDENCE_PG_*` role credentials;
- encryption: active key reference/key pairs for `..._PLAN_ACTIVE_*` and
  `..._EVIDENCE_ACTIVE_*`; complete optional `..._PREVIOUS_*` pairs allow one-step key rotation.

Keys use unpadded URL-safe base64 and are never written to readiness output or acceptance receipts.
Configuration and backend failures collapse to closed categories. The server passes only an exact
allow-list of variables to the child driver.

`HWPX_AGENT_PLAN_REVIEW_CLOCK_UNIX_SECONDS` exists only for deterministic server-owned acceptance
fixtures. It is not an MCP argument or a client-controlled value, is range bounded, and readiness
labels its use as `server_fixture`. Normal runs omit it and use the server clock.

## Verification boundary

`tools/p16/run_plan_review_staging_checks.py` creates a labeled disposable PostgreSQL 18.4
container and volume on `127.0.0.1`, applies the exact 13 migrations, seeds product-generated graph
identity and encrypted plan/evidence, and drives the pinned MCP Inspector through TLS. It checks
strict tool discovery, exact resource bytes, authorized rendering, foreign-project rejection,
HTTP authentication/origin/host/body limits, database and host restart, ciphertext tamper rejection,
graceful shutdown, secret exclusion and exact owned-resource cleanup.

This local host is the product registration boundary, but it is not evidence that the app has been
installed in an actual Codex/ChatGPT account. Actual account registration, production deployment,
Hangul execution and any later Hangul version remain separate gates.
