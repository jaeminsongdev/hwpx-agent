# P09-123 — 동일 source의 1 CPU 회귀 및 독립 기능군 확인

## 범위와 보존

기존 test worker1/BelowNormal/2초 감시에서 CPU affinity만2개에서1개로 더 제한했다.
85%3연속/RAM4GiB/test RAM2GiB/1800초/관측 실패 중단 조건은 유지한다.
P121 frozen Rust14/컴파일 executable10688512 bytes/SHA04fefdf7…는 수정하지 않았다.
P122 checkpoint5749 bytes/dde748e2…와 final audit2517 bytes/3af242bc…를 고정하고
원래 P122/P121/P120 validator를 변경하지 않은 상태에서 전수 실행한다.
source delta4/current declared source1121/previous1117/inherited raw pin entries2360을 유지한다.
기존 사용자 변경115개 및 PLANS 삭제1개는 보존한다. 전체 diff/로그/비밀 값을 출력하지 않는다.

## 전체228 실행 f — NOT_ACCEPTED

실제 session34916/PID56368을 같은 handle로 끝까지 관찰했다. timeout 때문에 재시작하지 않았다.
실행 중 source14 exact, 실제 affinity1/BelowNormal/Hwp0을 확인했다.
769.96초에 CPU100/97/100% 3연속으로 STOP_SUSTAINED_SYSTEM_CPU/exit-1이 됐다.
test RAM max28.87MiB/RAM 여유 min15246MiB/samples303이며 최종 test/Hwp process0이다.
실제 ok marker201/failed marker0이 있으나 terminal summary가 없어 전체228 PASS가 아니다.
partial marker를 최종 suite PASS로 바꾸거나 기존 d/e/그 이전 실패를 덮어쓰지 않는다.
이는 CPU affinity1의 엄밀한 성능 승인 또는 외부 압박 원인 진단도 아니다.

## 목록 대조와 독립 기능군 검증

같은 executable --list는228: actual_import200/full_document20/최상위 stored8이다.
초기에는 full_document28로 추정했지만 실제 목록과 실행은20/208filtered여서 수치를 정정했다.
f의201 markers는 actual_import200 + full_document 첫1개다. 미관측27개는 full_document19+stored8이다.
목록 자체는 실행 증거가 아니며201+20+8처럼 중복을 더해 full PASS를 만들지 않는다.

독립 full_document 실행:20 PASS/0failed/0ignored/208filtered/28.52초(wrapper28.63초).
test RAM max14.17MiB/RAM 여유 min15286MiB/source14 exact/같은 binary/CPU1/BelowNormal이다.
별도8 root cases는 각각1 PASS/227filtered/exit0/source14 exact/CPU1으로 terminal을 확인했다.
다음 원래 경로를 실행한다: 실제 sealed node ACL/AEAD/원래 compiler의 memory candidate,
기존 five control kinds/radio/default/empty-clear, fresh ACL 철회, policy/map/입력 거부,
tenant/subject/branch/document 바꿔치기 거부, quarantine/role/ciphertext 거부,
head advance 시 기존 준비 거부, debug/receipt/fixed errors의 비밀정보 비노출.
같은 prefix가 다른 사례를 포함하지 않았는지 실제 passed name1개와227filtered를 각각 확인한다.
이들은 SOURCE 구성요소이며 실제 SQL/신뢰 발급자/원자적 publication/transport/native가 아니다.

## 증거 검증과 상태

실제 targeted3 receipt를 활용한 기존 source/candidate/제한 검사12개 및 실제 document20에 대한
positive/가짜228/중복 name 거부3개 = Python15 PASS다. clone의 CPU1 정책 검사는 arithmetic unit이며
실제 CPU1 실행 증거는 위 runtime들이다. 조건을 낮추거나 mocked 결과를 runtime receipt로 저장하지 않는다.
새 checker는 old checkpoint/전체 source/각 runtime/원래 source freeze/binary 및 정확한 testcase name을
전수 대조한다. documents20/root8은 독립적으로 수용하되 interrupted201은 suite PASS로 수용하지 않는다.
현재 원장: `implementation/p09/evidence/p09-123-single-cpu-formula-regression.source-progress.v1.json`.

production Rust/Cargo/기존 guards 및 HWPX 원본 변경 없음.
한글/Hwp/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.
P09/A12/A13 OPEN/product false/P10 새 구현 없음/최소6 coarse groups closed0 및 최소30 비완전 조건 유지.
native34 NOT_RUN/재수용 필요, P26 failed_semantic_non_green, P62/P84 SQL UNRESOLVED.
원래 요구사항의 한글 저장·재열기·render/automation/differential/Gate를 이번 Rust checks로 대체하지 않는다.
목표는 active다. 이번 턴은 CPU 압박 외에 독립적으로 진행 가능한28 cases와 증거 검증을 완료했으므로
단순한 동일 차단 상태 반복이 아니다. 다음은 actual_import200의 최종 terminal 검증과 전체228 통합 검증을
남겨 둔다. 실제 source assertions201은 이미 관측됐으나 accepted full suite로 승격하지 않는다.
