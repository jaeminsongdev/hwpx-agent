# P09 r90: issuer 일반5개 수용과 corpus 잔여 분리

2026-10-09 문서 반영. 실제 실행 시각과 이전 날짜의 원장/문서는 변경하지 않는다.
목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용48/249 · 잔여201(일반195+corpus6) · 미closing후보0 · 다음index55.
whole 수용3 / 통합 성공본문whole재조정대기45. 원 legacy pending1은 별도다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 48/249는 고정 r07 개별 runtime 큐이며 P09 전체 완료율이 아니다.

## 제품 실행과 코드 경계 검토

r89 문서 receipt runtime43/다음44/131bound=fresh/finished/cleanup/오류·stop=null/
기존 CPU peak 보정 진단 보존을 현재 파일에서 확인했다.
같은 P222 source로44→45→46→53→54를 직렬 exact-one 실행했다.
기존 성공1~43 본문/수용된 driver·tests/P219 compact/P221 packed/원 P208 parent·
strict validator/Native pressure source를 수정·재실행하지 않았다.
매 실행88계약 PASS이며 서로 다른440개 계약이라는 뜻은 아니다.
이번에는 CPU 보호 중단/Native pressure 경고가 없어 제품 검증 소스를 재수정하지 않았다.

runtime_source_closing_r07.py의 runtime_plan은 pending 전체를 유지하고 CORPUS_PREFIX
항목을 heavy로 별도 분류한 뒤 runnable 일반 항목을 선택한다. 따라서 이 큐는 corpus6을
통과로 간주하지 않고46 다음53을 선택한다. 기존 select의 unsupported corpus 거부도 유지했다.
issuer.rs의 MAX_APPROVAL_BYTES=16384/MAX_CLAIMS_BYTES=8192를 추가 확인했고 상한을
늘리지 않았다. 원16MiB 원장 cap/32KiB 출력/64KiB inflate/한 sampler/600초/1440표본/
CPU·RAM·commit/32open/s/no burst 및 source 읽기 binary1·other2MiB/s를 유지했다.

## 실제 제품 검사

- case044/run010: 승인 증거 ACL 철회·격리·AEAD 변조·최신 철회 뒤 fresh/cached 결과를
  거부한다. source/policy 승인과 승인 증거의 fresh 검사 경계를 구분한다.
- case045/run011: source.verify와 원 정책 binding은 유효하고 승인 artifact에만 AEAD 변조가
  적용되는 별도 provider에서 byte 소비/callback/새 준비를 거부한다.
  승인 target 변조의 matches가 증가하며 callback은 호출되지 않는다.
- case046/run012: document·branch·project·subject·tenant 다섯 외부 scope의 byte 소비를
  거부한다. policy generation2 뒤 옛 cache 거부/새 준비 유효/current bytes 일치 확인 후,
  옛 승인 서명 재설치 시 새 준비와 fresh cache 소비도 거부하고 공개 경계를 보존한다.
- case053/run013: fixture에서 생성한 Ed25519 승인으로 원문/현재 입력 각각의 준비·재검증·
  current 결과 byte·변경 여부 및 권한 있는 reader를 검사한다. debug/receipt redaction/
  no_publication도 검사하고 require_current_product_route는 여전히 거부된다.
- case054/run014: 실제 fixture 키로 다시 서명한22개 foreign source/policy binding,
  audience/operation/trust generation/issuer/key/schema 변형이 제품 준비 권한이 되지 못한다.

위 항목들은 합성 store/trust/clock과 fixture crypto 제품 경로이다. 유효한 Ed25519 서명은
실제 운영 issuer/SQL 등록·corpus16·Native UI·transport/atomic/Gate 인수의 증거가 아니다.
고정 issuer 그룹35개 중 현재5개 개별 runtime 수용이며 나머지 그룹30개(일반24+corpus6)는
이 그룹 기준 미수용이다. 이전 formula_policy 그룹11개 수용과 섞어 전체 정책 인수로 승격하지 않는다.

