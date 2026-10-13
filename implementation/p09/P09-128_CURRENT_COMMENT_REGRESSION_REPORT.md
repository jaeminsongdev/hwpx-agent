# P09-128 — 수정된 댓글 보호 모델의 기존 경로 회귀

## 실제 실행 범위

P127 보호 수정 이후 현재 모델 및 그대로인 원래 호출부/저장소 구현을 다시 컴파일했다.
기존 comment_model10 / comment_operation16(원래 rich body8 포함) /
stored_comment_provider24(원래 stored rich body8 포함) =50개가 모두
terminal PASS/0failed/0ignored/0measured/0filtered/exit0으로 완료됐다.
P127의 새 반례4개는 별도 실행 증거로 유지한다. unit/model/source/component 결과를
한글/native/실제 SQL/운영 issuer/원자적 publication/제품 Gate 승인으로 승격하지 않는다.

이 회귀는 원래 five comment operations, strict 요청/상태/flow binding, protection,
불완전·순서·view 오류, fresh ACL/AEAD/head/scope/revision 검사, complete rich Flow body 및
원래 compiler의 최종 graph binding을 원래 테스트에서 검증한다.
새 importer나 작성자/시간 추측 기본값, source-import admission 우회는 추가하지 않았다.
prepared current product route가 unqualified 상태에서 거부되는 기존 동작도 유지한다.

## 실행과 자원

기존 P121 cache 재사용, cargo jobs1, logical CPU1/BelowNormal,
2초 sampling/CPU85%3연속/여유 RAM4GiB/root RAM2GiB 중단 조건을 유지했다.
test profile opt-level1/debug assertions=true/overflow checks=true/codegen-units1은
child 환경에만 적용하며 사용자 설정이나 기존 resource guard는 수정하지 않았다.
각 suite의 이름과 count10/16/24를 고정하고 전체 terminal 및 distinct passed names를 검사한다.

Model build1.95초/test0.07초, Operation build243.98초/test0.10초,
Stored build8.31초/test0.33초였다. 정량 성능 비교/제품 성능 승인으로 해석하지 않는다.
Operation build의 available RAM 최저9620MiB, child CPU 제한 관측268회였다.
원래 root RAM은 전체 build RAM이 아니며 별도 rustc 약3.0GiB/affinity1/BelowNormal을 관측했다.
빠른 모든 test는2초 안에 종료해 test RAM 최대값을 측정하지 못했다. baseline0을 실제0으로 보지 않는다.
session67687는 Model10 및 Operation build,54384는 Operation16/Stored build/Stored24를 정상 종료했다.
관찰 대기만으로 동일 process를 재시작하거나 실패 receipt를 덮어쓰지 않았다.

## 증거 검증과 보존

실제 Model10 receipt를 활용한 positive 및 잘못된 suite/CPU 증대/RAM·CPU 기준 완화/
CPU100%3연속·RAM 부족 관측/가짜 Gate/source drift/중복 case/ignored/failed 반례 검사12 PASS다.
복제한 반례 unit은 runtime 증거와 별도로 취급한다.
새 검증기는 각 receipt의 source7/8/10 전체 지문, 실제 exe 지문, 자원 threshold와 samples,
정확한 terminal count 및 distinct names를 모두 대조한다.
기존 P127 current audit를 수정하지 않고 호출해 보호 수정/원래 parent whole preimage와
초기3PASS/1FAILED/수정4PASS/기존 모든 source 및 역사적228개 증거를 전수 보존 확인한다.
원래 코드/기존 테스트/프로토콜/실패 evidence/PLANS 삭제/사용자 변경은 이번 턴 수정하지 않았다.

current source1140 = 이전1136 + 신규 driver/검증기/unit/report4개,
inherited raw pins2607/이전 checkpoint1/새 runtime6/실행 파일3개를 checkpoint에 고정한다.
생성 중 template 검증2회는 파일 생성 및 실행 전에 중단됐다. literal replacement로
PowerShell regex 달러 기호를 유지한 뒤 최종 driver만 생성·실행했으며 원래 driver는 불변이다.

## 다음 경계

현재 comment-scoped50 회귀는 수용하지만 현재 전체 workspace 및 수정 후 form-stored228
통합 회귀는 아직 수용하지 않는다. P126228은 한 parent preimage view의 역사적 증거다.
전체 통합 회귀와 원래 native comment metadata/qualified source/lowering/저장·재열기·render/
실제 issuer/SQL/원자적 실행·publication/Gate는 계속 남는다.
목표 active/P09 Gate OPEN/product false/P10 새 구현 없음.
한글/Hwp/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없음.
