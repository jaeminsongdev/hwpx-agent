# P09 r85: 읽기 권한 검증29와 compact receipt 실제 연결30

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용30/249 · 잔여219(일반213+corpus6) · 미closing후보0 · 다음index31.
whole 수용3 / 통합 성공본문whole재조정대기27. 원 legacy pending1은 별도 범위다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 위 수치는 고정 r07 개별 runtime이고 P09 전체 완료율이 아니다.

## 제품 경로 진행

1. P218 case029/run008: DocumentRead scope가 없으면 numeric model을 재사용하기 전에
   provider bind가 Scope 오류로 거부된다. 별도로 인증된 원 provider의 기존 receipt는 검증된다.
2. P220 case030/run001: 인증된 실제 source의 계산 결과를 prepare/verify/검증 후 byte 소비한다.
   각 경계에서 다운로드 재검증이7회 발생하며 원 source와 다른 candidate가 나온다.
   현재 제품 route는 RouteUnqualified로 거부되고 revision head/원 ingest 횟수2는 바뀌지 않는다.

원 source는 `actual_import/formula_evaluation.rs`와 `actual_import/formula_output.rs`다.
fixture 기반 일반 제품 경로 검사이며 runtime corpus6/signed16/제품 전체 Gate 증거로 승격하지 않는다.
권한 검사는 한글 접근 허용 창이 아니다. 이전 성공1~28 본문은 재실행하지 않았다.
P220는 원 성공1~29 큐를 소비하고 다음30만 실행했다.

각 exact1 PASS/248 filtered/exit0, source frame COMMITTED, Job cleanup/tree empty=true.
case029 전후1493입력 각118765485bytes, 잠금1799/복제2986 모두close/잔여0.
case030은 원1493입력과 새 제어5입력을 합친1498입력 전후 각118801078bytes를 읽었다.
잠금1804/복제2996 모두close/잔여0, 원 input/stream/path identity 검사는 유지한다.
실제 Native pressure frame 연결은 두 사례에서 유지된다.

| 관측 | case029 P218 | case030 P220 |
|---|---:|---:|
| 지원 계약 |40|62|
| 시스템 CPU 최고 |38.56%|31.13%|
| 제어 프로세스 CPU 최고(머신 분모) |1.127820%|0.803213%|
| 제어 private 메모리 최고 bytes |39342080|39485440|
| RAM 여유 최저 |41.1057%|41.4755%|
| 제품 Job CPU 누적 초 |0.312|1.125|
| 제품 Job peak private MiB |21.64|26.79|
| 원 parent elapsed 초 |211.19|195.82|
| 준비 metadata bound/fresh/finished |72/72/true|81/81/true|
| 준비 metadata 실제 읽기 bytes |118012886|130515415|
| Native warning / pause windows / 요청 대기 |0/0/0초|0/0/0초|
| 보호 중단 / cleanup |null/true|null/true|

두 사례는 서로 다른 본문/범위다. elapsed/CPU 차이를 성능 향상 benchmark로 해석하지 않는다.
root writer는 원 구현처럼 resource cleanup 뒤 실행되므로 위 자원 표본은 root 저장 전체를
포함한다고 보장하지 않는다. 외부 PID/Defender/물리 disk IO 원인도 확인한 것으로 바꾸지 않는다.

## 구현한 최적화와 범위

새 `receipt_compact_json.py`는 JSON 들여쓰기와 separator 공백만 줄인다. 모든 필드·표본·
실패 증거를 유지하며 원 파일은 재작성하지 않는다. 출력 batch는32768 ASCII chars 이하다.
각 쓰기 전후 caller checkpoint와 최대64 encoder token마다 checkpoint를 호출한다.
부분 쓰기/CPU·RAM·IO stop/비정상 JSON 값·순환 구조는 실패하고 자동 재시도하지 않는다.

P219 지원 계약12개는 값/순서/Unicode/값 내부 공백/원 객체 불변/쓰기 batch/원 guard/
초기·중간·최종 중단 전파/비유한 숫자/순환·비지원 값/옵션 변조/부분 쓰기 거부를 검사했다.
고정 case028 root/body를 메모리에서만 serialize하여 원 전체 JSON 값과 대조했다.

