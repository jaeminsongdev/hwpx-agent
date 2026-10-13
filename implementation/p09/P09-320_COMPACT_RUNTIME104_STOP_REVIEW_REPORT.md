# P320~P321: compact runtime 연결과 actual104 CPU STOP 검토

2026-10-09. 목표 ACTIVE, P09/A12/A13 OPEN.

## 현재 수용 상태

개별 runtime 97/249 수용, 잔여152(일반146 + corpus6), 다음104.
whole 재조정94, source 마감 미완료 후보0. 이번104는 수용0이며 제품 테스트를 시작하지 못했다.
이 수치는 P09 전체 완료율이 아니다. whole1470/historical67/full249/signed16/product 완료 및 PC 프리즈 해결은 미확정/FALSE다.

## 이번 구현과 최적화

새 `tools/p09/resume_compact_completed103_runtime.py`와 해당 test에 qualified P318 compact 체크포인트를 실제 runtime 경로로 연결했다. 기존 수용96 literal checkpoint, 원103 root/body, 현재 불변 code81, 새 compact reviewer/test2 및 runtime/test2를 바인딩한다. 이전 source1644를 그대로 유지하고 새4만 포함한 예정 범위는1648개/120,579,465bytes, ancestor308/controller181/code85다.

과거 authority 전체 체인 재구성 대신 독립적으로 qualified된 체크포인트를 사용한다. 현재 코드의 live/final-fresh 읽기, 원 source 두 전체 byte/Native identity 검사는 유지한다. 성공한 제품 본문은 다시 실행하지 않는다. CPU/RAM/600초/720읽기/Job/cleanup 보호도 유지한다.

정식 light에서 현재100 + following100 =200 실제 동작·거부 계약 PASS. 각 검사 전후200회 및 runner 전후2회를 기존 checkpoint로 확인했다. 과거 원78/compact26/helper21/retained1486은 qualified 결과를 재사용한 것이며 이번200 실행에 합산하지 않았다. 새 sampler/thread/sleep 또는 검사 제외는 없다.

정식 light: 94bound/fresh94/188read/6,952,952bytes. 독립 light 검토:95bound/fresh95/190read/7,020,826bytes, cleanup TRUE/STOP 없음. 200 계약 PASS는 제품104 PASS나 새 code85 전체 Native qualification이 아니다. formal light/actual 이후 해당 소스와 테스트는 수정하지 않았다.

## actual104: 1회 시도, 미수용

실행: `python -B tools/p09/resume_compact_completed103_runtime.py --mode actual --run 2`.

원 부모 반환은 DEFERRED_NOT_STARTED, error/resource STOP은 STOP_SUSTAINED_SYSTEM_CPU. 실제 제품 child FALSE, exit_code NULL, tests_passed NULL, elapsed86.18초, owned_tree_empty TRUE, cleanup TRUE다. 바깥 PowerShell exit0을 actual exit2/PASS로 취급하지 않는다.

- 준비95bound/fresh95/190read/7,020,826bytes와200 계약은 완료.
- Native acquisition1956개 완료 후 원20rate 복원. 전체 Native 핸들1956open/1956close/잔여0.
- source-before는1155/1648개,76,579,293bytes까지만 읽고 STOP. binary0/other76,579,293. before/after 두 전체 source 검사 완료가 아니다.
- borrowed duplicate1155open/1155close/offset resets1155/잔여0, pathname reopen0, active stream0.
- Frame CLOSED/등록해제, actual_byte_boundaries=[]/closing identity NULL. COMMITTED나 source PASS가 아니다.
- after_acquire140.1389725초, 원 first error226.3221415초 < 원600초. cleanup은 pressure/guard에 막히지 않는다.
- 원 부모 실패 sidecar87,572bytes와 빈 body placeholder0bytes를 불변 보존했다. 같은 실패 namespace 재시도를 하지 않는다.

원 root: `evidence/locked-r07/p320-case-104-run002.v1.json`,492,480bytes,SHA256 `f7c9a7a9e18bb436fc572fd87f2d62510afa0c51ada5c825b8683c85861250d4`.
원 sidecar: `evidence/locked-r07/cases/p320-failure-104-run002.json`,87,572bytes,SHA256 `99d5c8d3bf85a7388e8a8702d97159d789688fd39a6707116687fa05a766ef66`.

## CPU/RAM 관측과 원인 경계

기존 watcher484표본: system 최대100%, own 최대6.352087%, private45,645,824bytes/working set56,193,024bytes, 가용RAM 최소20.9935516855%. 마지막4개는 system100%/parent0%, logical read 증가800,218/0/0/0bytes, phase metadata_hash. 논리 읽기를 실제 디스크 I/O로 해석하지 않는다.

별도 전후 raw PerfProc2 query,249.2225964초 창: 비교357/drift4제외/종료10/새23, host busy 평균17.212485%. 평균 상위 RadeonSoftware5.005409%,System3.240154%,MsMpEng2.518378%; Git2 평균0%. endpoint 사이 생성·종료된 Python은 비교에서 빠졌으며0%라고 주장하지 않는다. 이 긴 평균은 순간100% 원인, 검증이 외부 부하를 유발한 인과, PC 프리즈 해결을 증명하지 않는다. 별도 counter를 원 guard에 공급하지 않았다.