실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결을 유지했다.
각 exact1 PASS/248 filtered/exit0/COMMITTED, 전후1503입력 각118841107bytes 일치.
잠금1809/복제stream3006 모두close/잔여0/close 실패0, Job active0/tree empty=true.
원 Rust785/고정EXE/두 전체 실제 byte 읽기/identity/seek/최종 fresh hash/affinity1/
BelowNormal/Job·GO·정리/원 guard를 유지했다. 검사 범위나 read/final fresh를 생략하지 않았다.
Git/build/SQL/한글 접근 허용/Defender·WSL·OS 설정/삭제·이동은 실행하지 않았다.

## 선택 index와 수용 수

|선택 index|누적 수용|전체 잔여|corpus 잔여|다음 일반 index|
|---|---:|---:|---:|---:|
|44|44|205|6|45|
|45|45|204|6|46|
|46|46|203|6|53|
|53|47|202|6|54|
|54|48|201|6|55|

47~52 corpus6은 실행하지 않았으며 NOT_RUN/미수용으로 남는다.
선택index54를 수용54개로 세지 않는다. 실제 수용48과 잔여201은 원 runtime plan에서 파생했다.
corp/signed16/full249/whole 재조정/P09 Gate는 여전히 별도 미완료 범위다.

## 자원 관측

|관측|case044|case045|case046|case053|case054|
|---|---:|---:|---:|---:|---:|
|시스템 CPU 최고(%)|59.50|34.10|29.88|82.39|87.69|
|제어 CPU 최고(머신 분모 %)|1.351351|1.383399|1.335878|1.375246|1.270417|
|제어 private 최고 bytes|40685568|41197568|40624128|40386560|40820736|
|RAM 여유 최저(%)|41.8396|41.0206|43.2139|42.0102|37.8891|
|제품 Job CPU 누적 초|5.766|3.688|13.219|41.578|2.25|
|제품 Job peak private MiB|29.63|28.75|34.62|34.9|24.08|
|원 parent elapsed 초|203.61|253.33|208.87|239.57|235.8|
|원 자원 표본 수|680|764|693|753|736|
|준비 bound/fresh/finished|116/116/true|118/118/true|120/120/true|122/122/true|124/124/true|
|준비 실제 읽기 bytes|174984550|176622095|178314860|179958153|181641386|
|Native warning / pause windows|0/0|0/0|0/0|0/0|0/0|
|보호 중단 / cleanup|null/true|null/true|null/true|null/true|null/true|

이번 다섯 시스템 CPU 최고는87.69%, RAM 여유 최저는37.8891%이다.
case053 Job CPU 누적41.578초는 다른 negative 사례보다 길지만 서로 다른 workload이며
풀로드·코드 결함·성능 개선으로 단정하지 않는다. 같은 workload 성능 비교를 실행한 것은 아니다.
제어/Job 메모리와 종료 정리만으로 PC 프리즈 해결을 확정하지 않는다.
root 저장은 원 resource cleanup 뒤 terminal lifecycle 검사이며 위 표본이 root 저장
전체를 감시했다는 뜻이 아니다. 전체249 결합 수명/600초 reader/1440표본 예산은 미수용이다.

## 이전 CPU peak 보존

r89 case043의 시스템 CPU 100% 두 연속 표본은 원인 미확정으로 유지한다.
Job 값 없음은 0이 아님. P223 원본과 P224 보정8계약/6bound=fresh/cleanup 증거를 보존하며
해당 Job active4/머신 CPU 최대0.483665%와 태그admission의 해석 경계를 유지한다.
이 보정 진단은 case043 고정 증거이며 이번 다섯의 원인을 새로 확정한 결과가 아니다.
직접 CPU가 낮아도 간접 OS/Defender 부하와 외부 PID 원인은 확정하지 않는다.
P225 문서 제공자가 P224 pin·6원 입력/원 P222 문서 provider를 다시 fresh 대조한다.
고정 진단 pin: p224-cpu-peak-review-run01.v1.json/8727bytes/
659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254.

## 동일 JSON 크기와 다음 consumer 비용

|동일 JSON 값|원 compact bytes|실제 carrier bytes|크기 감소|
|---|---:|---:|---:|
|44 root|1596445|566612|64.5079%|
|44 body|634807|168107|73.5184%|
|45 root|1668207|573960|65.5942%|
|45 body|765012|181615|76.2598%|
|46 root|1607703|567800|64.6825%|
|46 body|654946|169231|74.1611%|
|53 root|1658954|571276|65.5641%|
|53 body|757979|180227|76.2227%|
|54 root|1645621|572908|65.1859%|
|54 body|708068|177227|74.9703%|

