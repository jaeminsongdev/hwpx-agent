# P09 r84: 동일 Native pressure 진입점의 인증·변경 후 계산 검증27~28

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용28/249 · 잔여221(일반215+corpus6) · 미closing후보0 · 다음index29.
whole 수용3 / 통합 성공본문whole재조정대기25. 원 legacy pending1은 별도 범위다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 위 수치는 고정 r07 개별 runtime이고 P09 전체 완료율이 아니다.

## 실행과 검증 범위

원 P218 진입점/Native pressure helper/원 본문·closing validator source를 변경하지 않았다.
이전 성공1~26 본문 재실행 없음. 원 완료 큐를 소비해 다음 일반 사례만 단독 실행했다.

1. case027/run006: document·branch·project·subject·tenant를 각각 바꾼5가지
   인증 범위 대체에서 새 numeric model 계산과 기존 cached 계산 검증이 모두 거부된다.
2. case028/run007: blob 변조·artifact 읽기 권한 철회·revision head 변경·artifact 격리
   4가지 변경 이후 fresh 계산과 cached 계산 검증이 모두 Source 오류로 거부된다.

원 테스트 source는 `crates/product-cli/tests/form_stored_provider/actual_import/formula_evaluation.rs`다.
fixture 기반 일반 제품 경로 검증이며 별도 runtime corpus6/signed16 또는 제품 전체 Gate
수용으로 승격하지 않는다. 인증 범위 검사는 한글 접근 허용 창을 띄우는 검사가 아니다.

각 exact1 PASS/248 filtered/exit0, 전후1493입력 각118765485bytes 일치,
frame COMMITTED/잠금1799개·복제stream2986개 전부close/잔여0.
원 Job cleanup/tree empty=true, CPU·RAM 보호 중단null. 각 actual의 지원40계약도 PASS.
원 Source/Rust785/고정EXE/두 전체 byte 읽기/stream identity/seek/600초 deadline/
32open/s/no burst credit/binary1·other2MiB/s 및 원 CPU·RAM·commit guard를 유지했다.

| 관측 | case027 | case028 |
|---|---:|---:|
| 시스템 CPU 최고 |51.30%|35.71%|
| 제어 프로세스 CPU 최고(머신 분모) |0.982318%|0.743494%|
| 제어 private 메모리 최고 bytes |38281216|39682048|
| RAM 여유 최저 |43.3130%|43.1489%|
| 제품 Job CPU 누적 초 |0.188|0.578|
| 제품 Job peak private MiB |22.01|21.67|
| 원 parent 실행 elapsed 초 |214.48|196.53|
| 준비 metadata bound/fresh/finished |68/68/true|70/70/true|
| 준비 metadata 실제 읽기 bytes |104377720|111270929|
| Native warning / pause windows / 요청 대기 |0/0/0초|0/0/0초|
| 보호 중단 / cleanup |null/true|null/true|

이번 두 실행에서 Native95% warning은0이고 정상 부하에 추가 CPU 대기를 하지 않았다.
앞선 case022의 실제 높은 부하에서의2회/5window/요청2.5초와 별도 기록으로 유지한다.
시스템 CPU 관측을 제어 프로세스 CPU 사용으로 단정하지 않는다. 프리즈 원인/해결,
외부 PID/Defender/물리 disk IO 원인 및 전체 성능 개선을 증명하지 않았다.
CPU 보호 중단 시 자동 재시도 금지. Native 취득/GO 이전·metadata/admission 실패도
다음 실행에서 거부하며 원 실패와 현재 표본을 지우거나 guard를 낮추지 않는다.

## 추가 코드 검토와 남은 최적화 경계

Native pressure·borrowed stream·runtime frame·metadata reader 경로를 읽어 검토했다.
잠긴 핸들 재사용/단일 owner 직렬 stream/각 읽기의 seek(0)/원 stream identity guard/
CPU 대기에 의존하지 않는 handle 정리 경로는 유지되어 있다. 이번에는 이 코드들을 수정하지 않았다.
검토만으로 모든 성능 문제를 배제하거나 PC 프리즈 해결을 선언하지 않는다.

원 `LiveSQLReader.pin`은 fresh byte를 읽고 `json`도 실제 byte를 읽으며 `finish`는
전체 bound input을 다시 읽는다. 이 검사는 cached pin으로 대체하지 않는다.
case027→028의 준비 metadata 읽기 증가는6893209bytes다. 누적 원장의 JSON 크기와
재확인 비용은 후속 최적화 검토 대상으로 남긴다. 새 저장 형식은 이번 실제 경로에 연결되지 않았다.
향후 변경 시 기존 receipt bytes/SHA는 보존하고, 모든 필드·표본·실패 증거와 원 fresh
검사를 유지하는 별도 source 세대를 검증해야 한다. 미래 전체249의 준비 비용이 충분하다는
주장이나 실제 저장 형식 개선 수용은 하지 않는다.

## 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p218-case-027-run006.v1.json`|2187404|`276ef8ce58c76954a42f3b816476586b2cdad71727ceb9c1ca36f5743ff11974`|
|`cases/p218-case-027-run006.json`|839467|`43f03b098c88295cfc23390a7a18d8439f1d362fbfd669e1f6388c86f4fd8896`|
|`p218-case-028-run007.v1.json`|2166291|`1bf735447eeb2b7fafbd14baf6df5fb8b62204402df2d05504601b3ab7d5f590`|
|`cases/p218-case-028-run007.json`|803125|`7deb9983e4ccc7c76435a449627c27ff990d3de11d2e53b00944259180570e7d`|

실제 Native pressure frame 연결 및 현재 source/정리는 각 새 본문과 원 strict validator로
재검증했다. 기존 성공 본문을 다시 실행하거나 새 helper가 더 적용됐다고 주장하지 않는다.

## 문서 동기화와 다음 경계

원 r83 문서 bytes/SHA를 확인하고 `evidence/runtime-progress-r83/`에 복사했다.
동일 r84 prefix만 두 현행 문서에 추가하며 모든 원 byte suffix를 보존한다.
기존 Native document delta 제공자는 현재 runtime 큐/원 strict 검사/지원40+8계약/
새 실제 receipt hash/전체 bound input 최종 fresh hash/cleanup을 검증한다.
제품 본문/전체 source frame은 다시 실행하지 않는다. 원 문서·실패 증거는 보존한다.

Git/Cargo/build/SQL/Hangul/접근허용/OS·보안 설정 변경 없음.
다음은 같은 P218 진입점의 case029 단독 실행이다. corpus6/통합 whole closing/
whole1470·historical67 최신성/전체249/signed16/P09 Gate는 미수용이고 P10로 넘어가지 않는다.
