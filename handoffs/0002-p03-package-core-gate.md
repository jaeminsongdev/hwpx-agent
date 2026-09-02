# HANDOFF 0002 — P03 Package and Preserving XML Core Gate

> 작성일: 2026-09-02
> 상태: `PASS_SCOPED_CURRENT_PC_LOCAL`
> audited commit: `d5ff13547976d55204f63a030f07f7a628afb605`
> 다음 phase: `P04_DOCUMENTGRAPH_EDIT_TRANSACTION_REVISION`

## 완료 범위

- Bounded ZIP, closed PackageGraph, safe/preserving XML과 PreservationReport를 구현했다.
- current-2020 core typed ID/reference index와 8종 preserving PatchIntent를 구현했다.
- preserving/normalized writer, bounded construction, atomic no-overwrite publication과 full readback을 구현했다.
- RoundTripVerifier와 non-mutating RepairDiagnostic을 구현했다.
- 128 valid fixture, 128 byte mutation, 128 truncation corpus와 두 ASan fuzz target을 통과했다.
- 현재 PC exact 한글 2020에서 생성 output 4/4 open/readback, pair 2/2 semantic equality, 잔류 process 0을 확인했다.
- Windows/Linux `48/48`, current/clean-clone FULL `5/5`, security 0건, STRICT audit를 통과했다.

## 실패 fixture와 수정 이력

- 32-bit PowerShell의 `Get-FileHash` module-autoload 실패: managed SHA-256 stream으로 교체했다.
- Windows/Linux writer SHA 불일치: ZIP creator system과 regular-file permission을 고정했다.
- 빈 raw fuzz corpus의 저coverage 실행: authoritative evidence에서 제외하고 승인된 복사본 seed 6개로 다시 실행했다.
- structured fuzz target 누락: bounded valid-package generator target을 추가했다.
- structured target 빈 seed의 invalid XML comment: `xml_malformed`를 재현해 marker를 수정하고 1,000회를 재실행했다.

## 유지해야 할 경계

- source/user document in-place 수정 금지, public raw XML/action 실행 금지.
- preservation 불명확/opaque/rejected part를 editable로 승격하지 않는다.
- raw compressed stream, timestamp와 unavailable metadata를 preserved라고 주장하지 않는다.
- repair diagnostic은 자동복구가 아니다. 실제 transaction/revision은 P04에서만 구현한다.
- actual 2020 evidence는 승인된 disposable synthetic output의 read-only open/readback이다. Save/render/사용자 문서/다른 버전 범위가 아니다.
- 2022/2024와 다른 PC는 현재 evidence와 섞지 않고 별도 qualification한다.

## 재현 진입점

- `implementation/p03/P03_GATE_REPORT.md`
- `implementation/p03/P03-09_REPORT.md`
- `implementation/p03/P03-09_ROUNDTRIP_REPAIR_POLICY.md`
- `crates/hwpx-package/src/roundtrip.rs`
- `crates/hwpx-package/tests/roundtrip_gate.rs`
- `fuzz/fuzz_targets/roundtrip_admission.rs`
- `fuzz/fuzz_targets/structured_roundtrip.rs`

## 다음 exact task

`P04-01 DocumentGraph identity model`을 추론수준 `max`로 시작한다. package/part/node/revision의 immutable identity와 source lineage, canonical ordering, stable serialization, duplicate/stale/collision negative cases를 먼저 고정한다. P04 final Gate도 `max`다.
