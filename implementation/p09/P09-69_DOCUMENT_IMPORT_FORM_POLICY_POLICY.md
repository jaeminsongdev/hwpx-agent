# P09-69 실제 원본 기반 명시적 폼 정책 결합 정책

- 범위: P68의 실제 관측 폼에 caller가 **명시적으로 제공한 정책 필드만** 결합해 원래 domain `FormDocumentState`와 실제 body graph의 complete form COMPONENT state를 만든다. 권위 있는 정책 provider/issuer, complete document importer, persistence/publication/native/P09 Gate 승인이 아니다.
- entry: `document_import::forms::policies::PolicyBoundDocumentForms::bind(imported, source_binding, policies)`; immutable P68 source를 borrow한다. caller graph/map/current value/common/geometry/native ID를 입력받지 않는다. Date 등 미지원 native type을 새로 지원한다고 주장하지 않는다.
- profile `hwpx-agent.document-import-explicit-form-policy/partial-v1`; scope `explicit_caller_policy_source_bound_component_not_authoritative_full_document_or_execution`.

## 입력과 원본 검증

1. `FormPolicySourceBinding`의 document ID/whole package SHA/source provenance SHA/observed graph SHA 전체가 실제 P68 source에 일치해야 한다. digest는 caller의 권위나 서명이 아니다.
2. `SourceFormPolicy`는 source-order node ID와 actual version-bound source anchor 및 typed `ExplicitFormPolicy`만 가진다. 누락·추가·중복·재정렬·다른 버전/문서/anchor·종류 불일치를 거부한다.
3. 입력 policy는 text default/validation, checkbox default/must-be-checked, radio default/group-required, combo/list default-selection/validation만 제공한다. production default를 선택하거나 원본의 관측값을 자동 default로 해석하지 않는다.
4. 원래 domain default controls/input-byte ceiling에 따라 serialization을 **streaming SHA/finite byte budget**으로 제한한 뒤 정책을 clone/merge한다. policy의 유효한 외부 검증기 digest를 실제 검증기 실행·권위 증거로 승격하지 않는다.
5. immutable source의 실제 map을 다시 만들고 unchanged `NativeFormPackageReader`로 actual ZIP 전체를 reread한다. full native binding과 모든 관측 record가 P68 관측과 exact해야 한다. lookup은 bounded ordered map이며 반복 선형 검색을 하지 않는다.
6. 실제 관측값과 typed explicit policy field만 결합한 후 **unchanged original** `bind_policies` 및 `verify_domain_state`를 호출한다. current values/items/common/styles/positions/shape/opaque/catalog/resource/reference/protection과 complete defaults/global radio groups를 원래 검사한다. 기존 comparator/validator를 약화하지 않는다.
7. editable combo의 custom default 허용은 원래 domain 의미를 유지한다. 임의 non-member를 모든 combo에서 거부하지 않는다. invalid text/NUL/digest/min-max/list membership/group inconsistency 및 native bounds는 original validator로 거부한다.
8. no-form source는 이전 importer의 실제 body/None binding을 보존한다. 새 policy API는 `NoForms`로 거부하여 존재하지 않는 native catalog/security attestation을 만들지 않는다.

## 문서와 identity 경계

- 원래 domain의 `FormControlIdentity.native_object_id`는 원본 map이 만든 **source-local component reservation**이다. actual XML object/instance ID 또는 persistent crossrevision identity가 아니다. 별도 `component_identity_scope`를 receipt와 모든 complete state node에 명시한다.
- P68 관측 API/`observed_form_json`은 계속 reservation/default/validation을 포함하지 않는다. 새 component state는 그 관측을 변경하거나 Missing native identity를 숫자로 메우지 않는다.
- 동일한 FormControl node/common/source/inline 위치와 모든 본문·표·그 외 node·resource·opaque·security 값을 보존한다. 노드에 complete state/identity scope/policy qualification, metadata에 별도 policy profile/scope/digests만 추가한다.
- 기존 P67 source profile/scope와 P68 observed-form partial markers를 유지한다. 새 두 marker 중 하나만 있어도 기존 product full-document context는 Projection으로 거부한다. marker 제거는 importer/provider/issuer 권위 증명이 아니다.
- fresh whole source→body→observations→explicit policy→complete form state→graph를 재구성하고 source/observations/whole state/graph/receipt/policy 전체를 비교한다. digest만 갱신하지 않는다.

## 검증과 남은 범위

- 실제 locked HWPX10/8unique source SHA/누적50폼에 **명시적인 TEST caller 선택**을 사용한다. captured-base actual1쌍과 기존 derived4쌍이며 신규 native/default oracle 또는 real provider evidence가 아니다. probe는 값/raw XML/개인 파일 경로를 출력하지 않고 counts/digests/receipt만 출력한다.
- 기존 original domain/native/body/package/CLI regressions, 실제 source/non-policy graph exact parity, native actual missing identity, wrong envelope/order/anchor/type, invalid policy/budget/whole radio group, fresh source/policy drift, no-form/privacy 및 독립 product marker 거부를 검사한다.
- 실패 당시 whole source와 이전 source/ledger를 archive하고 원래 실패·private 증거를 보존한다. whole historical qualification CLI replay, P62 unresolved 원인, current native admission INPUT_CHANGED/full34 NOT_RUN/0green은 닫지 않는다.
- 실제 authoritative policy provider·필드/주석/참조/catalog/security 의미·persisted Source/Result/IR/previous-result input chain·issuer/ExecutionManifest/publication/idempotency·IR lifecycle/복구/동시성·native/render/differential/Gate는 미완료다.
- 접근 허용창·한글/COM/UI·DB 생성·system/trust/cache 변경·dependency 추가·stage/commit/push·P10 구현 없이 작업한다. Goal ACTIVE/P09 Gate OPEN을 유지한다.
