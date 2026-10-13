# P09 P216 r80: 동일 진입점으로 runtime16~18 계속 실행

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.

runtime 수용18/249 · 잔여231(일반225+corpus6) · 미closing후보0 · 다음index19.
whole 수용3 / 통합 성공본문whole재조정대기15. 원 legacy pending1과 범위가 다르다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
이는 고정 r07 실행 파일의 개별 runtime 진행이고 P09 전체 완료율이 아니다.
PC 프리즈 원인·해결 미확정.

## 실제 제품 경로와 결과

P215의 실행·잠금·borrowed stream·원 strict validator source를 수정하지 않았다.
기존 1~15번 성공 본문은 다시 실행하지 않았고 원 큐에서 다음 사례만 선택했다.

1. case016/run003: ACL 철회 후 새 의미 가져오기와 캐시 의미 검증이 모두 거부된다.
2. case017/run004: 부분 의미 모델의 개별 마커만으로 전체 컨텍스트를 얻지 못한다.
3. case018/run005: 실제 필드 그래프/컴파일 후보는 전체 가져오기·발급 권한이 아니다.
   native recalculation 미검증을 유지하고 debug/receipt의 대상 값 노출을 거부한다.

각 실제 본문 exact1 PASS/248 filtered/exit0, 원 Job cleanup/tree empty=true.
각 source 전후 실제1488입력 각118737453bytes 일치, frame COMMITTED.
READ 잠금1794/복제stream2976 전부close, 잔여0/active binding0.
원 전체 두 byte 읽기·stream identity·seek(0)·600초 deadline·32open/s 및 원 pacing 유지.
원18개 지원 계약은 각 actual에서 통과했으며 별도 제품 계약 수로 합산하지 않는다.

| 관측 | case016 | case017 | case018 |
|---|---:|---:|---:|
| 시스템 CPU 최고 |83.99%|81.28%|79.10%|
| 제어 프로세스 CPU 최고(머신 분모) |1.086957%|1.470588%|0.793651%|
| 제어 private 메모리 최고 bytes |37810176|38436864|38133760|
| RAM 여유 최저 |43.9804%|41.4282%|43.1866%|
| 제품 Job CPU 누적 초 |0.156|0.125|1.250|
| 제품 Job peak private MiB |21.04|17.89|28.38|
| 준비 metadata bound/fresh/finished |32/32/true|34/34/true|36/36/true|
| 보호 중단 / 정리 |null/true|null/true|null/true|

전후 전체 reader의 near-saturation warning entries는 모두0이다.
시스템 CPU 관측을 제어 프로세스 CPU와 혼동하지 않는다. foreign PID/Defender/
물리 disk IO 원인이나 프리즈 해결은 증명하지 않았다. owned Job의 CPU/RAM 비율
제한, affinity1/BelowNormal, 원 host CPU/RAM/commit hard stop을 유지했다.
CPU 보호 중단 시 자동 재시도 금지: 증거 보존, 중단 구간 코드·표본·정리 검토,
관련 최적화와 검증을 완료한 뒤에만 다음 실행을 수용한다.

## 고정 문서 동기화 검증기

`sync_generic_runtime_document_delta.py`는 앞으로도 같은 source로 다음 revision을
검증하도록 구성했다. 실행 원장을 원 `g.anchor`/`g.progress`/strict validator로
재검증하여 현재 수용 수/잔여/다음index/whole 재조정 수를 직접 계산한다.
수용 수나 통과 수를 CLI 인자로 지정하지 않는다. 새 제품 실행/전체 source frame 없음.

이전 문서 receipt의 정확한 ROOT_DOCS pin을 보존본과 대조하고, 두 현행 문서의
동일 새 prefix 및 이전 exact byte suffix를 검사한다. manifest/외부 경로를 통해
다른 파일을 읽도록 바꾸지 못하게 이전 receipt/report 경로와 revision을 제한한다.
최종 bound input 전체 fresh hash·resource stop·watcher 정리까지 끝난 뒤에만
overall PASS를 기록한다. corpus index와 수용 개수가 다른 경우도 이전 수용 이름
집합으로 새 실제 receipt를 구분하며 index를 완료 수와 혼동하지 않는다.

새8개 지원 계약은 경로/revision/이전 오류/CPU 중단/문서 pin 중복/제품 승격 거부
및 입력 불변성을 검사한다. 원18개 큐 계약과 구분한다. 전역/OS/보안 설정 변경,
Git/Cargo/build/SQL/Hangul/접근허용 실행은 없다.

r79 문서는 이전 수용 receipt의 bytes/SHA와 현재 파일이 일치함을 확인하고
`implementation/p09/evidence/runtime-progress-r79/`에 복사했다. r80 prefix를 추가하되
아래 전체 원문 bytes를 보존한다. 동기화 결과는 별도 새 receipt에 기록하며 이전
문서 검사 source/receipt 및 원 실패 증거를 다시 쓰지 않는다.

## 실제 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p215-case-016-run003.v1.json`|2052894|`582ede6d0779f8b4c9b8f9bbce8214a80f93682cdd226a510bb5999ea8b9c70f`|
|`cases/p215-case-016-run003.json`|791902|`c991091404e3f5cd976cbe48ccc23679d993c155b2e6ea9b1acf588380d2d7ee`|
|`p215-case-017-run004.v1.json`|2110917|`035ee1f3a7139cc12825659ec349253ed7edd2fbb3bbee42330657c82a0a2884`|
|`cases/p215-case-017-run004.json`|825111|`052303cdb4d677eb2b954913f8b52947b6449be8832c6165856e9279683729cc`|
|`p215-case-018-run005.v1.json`|2110684|`8482d13e956c84db753f1d4129244b73b8382e8e0a14b997645965b4e84e1b1a`|
|`cases/p215-case-018-run005.json`|798725|`b8ccc141ada8c06c658e37bdcd0185654144b88d506f7ffd61c7bb2ecdf12ccc`|

다음은 case019 단독 실행이다. 실제 성공 사례를 건너뛰되 corpus6/통합 closing/
whole1470·historical67 최신성/전체249/signed16/P09 Gate를 완료로 간주하지 않는다.
