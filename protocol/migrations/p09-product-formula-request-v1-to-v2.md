# P09 제품 요청 v1 → 공통 v2 source-only 수식 요청

기존 v1 form 요청은 변경하지 않는다. 기존 직접 StoredProductFormRequest 호출도 유지한다.
공통 StoredProductRequest 진입점에 v1+Some(original form bindings)를 주면 원래 Form preparation을 반환한다.
v1에서 bindings가 없거나, v2에 bindings가 있으면 거부한다.

source formula v2의 operation은 {"kind":"recalculate_table_formulas"} 객체다.
schema_version은 hwpx-agent.product-operation-request/v2이고 기존 project_id/document_id/base_revision/
expected_head_generation/expected_source_package_sha256/plan_id/idempotency_key identity를 포함한다.
계산값/AST/field selector/raw package/artifact/path/policy/approval 입력은 추가하지 않는다.
호출자는 provider가 이미 authentication한 current sealed Result를 임의로 대체할 수 없다.

공통 결과는 PreparedStoredProductOperation::Form 또는 TableFormulas다.
formula receipt는 changed(original compiled candidate)와 unchanged(exact original NoChange)를 구분한다.
unchanged compiled()는 None이며 whole source bytes가 그대로다. empty-operation compiler limit을 우회하지 않는다.
candidate는 fresh with_verified_bytes에서만 소비하고 require_current_product_route는 현 단계에서 거부한다.
canonical/identity hash는 요청 비교용이며 실행 idempotency/issuer authorization 또는 durable commit 증거가 아니다.

추가 transport/issuer/full field policy/full importer/signed registry/atomic durable execution을 구현·검증해야
제품 실행 경로를 열 수 있다. 실제 CLI는 create-vs0만 제공한다.
DB schema 및 original v1 parser/serializer와 실제 native field 명령 프로필은 변경하지 않는다.
원래 NoChange/보호 검사와 full import partial guard를 지우지 않는다.
