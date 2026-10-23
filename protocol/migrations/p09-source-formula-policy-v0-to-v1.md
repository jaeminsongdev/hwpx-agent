# P09-116 — Source formula policy data v0 → v1

## 이전과 이후

기존 source-form-policy/v1과 원래 form 정책 repo/SQL adapter는 그대로다.
새 application/vnd.hwpx-agent.source-table-formula-policy+json Evidence와
hwpx-agent.source-table-formula-policy/v1 payload는 별도 FormulaPolicyRepository가 선택한다.
form 정책의 허용 값이나 caller policy/approval을 field recalculation grant로 변환하지 않는다.

payload는 다음 필수 object 구성만 허용한다.

- schema_version: 새 formula policy schema 문자열.
- binding: 원래 SourcePolicyBinding의 explicit tenant/project/branch/document/source revision,
  head generation, result artifact, package/provenance/form graph SHA, policy UUID/generation/creator.
- meaning_graph_sha256: 원래 source-derived field meaning graph의 canonical SHA.
- targets: 모든 실제 TableFormula에 대한 reference_id, begin_anchor, end_anchor, ast_sha256,
  allow_recalculation(bool)을 가진 object 배열. 누락·추가·중복은 오류다.

원래 source graph/provenance hash 정의를 바꾸지 않는다. AST는 원래 typed FormulaAst의
serde JSON bytes SHA로 결합한다. caller AST는 받지 않는다. anchor 객체와 target 객체는
배열식 positional struct를 허용하지 않는다. nullable/default approval은 없다.
target 순서는 바뀔 수 있지만 raw artifact SHA와 sorted target-binding SHA는 별도 보관한다.

## 제품 호출

기존 v1 form request와 v2 source-only formula request의 schema/canonical serializer는 그대로다.
새 prepare_formula_with_policy(provider, server_repository, raw_request, now)는 v2만 받는다.
서버가 선택한 정책은 source exact binding과 원래 artifact service checks를 통과해야 한다.
deny가 하나라도 있으면 current/no-op을 포함해 요청 전체를 거부한다.
원래 lowerer/compile/protection 검사와 exact unchanged outcome은 유지한다.
결과 소비 전 latest/revocation/권한을 재읽으며 version/artifact/bytes/source가 바뀌면 재준비해야 한다.

## 미완료·호환성 경계

StoredFormulaPolicy는 Deserialize capability가 아니며 repository fixture는 trusted issuer 증거가 아니다.
새 field 정책 SQL adapter/서명 발급자·검증키·운영 등록부/atomic execution/transport/publication은 미완료다.
old ungated v2 준비 API와 새 policy-gated API 모두 actual product route는 계속 unqualified다.
서버 row와 artifact의 creator 일치가 외부 issuer 암호 검증을 대신하지 않는다.
새 native Field-result 계약에는 P06 table.formula의 과거 PASS를 적용하지 않는다.
P09 Gate OPEN/no P10/product false를 유지한다. 운영 데이터 자동 마이그레이션은 실행하지 않았다.
