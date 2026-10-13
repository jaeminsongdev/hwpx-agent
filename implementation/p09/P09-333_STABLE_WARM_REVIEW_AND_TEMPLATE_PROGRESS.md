# P09-333 — 고정 입력 수의 warm 검토·계약 fixture 최적화 (2026-10-09~10)

## 결과와 제품 경계

목표 ACTIVE. 제품 수용 **97/249**, 잔여 **152=146 regular+6 corpus**, 다음 **104**, whole 재조정 **94** 유지. P09/A12/A13 OPEN. 전체1470/과거67/full249/signed16/제품 완료/PC 프리즈 해결을 주장하지 않는다. Native는 여기서 **Windows 입력 파일 잠금·byte frame**이며 한글 대상 저장·재열기/시각 oracle 통과가 아니다.

현재 두 controller 경로만 버전 갱신했다. 기존 정확한 source/test 및 receipt를 버전별 archive에 보존·hash 대조한다. 새 namespace p331→p333의 과거 메타데이터 자격을 archive의 실제 bytes/hash와 논리 source pin으로 바인딩한다. full1654=기준1644+추가10/controller187/directory308/code91 유지. STOP마다 controller 입력 수를 늘리지 않는다. 실제 Rust/EXE/원본·사용자 변경은 변경하지 않았다.

## 구현

- 합성 serve 계약이 real warm 전역 자격을 초기화하지 못하도록 WarmTestIsolation의 진입/예외/정상 종료에서 WARM_EXPECTED_CODE/WARM_REVIEWED_CODE/LAST_TERMINAL을 원 객체로 복원한다.
- 독립 light-review는 동일 예열 Python에서 **별도 원 admission/Reader/final-fresh/정리**를 수행한다. 이미 통과한 계약은 여기서 재실행하지 않는다. 현재91 code pin/동일 light pin/동일 queue·scope·binding과 불변 계약 결과가 필수다.
- actual은 해당 current queue의 독립 fresh light 검토 없이는 GO를 거부한다. 실패 검토는 actual/Native/수용 자격을 대신하지 않는다.
- 계약 fixture의 전체 변환은 current/following runner별 한 번씩 구성한다. 테스트마다 전체 독립 deepcopy로 변형 격리를 유지하고, 두 검증군 사이 template을 reset한다. 구성 횟수 감소와 변형 격리를 계약으로 검증했다. 완전한 검증군/범위를 줄이지 않았다.
- p331 독립 검토에서 발견한 rp 지역변수 shadowing을 p333에서 수정했다. 원 오류/terminal trace는 p332 실패 receipt에 보존한다.
- NameError/IndexError/RuntimeError 형태의 terminal validation 오류는 원 complete/정리 호출을 대체하거나 재시도하지 않고 FAILED로 보존한다.
- 원 CPU98x4, RAM/commit 비율, Native600, metadata720, acquisition14/native20/metadata32, before/after 전체 byte·identity 및 Job/정리는 불변. pseudo Native identity나 과거 partial byte를 새 실제 byte로 재사용하지 않는다.

## 정확한 실행 증거

모든 경로 아래 `implementation/p09/evidence/locked-r07/`.

| 증거 | 결과 | 의미 |
| --- | --- | --- |
| p331-warm-preformal474-CPU-stop-run01.v1.json | 333 started/332 after-test checks, 113bound/0fresh, CPU STOP·정리 TRUE | 전체474 PASS 아님. 수정 전 코드 보존 |
| p331-warm-template478-preformal-run02.v1.json | 239+239=478, 113bound/113fresh/226read/10,097,382 bytes, 정리 TRUE | 예열 계약/메타데이터 PASS만 |
| p331-light-run001.v1.json | 정식478 PASS | rp 오류 수정 전 메타데이터 자격 |
| p332-warm-independent-validation-unbound-local-failure-run01.v1.json | UnboundLocalError, exit1, 독립 receipt 미생성, 제품 root/body0 | 원 complete는 validation 전에 finish_watcher 호출. 수치 관측/정리 receipt는 유실되어 가정하지 않음 |
| p333-light-run001.v1.json | 241+241=482, 116bound/116fresh/232read/10,455,140 bytes, 정리 TRUE | current source/test 계약 및 메타데이터 PASS |
| p333-light-review-run002.v1.json | 별도117bound/117fresh/234read/10,534,568 bytes, code91, 정리 TRUE | 계약 재실행 없이 독립 fresh PASS; 실제 제품/Native PASS 아님 |
| p333-case-104-run003.v1.json | owned_parent CPU STOP, preparation118fresh/236read, Native 모두 정리 | 아래 실제 유예 상세. 제품 수용0 |
| p333-stop-review-run004.v1.json | 별도121bound/121fresh/242read/11,497,652 bytes, 정리 TRUE | 원 실패를 실제 미실행·정리 완료의 후보로 검토. FAILED 원본 그대로 |
| p333-light-review-run005.v1.json | 별도122bound/122fresh/244read/11,583,296 bytes, 정리 TRUE | 검토된 실패를 포함한 독립 fresh PASS |
| p333-admission-run006.v1.json | anchor CPU STOP, 100bound/0fresh/100read/4,244,503 bytes, 정리 TRUE | 승인된 실패 검토 후 시도했지만 Frame/계약/제품 시작 전 중단; 아직 독립 실패 검토 미완료 |

