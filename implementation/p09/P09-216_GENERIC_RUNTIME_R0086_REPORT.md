# P09 r86: 동일 compact 진입점의 결과 byte·정책 검증31~33

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용33/249 · 잔여216(일반210+corpus6) · 미closing후보0 · 다음index34.
whole 수용3 / 통합 성공본문whole재조정대기30. 원 legacy pending1은 별도 범위다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 위 수치는 고정 r07 개별 runtime이고 P09 전체 완료율이 아니다.

## 제품 경로와 원 검증 범위

같은 P220 진입점/qualified compact writer/Native pressure helper/원 P208 parent·strict
validator source를 변경하지 않았다. 원 성공1~30 본문은 재실행하지 않았다.

1. case031/run002: document·branch·project·subject·tenant 5종 범위 대체에서 결과 준비와
   캐시된 byte 소비가 Source 오류로 거부된다. byte 소비 callback은 호출되지 않는다.
2. case032/run003: blob 변조·읽기 권한 철회·head 변경·격리 4종 변경 후 결과 준비/
   캐시된 byte 소비/현재 route가 모두 Source 오류로 거부되고 callback이 호출되지 않는다.
3. case033/run004: 원문과 이미 재계산된 입력 각각에서4개 formula target/allowed target 정책을
   bind/verify한다. 변경·현재 결과 후보가 재검증된 byte로 나오고 원 head/ingest·공개 경계는
   유지된다. debug 표현과 receipt의 원 비공개 필드 redaction assertion도 검사한다.

case033의 정책 저장소/키는 합성 fixture다. 원 artifact/source/compiler 검사는 유지하지만
실제 SQL 정책 저장소 연동이나 trusted issuer 자격은 아니다. qualification에는
NOT_trusted_issuer가 남고 현재 product route는 Product 오류로 거부된다.
일반 fixture 제품 경로 검증을 corpus6/signed16/실제 정책 저장소/전체 제품 Gate로 승격하지 않는다.

각 exact1 PASS/248 filtered/exit0/COMMITTED, Job cleanup/tree empty=true.
1498입력 전후 각118801078bytes 일치, 잠금1804/복제stream2996 모두close/잔여0.
실제 Native pressure frame 연결 및 실제 compact parent/root writer 연결은 유지됐다.
새 원장을 다음 호출/문서 제공자가 실제 읽고 canonical 표현의 길이/SHA까지 대조한다.
지원62계약은 매 호출 PASS이며 제품 본문을 추가로 실행하는 지원 테스트는 없다.

원 Rust785/고정EXE/두 전체 실제 byte 읽기/stream identity/seek/원 CPU·RAM·commit
보호/affinity1/BelowNormal/Job·GO·정리/600초/32open/s/no burst/
binary1·other2MiB/s 및 전체 bound input 최종 fresh hash를 그대로 유지했다.

## 자원·저장 관측

| 관측 | case031 | case032 | case033 |
|---|---:|---:|---:|
| 시스템 CPU 최고 |31.56%|40.15%|51.52%|
| 제어 프로세스 CPU 최고(머신 분모) |0.938086%|1.121495%|1.476015%|
| 제어 private 메모리 최고 bytes |39948288|39632896|38776832|
| RAM 여유 최저 |41.1412%|42.3184%|41.7335%|
| 제품 Job CPU 누적 초 |0.422|1.469|21.875|
| 제품 Job peak private MiB |25.88|26.83|34.66|
| 원 parent elapsed 초 |219.79|207.33|219.82|
| 원 완료 자원 표본 수 |660|648|710|
| 준비 metadata bound/fresh/finished |83/83/true|85/85/true|87/87/true|
| 준비 metadata 실제 읽기 bytes |135429283|140452102|145477066|
| Native warning / pause windows / 요청 대기 |0/0/0초|0/0/0초|0/0/0초|
| 본문 bytes / write batches |627379/20|634572/20|688629/22|
| 본문 최대 write chars |32768|32768|32768|
| 보호 중단 / cleanup |null/true|null/true|null/true|