## STOP 이후 관련 코드 전수 범위 검토

이번 STOP 호출 경로와 인접 코드만 bounded하게 확인했다.

- `sql_percentage_resources.py`: sample lock으로 system delta 측정 직렬화. watcher가 있으면 checkpoint는 두 번째 측정기/스레드를 만들지 않는다. 기존0.5초 watcher와98% 연속4회 보호 유지.
- `conservative_maintenance.py`/`pre_go_parent_cpu_observer.py`: GetSystemTimes total/idle 차분과 own ProcessTimes의 동일 분모 확인. affinity1/BelowNormal 유지. 이 경로에 계산 race나 전체 CPU와 own CPU 혼동은 발견하지 못했다.
- `build_current_issuer_probe.py`: 기존 표본 freshness 확인/재사용. 새 query loop 없음.
- `leading_metadata_entry_pressure.py`/`review_checkpoint_queue_stop.py`: hard guard 먼저, 기존 표본 재사용, bounded0.5초 대기/최대8window/원callback복원. 무한 busy-spin 없음.
- `weighted_audit_io.py`:64KiB/no idle burst/최대64예약대기, sleep 최대0.05초 전후 원 checkpoint. full byte 검사는 유지.
- `qualify_rejected_parent_connection_r2.py`: 부모1회 실행과 기존 failure capture. 성공 본문 재실행 없음.
- `receipt_compact_json.py`/`packed_receipt_json.py`:32KiB 쓰기/64token checkpoint, bounded16MiB gzip/inflate64KiB 및 원SHA/canonical 검증. 실패 root 직렬화는 STOP 이후이므로 source 단계 peak의 원인이라고 주장하지 않는다. 증거 형식을 임의 압축하거나 표본을 제거하지 않았다.

추가로 기록 순서 문제를 찾았다. runtime은 부모 반환 뒤 `held.mark('after_parent')` 원 guard를 호출하고 나서 capture.pending 표시를 넣는다. 이 guard가 먼저 STOP을 내면 root의 `original_parent_STOP_captured_not_accepted`가 누락된다. sidecar에는 원 상태가 보존되어 있다. 이것은 진단 정확성 문제이지 CPU 폭주 원인의 증거는 아니다. 이미 실행한 P320은 불변 보존한다. 다음 새 세대에서 원 반환/capture 상태를 guard 직전에 기록하고 같은 guard를 그대로 호출하는 최소 수정 및 거부 계약 검증이 필요하다. 아직 수정·runtime 연결 완료로 주장하지 않는다.

## 독립 STOP 검토 증거

첫 read-only 검토는 admission에서 DEFERRED_ALREADY_SATURATED_SYSTEM, Reader/Native/제품 전 유예였다. hard98x4 STOP로 바꾸지 않았다. 실패780bytes를 별도 보존했다.

코드 검토 뒤 완료된 독립 read-only 검토는 root/raw counter/sidecar3개를 live/final-fresh 읽었다:3bound/fresh3/6read/1,685,404bytes, cleanup TRUE/STOP 없음. 원 counter helper로 창을 재계산했다. 제품 재시도0. 증거 `p321-compact-runtime104-stop-review-run01.v1.json`는 진단 결과이지 수용 결과가 아니다.

## 다음 안전한 단계

문서 마감 첫 검증 스크립트는 실패104 root에 PASS/LIGHT 전용 closed_attempt classifier를 적용하는 잘못된 호출을 포함했다. 해당 classifier는 실패를 정상 거부했고 마감 결과는 FAILED_NOT_ACCEPTED였다. watcher 정리 TRUE/STOP 없음만 반환 끝부분에서 확인되며 전체 stdout이 표시 budget에 의해 잘려 상세 error/부분 IO는 복구되지 않았다. 잘린 출력과 정확한 명령은 p322-r127-status-truncated-failure-run01.v1.json에 보존했다. 이것을 CPU STOP나 문서 PASS로 바꾸지 않는다. 이후 스크립트에서는 기존 실패 schema/STOP/cleanup을 명시 검증하고 PASS/LIGHT classifier는 light에만 사용한다. 제품 또는 Native 재시도는 아니다.

P320 STOP/정리/qualified200/compact97과 불변 code85를 새 세대에 바인딩하고, 위 반환 기록 순서 문제를 최소 수정·검증한다. 모든 원 input/identity/byte/CPU/RAM/Job 보호를 유지한 뒤 미수용104만 진행한다. 호스트 포화에서는 진행을 강제하지 않는다. 동일 실패 세대 자동재시도, 완료97개 반복, 증거 삭제/실패 PASS 변경/guard 완화 금지.

r126 두 문서 전체를 `evidence/runtime-progress-r126/`에 byte-exact 복사하며 r127 prefix 이외 원문 suffix를 보존한다. 문서 최종 fresh 검증은 별도 결과로만 보고한다. 접근허용/Hangul/빌드/Git/Defender/WSL/OS 설정 변경/프로세스 종료 없음.

