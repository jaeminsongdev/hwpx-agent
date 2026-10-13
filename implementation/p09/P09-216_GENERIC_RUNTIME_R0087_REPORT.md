# P09 r87: 실제 무손실 원장 저장 연결과 runtime34~35

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용35/249 · 잔여214(일반208+corpus6) · 미closing후보0 · 다음index36.
whole 수용3 / 통합 성공본문whole재조정대기32. 원 legacy pending1은 별도다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 35/249는 고정 r07 개별 runtime 큐이며 P09 전체 완료율이 아니다.

## 관련 코드 검토와 이번 최적화

수용된 P220 소스/검증62계약/1~33 성공 본문은 변경·재실행하지 않았다.
P220 case034를 먼저 실행했고 이후 기존34를 봉인한 새 P222 진입점을 추가했다.
P221은 기존 P219 compact writer를 gzip level1/Base64 carrier에 연결하며 전체 JSON 값,
필드 순서, 표본, Unicode를 보존한다. 지원16계약과 고정32번 표본의 값/원본 대조가 통과했다.
지원 표본 root64.1285%/본문73.5880% 크기 감소는 실제 제품 경로 PASS와 구분한다.

P222는 원 P208 parent의 최종 writer만 원 Native frame checkpoint에 연결한다.
기존 ensure_ascii=False/indent=2 호출 형태를 엄격히 확인한 뒤 무손실 표현으로 저장한다.
superclass Reader의 원 fresh 실제 읽기/최종 hash를 유지하고 carrier의 외부 길이/SHA,
gzip 해제 길이/SHA/EOF/추가·연결 데이터 거부/내부 canonical JSON 대조를 추가한다.
carrier·해제 JSON 각16MiB 제한, inflate 호출 최대64KiB, 원 compact 출력32KiB를 유지한다.
원본·실패 원장은 재작성하지 않는다. 새 지원 계약은 자식/스레드를 만들지 않는다.
P222 light와 실제 case035 각각 원62+지원16+새 bridge10=88계약 PASS.
공식 기술 근거: https://docs.python.org/3/library/zlib.html (max_length/eof/unused_data/unconsumed_tail).

실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결이 case035에서 확인됐다.
원 Rust785/고정EXE/전체 입력 두 실제 byte 읽기/stream identity/seek/CPU·RAM·commit 보호,
affinity1/BelowNormal/Job·GO·정리/600초/32open/s/no burst/binary1·other2MiB/s가 유지됐다.
새 원장 소비자는 외부 파일 pin을 fresh 읽기로 대조하고 전체 값을 풀어 원 strict validator에 전달한다.
root writer는 원 resource cleanup 뒤에 실행한다. 원 terminal lifecycle 검사만 연결하며,
새 sampler/admission을 만들지 않는다. 아래 자원 수치가 root 저장 전체까지 관측했다는 뜻은 아니다.

## 실제 제품 경로 검증

- case034/run005: 허용 합성 정책이 있어도 원문/현재 입력의 section1 native protection이나
  잘못된 두 번째 section을 우회해 결과를 준비하지 못한다. 세 입력 모두 공개 경계를 유지한다.
  HWPX XML/fixture 경로이며 실제 한글 앱의 보안 설정 검증은 아니다.
- case035/run001: 원문/현재 재계산 입력 각각에서 정책/결과 ACL 철회, 정책/결과 격리,
  AEAD blob 변조, head 변경의6종 변경 뒤 cached 결과 byte 소비와 재준비가 거부된다.
  callback은 호출되지 않으며 head 변경을 제외한 경우 no_publication assertion을 확인한다.
  합성 정책 저장소/fixture이며 실제 SQL/trusted issuer/한글 접근 허용 검증은 아니다.

각 exact1 PASS/248 filtered/exit0, owned tree empty=true.
34는1498입력 전후 각118801078bytes;35는1503입력 전후 각118841107bytes.
35의 frame COMMITTED, 잠금1809/복제stream3006 모두close/잔여0/close failure0.
입력 범위 제외나 원 두 byte 읽기 생략은 없었다.

## 관측과 크기