case033은 원문·현재 결과를 모두 처리하며 Job CPU 누적21.875초였다. 이것을 시스템
CPU 풀로드나 코드 결함이라고 단정하지 않는다. 서로 다른 사례의 elapsed/CPU 차이는
동일 workload 성능 비교가 아니다. root 저장은 원 resource cleanup 뒤이므로 위 표본이
root 저장 전체까지 관측한 것으로 바꾸지 않는다. 외부 PID/Defender/물리 disk IO
원인·전체 CPU 개선·PC 프리즈 해결도 검증한 것이 아니다.

## 원장 읽기 비용 대조와 남은 예산 경계

| 준비 단계 | 관측된 증가 bytes | 추가 원장의 원 읽기 비용 |
|---|---:|---|
|case030→031|4913868|2×1542273(root030)+3×609774(body030)|
|case031→032|5022819|2×1570341(root031)+3×627379(body031)|
|case032→033|5024964|2×1560624(root032)+3×634572(body032)|

세 증가량이 각각 이전 새 root의2회/본문의3회 실제 읽기 크기와 정확히 일치했다.
compact 결과가 실제 다음 consumer에 연결됐다는 비용 증거이며 원 읽기/최종 재확인을
제거하지 않았다. P219 고정28 sample의 값 보존 크기 절감30.0462%/23.9468%는
별도 지원 증거다. 다른 사례 간 크기 차이를 같은 payload 절감률로 계산하지 않는다.

추가로 원 자원 collector/summary의1440표본 한도와 reader의600초 scope가 유지되는
코드를 확인했다. 누적 metadata와 실제 frame 작업은 한 owner의 수명에 포함되므로
현재33개 통과만으로 미래 전체249개의 결합 예산이 충분하다고 수용하지 않는다.
후속 전체 예산/범위별 수명 검토는 남은 최적화 경계이며 이번에는 owner/한도를 바꾸지 않았다.

CPU 보호 중단 시 자동 재시도 금지. Native 취득/GO 이전·metadata/admission 실패,
부분 JSON·정리 실패도 다음 실행을 막는다. 실패 원본을 보존하고 관련 코드와 관측을
검토해야 하며 guard/read scope/증거를 줄여 통과시키지 않는다.

## 증거 pin

경로 기준 implementation/p09/evidence/locked-r07/.

| 파일 | bytes | SHA256 |
|---|---:|---|
|p220-case-031-run002.v1.json|1570341|b30fe5d154ac1ccbd9d4a18f6b4d3259ce09939258d0ab3c433ad0a0ce1741ca|
|cases/p220-case-031-run002.json|627379|c26930d709c0288fcd466483bff46292a7727ee6d392a11541d90f9ff177546d|
|p220-case-032-run003.v1.json|1560624|885849bdd5aad4a136f43432a6342670db795324c66761c05559171836ac8e2b|
|cases/p220-case-032-run003.json|634572|c8b30d0554703b41f7077ccdb6da069a892f204d46d12d10b4fab8a8b69ee24a|
|p220-case-033-run004.v1.json|1613946|520e9b60a946537ced2e87424da0b79105c5b6274e75057d666d3b19a6c3e2d1|
|cases/p220-case-033-run004.json|688629|6f68db5fe234f996116a617164a6691365eae872c4bed3454bd18f8d0d06ec89|

## 문서 동기화와 다음 경계

원 r85 두 문서 bytes/SHA를 확인하고 evidence/runtime-progress-r85/에 복사했다.
동일 r86 prefix만 두 현행 문서에 추가하며 모든 원 byte suffix를 보존한다.
원 compact 문서 제공자는 P216 스키마/이력 보존, 원 strict/canonical 큐,62+8계약,
새 실제 세 root SHA/전체 bound input 최종 fresh hash/cleanup을 검증한다.
기존 성공 본문/전체 source frame은 다시 실행하지 않는다.

다음은 P220 case034 단독 실행이다. 누적 예산/범위별 수명 검토도 남아 있다.
corpus6/통합 whole closing/whole1470·historical67 최신성/전체249/signed16/P09 Gate는
미수용이고 P10로 넘어가지 않는다. Git/Cargo/build/SQL/Hangul/접근허용/OS·보안 설정
변경 없음. 원 STOP/FAILED는 보존한다.

