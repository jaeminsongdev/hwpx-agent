# P09-94 저장된 댓글 변경 준비 정책

원래 StoredFormProvider를 확장하여 현재 sealed revision이 선택한 Result와 DocumentIr를
원래 source/full_document_ir 읽기 경로로 읽고, P09-93의 원래 댓글 모델·compiler에 연결한다.
별도 importer/provider/store를 만들거나 기존 form guard를 완화하지 않는다.

## 입력과 결속

- 공개 입력은 expected head, plan ID, bounded 원래 댓글 request와 명시적 logical insertion
  binding뿐이다. artifact ID/path/키/scan verdict/전체 state는 요청으로 받지 않는다.
- 실제 Result와 IR의 tenant/actor/ACL/state/quarantine/AEAD/전체 bytes와 digest를 독립 확인한다.
  IR kind/media와 canonical JSON, sealed node의 세 digest binding도 원래 reader가 검사한다.
- graph.document_id는 provider 문서와 같아야 한다. complete state는 해당 IR의
  p09_complete_comment_state_json에서만 읽고 원래 typed validator 및 exact canonical bytes를
  확인한다. 1 MiB state 입력 한도와 unknown/duplicate/missing/lexical alias 거부를 유지한다.
- 원래 full-IR admission 및 complete section/style/review view 검사를 재사용한다.
  partial native importer, protected/signed/encrypted IR는 저장소에 있어도 거부한다.
- 원래 다섯 작업 REF-026~030을 그대로 prepare/compile한다. comment_delete는 P11 소유다.

## 재검증과 출력

PreparedStoredComment는 Deserialize, mutable snapshot, artifact writer/commit/claim API를
제공하지 않는다. verify는 같은 provider scope에서 원본과 IR를 다시 읽고, 전체 snapshot/state
비교 및 원래 compiler replay와 최종 head 확인을 수행한다. receipt도 전체 재계산해 비교한다.
반환되는 graph/plan은 메모리 candidate이지 저장 완료된 HWPX나 실행 권한이 아니다.
현재 require_current_product_route는 fresh 검증 후 항상 RouteUnqualified다.

일반 artifact 읽기 감사는 발생한다. 읽기 전후 head 검사나 여러 ACL 읽기는 원자적 CAS가
아니며, 반환 후 권한 철회/경쟁을 막는 실행 lease를 제공하지 않는다. 실제 execution/publication
경로에는 별도의 원자적 권한·revision/idempotency 결속이 필요하다.

## 증거의 범위

저장소 인증과 raw hash는 storage identity를 증명할 뿐 native 댓글 의미나 source→IR의
semantic provenance를 증명하지 않는다. 이번 positive fixture는 in-memory repository,
synthetic scanner/actor/key/complete caller IR와 **HWPX가 아닌 명시적인 storage-only bytes**다.
이를 실제 원본 댓글 캡처, qualified 작성자/시간/좌표, scanner/issuer 또는 SQL 증거로 세지 않는다.
작성자/시간/스타일 기본값, 빈 가짜 native 댓글, native 증거의 자동 승격을 만들지 않는다.

HWPX header/body/MEMO lowering, 실제 source-bound comment metadata/좌표,
durable PostgreSQL 제품 통합, trusted issuer, atomic execution/publication, 실제 한글
저장·재열기·렌더링·차이 비교 및 P09 Gate는 계속 미완료다.
한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설치·설정/commit·push는 실행하지 않는다.
사용자가 삭제한 root PLANS.md를 복원하지 않는다.