| 관측 | case034 | case035 |
|---|---:|---:|
| 시스템 CPU 최고 |80.7%|96.5%|
| 제어 CPU 최고(머신 분모) |0.968992%|1.165049%|
| 제어 private 최고 bytes |40030208|39837696|
| RAM 여유 최저 |40.9812%|41.1607%|
| 제품 Job CPU 누적 초 |2.875|22.031|
| 제품 Job peak private MiB |29.16|32.74|
| 원 parent elapsed 초 |221.97|230.39|
| 준비 metadata bound/fresh/finished |89/89/true|98/98/true|
| 준비 metadata 읽기 bytes |150770845|159919297|
| 보호 중단 / cleanup |null/true|null/true|

case035 Native warning1회/완료 냉각표본2개/요청대기1초.
원 기존95% 경고·2개 서로 다른 냉각 표본·최대8windows/98% 연속4표본 hard stop을
변경하지 않았다. warning pause 실제 동작은 확인했지만 96.5%의 외부 원인은 식별하지 않았다.
제어 낮은 CPU나 종료 시 Job 정리만으로 Windows 프리즈 해결을 확정하지 않는다.
자원 표본710개/한 owner/새 sampler 없음. 전체249의 결합 수명·600초 reader/1440표본
예산 충분성은 여전히 미수용이다. 압축 저장이 미래 예산을 보장한다는 주장은 하지 않는다.

| 동일 JSON 값 | 원 compact bytes | 실제 carrier bytes | 감소 |
|---|---:|---:|---:|
|case035 root|1619666|568292|64.9130%|
|case035 body|707931|175299|75.2378%|

root gzip426007bytes/body gzip131265bytes. 모든 필드·표본 보존/semantic_fields_removed=0,
original_files_rewritten=false. 같은 payload의 표현 크기 비교이며 CPU 속도 비교가 아니다.
case034→035 준비 비용에는 새 helper source/support/light의 검사도 포함된다.
다른 사례의 elapsed/CPU/metadata byte 차이를 동일 workload 개선으로 계산하지 않는다.

## 증거 pin

경로 기준 implementation/p09/evidence/locked-r07/.

| 파일 | bytes | SHA256 |
|---|---:|---|
|p220-case-034-run005.v1.json|1588449|49c1280ee39dac81d4140dba7ba0890b24375a87c659111bf561f8888889f6d8|
|cases/p220-case-034-run005.json|654324|6b24709076f77d02a506df32fd5b38767c9b3fc69f1bf4841fc25d2114a0cd9f|
|p221-packed-receipt-light-run01.v1.json|18137|c01529a6ade583042ef46fb5aef544f32a96cb7243a013bc73e23c1a3a3a554c|
|p222-case-035-run001.v1.json|568292|0b855f63cf3e789bfdd89b279f2cc179dbf98f349707a61c7dba7a1c6132659f|
|cases/p222-case-035-run001.json|175299|a48d1d3a8e3dcf41fcf833604eab0df010f0eefeed62cf188e509839a50c860e|

## 문서 동기화와 다음 경계

r86 두 현행 문서의 기존 receipt pin과 실제 bytes/SHA를 대조해
evidence/runtime-progress-r86/에 복사했다. 동일 r87 prefix를 추가하고 원 byte suffix를 보존한다.
새 doc provider는 P222 Reader로 새 carrier를 풀고 원 P216 문서8계약/원 runtime strict
검사/최종 fresh hash/정리를 수행한다. 문서 검사는 제품/frame을 재실행하지 않는다.
수용 기준은 새 실제 pair2개(34/35),88+8계약, 원 문서 bytes/실패 원장 보존,
bound=final fresh/finished/cleanup=true/오류·stop=null 및 모든 Gate OPEN이다.
해당 문서 receipt가 terminal PASS일 때만 r87 동기화 수용이며 이 보고서 작성 자체는 PASS가 아니다.

CPU 보호 중단 시 자동 재시도 금지. CPU STOP/실패/부분 원장/정리 실패는 재개를 막는다.
실패 원본 보존→해당 코드와 관측 검토→범위 안 최적화→별도 지원/제품 연결 검증 뒤 진행한다.
다음은 같은 P222의 미수용 index36이다. 성공1~35 본문은 재실행하지 않는다.
한글 접근 허용/전체 build/Git/SQL/Defender·WSL·OS 설정/삭제·이동 작업은 실행하지 않았다.
