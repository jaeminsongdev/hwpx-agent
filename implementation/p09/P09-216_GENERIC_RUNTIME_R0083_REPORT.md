# P09 r83: 동일 Native pressure 진입점의 계산 검증24~26

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용26/249 · 잔여223(일반217+corpus6) · 미closing후보0 · 다음index27.
whole 수용3 / 통합 성공본문whole재조정대기23. 원 legacy pending1은 별도 범위다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 위 수치는 고정 r07 개별 runtime이고 P09 전체 완료율이 아니다.

## 실행과 검증 범위

원 P218 진입점/Native pressure helper/원 본문·closing validator source를 변경하지 않았다.
이전 성공1~23 본문 재실행 없음. 원 완료 큐를 소비해 다음 일반 사례만 단독 실행했다.

1. case024/run003: 인증된 실제 source 순환 참조는 오래된 cached value를 사용하지 않고 거부한다.
2. case025/run004: 인증된 비숫자 source를 math/cache fallback으로 우회하지 않고 거부하며 ingest하지 않는다.
3. case026/run005: 잠금된 source36개를 direct 계산과 대조한다. values/source bindings/receipt가
   동일하고 기존 meanings graph/head를 바꾸지 않으며 추가 ingest 없이 전체 route 승격을 거부한다.
   원 테스트의 합계 assertion은 source36/formula targets16/source cell bindings128이다.

case026 내부 source36개는 이 일반 테스트의 입력이다. 별도 runtime corpus6 또는 signed16을
현재 수용한 증거로 바꾸지 않는다. fixture/source/개별 runtime/제품 전체 Gate 범위를 구분한다.

각 exact1 PASS/248 filtered/exit0, 전후1493입력 각118765485bytes 일치,
frame COMMITTED/잠금1799개·복제stream2986개 전부close/잔여0.
원 Job cleanup/tree empty=true, CPU·RAM 보호 중단null. 각 actual의 지원40계약도 PASS.
원 Source/Rust785/고정EXE/두 전체 byte 읽기/stream identity/seek/600초 deadline/
32open/s/no burst credit/binary1·other2MiB/s 및 원 CPU·RAM·commit guard를 유지했다.

| 관측 | case024 | case025 | case026 |
|---|---:|---:|---:|
| 시스템 CPU 최고 |47.08%|83.66%|36.69%|
| 제어 프로세스 CPU 최고(머신 분모) |1.771654%|1.117318%|0.946970%|
| 제어 private 메모리 최고 bytes |38825984|39202816|39383040|
| RAM 여유 최저 |43.4120%|42.9810%|43.3595%|
| 제품 Job CPU 누적 초 |0.234|0.219|8.719|
| 제품 Job peak private MiB |22.18|21.72|28.23|
| 준비 metadata bound/fresh/finished |61/61/true|63/63/true|65/65/true|
| Native warning / pause windows / 요청 대기 |0/0/0초|0/0/0초|0/0/0초|
| 보호 중단 / cleanup |null/true|null/true|null/true|

이번 세 실행에서 Native95% warning은0이고 정상 부하에 추가 CPU 대기를 하지 않았다.
앞선 case022의 실제 높은 부하에서의2회/5window/요청2.5초와 별도 기록으로 유지한다.
시스템 CPU 관측을 제어 프로세스 CPU 사용으로 단정하지 않는다. 프리즈 원인/해결,
외부 PID/Defender/물리 disk IO 원인 및 전체 성능 개선을 증명하지 않았다.
CPU 보호 중단 시 자동 재시도 금지. Native 취득/GO 이전·metadata/admission 실패도
다음 실행에서 거부하며 원 실패와 현재 표본을 지우거나 guard를 낮추지 않는다.

## 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p218-case-024-run003.v1.json`|2139183|`81aa767f01555786b2351620126544b6c2811d2c463e0d864c49c757909753e5`|
|`cases/p218-case-024-run003.json`|809726|`7be43ee555b8651c41d49de9d31b8f34e3eccde566096097a9bebc0c9913adca`|
|`p218-case-025-run004.v1.json`|2239083|`908f1fd351a0e3d466db064dbbff3d3d282379e0d1ef2239ec4a34fe11a35524`|
|`cases/p218-case-025-run004.json`|896514|`bfb0a70653259069dccb8330918c45f2175c1b4087cef0703ae5a49d552fb876`|
|`p218-case-026-run005.v1.json`|2203576|`5797c1c9bce3d0166ce304a9f804691c71f3a107b064458242252cfd963f5495`|
|`cases/p218-case-026-run005.json`|851431|`a655bab9ef9acf8f77e3d002376271de9736f7b5f6a6005a88e608f462a9bdb8`|

실제 Native pressure frame 연결 및 현재 source/정리는 각 새 본문과 원 strict validator로
재검증했다. 기존 성공 본문을 다시 실행하거나 새 helper가 더 적용됐다고 주장하지 않는다.

## 문서 동기화와 다음 경계

원 r82 문서 bytes/SHA를 확인하고 `evidence/runtime-progress-r82/`에 복사했다.
동일 r83 prefix만 두 현행 문서에 추가하며 모든 원 byte suffix를 보존한다.
기존 Native document delta 제공자는 현재 runtime 큐/원 strict 검사/지원40+8계약/
새 실제 receipt hash/전체 bound input 최종 fresh hash/cleanup을 검증한다.
제품 본문/전체 source frame은 다시 실행하지 않는다. 원 문서·실패 증거는 보존한다.

Git/Cargo/build/SQL/Hangul/접근허용/OS·보안 설정 변경 없음.
다음은 같은 P218 진입점의 case027 단독 실행이다. corpus6/통합 whole closing/
whole1470·historical67 최신성/전체249/signed16/P09 Gate는 미수용이고 P10로 넘어가지 않는다.
