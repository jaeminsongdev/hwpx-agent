# P09-105 저장 원본·템플릿 표 출력 정책

## 실제 서비스 연결

P09-104 실제 source-bound review table output을 원래 StoredFormProvider의
authenticated actual import에 연결한다. StoredImportedReviewBodies::prepare_table은
대상 document와 template의 독립 provider 및 immutable StoredImportedDocumentForms를
받는다. request는 actual source anchors + explicit 신규 geometry이며 caller XML/
bytes/offset/native metadata/full-Flow hash/approval bit를 받지 않는다.

같은 authenticated tenant/subject만 두 provider에 사용할 수 있다. document/project/
branch는 서로 달라도 각각의 원래 scope/ACL/head/AEAD/result-kind/scanner/digest/whole
archive 검사를 반드시 통과해야 한다. imported getters/receipt는 캐시이며 접근권한이 아니다.

## 최신 접근 확인과 원래 출력

생성 전에 actual review/source를 fresh verify하고 template도 original fresh_source로
다시 읽는다. 실제 선택/context를 원래 P09-103 API로 재구성하고 P09-104 package output을
lower한다. 출력 뒤 둘 다 다시 확인한다. verify/with_verified_bytes도 두 original
services와 complete deterministic output을 replay하고 immutable receipt/artifact를 대조한다.
한쪽이라도 실패하면 consumer callback을 실행하지 않는다.

이 repeated reads는 atomic execution lease/CAS나 durable importer persistence가 아니다.
current product route는 모든 fresh 검사를 선행한 뒤 RouteUnqualified로 계속 거부한다.
진단은 closed static actor/source/template/output/binding/route codes다.
public receipt는 source/template head generation + 원래 package output receipt이며
document/actor/request/path/XML/content 값은 넣지 않는다. Debug는 redacted다.

source/template byte acquisition은 원래 sealed current Result만 사용한다. arbitrary
artifact/path/cached template bytes/scanner verdicts를 새로 허용하지 않는다.
artifact ingest/revision commit/publication은 실행하지 않는다. 정상 read audit만 발생한다.

## 완료하지 않은 범위

stored_source_and_template_table_output_authenticated만 현재 source-component에서 true다.
full comment metadata/coordinates/Flow/compiler/protection/issuer/atomic publication,
durable actual SQL integration/root cause/native save-reopen/render/differential은 false다.
original native blank template/exact header 제한과 opaque ID closure 미검증을 유지한다.

P09/A12/A13 OPEN, Native34 NOT_RUN/green0, INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, no P10, full product false다.
최소6개 큰 잔여 묶음은 그대로이고 세부 작업 수는 확정되지 않았다.
전체 P09~P20 목표는 active다. 접근허용/한글/COM/UI/actual SQL/운영·trust DB/
설정·설치/stage·commit·push/삭제·이동을 수행하지 않으며 PLANS.md를 재생성하지 않는다.
