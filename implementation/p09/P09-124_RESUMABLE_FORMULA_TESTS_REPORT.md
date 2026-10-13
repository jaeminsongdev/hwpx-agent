# P09-124 — 자원 제한을 유지한 단일-case 이어 실행

## 중단 및 원인 범위

동일 frozen Rust14 / executable10688512 bytes / SHA04fefdf7…로 actual_import200을 실행했다.
논리 CPU1/BelowNormal/worker1/2초 감시로 362.47초에 STOP_LOW_AVAILABLE_RAM/exit-1이 됐다.
마지막 관측: system CPU100%, 여유 RAM3210MiB, test working set20.03MiB.
test RAM 최대25.18MiB, ok marker50/failed marker0, terminal summary 없음이다.
marker50은 suite 성공으로 수용하지 않으며 해당 원래 receipt를 보존했다.
이후 read-only snapshot은 CPU6%/여유 RAM14356MiB/test process0/Hwp0였다.
이 두 시점만으로 다른 앱의 RAM/CPU 압박 원인을 확정하거나 테스트 자체 영향이 없다고 단정하지 않는다.

## 최적화 범위

200개 묶음의 반복 중단 후 처음부터 재실행하는 낭비를 줄이기 위해 새 보조 실행기를 추가했다.
기존 runner/검증기/production Rust/Cargo/source freeze/HWPX 원본/사용자 변경은 수정하지 않았다.
기존 threshold CPU85%3연속/여유 RAM4GiB/test RAM2GiB를 그대로 유지한다.
각 case는 논리 CPU1/BelowNormal/worker1/2초 감시/600초 상한이다.
한 invocation은 다음 1개만 실행하고 즉시 반환하며 자동 retry/병렬 실행은 없다.
실제 executable --list의228 = actual_import200 + documents20 + root8을 대조한다.
현재 runner의 substring filter에 정확히 한 case만 매칭하는 이름인지 시작 전에 확인한다.
최종 receipt의 terminal1PASS/227filtered/정확한 name/원래 source14와 binary pin/자원 정책을
모두 검증한 case만 다음 실행에서 건너뛴다. 중단 receipt는 새 attempt로 보존하며 기존 파일은 덮어쓰지 않는다.
완료를 나누어 보존하는 scheduling 최적화이며 실행 시간 단축의 정량 benchmark가 아니다.

## 실행과 검증

새 unit14 PASS: 실제 이전 root1 receipt positive, terminal 누락, filter 다중 매칭,
case/binary/source 바꿔치기, RAM 기준 완화, 중단 marker, 중복 승인, unknown 상태,
목록 count 및 실제 substring 충돌 거부, 이어 실행 위치 확인이다.
복제 receipt/가상 목록 unit은 runtime 증거와 구분한다.
실제 첫 case0.12초 및 두 번째0.16초: 각각1PASS/0failed/0ignored/227filtered/exit0.
첫 번째의 최종 기록을 읽어 두 번째를 실행했으며 같은 case를 반복하지 않았다.
두 실행 모두2초보다 짧아 test-process RAM sample은 없고 baseline RAM만 관측했다.
따라서 sample의0MiB를 실제 테스트 RAM 사용량0이라고 주장하지 않는다.
baseline 여유 RAM은 각각14043/14085MiB이다.
이번 checkpoint: 독립 single cases2/200, 남은198. 중단200 묶음 및 single-process228은 미수용이다.
P123의 documents20/root8 및 이전 corpus 증거는 별도 유지한다.

## 이어 실행 및 경계

`python -B tools/p09/resume_single_case_formula_tests.py`는 read-only plan을 출력한다.
`python -B tools/p09/resume_single_case_formula_tests.py --run-next`는 다음 한 case만 실행한다.
현재 다음 index3이며 resource 중단이면 무조건 자동 재시작하지 말고 상태를 먼저 확인한다.
runtime stdout/stderr/XML/key/subject 값은 출력하거나 저장하지 않고 안전한 JSON receipt만 사용한다.
checkpoint audit는 원래 P123/P122/P121/P120 source 검증을 변경 없이 호출하고
이전 checkpoint2, 신규 source4, runtime3의 물리 pin을 확인한다.
현재 source1125/이전1121/inherited raw pins2376; historical failed receipts는 전부 유지한다.

한글/Hwp/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.
PLANS는 재생성하지 않았다. 목표 active/P09 Gate OPEN/product false/P10 새 구현 없음.
native34 미실행 또는 재수용 필요/P26 의미 검증 실패/P62·P84 SQL 미해결 상태를 승격하지 않는다.
