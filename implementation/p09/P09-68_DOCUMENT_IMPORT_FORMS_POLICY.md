# P09-68 실제 원본 기반 관측 폼 IR 정책

- 범위: 실제 HWPX의 5종 native form 관측값을 원본에 연결된 본문 `FormControl` 노드로 변환한다. 전체 문서 의미·기본값·검증 정책·제품 실행·Gate 승인이 아니다.
- entry: `document_import::forms::ImportedDocumentForms::import(ImportedSourcePackage)`; private immutable source/body와 실제 관측 graph를 함께 소유한다. caller map/state/graph나 임의 파일 경로를 입력받지 않는다.
- profile: `hwpx-agent.document-import-observed-forms/partial-v1`; observation scope: `observed_native_values_not_default_validation_or_execution_policy`.
- 기존 P67 source profile/scope도 그대로 PARTIAL로 유지한다. 이 API는 기존 `ImportedDocumentStructure`의 허용 조건을 바꾸지 않는 별도 단계이다.

## 실제 원본과 기존 validator 연결

1. 실제 spine·namespace-aware element tree·P66 version-bound anchors에서 모든 문단과 native edit/checkBtn/radioBtn/comboBox/listBox의 논리 map을 도출한다. native 숫자 ID를 논리 ID로 쓰지 않는다.
2. 기존 native reader의 `FormControlIdentity.native_object_id`는 내부 component reservation만을 위한 전역 순번이다. 관측 native ID와 다르며 public 관측 record/폼 IR로 내보내지 않는다. 실제 missing/object/instance identity는 original reader의 관측을 그대로 기록한다.
3. 실제 immutable original ZIP 전체에 **기존 NativeFormPackageReader를 수정 없이** 적용한다. catalog·resource·reference overlay·native ID·physical placement·값·보호 신호·opaque binding과 기존 bounded ZIP/XML/map guards를 그대로 재사용한다.
4. typed map의 control마다 actual source anchor 및 raw control subtree SHA가 original reader의 관측과 일치해야 한다. 실제 문단/run/inline 위치도 원본 logical paragraph anchor에 연결된다.
5. 본문에 대응되는 source-backed XML 객체만 폼 노드로 변환한다. node ID/common/source/resource refs와 inline control refs·문단·표·기타 모든 비폼 구조를 보존한다. 알려진 폼이 현재 body mapping 밖에 있으면 `Unrepresented`로 거부하고 사라진 폼을 성공으로 집계하지 않는다.
6. 노드에는 `observed_form_json`만 추가한다. original observed payload/common/native identity/geometry/opaque hashes를 보존하며 `complete_control_state_json`, default_value, default_selected_value, required/external validator 등의 policy를 원본에서 추측하지 않는다. command digest를 읽은 것은 명령 실행 권한이 아니다.
7. 폼이 없으면 실제 본문을 보존하고 empty observation을 반환한다. native binding/reference verdict는 None이며 catalog/security acceptance를 꾸며내지 않는다. 미지원 객체는 기존 exact source opaque로 남는다. 기존 native reader의 지원 profile 밖인 문서를 이 단계에서 성공으로 fallback하지 않는다.
8. `protection_signal_observed`는 관측 사실만 별도로 남긴다. generic graph의 unqualified security-state 기본 bool을 보호 부재/잠금 해제 attestation으로 바꾸지 않는다.
9. original legacy IdIndex verdict와 independently verified native reference overlay issue 수를 receipt에 그대로 보존한다. overlay acceptance를 legacy profile PASS 또는 전체 참조 의미 검증으로 바꾸지 않는다.

## 제품과 검증 경계

- fresh bytes로 source 전체→본문→native observations→graph 전체를 재구성하고, source/body graph/form graph/모든 관측 record/receipt를 비교한다. digest만 갱신해 통과시키지 않는다.
- product full-document context는 기존 P67 profile/scope와 별도로 새 observed-form profile/scope 중 하나라도 있으면 Projection으로 거부한다. marker 검사는 importer issuer 권위 증명이 아니며 arbitrary caller graph의 권위를 보장하지 않는다.
- 실제 source/output10 사례의 5종·누적50개 폼과 P67 body10/table16의 exact 결과를 확인한다. unique source SHA8개와 case 누적 수를 구분한다. captured-base actual1쌍과 기존 derived 사례4쌍이며 파생본을 native 저장/실행 증거로 승격하지 않는다. 실제 empty/no-form·catalog/attribute/native-ID rejection·namespace prefix independence·non-form parity·개인 값 log privacy를 검증한다.
- 현재 관측 typed 값은 실제 target UI·저장·재열기·render·direct differential 검증과 구분한다. Date·새 native shape·기본값/검증 policy·전체 importer/catalog/security·실제 persisted Source/Result/IR·issuer/manifest/publication/lifecycle는 미완료로 남긴다.
- P62 이전 실패·original source/private/failed receipts는 보존한다. current native admission INPUT_CHANGED/full34 NOT_RUN/P09 Gate OPEN/no P10를 유지한다.
- COM/UI/Hwp/접근 허용창·DB 생성·system/trust/security setting·dependency 변경·stage/commit/push 없이 구현한다.
