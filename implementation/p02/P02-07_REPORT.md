# P02-07 Target Automation Binding Model Report

- Completed: 2026-09-02
- Audited source commit: `01deaf67f6f8f2ca8999ca3530defda02f8f709b`
- Task state: `pass_current_pc_local`
- Review: `STRICT / xhigh`, blocker/major/minor `0/0/0`

## Delivered

- Draft 2020-12 `AutomationBindingRegistryV1` for exact target identity, invocation, Action/ParameterSet candidate, source references, probe placeholders, availability reason, routing state and complete coverage.
- Additive protocol catalog v3 plus Rust/TypeScript generated models and an explicit v2-to-v3 migration note. Catalog v2 remains byte-identical.
- A source-locked generator and an independent verifier that pin the reviewed catalog, 609-row canonical matrix, Automation SourceRecords and exact target profile before producing a registry.
- Every `AUTOMATION_FULL` and `HYBRID` capability is represented exactly once. A reviewed ActionTable mapping becomes `candidate_unverified`; otherwise the capability becomes `unavailable_with_reason=no_reviewed_action_mapping` without inventing an identifier.
- Documented ParameterSet signals are retained as candidates. Source-authored `-` becomes an explicit no-ParameterSet state; parameter maps remain empty and pending runtime probe.
- Raw identifiers exist only inside the restricted private registry. CLI receipts and verifier output expose only identities, counts and SHA-256 values.
- Every binding has `runtime_support_state=unverified`, a `not_run` probe, `routing_enabled=false`, unknown modal/external-side-effect risk and no runtime-qualified claim.
- Restricted derivative confinement, atomic no-overwrite publication, traversal/symlink checks and input-change detection cover all locked inputs.

## Exact current-PC target

- Profile: `hancom-hangul-2020-secondary` (stable historical ID; current role is primary development).
- Product/build/locale/architecture: Hancom Hangul 2020 / `11.0.0.9136` / `ko-KR` / x86.
- Target profile SHA-256: `538b7b2eb953ea81d95b30f46479e81983d309277f6d16ca6e6f8d0a24d48af2`.
- The profile permits bounded personal noncommercial local validation, keeps production disabled and does not enable a production desktop-automation route. P02-07 therefore emits candidates but cannot enable routing.

## Actual locked registry

| Metric | Count |
|---|---:|
| required automation capabilities | 536 |
| `AUTOMATION_FULL` | 191 |
| `HYBRID` | 345 |
| candidate, unverified | 32 |
| unavailable with concrete reason | 504 |
| documented ParameterSet candidate | 19 |
| source declares no ParameterSet | 13 |
| missing/duplicate capability | 0 |
| runtime-qualified binding | 0 |
| routing-enabled binding | 0 |

- Reviewed catalog input SHA-256: `88b4c5238c1911ae4cd3f40874a0328401a12dda9b57f51d2e1c5663834d5609`.
- Automation SourceRecords SHA-256: `03db035d408d03ce3f78d4eca8ca76d7f9e8076ef8fadd49d8f3ed4b885317b5`.
- Canonical matrix SHA-256: `695122da1bc8769f1f72ba23842036c94a152063fcd8c579f692dff8967d050d`.
- Private registry: 541,281 bytes, SHA-256 `986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48`.
- Three no-overwrite emissions, including one from committed source, were byte-identical.
- Independent actual-output verification: errors 0; binding coverage 536/536; candidate 32; unavailable 504; runtime/routing 0; raw identifier values in receipt false.

The authoritative artifact remains local at [private exact-2020 binding registry](evidence/bindings/automation-bindings.2020.v1.final.json) and is Git-ignored.

## Protocol compatibility

- `schema-catalog-v2.json` stays at SHA-256 `21732da04009162452492026198654dd895d2537f69569788e44f8e2323605f5`.
- Additive `schema-catalog-v3.json` is locked at SHA-256 `066c8cca91eb0bcbdf599748015267518945e54fbacaf2381912812be92551a8`.
- Rust and TypeScript generated model drift checks passed; TypeScript typecheck/build/tests passed.

## Validation

- Windows combined P02 suite: 43/43 passed; schema validation, Python compileall, Rust format/clippy/test, codegen drift and Prettier checks passed.
- Official Python 3.13.13 Linux image `sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286`, read-only repository mount: 43/43 passed.
- Current repository FULL bootstrap: 5/5 lanes passed; secret findings, vulnerabilities and forbidden licenses 0; CycloneDX components 147.
- Clean clone `D:\개발데이터\Temp\hwpx-agent-p02-07-clean-01deaf6` at the audited source commit: FULL bootstrap passed and post-run Git status changes 0.
- Negative coverage includes every locked-input hash/identity mismatch, target license/release mismatch, missing/duplicate required capability, reviewed projection drift, missing Action record, malformed ParameterSet signal, control characters, restricted-output escape, runtime/routing promotion, traversal and overwrite.

## Preserved boundaries

- A candidate is documentation provenance, not an executable or supported binding. No Action was invoked and no default ParameterSet was read in P02-07.
- The 504 unavailable entries are honest absence of reviewed binding evidence, not permanent product-unsupported claims.
- Raw Action and ParameterSet identifiers are not reproduced in this report, public protocol catalogs, CLI receipts or Git history.
- 한글/COM/UI, user documents and installed Hancom files were not opened or modified.
- 2022/2024, other PCs, production/provider use and redistribution remain outside this task.

## Failed checks retained

No actual generation or validation check failed after the P02-07 contract was fixed. The schema design was tightened before actual publication so synthetic public identifiers and restricted official identifiers keep distinct publication behavior.

## Next exact task

Implement `P02-08 Runtime probe tool` for the exact current-PC 2020 x86/STA target. It must consume the locked binding registry, use only disposable fixtures, capture default ParameterSet and pre/post semantic state, bound modal/process timeouts and preserve all bindings as unverified unless probe evidence passes. Recommended reasoning effort: `max`; P02-09 signing/drift and the P02 final Gate: `max`. User local operation is not required until the probe harness is ready for the real 한글 2020 run.
