# P09-69 실제 원본 기반 명시적 폼 정책 결합 결과

- 상태: **actual source-bound explicit caller form-policy COMPONENT PASS / authoritative provider·complete importer·persistence·실행·native·Gate 미완료**.
- 정책: [P09-69_DOCUMENT_IMPORT_FORM_POLICY_POLICY.md](P09-69_DOCUMENT_IMPORT_FORM_POLICY_POLICY.md).
- 새 policies child module/tests/fresh probe와 fixture-only caller choices를 추가했다. P68 root는 module declaration 및 component identity 설명 주석만 변경했다. 제품 full context는 두 policy partial marker 독립 거부만 추가했다. original readers/domain validators/old tests/dependencies/Cargo.lock 변경 없음.
- 임의 caller graph/map/current value를 받지 않는다. 실제 source/document/provenance/observed-graph/ordered node/anchor를 확인하고, original whole native reader의 실제 관측에 명시적인 policy field만 결합한다. 기존 `bind_policies`/`verify_domain_state`로 complete form state를 검증한다.
- policy serialization을 default1MiB finite streaming budget으로 제한한 뒤 clone/merge하며, actual observation lookup은 ordered map으로 연결한다. 비폼 graph 전체·원본 source/inline 위치·observed missing native identity를 보존한다.

## 실행 검증

| 검증 | 실행 근거 | 결과 / 범위 |
|---|---|---|
| 새 정책 tests | aad461 / 5bbb99; 통합932649 | 14 PASS: actual10/original reader parity/envelope/order/anchor/kind/default/digest/complete radio group/custom combo/fresh source-policy drift/budget/local identity/non-policy full graph/no-form/privacy |
| package named Rust suites | 08ae2e / 932649 / b14f19 | 203 PASS, failed/ignored/filtered0; 기존 P68 named189 + new14 |
| product CLI lib/tests | a0c073 / 0f3bd1 / fcb7cd / fc8e9a | 90 PASS, failed/ignored/filtered0; 기존89 + 실제 policy-bound graph의 두 marker 독립 거부1 |
| original public domain suites | 96fc61 | form_control8 + form_input_public15 =23 PASS; defaults/groups/access/external-validator-not-executed/atomic state original guards |
| 별도 filtered unit | 20456a | private tamper1 PASS/17filtered; 전체 domain test 실행으로 집계하지 않음 |
| 엄격 lint | 0e22bc / b5b9c3 / c9ac83 / 4d32d2 | package/CLI/artifact/revision lib/tests + 새 example `-D warnings` PASS; allow/skip 없음 |
| fresh consumer | source-progress actual_source_consumers | 마지막 compiled executable에서 두 fresh processes의 actual10/누적50폼/5종/whole receipts exact. TEST caller 정책이며 native defaults 또는 actual provider 증거 아님 |
| 이전 실제 consumers | 12c759 | P68 forms10/P67 body10/table16 saved evidence 전체 exact. 기존 executable/current admission 재승인 아님 |
| 원본 코드 호환 | 56a42d | P68 root declaration/comment inverse, product additive guard inverse 전체 exact. 나머지 predecessor crate files30 whole bytes/SHA exact |
| 보존 | 6ac4bf + final source audit | prior544 declared pins/original graph1551 files·51047460 bytes/24origins/native75 exact; whole original qualification CLI replay 아님 |

package/CLI named **293 =203+90**. Original public domain23을 포함한 명시적 테스트는 **316 PASS**이며, 별도 filtered unit1은 구분한다. 전체 Python/legacy/current qualification/product/native/Gate PASS가 아니다.

## 실제 의미와 한계

- actual manifest10은 unique source SHA8개, edit10/check8/radio16/combo8/list8의 case-누적50폼이다. captured-base actual1쌍과 기존 derived4쌍을 읽은 것이며 독립 native 실행50회나 신규 실제 저장 증거가 아니다.
- caller가 선택한 empty/unchecked/optional/no-external-validator 테스트 정책을 production default로 설치하지 않았다. actual authoritative policy provider/issuer의 구현과 운영 검증은 남는다.
- 정책을 바꾸면 policy/state/full graph digest가 달라지고 동일한 원본 native binding은 유지된다. 외부 검증기 digest가 유효해도 실행·권위·결과는 미검증이다.
- domain identity의 숫자는 source-local COMPONENT reservation이라고 receipt/node에 표시한다. P68 `observed_form_json`과 실제 native Missing identity는 바뀌지 않는다. persistent ID나 관측 XML native ID가 아니다.
- complete state/identity scope/policy qualifier와 별도 metadata를 제거한 graph 전체가 P68 graph와 exact하다. 기존 partial markers와 security 상태는 보존되며, 새 두 marker도 독립적으로 full product context를 거부한다.
- 원래 legacy reference verdict `id_index_validation_failed`와 verified native overlay 총100을 유지한다. overlay를 legacy/complete reference PASS로 바꾸지 않는다.

## 실패 및 남은 작업

초기 compile2오류, 새 test compile오류, editable combo에 대한 새 fixture 오판12PASS/1FAIL과 diagnostic, 새 lint semicolon오류, predecessor receipt wrapper 선택 오류를 실패 JSON 및 whole source archive로 보존했다. 기존 validator/reader/테스트를 수정하거나 검사 허용조건을 낮추지 않았다.

다음은 actual authoritative policy provider와 필드·주석·참조·catalog/security의 완전한 의미 해석, 실제 persisted Source/Result/IR/previous-result→input, issuer/ExecutionManifest/idempotent publication, IR lifecycle/복구/동시성 및 whole replay/current admission이다. P62 `16fde8` 원인은 아직 UNRESOLVED. 기존 P65 synthetic IR/authority 증거를 actual importer→persisted end-to-end 증거로 재사용하지 않는다.

접근 허용창/한글/COM/UI·DB·system/trust/config·dependency·stage/commit/push·P10 없음. Goal ACTIVE/P09 Gate OPEN/current native admission INPUT_CHANGED/full34 NOT_RUN/0green.
