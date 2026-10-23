# P09-117 — Source formula policy SQL20 → SQL21 source profile

기존 SQL20 form policy tables/functions/artifacts와 원래 exact schema17/19/20 connectors는 그대로다.
새 migration0021은 schema20 이후에만 source_formula_policy_versions/revocations와 별도 register/read/revoke
함수를 만든다. form policy namespace를 rename/drop/업데이트하지 않는다.

새 policy artifact media는 application/vnd.hwpx-agent.source-table-formula-policy+json이다.
Evidence artifact의 ACL/scanner/AEAD/whole SHA와 원래 source binding을 유지하며,
P116 consumer가 whole actual field meaning graph/각 수식 AST와 begin/end anchors를 재검증한다.
formula artifact와 form artifact는 교환할 수 없고 revoked latest를 old policy로 대체할 수 없다.

new artifact connect_source_formula_policy_schema21 및 LocalPostgresSourceFormulaPolicyRepository::connect는
모든1~21 migration fingerprints와 original role/RLS/security checks를 요구한다.
원래 connections의 profile을 암묵적으로 업그레이드하지 않는다.
PostgresFormulaPolicyProvider가 원래 source-only product policy preparation에 새 server repo를 연결한다.
등록·조회·철회는 metadata source 구현이고 external issuer/signature/execution 권한 검증이 아니다.

적용 시 관리자가 기존 방식대로 새 migration SHA를 제공하고 지정된 앱 역할에 새 named register/read/revoke
함수의 EXECUTE만 명시적으로 부여해야 한다. PUBLIC/helper EXECUTE와 direct history table grants는 허용하지 않는다.
이 문서는 적용 조건이며 실제 schema migration/권한 설정/운영 DB 변경을 실행하지 않았다.
rollback source는 explicit destructive gate와 최신 schema21 및 비어 있는 formula history/revocation을 요구한다.
데이터가 있으면 rollback을 거부하며 source form history를 삭제하지 않는다. rollback 실행은 NOT_RUN이다.

actual SQL admission/RLS/ACL/read/register/revoke/CAS/concurrent changes/rollback와 product registration issuer,
atomic execution/publication/native/transport acceptance는 미완료다. old P84 SQL 간헐 원인도 UNRESOLVED다.
신규 source/compile tests를 actual SQL PASS로 확대하지 않는다. P09 Gate OPEN/no P10/product false다.
