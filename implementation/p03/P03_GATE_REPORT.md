# P03 HWPX Package and Preserving XML Core Gate Report

- Generated: 2026-09-02
- Audited source commit: `d5ff13547976d55204f63a030f07f7a628afb605`
- Audit mode: `STRICT / max`
- Overall state: `pass_scoped_current_pc_local`
- P04 authorization: `authorized_current_pc_local_only`
- P10 technical prerequisite: `satisfied_by_P03_current_pc_local_only`

P03-01~09를 현재 PC 로컬 범위에서 구현하고 재현했다. untrusted HWPX를 bounded ZIP으로 받아 closed graph, safe/preserving XML, preservation map, typed ID/reference, checked patch transaction, deterministic writer와 round-trip evidence까지 연결했다. 실제 current 한글 2020 evidence는 승인된 disposable synthetic output의 read-only open/readback에 한정한다.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P03-01 bounded ZIP | `pass` | malicious ZIP 8/8, strict path/collision/header/CRC/nesting limits | ZIP64/encryption/unsupported methods remain rejected |
| P03-02 PackageGraph | `pass` | closed mimetype/container/manifest/spine/relationship graph 8/8 | Unknown graph forms fail closed |
| P03-03 safe XML | `pass` | XML 1.0 UTF-8, namespace resolution, DTD/entity/PI/CDATA and finite-limit rejection | Legacy encodings are unsupported |
| P03-04 preserving XML | `pass` | checked byte spans, token/tree index, untouched parse identity | Semantic editing uses typed intents only |
| P03-05 preservation map | `pass` | evidence-ranked byte/token/semantic/opaque/rejected classification | Opaque is never promoted to editable |
| P03-06 ID/reference | `pass` | duplicate/dangling/wrong-type fail closed, actual fixture 2/2 with 73 declarations/184 references | Profile is current-2020 core v1 |
| P03-07 patch engine | `pass` | 8 typed intents, conflict/rollback/order/allocation/closure tests, actual in-memory mutation 2/2 | Higher-level transactions are P04 |
| P03-08 atomic writer | `pass` | explicit preserving/normalized modes, bounded build, staged/full reopen, atomic no-overwrite, absent-or-complete faults | OS power-loss durability is not claimed |
| P03-09 round-trip/repair | `pass` | 128 valid + 256 negative replays, untouched 0, two sanitizer targets, exact 2020 output oracle 4/4 | Repair is diagnostic-only |
| Common phase constraints | `pass` | versioned policies/migrations and negative tests, unexecuted states preserved, source in-place writes 0, failure fixtures/handoff recorded | Other versions and production remain deferred |

## End-to-end evidence chain

```text
explicit HWPX bytes
  -> bounded ZIP admission
  -> closed PackageGraph
  -> safe/preserving XML + PreservationReport
  -> typed IdIndex
  -> checked no-op or allowlisted PatchIntent transaction
  -> preserving or normalized deterministic writer
  -> staged and published full reopen
  -> RoundTripEvidence / non-mutating RepairDiagnostic
  -> exact Hancom 2020 read-only open and semantic readback
```

## Validation summary

- Windows and offline read-only Linux `hwpx-package`: `48/48` passed; Clippy `-D warnings` passed.
- Deterministic valid corpus: 128; mutation replay: 128; truncation replay: 128; partial evidence/output 0.
- Cross-platform semantic corpus digest: `b0f187093072a78bc50e12de31f6d30c88d679fb35c8a7ab309203937ba06823`.
- Cross-platform writer aggregate: `d5492303a282c3fe4b00b7fa9b0cfd8a8528f7f2b060ffc24b086341e06d0224`.
- ASan fuzz: raw target final exact-commit 1,000 runs (`cov 7599`, artifact 0); structured target 1,000 runs (`cov 7286`, artifact 0).
- Exact current Hancom 2020: four generated outputs `4/4`, preserving/normalized text pair equality `2/2`, timeout/save/input mutation/residual process 0; static script `36/36`.
- Current repository and exact final-commit clean clone FULL bootstrap: each `5/5`; both post-run Git changes 0.
- Current security: 509 files scanned, secrets/vulnerabilities/forbidden licenses 0; SBOM components 271.

## Strict review

- Change risk: `high`; untrusted archive/XML bytes, atomic filesystem publication, exact desktop runtime and sanitizer harness를 포함한다.
- Verdict: `approve_scoped_current_pc_local`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Cross-platform ZIP metadata drift, x86 hash module-autoload dependency, empty low-coverage fuzz corpus, missing structured fuzz target와 invalid empty-seed comment를 발견해 수정·재실행했다.
- `#![forbid(unsafe_code)]`를 유지하고 product library의 network/process 호출은 0이다. 파일 쓰기는 explicit `AtomicPackagePublisher`와 private `SecureWorkspace`에만 있다.
- Synthetic, Linux and fuzz evidence를 actual Hancom evidence로 승격하지 않았다. Actual oracle도 open/readback만 증명하며 save/render equivalence를 주장하지 않는다.

## Failure fixtures and residual risks

- Malformed ZIP/header/CRC/path/collision, invalid mimetype/container/manifest/relationship, unsafe XML, duplicate/dangling/wrong-type ID, stale/overlap patch, output limit/overwrite/post-visibility failure가 typed negative corpus로 남아 있다.
- Unsupported/ambiguous source는 자동복구하지 않고 `not_repairable` 또는 stable fail-closed diagnostic으로 종료한다.
- Fuzz budget은 bounded smoke baseline이며 exhaustive proof가 아니다. Seed corpus와 artifact는 private temporary evidence이고 Git에 포함하지 않는다.
- Exact current-2020 oracle는 승인된 두 synthetic fixture의 네 생성물만 열었다. 사용자 문서, 범용 save, rendering, native equation, printing은 이 Gate에서 수행하지 않았다.
- 한글 2022/2024와 다른 PC는 각 PC에서 별도 exact target profile과 독립 evidence bundle로 qualification해야 한다.

## Phase decision

P03은 현재 PC 로컬 범위에서 종료한다. P04와 P10의 P03 기술 선행조건은 충족됐지만 전체 제품 로드맵은 P04부터 순차 진행한다. 다른 버전/PC/production 범위는 P03 PASS에 포함하지 않는다.

## Next exact task

Start `P04-01 DocumentGraph identity model` with reasoning effort `max`. Lock immutable package/part/node/revision identity, canonical ordering and stable serialization before implementing edit transactions. P04 final Gate also requires `max`.
