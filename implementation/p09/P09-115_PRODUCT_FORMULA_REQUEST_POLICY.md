# P09-115 — 공통 제품 API의 source-only 수식 재계산 요청 정책

## 실제 API 계약

form_product_request::stored_operations::StoredProductRequest::prepare_json은 원래 제품 API의 공통 진입점이다.
기존 hwpx-agent.product-form-request/v1은 원래 Request/StoredProductFormRequest 및 원래 form bindings로 처리한다.
새 hwpx-agent.product-operation-request/v2는 operation.kind=recalculate_table_formulas만 받는다.
project/document/base_revision/expected_head_generation/source SHA/plan ID/idempotency key는 요청 identity다.
artifact ID/path/raw bytes/graph/map/AST/계산값/field selector/policy/access/approval/form_input은 v2 입력이 아니다.
v2는 form bindings가 있으면 거부하고 원래 sealed current Result만 선택한다.

원래 bounded 2MiB envelope 및 recursive duplicate-free UniqueJson을 재사용한다.
operation은 map-only typed visitor로 exact kind 하나만 받는다. root/nested unknown, escaped duplicate,
array/coerced operation, unknown kind, missing/invalid IDs/head/hash 등을 artifact read 전에 거부한다.
기존 form request의 byte/serialization/hash 계약을 바꾸지 않는다.

## 실제 원본 → 작업 준비

provider의 원래 project/document/head/SHA 검사를 전후 수행한다.
actual forms → fields → source meanings → original math → preserving result outcome →
original OperationPlanCompiler의 기존 P114 연결을 사용한다. caller result/graph/policy로 대체하지 않는다.
새 prepared product는 source/request/plan/candidate를 소유하고 unsafe self-reference 없이 재구축한다.
재검증 때 원래 ACL/AEAD/head/scope/whole source/math/protection/candidate/plan equality를 검사한다.
candidate bytes는 fresh with_verified_bytes callback으로만 노출한다. compiled()는 실행 권한이 없는 데이터다.

changed outcome은 nonempty original Atomic plan이며 원래 finite budgets와 P114 Field target contract를 따른다.
exact original FormulaResultOutputError::NoChange만 unchanged outcome이 된다.
보호/invalid source/no targets/limit/patch/readback 오류를 no-op으로 바꾸지 않는다.
NoChange도 원래 source/math/보호 검사와 fresh callback 검사를 통과해야 한다.
unchanged에서는 compiled=None이고 원본 whole bytes를 그대로 반환한다. 빈 plan을 합성하지 않는다.
native cache/recalculation, full importer, full field policy의 검증을 의미하지 않는다.

## 권한과 저장 경계

kind-specific bindings는 original v1에서만 사용한다. source formula 요청은 caller bindings를 거부한다.
request hashes/key는 tenant-global execution identity, idempotency claim, exactly-once 또는 held lease가 아니다.
original result/form route denial, full-source partial markers/Projection guard,
P06 table.formula native qualification와 새 Field-result argument 계약의 분리를 유지한다.
unchanged도 explicit RouteUnqualified이며 changed는 original source result route를 통해 거부한다.

현재 main.rs는 create-vs0만 노출한다. 이번 공통 product library API는 CLI/HTTP transport 연결이 아니다.
DB schema/운영·trust DB/issuer/signed registry/ExecutionManifest/backend/CAS/idempotency claim/publisher는 변경하지 않는다.
한글/COM/UI/접근허용/실제 SQL/설정·설치/stage·commit·push/삭제·이동을 실행하지 않는다.
P09 Gate OPEN/no P10/product false/full goal active. 최소6 coarse groups 유지/closed0.