| P219 고정 sample | 원 bytes | compact bytes | 절감 bytes | 절감률 |
|---|---:|---:|---:|---:|
|case028 root|2166291|1515402|650889|30.0462%|
|case028 body|803125|610802|192323|23.9468%|

지원 qualifier의 bound5/fresh5/finished=true, cleanup=true, stop/error=null.
이는 지원 증거이며 해당 qualifier의 actual bridge/product compact flags는false다.

새 `resume_compact_pressure_runtime.py`는 원 P208 parent와 Native pressure frame을 호출한다.
parent가 원 strict 검증을 마친 최종 dump만 새 writer로 연결하며 원 ensure_ascii=false/
indent2 옵션을 확인하고 값이 동일한 ASCII escape/무공백 표현으로 저장한다.
본문 writer는 원 frame.check로 owner CPU·RAM/IO/잠금600초 guard를 실행한다.
root는 원 cleanup 이후 종료 lifecycle만 확인하고 종료된 resource owner를 다시 시작하지 않는다.
원 c.run/GO/Job/affinity1/BelowNormal/CPU·RAM 비율/98%x4/IO600초/32open/s/
binary1·other2MiB/s/전후 두 전체 실제 byte 읽기/최종 fresh hash는 유지된다.

원 support40+compact12+새 bridge10=62계약과 첫 light next30 선택은 actual 실행 전 통과했다.
실제 compact parent/root writer 연결은 별도 case030 증거로 수용한다.
case030 본문은609774bytes/19write batches/최대32768chars, root는1542273bytes다.
새 consumer는 파일을 실제 다시 읽고 compact 표현으로 재생성한 SHA/길이까지 대조하여
선언된 flag만으로 연결을 인정하지 않는다. 원 strict parent/source/큐 검사도 적용한다.

이전 파일의 들여쓰기/bytes/SHA는 보존하고 새 결과부터만 적용한다. 삭제·cache로
원 fresh 읽기를 대체하지 않는다. 후속 metadata 읽기량/CPU/RAM/전체249의 resource budget
충분성은 아직 별도 수용하지 않았고 CPU 개선·PC 프리즈 해결을 선언하지 않는다.
CPU 보호 중단 시 자동 재시도 금지. Native 취득/GO 이전·metadata/admission 실패와
부분 JSON도 다음 실행을 막으며 코드 검토·명시적 새 증거 없이는 같은 body를 반복하지 않는다.

## 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p218-case-029-run008.v1.json`|2222962|`6cc90037a0fe969aae7467cab32ea667bf2e08a88c148ccd7da717424b7652d1`|
|`cases/p218-case-029-run008.json`|818884|`4dd91230e02228ea4073c16b26a1d3a060f473c2dc0b4080e158ff60ea036e8b`|
|`p219-compact-receipt-light-run01.v1.json`|18123|`fedd3863a799814fa883f5bf1a57a159d4781aaf9466cc120edce5a6c9b901bf`|
|`p220-case-030-run001.v1.json`|1542273|`35032b1e17b1d7f02c7a500dcab0dfacf47bfe110718ae20dc0c7389378ccae3`|
|`cases/p220-case-030-run001.json`|609774|`b622b02cb251af2a32faa722bce88ae3901b0800bd33083607f44a05f2b9da50`|

## 문서 동기화와 다음 경계

원 r84 두 문서 bytes/SHA를 확인하고 `evidence/runtime-progress-r84/`에 복사했다.
동일 r85 prefix만 두 현행 문서에 추가하며 모든 원 byte suffix를 보존한다.
새 compact 문서 제공자는 원 P216 스키마/이력 보존 기준, P220 strict/canonical 큐,
62+8계약/새 실제 두 root SHA/전체 bound input 최종 fresh hash/cleanup을 검증한다.
기존 성공 본문/전체 source frame은 다시 실행하지 않는다.

다음은 P220 case031 단독 실행이다. corpus6/통합 whole closing/whole1470·historical67 최신성/
전체249/signed16/P09 Gate는 미수용이고 P10로 넘어가지 않는다.
Git/Cargo/build/SQL/Hangul/접근허용/OS·보안 설정 변경 없음. 원 STOP/FAILED는 보존한다.
