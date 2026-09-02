# P04-07 Semantic diff report

- Generated: 2026-09-02
- Audited source commit: `3744a980106f1528c26d5616741ca997c1c595f9`
- State: `pass_current_pc_local_pure_model`
- Reasoning/review mode: `xhigh / identity, ordering, privacy and opaque-change boundary`

`domain-ir`에 두 validated DocumentGraph v2 snapshot을 revision과 canonical digest로 고정해
비교하는 pure semantic diff를 구현했다. 결과는 raw 본문/속성/ID 대신 typed category/path,
domain-separated subject/value SHA-256와 reference-impact count만 포함한다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Snapshot trust | `pass` | exact document/revision/canonical graph digest validation |
| Node changes | `pass` | stable-ID added/removed/modified/moved/modified-and-moved |
| Structural movement | `pass` | parent/scope/depth plus relative order among common stable siblings |
| Style/resource | `pass` | independent content delta and before/after reference-impact count |
| Table | `pass` | table grid/properties, cell row/column/span/properties and nested cell flow |
| Equation | `pass` | source kind/content, display and properties in dedicated category |
| Object | `pass` | drawing/chart/field/form/break/embedded resource and property signatures |
| Reference | `pass` | note/reference/review subjects and nested note flow |
| Unknown/opaque | `pass` | arbitrary property and opaque preservation digest/size changes stay visible |
| Privacy | `pass` | raw document values, logical/revision IDs absent from receipt/Debug/error |
| Determinism | `pass` | canonical sorted v1 output and Windows/Linux golden SHA-256 equality |
| Finite behavior | `pass` | entity/change/depth/serialized-size ceilings and no partial diff |

## Validation evidence

- Windows Rust 1.96.0: semantic diff `10/10`; combined `domain-ir` `55/55`, doc tests and
  Clippy `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, repository/registry read-only, Cargo offline and executable tmpfs; semantic diff
  `10/10`, combined `domain-ir` `55/55` and Clippy passed.
- Canonical comprehensive golden SHA-256:
  `b12f8a542b42286470f981daff8de67ed352c5715742eec1c2fce4d892749f7e` on both OSes.
- Corpus covers all 9 categories, add/remove/modify/move/inverse, nested table/drawing/note paths,
  catalog order normalization, insertion shift, unknown/opaque visibility, identity/digest/revision
  conflicts, all finite limits and raw-value privacy sentinels.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Security: current and clean clone each scanned 551 files; secrets/vulnerabilities/forbidden
  licenses 0; current SBOM 272 and clean-clone SBOM 230 components.
- P03 and P04-01~06 regressions remain green in both FULL runs.

## Strict self-review and remediations

- Change risk: `high` because later conflict/revision UI will trust this classification.
- Initial implementation treated every ordinal shift after insertion/removal as a move. Movement now
  compares relative order only among common stable siblings, so unchanged shifted siblings are not
  over-reported while real reorder and parent changes remain visible.
- Specialized table/equation/object subjects no longer duplicate an outer-node ordinal move; their
  own structural parent or semantic value must change. The outer stable node records flow movement.
- Resource reference-impact counts avoid double-counting a specialized resource already present in
  the node's common resource set.
- Two production functions exceeded strict review length. They were split by document/catalog/flow
  and table/equation/drawing/leaf-object responsibility; no lint exception was added.
- Remove/add pairs remain separate and are never guessed to be rename/move. Same revision with
  different graph digest fails before any change list is returned.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04-07 compares semantics represented in synthetic DocumentGraph v2 values. It does not prove that
an HWPX lifter captured every Hancom semantic, that formula strings are mathematically equivalent,
or that geometry changes have visual parity. The SHA-256 references deliberately make raw values
absent but are not an encryption claim. No user document was opened or modified and no Hancom
process was run. Other PCs and Hangul 2022/2024 remain deferred.

## Next exact task

Start `P04-08 Idempotency·CAS` with reasoning effort `xhigh`. Bind a finite idempotency key to exact
request/manifest/expected-revision hashes, allow one owner/fencing generation, replay an identical
terminal result, reject key reuse with different bytes and make stale-head CAS side-effect-free.
Explicitly separate in-progress, terminal and outcome-unknown reconciliation; prove concurrent
duplicates and retries cannot create a second artifact/revision. P04-09 actual Hangul 2020 vertical
Gate and the P04 phase Gate remain `max`. No user local operation is required for P04-08.