필드·표본 보존/semantic_fields_removed=0/original_files_rewritten=false.
외부 file pin/내부 길이·SHA·canonical JSON/EOF·추가 데이터 거부를 유지한다.
위는 같은 JSON 값의 표현 크기 비교이며 CPU 성능 개선 주장이 아니다.

|준비 단계|실제 증가 bytes|원 fresh 읽기 대조|
|---|---:|---|
|43→44|1728901|2×585368+3×186055|
|44→45|1637545|2×566612+3×168107|
|45→46|1692765|2×573960+3×181615|
|46→53|1643293|2×567800+3×169231|
|53→54|1683233|2×571276+3×180227|

각 증가량은 이전 root2회+body3회의 실제 packed 크기와 일치했다.
비연속 index46→53에서도 그 전에 실제 수용된46 원장을 소비하며 corpus 본문은 재실행하지 않는다.
저장 비용 감소가 미래 전체249 예산 충분성을 보장하는 것은 아니다.

## 증거 pin

경로 기준 implementation/p09/evidence/locked-r07/.

|파일|bytes|SHA256|
|---|---:|---|
|p222-case-044-run010.v1.json|566612|e1fe24a5060102fe48c5153cd9a57d3eae323e679757ca36ed66fe1ac186b8c3|
|cases/p222-case-044-run010.json|168107|15a63e1069dbef3fd7b0e85d15b9223ffb1da9b0b9f45f7b8d6e988c72178461|
|p222-case-045-run011.v1.json|573960|cbc5b72e400a5afb7c94c3046eeb65655357df80180d4db06cdb0749ccf41d30|
|cases/p222-case-045-run011.json|181615|72109a976d528c3c9b94319859b1f6efc90e124a2471eb73f2e95106f4d87b6c|
|p222-case-046-run012.v1.json|567800|ddba0b8ef2f4dffcfe5fbf8cb1d55938f1bc2cb034abedf90ed389372b1115c5|
|cases/p222-case-046-run012.json|169231|6d28d549452662e4229ccfb17f884a56f290d0390b259a20295c6153294a0171|
|p222-case-053-run013.v1.json|571276|f64dbc2d4195bd453d5c8d9654a2e47145d0e8b0462fe618f88bdaabad2681ef|
|cases/p222-case-053-run013.json|180227|d177593a569981889b6fc6cd3fae94d700610fa0af56ea1e77ca6d9996af8b8b|
|p222-case-054-run014.v1.json|572908|6568ff02a570deb252be18ccdfd25a89cb38e04204860a52d9745f3aeb6e9a17|
|cases/p222-case-054-run014.json|177227|a8885e500ac70cad6aebd55498d8d097288b9b79ceb4b293f56bd5d3720b1b82|

## 문서 동기화와 다음 경계

r89 두 문서의 기존 receipt pin/길이/SHA를 대조해 evidence/runtime-progress-r89/에 복사했다.
동일 r90 prefix를 추가하고 원 byte suffix를 보존한다. 실행 시각·원 날짜를 재작성하지 않는다.
같은 P225로 새 pair5개/runtime88+문서8계약/고정 진단8계약 receipt/
최종 전체 fresh/문서 bytes·실패 보존/cleanup/오류·stop=null/Gate OPEN을 대조한다.
보고서 작성 자체는 문서 PASS가 아니며 별도 terminal r90 receipt로만 동기화를 수용한다.
문서 검증은 새 제품/frame을 실행하지 않는다.

CPU 보호 중단 시 자동 재시도 금지. 실패/CPU STOP/부분 원장/정리 실패는 재개를 막는다.
관련 코드·관측 검토→안전한 최적화·지원/실제 연결 검증 후 다음 미수용 항목을 진행한다.
다음은 같은 P222의 index55이다. 기존 성공48개 본문은 재실행하지 않는다.
P09 Gate가 권위 있게 닫히기 전 P10 새 구현으로 넘어가지 않는다.
