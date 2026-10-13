# P09 r88: 고정 packed 경로의 runtime36~38 검증

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용38/249 · 잔여211(일반205+corpus6) · 미closing후보0 · 다음index39.
whole 수용3 / 통합 성공본문whole재조정대기35. 원 legacy pending1은 별도다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 38/249는 고정 r07 개별 runtime 큐이며 P09 전체 완료율이 아니다.

## 이번 실행과 관련 코드 검토

현재 r87 문서 receipt를 최신 파일에서 확인했다. runtime35/다음36, bound109=fresh109/
finished/cleanup=true/오류·stop=null/원 문서·실패 보존을 확인한 뒤 진행했다.
수용된 P222 driver/test·P221 packed helper/test/qualification·P219 compact writer와
원 P208 parent/strict validator/Native pressure helper는 수정하지 않았다.
이미 성공한1~35 본문은 재실행하지 않았으며36→37→38을 직렬로 exact-one 실행했다.
이 턴에 CPU 보호 중단은 없었다. 실행당 동일88계약 PASS이며 서로 다른264개 계약이라는 뜻은 아니다.

추가 검토한 원 입력 잠금 경로는 방문 디렉터리 set으로 공통 조상을 재순회하지 않는다.
borrowed stream은 원 READ handle만 복제하고 원 process/thread 단일 owner를 확인한다.
매 읽기 seek(0)/원 stream identity 검사를 유지하며 중복 pre-descriptor metadata 조회는
하지 않는다. 원 한 sampler를 재사용하는 IO·Native pressure 경로와 cleanup가 pause
guard에 막히지 않는 경로를 확인했다. 이번에는 이 수용된 소스를 바꾸지 않았다.
전체249의 결합 시간·600초 reader/1440표본 예산 충분성은 여전히 미수용이다.

실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결은 세 실행 모두 유지됐다.
원 Rust785/고정EXE/두 전체 실제 byte 읽기/stream identity/CPU·RAM·commit 보호/
affinity1/BelowNormal/Job·GO·정리/600초/32open/s/no burst/binary1·other2MiB/s/
최종 전체 bound input fresh hash를 유지했다. 새 sampler/SQL/Git/build/한글 접근 허용은 없다.
원 source 범위1503입력 전후 각118841107bytes 일치, frame COMMITTED.
잠금1809/복제stream3006 모두close/잔여0/close 실패0, owned Job active0/tree empty=true.
실행 범위를 줄이거나 캐시 pin을 현재의 실제 byte 검증으로 대체하지 않았다.

## 실제 제품 경로 검사 범위

1. case036/run002: 준비된 정책 수식 결과라도 document·branch·project·subject·tenant
   다섯 외부 provider 범위로 byte를 소비할 수 없다. 각 callback 미호출과 no_publication을 검사한다.
2. case037/run003: 원문과 현재 재계산 입력 각각에서 네 target 중 하나의
   allow_recalculation=false가 allowed_targets=3이어도 전체 재계산 권한/제품 준비를
   Denied로 거부하고 공개 경계를 유지한다.
3. case038/run004: Evidence+source-policy media, Evidence+application/json,
   Source/Result/DocumentIr+formula-policy media의 다섯 잘못된 descriptor 조합에서
   bind_stored_formula_policy가 Artifact 오류로 권한을 부여하지 않는다.
   내용 dedup 의미를 유지하기 위해 각 descriptor는 별도 fixture store로 검사한다.

각 exact1 PASS/248 filtered/exit0. 위 세 항목은 합성 정책 저장소/fixture 제품 경로이다.
실제 SQL 정책 저장소/trusted issuer/corpus6/signed16/한글 UI/전체 제품 Gate가 아니다.
fixture/개별 runtime 수용을 다른 Gate PASS로 승격하지 않는다.

## 자원·표현 관측

| 관측 | case036 | case037 | case038 |
|---|---:|---:|---:|
| 시스템 CPU 최고 |76.89|70.08|36.05|
| 제어 CPU 최고(머신 분모) |1.343570|1.724138|1.590457|
| 제어 private 최고 bytes |39768064|39919616|40030208|
| RAM 여유 최저 |41.6309|42.4553|42.9671|
| 제품 Job CPU 누적 초 |2.828|1.25|0.781|
| 제품 Job peak private MiB |31.75|27.92|23.8|
| 원 parent elapsed 초 |304.97|196.61|196.66|
| 원 완료 자원 표본 수 |803|655|655|
| 준비 metadata bound/fresh/finished |100/100/true|102/102/true|104/104/true|
| 준비 metadata 실제 읽기 bytes |161581778|163303867|164927732|
| Native warning / pause windows / 요청 대기 |0/0/0초|0/0/0초|0/0/0초|
| 보호 중단 / cleanup |null/true|null/true|null/true|

