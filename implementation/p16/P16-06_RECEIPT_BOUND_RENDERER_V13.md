# P16-06 receipt-bound plan-review renderer v13

- Date: 2026-09-06; scope: current-PC source implementation and synthetic in-process evidence.
- Decision: authenticated stored-plan-to-snapshot binder PASS; durable evidence repository,
  registered endpoint and P16-06 remain open.
- Predecessor: encrypted durable compiled-plan store v12 at `5b112e5`.
- Review risk: HIGH / STRICT; recommended reasoning `max`.

`mcp-control-plane::PlanReviewRenderer` now performs the read-only server binding that was missing
between the short-lived compiled-plan registry and the existing plan-review widget contract. It
first authenticates `project.read`, checks current project/source ACL, exact owner, expiry, source
revision and source graph through either the volatile or PostgreSQL plan store. Only after that
boundary succeeds may an authoritative evidence repository see the exact tenant, subject, project,
compiled plan and plan digest. Public input remains the existing strict six-field request.

The renderer accepts only typed per-operation `RouteDecision` receipts and binds their ordered
digests to the compiled-plan digest and exact current target: profile
`hancom-hangul-2020-secondary`, build `11.0.0.9136`, x86. Missing, duplicate, reordered,
mixed-registry or mixed-backend receipts fail closed. The public projection remains content-free
and uses only the widget's closed `direct_hwpx`, `hancom_2020` or `hybrid` values.

Dry-run, semantic diff, signature and execution-policy receipts are mutually bound by source/result
graph, plan, route-set and receipt digests. The policy receipt additionally binds tenant, caller and
project. `execution_allowed` can be true only for a verified dry run, no signature impact, no
blocking warning and an affirmative server policy receipt. A client cannot submit any of these
security facts. Warning codes, routes, diff categories and totals have hard limits and closed
grammars; debug output omits bearer tokens, identities, plan arguments and document content.

## Verification

- `cargo test -p mcp-control-plane --test plan_review_renderer`: 8/8 PASS. This covers exact output,
  authentication and strict-input ordering, live source ACL, all execution guards, cross-plan
  evidence rejection, exact 2020 build/architecture, route ordering, warning bounds and redaction.
- `cargo clippy -p mcp-control-plane --all-targets -- -D warnings`: PASS.
- `cargo test -p mcp-control-plane --all-targets`: 89/89 PASS.
- `python tools/p16/run_plan_review_checks.py`: widget 126/126, response-contract 1/1,
  plan-review policy 16/16, deterministic build and five-call local E2E PASS.
- `cargo test --workspace --all-targets`: PASS.
- `cargo clippy --workspace --all-targets -- -D warnings`: PASS.
- P01 CI: `linux-core`, `windows-worker`, `widget` and `security` PASS. The first Windows run
  lacked ignored current-PC evidence in this worktree; exact hash-matching copies from the preserved
  root were placed under the ignored evidence path and the full Windows lane then passed. `docs`
  remains FAIL because the immutable P14 artifact contract pins an older
  `mcp-control-plane/src/lib.rs` digest. That predecessor lock was not rewritten or weakened.

Review caught and corrected two contract defects before acceptance: the desktop backend initially
serialized as `hancom2020` instead of `hancom_2020`, and route receipts initially proved only the
profile identifier rather than the exact build and architecture. Tests now lock both corrections.

No Hangul process, COM operation, user document, external account, registered ChatGPT/Codex host,
real dry-run executor or durable route/diff/signature receipt repository was used. This source
increment does not authorize document execution and is not an actual registered-host PASS. Next,
persist and load the exact evidence bundle from a tenant-isolated authoritative repository, then
wire this renderer into the dedicated `render_plan_review_widget` server registration boundary.