P333 실제104 run003 root420,388 bytes/SHA `0c1ae08e…fd528`; sidecar24,356/SHA `20c47d55…fe049`. 정확한 전체 hash와 관측은 p334-warm-stable-scope-diagnostic-run02.v1.json에 있다.

## 실제104 run003과 CPU 검토

- full1654/120,875,572 bytes/ancestor308의 입력 잠금 **1,962개 모두 acquire 후 close**, close 실패0, remaining0.
- 복제 stream105개 모두 close, remaining/failed0, reader/stream0, Frame CLOSED/unregistered, 실제 완료 byte boundary0.
- before 전체 byte 검사는 **105/1654, 33,393,592 bytes**까지 읽었으므로 before/after 전체 검증은 **미완료**.
- 원 parent DEFERRED_NOT_STARTED, worker_created/job_assigned/actual_product FALSE, exit=NULL, owned tree empty/cleanup TRUE. return2/pendingTRUE를 원 after_parent guard 이전에 기록했다.
- 원390 표본의 own private 최대58,609,664 bytes, RAM free 최소20.921866%, own CPU 최대6.500956%. 마지막 4표본은 host100/own0/읽기delta0. own 작업의 비정상적인 전체 코어·RAM 폭증 증거는 아니다.
- 기존 빈 body를 삭제·덮어쓰지 않았다. 독립 실패 검토에서 bytes0/SHA(empty) 확인. 성공한 제품 본체 재실행0.
- source frame check는 O(1)의 소유자/상태/원 deadline·guard 검사이고, 64KiB/1·2MiB pacing은 최대64 반복과 실제 sleep을 갖는다. borrowed stream은 이미 중복 pre-descriptor native metadata query 없이 원 identity check를 보존한다. 정리 후 과거105 byte를 재사용하면 원 두 전체 fresh-byte 조건을 약화하므로 하지 않는다.

run006은 anchor에서 멈췄다. 계약/Frame/제품 없음. own private 최대47,771,648 bytes, own CPU 최대1.296296%, 마지막 3표본 own0/읽기delta0/host100. 같은 시도의 즉시 반복 없음.

PerfProc endpoint 진단은 p334-warm-actual104-perfproc-window-raw-run01.v1.json에 원 십진 uint64로 보존한다. 356.726839초 창의 Idle 약82.245%, MsMpEng 약6.798% 평균은 **중단 순간의 CPU 기여나 프리즈 원인을 증명하지 않는다**. 외부 프로세스·OS·Defender·WSL을 변경하지 않았다.

## 남은 own 최적화 및 다음 경계

현재 terminal_session_summary는 CPU STOP 후 reader/Native 정리가 모두 확인되어도 보수적으로 예열 세션을 닫는다. 이후 helper import가 다시 발생하는 비용이 남아 있다.

다음은 **독립 검토로 확인 가능한 pre-product CPU STOP이며 원 watcher/reader/stream/handle/Job 정리가 완료된 경우에만** 작은 loaded-code 자격을 보존하는 경로다. Native 잠금/시간예산/active watcher/대형 원장을 idle에 보존하지 않는다. actual 자격은 무효화하고 원 실패의 명시적 review 및 새 fresh 검토 없이는 GO를 허용하지 않는다. post-product/불확실한 정리는 계속 session 종료한다. 자동 반복/보호 기준 완화 없음.

run006 미완료 검토와 실제104 두 전체 byte·Job·본체·마감 검증은 남아 있다. 현재 code91의 full1654 Native 자격/제품 PASS로 승격하지 않는다. 상태 문서 마감 fresh는 이번 턴 NOT_RUN이며, 마지막 수용상태 자격은 r128/P325이다.

현재 모든 exec/PTYS handles는 terminal이다. 목표 ACTIVE 유지. Git/Review, Cargo/build, 한글/접근 허용, 전체 OS 설정·외부 프로세스 조작, 파일 삭제·이동 없음.
