# P10-06 signed binding executor core report

- Generated: 2026-09-04
- Implementation commits: `3281693`, `2f92654`
- State: `builder_pass_actual_executor_pending_p10_05`
- Reasoning/review mode: `max` / STRICT signature, target binding, typed dispatch and replay audit

P10-06 now implements a fail-closed Ed25519-signed binding envelope and exact-target payload for the
P10 Windows worker. Public plans carry semantic capability IDs only. Raw Hancom action,
ParameterSet and item identifiers remain inside a private signed bundle and are never accepted from
the public request surface.

## Core acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Signed immutable bundle | pass_component | canonical payload digest and Ed25519 signature are checked before deserialization/use |
| Exact target/capability binding | pass_component | build, architecture, executable, capability registry, plan/artifact and lease identities must all match |
| Finite typed parameters | pass_component | text, bool, int32, enum and rational values are bounded and validated before COM dispatch |
| Unknown/raw rejection | pass_component | unknown fields, duplicate JSON keys, raw action inputs, extra/missing parameters and target drift reject before COM |
| Replay/fencing boundary | pass_component | Agent admits fixed read-only plan/bundle/key files and a single-use security lease |
| COM result handling | pass_component | `Run`, action creation, ParameterSet binding and execution require exact successful return types/results |
| Trusted offline builder | pass_current_pc | exact signed P02 evidence projects into a separately signed P10 bundle with redacted receipt |
| Actual signed target action | pending | signed bundle exists; production Agent/Worker execution still requires the P10-05 registered module |

## Validation evidence

- Binding smoke passed `14/14` under both x64 and the installed x86 .NET runtime.
- Windows Agent smoke passed `13/13`; the post-implementation lifecycle regression passed `10/10`.
- Binding static checks passed `35/35`. Both Draft 2020-12 schemas are meta-valid; two valid schema
  cases and all six negative cases passed.
- Builder tests passed `11/11`, Ruff checks passed and the expanded static suite passed `41/41`.
- The policy-enforced actual bundle contains only the two runtime-verified parameterless P02
  canaries. Independent reconstruction and signature verification passed; no-overwrite replay left
  the envelope and receipt unchanged.
- Current checkout and exact commit `2f92654` clean checkout passed all `5/5` bootstrap lanes; the
  clean checkout remained Git-clean.
- Security checks reported no failed checks or vulnerable dependency finding. The current checkout
  SBOM contained 612 components and the exact-clean checkout SBOM contained 407 components.
- STRICT review fixed non-boolean `Open` acceptance and a duplicate-JSON failure disposal leak before
  this report. Final blocker/major/minor findings for the bounded core scope are `0/0/0`.
- Schema catalog v2/v3 hashes remain immutable. The additive private P10 schemas are isolated in
  catalog v4 with an explicit migration document.

## Unverified boundary

The actual bundle is derived from the signed current P02 registry, but this evidence does not prove
actual COM action/ParameterSet execution through the production Agent/Worker, a registered P10-05
security module, modal supervision, another PC/version, distribution or production use. Component
and bundle-construction evidence is not promoted to those claims, so the P10-06 roadmap checkbox
remains open.

## Next exact task

Complete the P10-05 actual security-module dependency before running this bundle through the
production executor on the exact current target. P10-07 event/modal watchdog core work may proceed
independently. Continue at reasoning effort `max`.
