# P03-09 Round-trip and repair Gate report

- Generated: 2026-09-02
- Audited source commit: `d5ff13547976d55204f63a030f07f7a628afb605`
- Product-byte commit used by the exact Hancom oracle: `ac17426d98995ca21814fab059222f757a715394`
- State: `pass_current_pc_local_core_and_exact_2020_oracle`
- Reasoning/review mode: `max / document-byte preservation, runtime oracle and fuzz boundary`

`hwpx-package`에 `RoundTripVerifier`, non-mutating `RepairDiagnostic`, explicit private-workspace CLI example, deterministic 128-fixture corpus와 raw/structured sanitizer fuzz target을 구현했다. 검증기는 bounded ZIP부터 graph, preservation, ID/reference, no-op patch, preserving/normalized writer까지 다시 열어 확인하며 한 계층이라도 실패하면 부분 evidence를 반환하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Explicit bounded entry point | `pass` | caller가 source와 private `SecureWorkspace`를 명시하며 source in-place write, implicit scan, public raw-byte getter 0 |
| Layered full reopen | `pass` | ZIP→PackageGraph→PreservationReport→IdIndex→no-op Patch→두 writer를 fail closed로 재검증 |
| Deterministic valid corpus | `pass` | synthetic 128개, 각 5 parts, untouched violation 0, preserving/normalized repeated SHA equality |
| Cross-platform corpus identity | `pass` | semantic digest `b0f187093072a78bc50e12de31f6d30c88d679fb35c8a7ab309203937ba06823`, writer aggregate `d5492303a282c3fe4b00b7fa9b0cfd8a8528f7f2b060ffc24b086341e06d0224`가 Windows/Linux에서 동일 |
| Structured variation | `pass` | entry permutation, stored/deflated 선택, semantic marker와 attribute variation을 고정 seed로 생성 |
| Negative replay | `pass` | one-byte mutation 128개와 truncation 128개를 각각 두 번 실행해 동일 success evidence 또는 동일 error/diagnostic; partial evidence 0 |
| Repair diagnostics | `pass` | archive/graph/preservation/ID/patch/publication/internal 계층, stable code, repairability와 recommended action만 노출; 자동수정과 원문/path/value 출력 0 |
| Raw-byte sanitizer fuzz | `pass` | pinned nightly+ASan, approved seed 6개, exact final commit 1,000 runs, `cov 7599`, `ft 12470`, final corpus 74/1,074 KiB, crash/timeout/OOM artifact 0 |
| Structured sanitizer fuzz | `pass` | bounded valid-package generator, 1,000 runs, `cov 7286`, `ft 9694`, corpus 155, artifact 0 |
| Fuzz dependency policy | `pass` | separate `fuzz/deny.toml`, exact `libfuzzer-sys@0.4.13`만 NCSA exception; advisories/bans/licenses/sources pass, root product policy 불변 |
| Current exact Hancom 2020 oracle | `pass` | preserving/normalized output 4/4 read-only open, fixture pair semantic readback 2/2 equal, Hwp remainder 0 |
| Oracle safety/privacy | `pass` | Registry32, x86 PowerShell, STA, exact build/hash pin, source/input mutation 0, save 0, network/registry/system setting/UI automation 0, raw text/private absolute path receipt 0 |
| Regression | `pass` | Windows/Linux `hwpx-package 48/48`, PowerShell static oracle `36/36`, current/clean-clone FULL `5/5` |
| Versioned policy/migration | `pass` | `P03-09_ROUNDTRIP_REPAIR_POLICY.md`, `roundtrip-repair-v0-to-v1.md` |

## Exact current-target oracle

- Target: licensed Hancom Hangul 2020 build `11.0.0.9136`, 32-bit COM registration, x86 STA client.
- Corpus manifest SHA-256: `9a5d92baee5602ebb05e6f3cdc45611f604f483bf9d0a87a4070377c4cee9747`.
- Cases: two approved disposable synthetic fixtures × preserving/normalized = `4/4 pass`.
- Pair comparison: normalized Unicode text digest and UTF-8 length equality = `2/2 pass`.
- Every child exited 0 without timeout; cleanup refused/error/remaining process counts were all 0.
- Input and source artifacts were not modified. The oracle called neither `Save` nor `SaveAs`; it proves open/readback compatibility, not save/render equivalence.
- The receipt and per-case traces are restricted local evidence and remain outside Git.

## Validation evidence

- Current Windows exact final commit: FULL bootstrap `5/5`; `hwpx-package 48/48`; format, Clippy `-D warnings`, workspace tests/doc tests, generated drift, C# worker, TypeScript widget, docs and security all passed; post-run Git changes 0.
- PowerShell oracle static suite: `36/36`; no Hwp process remained.
- Linux: derived image `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`, network off, source/registry read-only, Cargo offline, executable tmpfs; `48/48` and Clippy passed.
- Clean clone: exact commit `d5ff13547976d55204f63a030f07f7a628afb605`, FULL bootstrap `5/5`, post-run tracked/untracked changes 0.
- Security: current repository 509 files scanned, secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 271.

`cargo deny`의 기존 `hashbrown`/`syn` duplicate-version 메시지와 fuzz allowlist의 unmatched Apache LLVM allowance는 warning policy 안의 메시지이며 advisories/licenses/sources/bans 실패가 아니다.

## Strict self-review and remediations

- Change risk: `high` (untrusted document bytes, output publication, exact desktop runtime and sanitizer execution).
- 32-bit Windows PowerShell이 `Get-FileHash`를 module-autoload하지 못한 환경 의존 실패를 발견해 parent/child 모두 managed SHA-256 stream으로 바꿨다.
- Windows와 Linux ZIP creator metadata 기본값 차이로 writer SHA가 달라지는 결함을 발견해 creator system을 Unix, regular-file permission을 `0644`로 고정했다. semantic digest와 writer digest를 분리해 corpus drift와 writer drift를 각각 검증한다.
- 빈 raw fuzz corpus의 1-byte 저coverage 실행을 authoritative evidence로 채택하지 않고 승인된 6개 복사본 seed로 다시 실행했다.
- STRICT 감사에서 structured package fuzz target 누락을 발견해 별도 bounded valid-package generator를 추가했다. 첫 빈 seed의 XML comment 생성 오류는 `xml_malformed`로 재현한 뒤 수정하고 전체 1,000회를 재실행했다.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P03-09는 현재 PC의 exact 한글 2020에서 승인된 disposable output의 read-only open/readback까지 검증한다. 범용 자동복구, save/render/PDF 동등성, 사용자 문서 corpus, 2022/2024, 다른 PC, production/provider/배포는 검증했다고 주장하지 않는다. Repair diagnostics는 조치 분류만 제공하며 실제 transaction과 revision 기능은 P04 범위다. 제한된 fuzz budget은 모든 결함의 부재를 증명하지 않는다.

## Next exact task

`P04-01 DocumentGraph identity model`을 시작한다. package/part/node/revision identity, immutable source lineage, canonical ordering과 stable serialization 계약을 먼저 고정한 뒤 negative fixtures를 작성한다. 구현과 P04 final Gate 모두 추론수준 `max`를 사용한다.
