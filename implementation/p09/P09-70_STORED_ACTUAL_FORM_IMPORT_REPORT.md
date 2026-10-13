# P09-70 저장된 실제 Result의 원본 기반 폼 읽기 결과

- 상태: **actual service read→actual source-backed form import→explicit policy COMPONENT PASS / durable actual lineage·policy issuer·full importer·실행·native·Gate 미완료**.
- 정책: [P09-70_STORED_ACTUAL_FORM_IMPORT_POLICY.md](P09-70_STORED_ACTUAL_FORM_IMPORT_POLICY.md).
- `StoredFormProvider::import_actual_forms`를 추가해 sealed current Result에서 실제 bytes를 읽고 원본 기반 폼을 직접 import한다. caller map/state/graph 또는 임의 artifact/path를 받지 않는다. `StoredImportedDocumentForms` 및 policy-bound 객체는 private immutable/non-deserializable snapshots다.
- 기존 provider `source`/`check_head`와 artifact/revision service의 ACL/descriptor/scanner/quarantine/AEAD/digest/sealed-head guards를 그대로 재사용한다. 기존 Source-only 승인 guard나 dedup 종류를 바꾸지 않았다. head 재읽기는 atomic CAS/held lock이 아니다.
- policy 결합과 재검증 전에 fresh service access를 다시 확인한다. P69 원본/문서/anchor/order/default/domain/group/budget 계약과 P67/P68/P69 partial product rejection을 그대로 유지한다.

## 실행 검증

| 검증 | 실행 근거 | 결과 / 범위 |
|---|---|---|
| 신규 service importer tests 첫 실행 | 3078d9 / 012aff | 9 PASS/28filtered; 전체 old suite PASS로 집계하지 않음 |
| 최종 전체 CLI lib/tests | e410d9 / 3185e9 | 99 PASS/failed0/ignored0/filtered0; original90 + new9. 저장 경로 suite는37개 |
| 독립 fresh final tests | abb105 / 9f0988 | new9 PASS/old28filtered; 최종 scope5대체 검사를 포함한 별도 실행 |
| current package named suites | 80df70 / f10f2a | 203 PASS/failed0/ignored0/filtered0; source/body/observed forms/policy/native/package/graph/text/table regressions |
| original public domain suites | d44765 | original form_control8 + form_input_public15 =23 PASS |
| strict lint | 85daa8 / d9d9f3 / 4780f1 / 762c75 | product/package/artifact/revision lib/tests `-D warnings` PASS; allow/skip 없음 |
| whole compatibility | 6d5e70 | provider/test root module declarations를 제거하면 whole prior sources exact; 나머지 prior crate files37 bytes/SHA exact |
| 이전 증거 보존 | 65a821 + final audit | prior639 declared pins/original1551 files·51047460 bytes/24archive origins/native75 exact; original whole qualification CLI replay 아님 |

명시적 current named tests **325 = package203 + CLI99 + original public domain23**. 신규9 포함. 별도 filtered runs를 더해서 중복 집계하지 않으며, 전체 workspace/Python/legacy/qualification CLI/product/native/Gate PASS가 아니다.

## 실제 서비스 연결과 증거 경계

- locked manifest의 실제 source/output10/8unique SHA/case-누적50forms를 서비스 APIs로 ingest한 **Result**에서 다시 download한다. original direct importer와 source/whole graph/all observations/complete form state/receipt가 exact하다. original legacy failed verdict와 observed Missing native identities를 유지한다.
- 테스트 metadata/revision adapters는 in-memory이고 scanner/opaque sealed-node metadata/crypto keys는 fixture다. actual captured/derived package bytes와 original production AES-GCM/ACL/revision checks를 사용하지만, PostgreSQL durability·real scanner·external issuer·signed manifest 또는 actual authoritative policy provider 증거가 아니다.
- cached provider scope의 document/branch/project/subject/tenant 대체를 모두 거부한다. fresh ACL 철회, 실제 repository head advance, 실제 encrypted blob tamper가 import/verify/policy 단계 모두에서 원래 service error로 거부된다.
- head advance 후 Result bytes가 같아도 old snapshot은 실패한다. 새 head에서 명시적으로 다시 import하면 같은 실제 graph를 새 generation receipt에 결합한다. 이를 atomic CAS/idempotent execution 또는 commit으로 부르지 않는다.
- Source-kind artifact·Unverified/quarantined descriptor는 기존 source guard에서 거부된다. invalid HWPX는 실제 importer에서 거부되며 fallback 성공이 없다. no-form actual body는 유지하고 native/policy attestation을 만들지 않는다.
- policy envelope 또는 ordered policy를 바꾸면 P69 Binding으로 거부한다. source ACL 확인은 caller 정책의 issuer 권위가 아니다. 모든 실제 policy-bound graph는 여전히 full product context Projection이다.
- 서비스 ingest 수는 setup prior Source+Result의 두 개 그대로이고 head/node/result는 변하지 않는다. 새 경로의 서비스 write는 원래 read audit뿐이다. setup prior Source는 synthetic이므로 실제 previous-result→next committed input chain으로 승격하지 않는다.
- 공개 receipt/debug에는 raw package/XML/graph/state/policy values·tenant/subject 또는 private paths를 출력하지 않는다.

## 실패와 다음 경계

새 test compile984675는 기존 `audit_events` trait import 누락이었다. 실패 당시 whole child test를 archive하고 새 child에 trait import만 추가했다. 기존 service/tests/assertions/guards는 바꾸지 않았다. P69 및 이전 실패·private 증거는 그대로 보존했다. P62 `16fde8` 원인은 여전히 UNRESOLVED다.

다음은 이 actual importer의 실제 durable Source/Result/IR provenance 및 이전 결과의 다음 입력 연결, 정책 issuer/provider와 complete field/note/reference/catalog/security 의미, 정식 ExecutionManifest/publication/idempotency, IR lifecycle/복구/동시성 및 whole replay/current admission이다. 현재 결과를 기존 P65 DB acceptance나 정식 제품 실행 증거로 합쳐서 승인하지 않는다.

COM/Hwp/UI/접근 허용창·DB/container·trust/security/config·dependency·stage/commit/push·P10 없음. Goal ACTIVE/P09 Gate OPEN/native INPUT_CHANGED/full34 NOT_RUN/0green.
