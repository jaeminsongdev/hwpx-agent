# P07 Native Equation Engine Gate Report

- Generated: 2026-09-14
- Profile: `hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1`
- Overall state: `pass_scoped_current_pc_hangul_2020_native_equation`
- Contract validators: `10/10 pass`
- Closed tasks: `9/9`
- P08 authorization: `authorized_current_pc_local_only`

P07-01~09 are complete in their declared component or exact-current-target scopes. The phase now
connects bounded LaTeX/MathML/EqEdit input, normalized `MathAst`, native HWPX lowering/readback,
automation insert/edit, exact-sample layout, Tier B corpus, editor smoke and a matched
direct/automation differential. It does not authorize arbitrary-document or production use.

## Gate criteria

| Criterion | State | Evidence boundary |
|---|---|---|
| P07-01 MathAst | `pass` | Finite normalized AST and typed failures; no target claim |
| P07-02 LaTeX adapter | `pass` | Bounded source profile; no full-LaTeX claim |
| P07-03 MathML adapter | `pass` | Namespace-strict finite profile; no arbitrary MathML claim |
| P07-04 EqEdit adapter | `pass` | Exact installed-source profile; no runtime claim |
| P07-05 native equation HWPX | `pass` | Exact current Hangul 2020 direct-lowerer save/reopen/render fixture |
| P07-06 equation automation | `pass` | Exact current target insert/edit/readback; render not claimed by this task |
| P07-07 layout | `pass_exact_samples` | 4 inline + 4 display native/raster/user-attested samples; general estimator inactive |
| P07-08 Tier B corpus | `pass` | 14/14 exact-target save/reopen/native readback; render not claimed by this task |
| P07-09 editor smoke | `pass` | Exact-target edit/save/reopen/readback; visual oracle remains false |
| Direct/automation differential | `pass` | 8/8 semantic/script/layout matches with zero silent fallback |

## P07-07 exact-target decision

The P07-07 run created, reopened and exported four inline plus four display native equations. The
structural raster verifier found zero page-edge contact. The user inspected all eight displayed
original-detail samples and confirmed zero clipping, overlap and silent fallback. The manual review
is bound to the exact plan, target, raster and PNG SHA-256 values as `user_attested`; Computer Use
did not click or type. The bounded lifecycle used three HWP sessions and left zero owned `Hwp.exe`
processes.

The fitted model's maximum extent and baseline errors are 1868 and 105 HWPUNIT, exceeding the locked
150/50 limits. This does not silently weaken the thresholds: only the eight exact reviewed samples
are admitted as `target_readback`. The general estimator remains inactive, and unknown shapes have
no evidence digest and remain provisional with `render_required=true`.

## Direct/automation differential

Eight cases—four inline and four display—match normalized semantic SHA-256, canonical EqEdit script
SHA-256 and layout between the direct component and exact-target automation artifacts. The direct
lowerer performs strict native readback before returning and its exact-target compatibility is bound
separately by the P07-05 current-target evidence. ZIP bytes, object IDs, measured extents and line
caches are normalized non-identities and are not falsely asserted equal.

## Validation boundary

The aggregate validator independently executes all nine task validators plus the differential
validator and rejects source drift, result mismatch, missing user attestation or premature phase
promotion. The final validation bundle requires P07 Python tests, focused Rust tests, format,
Clippy `-D warnings`, PowerShell parser checks, qualification oracle replay, `git diff --check` and
zero residual HWP processes.

## Scope and residual risks

- The PASS applies only to licensed Hangul 2020 `11.0.0.9136` x86 on this PC for bounded local
  development fixtures.
- The verified general layout estimator is inactive; unknown equation shapes require render.
- P07-06 and P07-08 do not independently claim render, and P07-09 does not claim a visual oracle.
- Arbitrary equations/documents, user-document editing, Hangul 2022/2024, other PCs, production,
  distribution and whole-product completion remain unqualified.
- Failed predecessor attempts remain failures and private evidence remains untracked.

## Phase decision

P07 is complete for the scoped current-PC Hangul 2020 native-equation boundary. P08 authorization is
limited to the same current-PC local-development scope. No production or whole-product authorization
is implied.

## Next exact task

Rebaseline P08 from its live WBS, current contracts and matrix evidence, then implement the first
dependency-ready open P08 work package without promoting existing component evidence to target PASS.
