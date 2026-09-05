# P16-06 authenticated compiler-plan registry — implementation checkpoint

- Scope: current-PC local server component; no Hangul launch, COM or document write.
- Risk/review: HIGH / STRICT. P16-06 remains in progress; not an implementation closure.
- Parent: `477d4023d6e29c944d08fb81b9193d0fe3010276`; main integration remains pending.

## What is implemented

`mcp-control-plane::StoredPlanRegistry` retains actual immutable `CompiledOperationPlan` instances,
not JSON fixtures or a client claim that a plan compiled. Its lookup returns a non-serializable
internal read receipt containing that exact plan and its canonical digest. It does not return a
widget snapshot, execute a plan, validate a route or grant permission for a later write.

The existing app remains interactive-decoupled: Rust service authority and a separate bounded web
view. Per-invocation authentication follows the official [MCP server guidance](https://developers.openai.com/plugins/build/mcp-server)
and [authentication guidance](https://developers.openai.com/plugins/build/auth); tool annotations or
widget state are not authorization. The local HMAC development verifier is not a production IdP.

Admission re-authenticates `project.write`, checks project write membership, reads the current
source through the repository ACL, and compares tenant/project/revision/graph identity with the
compiler receipt. Plan owner and tenant come exclusively from verified `AuthContext`.
Lookup re-authenticates `project.read`, strictly validates the existing six-field renderer request,
re-checks current project membership and stored-plan ownership, and re-reads the current source.
Changing either the revision or graph content fails, even if the other identity remains unchanged.
Unknown/cross-tenant/non-owner lookups do not reveal plan contents or query the source repository.

`ProjectPolicy` factors existing project membership logic out of `ToolPolicy` without changing the
public 18-tool catalog. The renderer no longer needs to impersonate an unrelated public tool just
to check project access. `CompiledOperationPlan::base_graph_sha256` exposes the immutable compiler
binding; canonical plan serialization is unchanged. The only dependency change is a local path edge
from `mcp-control-plane` to existing `domain-ir`; no new third-party package/version is added.

## Bounds and non-authority

- At most 256 entries, 1 MiB canonical bytes per plan, 16 MiB aggregate canonical plan bytes.
  These are admission budgets, not an exact heap-allocation bound. Overflow fails without eviction.
- Records expire after at most 900 seconds and no later than the original token's exact expiry.
  Clock skew is not permission to extend a review receipt. The registry remembers the maximum
  observed server time; a rollback fails before lookup or insertion, so expiry cannot be undone.
- No overwrite, ID reuse, eviction, refresh or lifetime extension within a registry instance.
  Expired records still consume capacity. A new process/registry has no old plans and must obtain
  fresh authenticated compiler submissions. This is intentionally not durable idempotency.
- Source graphs are streaming-hashed with a 64 MiB bound. Plan admission also streaming-hashes
  before retaining the plan; no additional full canonical plan/graph buffer is allocated here.
- Requests reject duplicate, missing, extra, oversized or malformed fields. Total ID length is
  124, including the five-character plan prefix. Locale/client-surface values are presentation
  inputs only. No warning, route, diff, owner, tenant, time, path or execution flag is accepted.
- The clock is supplied by trusted server code, never JSON arguments. Tokens/raw request buffers
  use `Zeroizing`; Debug and stable errors omit private plan text, IDs, graphs and bearer values.
- Read receipts are internal and request-scoped, not reusable authorization. Fresh checks at the
  eventual write boundary, current revision CAS and durable idempotency remain mandatory.

## Verification so far

New integration tests compile real synthetic graphs/plans through the domain compiler, sign local
disposable tokens through the existing auth middleware, use project membership checks, and exercise
a test source repository returning actual source-graph receipts. They do not prove a production
repository adapter or a registered host. Fourteen target tests pass with no ignored tests.

The first target build exposed a test helper's wrong auth method name; it was corrected to the
existing `revoke_token_id`. Initial Clippy findings were repaired without lint suppression.
STRICT self-review then reproduced an actual clock rollback bug: after expiry, moving the clock
back restored lookup. `before-clock-rollback.log` records failure; the maximum-observed-time guard
and unchanged regression now pass. Earlier successful logs precede that fix and are not final proof.

Final source `python tools/p01/run_ci.py --lane linux-core` passes: workspace formatting,
all-target Clippy, all workspace tests/doc-tests (481 passed) and generated protocol freshness.
This lane ran on Windows; its name alone is not actual Linux evidence. The separate security lane
passes all nine checks, including secret scan, dependency/license checks and a 610-component SBOM.
Duplicate-dependency warnings remain visible, not suppressed.

Logs under `artifacts/p16/stored-plan/` in this worktree:

| Evidence | SHA-256 |
|---|---|
| `before-clock-rollback.log` | `46b2fee11afc51e3c29b8570841c690ee3ae69dad24b3c6e399d9c85ffef811a` |
| `target-after-clock.log` | `f9f4885076312371b859daa0468a5c777be1e1618197bd5e2c2e751b4aa6e21f` |
| `clippy-after-clock.log` | `0da123c3230b03ce431188cf3d66d628150583a6f8f421b8ce8dfa98dc1ba196` |
| `linux-core-ci.log` | `9c3e69ada77117608c4e73e53c7e26a8d874bae92e24a13b7d6ef68a89e4981d` |
| `security-ci.log` | `ee35806d2525952aa97892993903b8e288017dffa7cdd3f35adb0aa68713b0ce` |
| `linux-offline.log` (pre-build failure) | `fcc311c9ca748ae64f1c74bde631750734066cf267073dd406babe10d0d9e569` |
| `linux-offline-retry02.log` (linker failure) | `6a82daba22f1a7d59c168fe0f315f9279ad43850b1f1c2a686f94e83fa87915a` |
| `linux-offline-retry03.log` (PASS) | `0b611f40d3c16645e04e1ad344217f6e5f428cdf17b61afad9cdefc38c6c24d0` |

Security run: `implementation/p01/evidence/security-runs/089ef37892c2497688f7e874e6294e3e/report.json`.
Actual offline Linux target tests/Clippy pass in `linux-offline-retry03.log`: 157 tests across auth,
domain and MCP control plane, followed by all-target Clippy for the two changed packages. Session
7210 is terminal exit 0; all temporary containers were removed and no matching container remains.
The first attempt stopped before compilation when rustup tried updating its read-only toolchain.
Retry 02 selected the already installed exact `1.96.0-x86_64-unknown-linux-gnu` toolchain, but the
linker terminated with signal 7 (Bus error) under the 2 GiB memory / 1.5 GiB tmpfs budget. This is
not a uniquely confirmed cause. Retry 03 keeps the same source, compiler and tests, uses 4 GiB memory /
3 GiB build tmpfs, and records filesystem usage at each terminal build stage. No debug/test profile,
assertion or check is disabled. The successful run used 1.7 GiB after tests and 1.9 GiB after Clippy,
above the original tmpfs capacity, consistent with a constrained-build-space problem. Logs of both
failures are retained; neither is a test PASS. Source and Cargo registry were read-only, network
disabled, container root read-only, all capabilities dropped and no-new-privileges enabled. The
exact pre-existing image is `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`;
compiler `rustc 1.96.0 (ac68faa20 2026-05-25)`. No host settings or installed packages were changed.

## Explicit remaining work and review verdict

REQUEST_CHANGES at card level. This is a process-local registry, not encrypted durable storage.
`PlanSourceRepository` currently has a test adapter only; the repository must provide authoritative
current sealed source/branch ACL reads before wiring the renderer. The staging gateway remains
fixture-driven and no new MCP tool/HTTP route is registered by this change.

Next implement the durable source/plan adapter and connect the actual renderer to this lookup.
Then bind exact execution/preview receipts to the compiled-plan digest, source and result before
combining semantic diff with route/risk/signature/dry-run facts. Merely sharing a before-graph hash
does not prove an unrelated after-graph/diff was produced by this plan. Do not manufacture zero diff,
unsupported routes or verified state to fill a response schema while evidence is absent.

P15 catalog digest `94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001` and P16-05
contract digest `227be012d78ad9d055f85873096d4a3c3e3faebfde3e3de6f97d2efe8fc81e48` are unchanged.
The previously recorded three P16 formal-suite failures for `policy.visual.preview_digest` remain
open, not skipped or reclassified. The current direct formal validator was rerun and fails on the
same preview digest (`artifacts/p16/stored-plan/formal-pending.log`); the 93-test suite was not rerun
in this registry increment. New current/independent FULL, updated formal P16 evidence,
registered-host E2E and actual document execution remain separate gates. Next reasoning: `max`.
