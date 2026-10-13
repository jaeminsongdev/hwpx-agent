# P09-114 — authenticated source formula-result original compiler 연결 정책

## 범위와 실제 경로

StoredFormProvider의 원래 source download/ACL/AEAD/head 검사 → actual form/field range/meaning →
original decimal evaluator → preserving whole result candidate → 원래 domain_ir::OperationPlanCompiler.
호출자는 PlanId만 지정하며 결과값, AST, graph, source map, policy, authority는 공급하지 않는다.
원본 source head/revision, 실제 meaning graph와 source fieldBegin logical ID를 그대로 사용한다.
partial metadata/structure/form/field/meaning/review/settings marker를 지우거나 full graph를 합성하지 않는다.

changed field만 source spine/element 순서로 하나의 Atomic compiled plan에 묶는다.
source/candidate/evaluated-values SHA 및 실제 Decimal JSON을 required locked Text argument로 묶는다.
current cache는 original Unverified Decimal과 정확히 같을 때만 건너뛰고 모든 field 보호 검사와
source begin anchor/coordinate 검사는 유지한다. 의미·결과 lookup은 immutable reference-ID 인덱스로
수행하며 중복 key는 거부한다. 원래 input bounds는 완화하지 않는다.

original leaf-intent4096 budget에 맞춰 changed operations1365, dependencies4096, args16,
string4096, totalargs2MiB, canonicalplan8MiB를 적용한다. caller map으로 limit/target을 대체하지 않는다.
compile 전후와 cached plan/candidate consumption 전에 fresh original source/result 검사를 한다.
이 fresh check는 transactional lease/CAS/publication 보장이 아니다.

## authority 경계

capability ID table.formula를 사용하지만 이번 source-result Field target 및 4개 argument 계약은
새 compiler-data 계약이다. P06의 기존 table.formula native/signed/public route PASS를
이번 계약의 자격으로 상속하지 않는다. CapabilityCatalog는 original compiler argument 검사용이지
signed registry, ExecutionManifest 또는 issuer authorization이 아니다.

compiled()는 immutable typed compiler data만 노출한다. PreparedStoredFormulaPlan은 private fields,
non-Deserialize, redacted Debug이고 receipt는 hashes/counts/headgeneration만 담는다.
original require_current_product_route는 여전히 RouteUnqualified를 반환한다.
original FullDocumentFormContext partial-source 거부, issuer, full field policy, registry/backend guard를
변경하지 않는다. 후보 바이트를 받을 수 있다는 것이 native/durable 실행 허가가 아니다.

## 검증 기준과 잔여

원래 실제 corpus manifest는 고정하고 fixture만 in-memory derivative로 만든다.
두 구역·4개 수식, current/empty 혼합, original Field targets와 whole candidate 비교,
ACL/AEAD/head/quarantine, tenant/subject/project/branch/document scope, 보호/invalid source 전체 거부,
canonical roundtrip과 original full/route 거부를 검증한다. 최종 결과는 별도 receipts에 기록한다.

native/COM/UI/permission popup/actual SQL/operating trust DB/settings/install/Git publication/deletion/move 금지.
P09 Gate OPEN/product false/no P10/full goal active, 최소6 coarse groups 유지/이번 closed0.
PLANS 삭제 상태와 모든 old source/executable/실패 증거를 보존한다.
