# P09 r82: Native open 부하 완화의 실제 frame 연결 및 runtime22~23

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용23/249 · 잔여226(일반220+corpus6) · 미closing후보0 · 다음index24.
whole 수용3 / 통합 성공본문whole재조정대기20. 원 legacy pending1은 별도 범위다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 위 수치는 고정 r07 개별 runtime이며 P09 전체 완료율이 아니다.

## 구현과 실제 연결

`resume_native_pressure_runtime.py`는 원 P215 코드/실제 성공 본문1~21을 변경하거나
재실행하지 않는다. 원 anchor/strict validator로 기존 큐를 재검증한 뒤 runtime21/
next22를 소비한다. P217의 literal light pin 및 원9개 입력의 현재 pin도 확인한다.

원1488입력에 Native helper/test, 지원 qualifier 및 새 driver/test 5개를 더해1493입력.
원 Rust785 집합/동일 고정 r07 EXE/기존 전체 입력을 유지하며 subset을 수용하지 않는다.
실제 owner를 Native pacer에 연결한 `PressureInputLocks`가 같은 frame에서 살아 있음을
확인한다. 원 `p.run_parent`/GO/Job/환경/본문/전후 두 전체 byte 읽기/identity/정리를
그대로 사용하며, 정리·resource 필드·최종 원 closing 검사 뒤에만 overall PASS를 기록한다.

실제 Native pressure frame 연결은 case022/run001 및 case023/run002에서 확인했다.
Native acquisition 이전·중간/GO 이전/metadata/admission 실패도 다음 계속 실행에서
거부한다. 원 실패 reason이 null이더라도 실제 frame 취득 실패를 자동 재시도하지 않는다.
CPU 보호 중단 시 자동 재시도 금지. 조사·최적화·별도 검증 없이 실패를 없애지 않는다.

지원40계약=원 큐18 + Native pressure10 + 새 bridge12. 첫 light 선택22,
actual22 수용 뒤 light 선택23, 동일 source의 actual23 수용 뒤 다음은24.
실제 제품 본문 통과 수와 지원 계약 수를 합산하지 않는다.

## 실제 제품 경로

1. case022: 보호되거나 잘못된 두 번째 section에서 부분 stored plan을 만들지 않는다.
2. case023: 다른 document/branch/project/subject/tenant provider로 컴파일한 batch나
   후보를 다시 바인딩할 수 없고, cached consumer가 실행되지 않는다.

각 exact1 PASS/248 filtered/exit0, 전후1493개 각118765485bytes 일치,
frame COMMITTED/잠금1799개·복제stream2986개 전부close/잔여0.
원 Job cleanup/tree empty=true, CPU·RAM 보호 중단null.
원600초 deadline, 32open/s/no burst credit, binary1/other2MiB/s 및 원 byte pressure 유지.
새 샘플러/감시 thread나 foreign PID 조회는 만들지 않았다.

| 관측 | case022/run001 | case023/run002 |
|---|---:|---:|
| 시스템 CPU 최고 |99.30%|74.80%|
| 제어 프로세스 CPU 최고(머신 분모) |1.111111%|1.343570%|
| 제어 private 메모리 최고 bytes |39247872|38600704|
| RAM 여유 최저 |24.5140%|29.6253%|
| 제품 Job CPU 누적 초 |0.672|1.203|
| 제품 Job peak private MiB |27.11|28.35|
| 준비 metadata bound/fresh/finished |55/55/true|58/58/true|
| Native pressure warning entries |2|0|
| 원 distinct pause windows / 최대 한 구간 |5 /3|0 /0|
| Native 추가 대기 요청 초 |2.5|0|
| 보호 중단 / cleanup |null/true|null/true|

case022는 실제 고부하 표본에서 Native open의 완화 경로가 두 번 작동했다.
원 표본의 서로 다른 cool window 두 개를 확인한 뒤 open을 재개했고 5개 window/
총2.5초 요청 대기를 기록했다. 원639표본에서 >=98% 최장 연속은1개여서 원
98%×4 hard stop은 충족되지 않았다. 원 CPU/RAM/commit/IO guard 및 잠금 deadline은
그대로 실행했다. case023은 경고0으로 불필요한 Native CPU 대기가 없었다.
이 결과는 실제 연결·대기·원 검증·정리가 작동한 증거이지 프리즈 해결이나 측정된
CPU 개선/외부 부하 원인의 증거가 아니다. RAM 여유 변화도 다른 앱 원인으로 단정하지 않는다.

## 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p218-case-022-run001.v1.json`|2207155|`340efcf21d3b1e02eab7f28e65ad4a1f559983c6936f94dc80caf5c1f5402d4e`|
|`cases/p218-case-022-run001.json`|814807|`99b0aea58b74349c8349970b01a0d44bfd0a79aed7fc6b7109657155c80cdcc1`|
|`p218-case-023-run002.v1.json`|2121841|`0131a422cab2f6d19fe60085ca95a9911f71cd5153d1f141633e4aadc0a04dc9`|
|`cases/p218-case-023-run002.json`|797982|`210092f405b6de3c2eb7c81a81f59b8ed3ab8497cda163f2ad854f3a561bc4b5`|

## 문서 동기화와 다음 경계

원 r81 document bytes/SHA를 확인하고 `evidence/runtime-progress-r81/`에 복사했다.
동일 r82 prefix만 두 현행 문서에 추가하며 모든 원 byte suffix를 보존한다.
새 `sync_native_pressure_document_delta.py`는 원 P216 문서 스키마/보존 기준과
지원8계약을 재사용하되, runtime 큐/strict frame 검사에는 P218 제공자를 사용한다.
원 지원40계약, 새 실제 receipt hash, 전체 bound input 최종 fresh hash/cleanup을
검증하지만 제품 본문이나 전체 source frame을 다시 실행하지 않는다.

Git/Cargo/build/SQL/Hangul/접근허용/OS·보안 설정 변경 없음.
다음은 동일 P218 진입점의 case024 단독 실행. corpus6/whole1470·historical67 최신성/
전체249/signed16/통합 whole closing/P09 Gate는 미수용이며 P10로 넘어가지 않는다.
