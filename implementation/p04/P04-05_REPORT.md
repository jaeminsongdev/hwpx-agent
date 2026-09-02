# P04-05 Capability router report

- Generated: 2026-09-02
- Audited source commit: `39ead792ab74c5aaea8d3b88af0c3a1943cb784e`
- State: `pass_current_pc_local_pure_model`
- Reasoning/review mode: `xhigh / evidence, policy, preservation and health routing boundary`

`domain-ir`에 P04-04 `CompiledOperation`과 immutable `RouteContext`를 입력으로 받는 pure
fail-closed capability router를 구현했다. 실행 가능성은 exact target profile, signature-verified
registry snapshot, support state, current-PC policy, preservation impact와 bounded backend health가
동시에 맞을 때만 성립한다. 최고 priority/cost 후보가 둘이면 ID로 임의 선택하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Pure decision boundary | `pass` | graph/filesystem/network/process/COM/HAction/backend execution dependency 0 |
| Exact target | `pass` | typed profile ID + build + x86/x86_64/arm64 architecture equality |
| Registry trust | `pass` | nonzero payload SHA-256/sequence + `signature_verified`; unverified/invalid rejected |
| Support evidence | `pass` | only `verified`; candidate/unavailable/failed/risk-blocked/not-run rejected |
| Current-PC policy | `pass` | production/provider/network/unsafe and unresolved confirmation fail closed |
| Preservation | `pass` | normalized/surgical/exact strength, opaque loss denial and signed-document impact |
| Health snapshot | `pass` | backend ID, nonzero generation, observed time, bounded TTL and explicit state |
| Degraded behavior | `pass` | binding-level explicit opt-in only; unhealthy/unknown/stale never route |
| Deterministic ranking | `pass` | priority descending/cost ascending; equal top returns `ambiguous_route` |
| Backend kinds | `pass` | direct HWPX, hybrid and desktop automation are distinct typed routes |
| Versioned receipt | `pass` | `hwpx-agent.capability-route-decision/v1` canonical JSON/SHA-256 |
| Finite/privacy | `pass` | catalog/health/build/TTL ceilings, duplicate rejection and redacted Debug |

## Validation evidence

- Windows Rust 1.96.0: router `9/9`; combined `domain-ir` `45/45`, doc tests and Clippy
  `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, root/source/registry read-only, Cargo offline and executable tmpfs; router `9/9`,
  combined `45/45` and Clippy passed.
- Routing matrix covers profile/build/architecture and registry drift, all non-verified states,
  policy restrictions, protected/signed documents, preservation strength, health state/generation/
  timestamp/TTL, degraded opt-in, filtered fallback, equal-top ambiguity and input-order equality.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Security: current and clean clone each scanned 537 files; secrets/vulnerabilities/forbidden
  licenses 0; current SBOM 271 and clean-clone SBOM 229 components.
- P04-01~04 regressions remain green on Windows/Linux and in both FULL runs.

## Strict self-review and remediations

- Change risk: `high` because transaction execution will trust the route receipt.
- Raw digest/sequence equality did not itself record signature verification. The immutable context
  now rejects `unverified` and `invalid` registry trust before routing.
- A receipt without a schema tag could drift across transaction versions. The canonical receipt now
  carries exact v1 schema identity.
- Four independent policy booleans were replaced with a sorted typed restriction set, eliminating
  contradictory flag interpretation while keeping multi-restriction bindings deterministic.
- Stable backend ID remains an evaluation-order key only. It cannot break a top priority/cost tie;
  ambiguity is a typed failure.
- Health observations validate generation, future/stale time, TTL overflow/ceiling and explicit
  degraded opt-in. Missing or malformed health cannot trigger a lower-assurance execution path.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04-05 proves pure routing against synthetic compiled operations and typed evidence. It does not
parse the P02 signed registry envelope, execute a route, create a workspace, mutate/publish HWPX,
open Hancom, deserialize a public wire payload or prove any public capability available. The P02
exact-2020 signed registry still has routing enabled 0; this task does not promote candidate evidence.
No user document was opened or modified. Other PCs and Hangul 2022/2024 remain deferred.

## Next exact task

Start `P04-06 Workspace transaction` with reasoning effort `xhigh`. Create an isolated per-job
working copy bound to compiled-plan/route/base-revision hashes, enforce a finite state machine,
stage and validate output before no-overwrite commit, and fault-inject every transition. Any failure
must leave source bytes/revision unchanged; artifact-after-CAS failure must quarantine explicitly.
P04-09 actual Hangul 2020 vertical Gate and the P04 phase Gate remain `max`. No user local operation
is required for the P04-06 core transaction task.
