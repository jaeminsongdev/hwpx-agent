# P09-193 — 순차 재개 유지 및 metadata 관측

2026-10-08. 목표 active, P09/A12/A13 OPEN, product=false.
이번 단계에서는 product EXE/Cargo/SQL/Hangul/접근허용 검증을 시작하지 않았다.

## 제품 큐와 다음 경계

P191 case001 및 P192 case002/003은 정상 종료와 별도 whole closing으로 수용된 그대로다.
완료 3/249, pending 246 = 일반240 + 별도 고부하 corpus6. 다음 index4/attempt1.
이 수치는 현재 executable 테스트 큐이며 P09 전체 완료율/세부작업 수가 아니다.
compiled249=true/full249=false/signed16=false, 실제 Hancom/native/SQL Gate는 미수용이다.

통과 항목은 동일한 source/EXE/receipt binding과 closing 확인 후 재사용한다.
실패한 전수 실행의 이름별 결과가 봉인되지 않은 48개를 추가 완료로 세지 않는다.
다음 제품 실행은 `--max-cases 1`로 하나만 시작하고 원 exact/threads1/owned Job 경로를 유지한다.
기존 완료3을 재실행하지 않는다. fixture 계약검사와 입력 freshness 확인은 runtime 재실행과 다르다.
현재까지 새 case004는 NOT_RUN이며, corpus6과 접근허용 대상은 실행하지 않았다.

## 보완 범위

- 신규 `tools/p09/observe_shared_metadata_recheck.py`와 `tools/p09/tests/test_observed_shared_metadata.py`만 추가.
- 기존 P190/P191/P192 구현, 제품 Rust 소스, 원 통과/실패 receipt를 변경하지 않음.
- 원 `sync_shared_resumable_r07_progress.py` verify body를 어댑터에서 그대로 호출.
- 기존 .5초 수동 표본을 재사용. 각 표본에 현재 프로세스 메모리 query 하나만 추가.
- 원 parent CPU 분모/affinity/BelowNormal, resource 판단, 입출력 속도,600초 scope,최종 fresh 전체해시 유지.
- 내 private/working-set 바이트와 총RAM 비율, 공개 고정 phase label, 논리 reader byte/pass counter 저장.
- 새 sampler thread/외부 PID 조회/새 product child/임계치 완화/전역 설정 변경/삭제 없음.
- 한 표본은 여러 단계에 걸칠 수 있고 논리 읽기량은 실제 디스크 IO가 아니므로 원인 추정에 주의.
- query 실패를 0 사용량으로 바꾸지 않음. STOP/실패에도 완료된 표본을 제한된 allowlist로 보존.

메모리 API 근거: https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo

## 검증 및 실패 보존

`p09-193-metadata-observation.light-run01.v1.json`은 인자 어댑터의 `old.sys` 참조 오류로 계약검사 실패.
수정 전 helper/test 전체는 source-archive/p09-193-pre-argument-adapter-repair/에 보존했다.
light-run02는 원154 + 신규10 synthetic contract PASS다.

observe-run01은 기존 fixture reader도 바꾼 어댑터 때문에 BACKPRESSURE_ORIGINAL37_PLUS6로 실패했다.
수정 전 helper/test는 source-archive/p09-193-pre-reader-role-repair/에 보존했다.
실제 검증 소유자만 관측하고 fixture는 원 reader에 그대로 위임하도록 분리했다.
light-run03은 원154 + 신규10 PASS, resource_stop=null/cleanup=true다.

observe-run02는 P152_FULL_REDACTED_FAILURE, stop=null/cleanup=true로 미수용이다.
exception 상세는 당시 원 redaction 경로로 남지 않아 원인을 확정하지 않는다.
어댑터 연결 계약검사만 따로 확인한 결과154 및154+10 PASS였고,
다음 observed run03에서는 전체 metadata body가 정상 완료됐다.
run02 실패를 소급 PASS하거나 오류 원인이 해결됐다고 단정하지 않는다.
별도 관측 채널을 붙인 run03에는 error 자체가 없어 추가 exception frame이 출력되지 않았다.

최신 observe-run03:

- PASS_SHARED_R07_TWO_RUNTIME_CASES_AND_SKIP3_DOC_SYNC_ONLY_NOT_FULL_OR_GATE.
- 원154 + 신규 관측10 계약검사 PASS, stop=null, watcher cleanup=true.
- bound30/final fresh30/read71/26492401bytes/finished=true.
- 원 metadata 입력에 새 관측 controller/test와 원 P192 CPU STOP receipt를 추가 바인딩/최종 재해시.
- 기존 case3 완료/246 pending 계획을 확인했을 뿐 새 product test를 실행하지 않음.
- 현재 수정된 P192 보고서 문구와 두 상태 문서의 기존 r63 prefix/suffix 검사를 정상 완료.

관측 완료17표본: system CPU 최대78.17%, own parent CPU(machine) 최대2.714286%,
own private 최대51544064bytes(약49.16MiB), own working set 최대62541824bytes(약59.64MiB),
available RAM 최소15.7279901230875%.
이 구간의 내 프로세스가 CPU/RAM을 직접 전부 점유한 수치는 아니다.
과거 STOP 시점이나 IO로 인한 간접 부하, 외부 프로세스의 원인, PC 프리즈 해결을 입증하지 않는다.
시스템 여유RAM은 이 검사 도중 낮아졌으므로 이번 단계 후 새 제품 실행을 시작하지 않았다.

## 정확한 최신 증거

| 경로(implementation/p09/evidence/ 기준) | bytes | SHA256 |
|---|---:|---|
| p09-193-metadata-observation.light-run03.v1.json | 2938 | bab48be7eba9d84fd6c3e9266500210d19f3ff684e2f61098906b2dfd819ba01 |
| p09-193-metadata-observation.observe-run02.v1.json | 20868 | 1cbad95d90631713941d9ecf89bd1a4e4604f34b34691eea4e4aedd4ca15f852 |
| p09-193-metadata-observation.observe-run03.v1.json | 31498 | e4dbb16c6da6a53fc7567b43031b37aa21839deec5e6552ac632dbe0345d012e |

최신 관측 입력 helper 10213bytes/SHA49b0960aa6ffb4be31eec630c66f263938f9cbcbe2b65d52dff3d69be9fca735,
test 5733bytes/SHA7d6248ee6c9ece4ffefbde81f2291d50d008a0cbca03106e56dc4a062cf0fabe.
두 파일의 현재 bytes hash가 관측 receipt의 bound pin과 일치함을 확인했다.

원 P192 CPU STOP 및 P193 실패 기록은 모두 보존한다. CURRENT_STATE.md와 P09-149의 r63
본문은 제품 큐의 권위 있는 상태를 그대로 유지하며, 최신 metadata 관측의 권위는 이 보고서와 run03이다.
이 새 보고서가 observe-run03의 입력이었다고 주장하지 않는다(검사 완료 뒤 작성).
