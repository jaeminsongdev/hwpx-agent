# P275~P276: 실제95 CPU STOP 검토·획득 phase14 후보·support 읽기 최적화

2026-10-09. 목표 ACTIVE. 실제 runtime 수용88/249, 잔여161(일반155+corpus6), 다음index95, whole재조정대기85, 독립source 마감대기0. P09·A12·A13 OPEN. 전체249/signed16/whole1470/historical67/제품 완료/PC 프리즈 해결은 미확정. 접근허용·한글 UI·빌드·Git·설치·OS/Defender/WSL 변경 없음.

## 실제95: FAILED_NOT_ACCEPTED, 본체 미실행

원 P273 actual run003은 `STOP_SUSTAINED_SYSTEM_CPU`로 source_frame_acquire 단계에서 중단. 정확한 선택은 `actual_import::formula_policy_revocation::stale_head_quarantine_and_aead_tamper_deny_before_revocation_write`. Rust 본체에는 `0..3`의 유한 사례 반복이 있으며 검토한 본체/연결/대기 경로에서 무한 반복·병렬 증식은 확인되지 않았다. 실행된 source 범위 밖 전체 코드에 대한 결론은 아니다.

650 계약과 prep412 reads/bound199/fresh199은 완료했지만 전체 Frame 획득이 중단됐다. 잠금737개/metadata737회, 열린737개 모두 닫음·잔여0·등록 해제·Frame CLOSED. byte boundary0, borrower/duplicate 측정은 null(0으로 발명하지 않음), 원 제품 parent·Job·95 본체는 호출 전. 본체 파일도 생성되지 않았다. 원 제품 Job 정리를 실행·확인했다고 주장하지 않는다. 기존92·93·94 본체 재실행 없음.

원 잠금600초 중 최초 오류는40.801785초/guard3793/phase metadata_hash. 기존 조기90 대기는2회 경고·7 windows·3.5초 작동한 상태에서 원98%x4 보호가 중단시킴. 마지막4 표본은 시스템CPU100%/own CPU0%/logical byte delta0. 총174표본, own CPUmax5.780532%, private57966592bytes, 가용 RAM 최저19.907594%. 이는 시스템 고부하가 원 guard에 관측되었다는 뜻이며 외부 프로세스·Defender·WSL·I/O의 단독 원인 또는 프리즈 해결 증거가 아니다.

원95 root: `implementation/p09/evidence/locked-r07/p273-case-095-run003.v1.json`, bytes223604, SHA256 `7880cdce8abe86f32c337d77ab3accd7fae46e4e6a81c8e1a773e4fd11e3d61e`. 실패·소스·원 보호는 보존하며 실패를 소급 수용하지 않는다.

## 획득 구간의 코드 개선

새 `qualify_acquisition_phase_pressure.InputLocks`는 기존 TimedInputLocks를 확장해 **획득 중에만** 기존 단일 pacer를20→14회/초로 설정한다. 성공·실패 모두20을 복구하며 원 clock/sleeper/checkpoint/previous/open counter를 초기화하지 않는다. idle burst credit·새 sampler/thread·별도 Native/CPU query·cleanup guard·바이트 검사 생략 없음. 전후 바이트 stream reservation은 원20/s로 유지한다.

원 CPU/RAM·잠금/IO600·공유metadata720·Job6.25%/affinity1/BelowNormal·전체byte/identity/보호없는 정리 기준 유지. 정상 획득 reservation의 명목 밀도는30% 감소하지만 실제 전체 실행의 CPU/프리즈 개선을 입증한 것은 아니다.

## P275 지원 검증 실패와 실제 비용 검토

P275 원lower6+신규26=32 계약은 통과. 그러나 과거 전체 ancestry를 다시 읽는 q.finish 단계에서 CPU STOP: metadata368 reads/201 bound/135 final fresh/52539972bytes, finished false. **작은 Native 프로브에도 도달하지 못함**. 진단 stage는 코드상 contract_tests로 남았지만 원 sample phase와 traceback은 final_fresh_hash 읽기였음. 실제95 본체/전체source 미실행·watcher 정리 확인.

P275 root: `implementation/p09/evidence/locked-r07/p275-acquisition-phase-pressure-run01.v1.json`, bytes112398, SHA256 `0d84b558fb3c5785d66105bfd9ff95bb94e129c926176a18fc2bccca667695f1`. 전체CPU100%, ownCPUmax1.535509%, private55341056bytes, 가용RAM 최저13.899891%. 원 지원 실패는 미수용·보존한다.

## P276 support 전용 bounded literal 읽기