원98% 연속4표본 CPU STOP,95% 경고·서로 다른2냉각 표본·최대8windows, RAM·commit
보호는 그대로다. 세 호출은 Native 경고/보호 중단 없이 끝났다.
개별 workload와 호스트 부하가 달라 elapsed/CPU 차이를 동일 workload 성능 개선으로 계산하지 않는다.
제어 메모리/Job 정리/이 세 결과만으로 외부 PID·Defender·물리 IO 원인이나 PC 프리즈
해결을 확정하지 않는다. root 저장은 원 resource cleanup 뒤 terminal lifecycle 검사만
연결하므로 이 자원 표본이 root 저장 전체를 감시했다는 뜻도 아니다.

| 동일 JSON 값 | 원 compact bytes | 실제 carrier bytes | 크기 감소 |
|---|---:|---:|---:|
|case36 root|1700661|579232|65.9408%|
|case36 body|799761|187875|76.5086%|
|case37 root|1572935|562712|64.2253%|
|case37 body|610601|166147|72.7896%|
|case38 root|1573169|562368|64.2525%|
|case38 body|609562|163539|73.1711%|

원 P221의 carrier·해제 JSON 각16MiB/inflate64KiB/외부 pin·내부 원 길이/SHA/
EOF·추가 데이터 거부/canonical 값 대조를 그대로 사용했다.
semantic_fields_removed=0/original_files_rewritten=false/CPU improvement claimed=false.
모든 필드와 표본이 보존된 표현 크기 비교이며 CPU 성능 비교가 아니다.

## 실제 다음 소비자의 읽기 비용

| 준비 단계 | 실제 증가 bytes | 원 fresh 읽기 크기와 대조 |
|---|---:|---|
|case35→36|1662481|2×568292+3×175299|
|case36→37|1722089|2×579232+3×187875|
|case37→38|1623865|2×562712+3×166147|

세 증가량은 각각 이전 packed root2회+body3회의 실제 파일 크기와 정확히 일치했다.
압축 원장을 다음 consumer가 실제 사용하며 원 read/final fresh 횟수를 생략하지 않았다는 증거다.
해제·canonical 검사를 추가하므로 크기 감소만으로 CPU 개선을 주장하지 않는다.
저장 비용이 줄어도 미래 전체249의 시간·표본 예산이 충분하다는 증거는 아직 없다.

## 증거 pin

경로 기준 implementation/p09/evidence/locked-r07/.

| 파일 | bytes | SHA256 |
|---|---:|---|
|p222-case-036-run002.v1.json|579232|150494ac692875e83df34f9c0fed55a3b7a698b33fca928dc03153aa3cd1ac3f|
|cases/p222-case-036-run002.json|187875|1e514ecb3574c633f320357dc341e1e254c0c08071a82fa218ed039db3426067|
|p222-case-037-run003.v1.json|562712|c8335a3bdccd4f65bd78d4ae8b26cb3fa11d03a5ef6a87fbcc76d11cd9f9ff5b|
|cases/p222-case-037-run003.json|166147|3d894f23aa0cb81e8c7f7eb4290cfa8537f812805a178b156c5e362e904bf801|
|p222-case-038-run004.v1.json|562368|eb190905b98d648972c8184425a824e19ad8f7293639675cad455f3e9fd8315b|
|cases/p222-case-038-run004.json|163539|268a447c7bc2b7f6eb585294dfde16943c4c636156d8cba50c503001a2de52d2|

## 문서 동기화와 다음 경계

r87 두 현행 문서의 receipt pin과 실제 길이/SHA를 대조해
evidence/runtime-progress-r87/에 복사했다. 같은 r88 prefix를 추가하고 원 byte suffix를 보존한다.
P222 문서 제공자로 실제 새 pair3개/원 runtime88계약/문서8계약/전체 final fresh/
원 문서 bytes·실패 원장 보존/cleanup/모든 Gate OPEN을 검증한다.
문서 제공자는 새 제품/frame을 실행하지 않는다. 보고서 작성 자체는 문서 PASS가 아니다.
별도 terminal r88 문서 receipt가 위 조건을 통과할 때만 문서 동기화를 수용한다.

CPU 보호 중단 시 자동 재시도 금지. 실패/CPU STOP/부분 원장/정리 실패는 재개를 막는다.
원본 보존→관련 코드·관측 검토→안전한 최적화→지원/실제 연결 검증 뒤 다음 미수용 항목을 진행한다.
다음은 같은 P222의 index39이다. 성공1~38 본문은 재실행하지 않는다.
P09 Gate가 권위 있게 닫히기 전 P10 새 구현으로 넘어가지 않는다.
