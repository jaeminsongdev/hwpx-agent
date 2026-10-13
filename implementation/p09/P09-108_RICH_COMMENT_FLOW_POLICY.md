# P09-108 완전한 호출자 댓글 본문과 기존 처리 계획의 연결

## 대상과 입력

원래 P93 CommentOperationContext/strict CommentRequest/CommentBuilder/selector/compiler를
유지하고 완전한 명시적 caller-owned CommentRichBody의 실제 typed Flow를 연결한다.
native source importer를 완전한 IR로 승격하는 작업이 아니다. 기존 부분 import markers,
작성자·시간·상태·native 좌표의 미확정 상태를 지우거나 기본값으로 대체하지 않는다.

호출자는 기존 완전한 CommentDocumentState와 graph 및 body 전체를 제공한다.
graph metadata의 p09_complete_comment_rich_bodies_json이 body 전체의 정확한 canonical
typed JSON과 일치해야 한다. 준비 과정에서 원본 graph에 이를 임의로 주입하지 않는다.
전체 순서는 hidden explanations, 그 다음 기존 comments의 presentation order다.
각 review logical ID 및 기존 body_graph_sha256과 실제 Flow JSON SHA256이 일치해야 한다.
native subList/plain text/cache의 기존 지문은 이 지문과 동일하다고 가정하지 않는다.
새 body type/receipt/prepared operation은 Deserialize 또는 mutable prepared accessor가 없다.

## 기존 검증과 최종 계획

- 원래 완전 문서 admission을 source 및 final target에서 유지한다. 문서 보호·암호화·
  서명·부분 import 및 whole graph budget/ID/style/resource/table 검사를 완화하지 않는다.
- body의 실제 section에 노드를 추가한 disposable graph로 원래 전체 graph validator를
  실행한다. 표 셀 및 drawing child의 중첩 Flow도 포함한다. 이 검증 graph는 결과로
  반환하지 않는다. 원문 sections/notes/resources/references를 body 평탄화로 변경하지 않는다.
- 개별/전체 body JSON은 최대8MiB다. 기존 whole document32MiB 및 domain limits도 유지한다.
  초과는 거부하며 자르거나 본문을 plain text로 대체하지 않는다.
- 별도 보수적인 caller convention으로 protected/locked/read_only 표시가 있으면
  Boolean(false)만 허용한다. true 및 타입 불명은 거부한다. node semantics/layout_hints,
  paragraph/node/table cell properties와 nested Object/List 및 drawing child를 확인한다.
  이는 실제 native protection 의미 검증이나 absent property의 native unprotected 증명이 아니다.
- 원래5 operations를 그대로 사용한다. InsertComment에는 해당 새 comment의 실제 body가
  필수이며 exact ID/digest/order가 일치해야 한다. 나머지4 operations의 extra body는 거부한다.
- 원래 compiler에 최종 rich-body target graph SHA를 넘긴다. 삽입 전 중간 P93 target hash를
  최종으로 재사용하지 않는다. 원래 domain plan/selected source nodes/source package binding은 유지한다.
- immutable preparation의 verify는 원래 preparation 검증 후 전체 rich body/target/compiled
  plan/receipt를 fresh caller context에서 재구성한다. package/revision/body/graph drift는 거부한다.
- require_current_product_route는 fresh 검증 후 항상 기존 RouteUnqualified다.

## 권한과 미완료 범위

native_metadata_verified/hwpx_lowered/execution_authority_verified는 false다.
actual source에서 완전한 작성자·시간·해결 상태·좌표를 추출하는 일, source import부터
full comment body/compiler를 연결하는 일, durable stored rich-IR route, 실제 HWPX lowering,
trusted issuer/protection/atomic publication 및 P84 SQL actual 검증은 완료하지 않았다.
원래 부분·unsupported metadata나 opaque native ID를 임의로 변환하지 않는다.

P09~P20 전체 목표는 그대로다. 최소6개 큰 잔여 묶음을 이번 부분 구현으로 차감하지 않는다.
native34 NOT_RUN, P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
INPUT_CHANGED_RE_ADMISSION_REQUIRED, P09/A12/A13 OPEN, green0/no P10/product false를 유지한다.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동을 하지 않는다.
PLANS 삭제 상태와 사용자 dirty/private/native/실패 증거를 보존한다.
