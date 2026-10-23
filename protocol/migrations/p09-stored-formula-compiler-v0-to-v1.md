# P09 stored formula compiler v0 → v1

기존 authenticated field-result 후보에서 새 compile(provider, PlanId, now)을 호출하여
PreparedStoredFormulaPlan을 얻는다. 기존 결과 API와 오류/route guard는 제거하지 않는다.
새 plan은 실제 source head/revision/meaning graph/Field targets와 whole candidate에 묶인
원래 OperationPlanCompiler 결과다. arguments는 source/candidate/evaluated-values SHA 및 Decimal JSON이다.

DB schema, native field schema, public JSON product request, signed registry, backend route,
ExecutionManifest/issuer, native command, original full-source admission은 변경하지 않는다.
table.formula ID의 기존 native PASS가 새 Field-result argument 계약을 검증한 것으로 승격되지 않는다.
재검증 실패 시 callback 전에 거부하고 일부 plan/candidate를 publish하지 않는다.
canonical compiled data roundtrip은 execution authority roundtrip이 아니다.

full field/date/external/document semantics, full importer/product envelope, trusted protection/issuer,
atomic durable publisher 및 actual native/SQL qualification이 갖춰져야 다음 경로 자격을 부여할 수 있다.
P09 Gate OPEN, P10 금지와 기존 evidence 상태를 유지한다. rollback은 새 child 사용을 중단하는 것이며
old parent 전체 preimage는 별도 보존한다. 조사 없이 dirty source 전체를 되돌리지 않는다.