지원 자격검증은 고정 SHA의 실제 수용94 root/body, 원95 STOP, P275 STOP, 사용 코드16 및 지원 코드/보존 preimage를 current fresh 검토한다. 이미 수용된94의 whole1579 byte 증거와 원 Job 정리를 재실행·새 현재 fullscope 검증으로 바꾸지 않는다. 제품 전체 실행의 기존 ancestry·전체 입력·전후 byte·identity·정리 검사는 제거하지 않는다. 지원 출력은 actual_full_runtime_connection_qualified=false이며 원 product/runtime 수용 수를 변경하지 않는다.

P276 run01: 신규6+원32=38 통과, support49reads/24bound/fresh24/2837996bytes 완료. Native14 획득7개 완료·rate20 복구 후 첫 boundary의 원 TraceReader에 diagnostics 인터페이스가 없어 AttributeError. 잠금7/duplicate3 전부 정리, boundary완료0, CPU STOP 없음. 원 source/test를 `implementation/p09/evidence/preflight-controller-snapshots/p276-literal-reader-interface-run01/`에 exact length/SHA 보존한 뒤 diagnostics 집계 adapter와 새2계약만 추가했다. 원 _read/source/guard 불변.

P276 run01 root: bytes33781, SHA256 `fda60a11e0ea0f060c2b6b51c02d8a6590a128994b28e4ded8f5b7b0306f4d66`. 실패는 미수용. 작은 획득 성공만으로 전체 프로브 PASS를 주장하지 않는다.

## P276 run02: support qualification PASS, 제품 수용 아님

`PASS_LITERAL95_STOP_REVIEW_AND_SMALL_NATIVE14_NOT_FULL_RUNTIME_OR_GATE`. 원32+신규8=40 계약. 지원55 reads/27 bound/27 final fresh/2938792bytes, finished true. 실패한 P275가 중단 시점까지 읽은52.54MB보다 적은2.94MB로 지원 qualification을 완료했다. 실패 전 부분 읽기와 성공 완료 읽기의 비교이므로 기존 완료 실행 대비 CPU 개선율/시스템 부하 개선율을 산출하지 않는다.

실제 작은 Native3파일·33667bytes를 before/after 각각3 reads로 완전히 읽음. Frame CLOSED(제품 Job 없음·COMMITTED 아님), 등록 해제. 기존 single pacer 획득14/s에서7 reservation·성공 후20 복구, 잠금7/duplicate6/offsetreset6 모두 정리·잔여0·pathname byte reopen0. 원 guard108회, 최초오류null, 획득완료0.432485초. 현재 원 cleanup/CPU/identity 기준 보존을 작은 범위에서 확인했다.

표본8개: 시스템CPUmax7.16%, ownCPUmax2.094241%, own private40566784bytes, 가용RAM 최저22.454013%. STOP null·watcher cleanup true. 다른 시간의 시스템 상태와 비교해 인과 개선으로 해석하지 않는다. 프리즈 해결은 미확정.

수용 support root `implementation/p09/evidence/locked-r07/p276-literal-phase-pressure-run02.v1.json`: bytes35487, SHA256 `e92558b203396aa5aa4355fec8c32d50839befdf909cc44d5159bc3bbb710c8d`.

최종 helper `tools/p09/qualify_acquisition_phase_pressure_r2.py`: bytes14022, SHA256 `5eef3170b4541e4978447c47056aa3bc4e733e7e7f83899144cb22237dade897`. test `tools/p09/tests/test_acquisition_phase_pressure_r2.py`: bytes2595, SHA256 `06e4ca875ec375fcb01aaed8d6561b8c987503b7c7966ffaf81ecb603105512e`. 실행된 성공 코드/원 실패 코드·증거는 변경하지 않는다.

## 다음 경계

명목 상한은 원1579+새 코드/preimage8=1587입력, 획득14/s·byte reservation20/s·원306 directories·binary1/other2MiB/s·기존 allowances/margin 유지 시577.569276초<원600. 이는 모델이며 완료 보장이 아니다. 새 실행기는 실제 추가 pin 수·bytes 상한·전체검사·원 보호를 다시 검증해야 한다.

전체 runtime 연결과 95 actual은 **NOT_RUN**. 다음 실행기에서 원95 STOP을 명시 검토하고 이 후보를 전체범위에 연결·current/following 계약과 사전검증을 닫은 후에만 아직 실행되지 않은95 본체를 한 번 실행한다. 88/249·다음95·잔여161 유지. 원 P273progress의 실패 차단을 우회해 같은 코드를 재시도하지 않는다.
