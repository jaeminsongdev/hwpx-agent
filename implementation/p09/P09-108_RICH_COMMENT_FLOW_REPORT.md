# P09-108 완전한 호출자 댓글 본문과 최종 처리 계획 연결 보고서

## 실제 구현

기존 P93 댓글 처리 경로에 실제 typed review Flow 본문 전체를 연결했다. 기존 모델은
body_graph_sha256만 가지고 있었으므로 본문 실제 구조/ID/style/resource/table과 지문을
함께 검증한다. 원래 strict parser/CommentBuilder/selector/compiler와 전체 문서 admission은
유지한다. 호출자가 명시적으로 제공한 완전한 상태에서만 동작하며 native 원본의 미확정
작성자·시간·해결 상태·좌표를 채워 넣지 않는다.

5개 기존 동작 모두 처리한다. 새 댓글 삽입은 actual body의 exact ID/digest/order가 필수다.
root body snapshot과 최종 target graph SHA를 compiler에 연결한다. 중간 P93 graph의 지문을
최종 지문으로 재사용하지 않는다. immutable preparation은 fresh 전체 상태에서 재구성한다.
문서 main content에 body를 평탄화하지 않는다. disposable graph에서만 기존 validator를
실행하며 반환되는 sections/notes/resources/references는 원래 내용을 보존한다.

body JSON 개별/전체8MiB 및 원래 whole graph32MiB/domain limits를 유지한다.
새 inserted body object는 복사하기 전에8MiB serialization budget을 확인한다.
중첩 paragraph/table cell/drawing 및 property Object/List의 명시적 caller protection
표시도 보수적으로 거부한다. 이는 실제 native protection mapping 완료가 아니다.

## 검증

- 최종 Rust381 실행 PASS, failed/ignored0: unchanged package182 + current product199.
- product199 = comment16 + stored form/import167 + stored comment16.
  comment16 = 원래8 + 신규8. 이전350 unique에 신규8을 더해358 unique다.
- 원래 package native8/context7가 두 suite에 있고 product에도 native8가 재사용된다.
  정확한 module 경로를 유지하되 재사용된 native fixture의 경로만 정규화해15 functions의
  중복 실행23회임을 확인했다. 다른 모듈의 동명이인 테스트를 합치지 않는다.
- 신규8은5 operations의 actual nested Flow/final compiler/preservation/privacy,
  complete inventory/order/body digest, global IDs/styles/resources/table geometry,
  원래 partial/document admission 및 nested caller protection, 삽입 body missing/mismatch/
  extra/oversized, fresh package/revision/graph/body drift, strict request unknown key/flow
  drift, explicit empty Flow 및 개별/aggregate byte budget을 검사한다.
- package source는 그대로다. 원래 P10617 test executables의 raw bytes/SHA를 확인해
  직접 실행했다. 새 package build/native qualification으로 세지 않는다.
- 최종 current CLI3 suites 재빌드·실행 및 엄격한 lint PASS.
- Python8 whole parent inverse/inherited raw/current inventory/claim guard PASS.
  신규 Rust2 isolated format 및 diff check PASS.
- 원래 current-source upstream component15 PASS, green0/OPEN.
  원래 default는 FAIL:matrix_drift 그대로다. 이 결과를 native/product/Gate PASS로 바꾸지 않는다.
- 실행 명령·session/terminal chunk·각 현재 suite의 실제 test list 및 중복 inventory는
  evidence/p09-108-rich-comment-flow.source-regression.v1.json에 기록한다.

## 실패·원본 보존

첫 test compilation은 Properties.remove/PropertyValue.Bool/fixture shadowing3 errors로
실패했다. 수정 후 runtime에서 nested protected body 거부 테스트가 실제로 실패했으며
15 PASS/1 FAIL 실행 파일과 exact source/test를 보존했다. 거부 assertion을 유지하고
새 body 검증을 보완했다. 엄격한 lint의 doc_markdown/too_many_lines2 오류는 doc correction과
private helper extraction으로 수정했으며 lint allow를 추가하지 않았다.

초기 library check의 Debug warning은 실패로 세지 않는다. pre-debug snapshot은 그 수정
직전 source이며, 중간 admission/replay 보강이 있어 최초 check가 읽은 정확한 source와
동일하다고 주장하지 않는다. pre-lint 및 pre-insertion-budget의 각199 PASS diagnostic
실행도 보존하지만 최종381 count/unique count에 반복 합산하지 않는다.

기존942 source entries 중940 unchanged, 부모2 whole preimages 및 whole inverse exact다.
원래 함수/test bodies/helper visibility/guards는 변경하지 않았다. 부모 각각에 새 module
declaration만 있다. 이전 unchanged audit를 exact read-view로 검증했다.
inherited raw1703, old executables265 보존이며 그 모두를 재실행했다는 주장은 없다.
현재952 source entries/delta12/archives9/predecessors2/current executables13이다.
현재13은 최종4 + pre-lint4 + pre-budget4 + failed runtime1이다. 각 CLI3는 미실행 inventory다.
최종 test3개만 현재 product199 PASS 주장에 사용한다.

## 미완료 범위와 다음 경계

이번 구현은 완전한 caller review Flow의 original compiler binding이다.
actual source/native metadata/coordinates에서 시작하는 완전한 comment 경로, 실제 HWPX
lowering, durable stored rich-IR integration, 날짜/외부/문서 필드 의미, trusted issuer/
protection/atomic execution/publication 및 actual P84 SQL cause/regression은 미완료다.
require_current_product_route는 fresh 검증 뒤 계속 RouteUnqualified다.

최소6개 큰 잔여 묶음은 이번 일부 구현만으로 차감하지 않는다.
native34 NOT_RUN, P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
INPUT_CHANGED_RE_ADMISSION_REQUIRED, P09/A12/A13 OPEN, green0/product false/no P10을 유지한다.
전체 P09~P20 목표는 active다. 한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/
stage·commit·push/삭제·이동을 하지 않았다. HEAD/사용자 dirty/private/native/실패 증거와
PLANS 삭제 상태를 보존했다.
