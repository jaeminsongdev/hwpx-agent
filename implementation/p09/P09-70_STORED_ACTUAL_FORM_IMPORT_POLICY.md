# P09-70 저장된 실제 Result의 원본 기반 폼 읽기 정책

- 범위: existing `StoredFormProvider`가 선택하는 실제 sealed current Result를 읽어 P68 원본 기반 관측 폼 모델과 P69 explicit policy COMPONENT에 연결한다. 외부 issuer·authoritative policy provider·complete importer·IR persistence·CAS/publication·native/P09 Gate 승인이 아니다.
- API: `StoredFormProvider::import_actual_forms(expected_head, now)` → `StoredImportedDocumentForms`; `verify(provider, now)`와 `bind_policies(provider, binding, policies, now)`; 반환된 `StoredBoundFormPolicies::verify`는 fresh service access와 whole source/policy/state/graph를 재검증한다.
- caller path/artifact selector/map/current values/graph/scanner verdict/permission bit를 받지 않는다. source는 provider의 trusted tenant/subject/project/branch/document scope 및 sealed head가 결정한다. library contexts는 provider-authenticated 입력이며 외부 issuer 구현/운영 검증이 아니다.

## 실제 서비스와 원본 연결

1. **unchanged original** `source`/`check_head`를 그대로 호출한다. tenant/subject/read scope, sealed node/project/revision/generation, Result descriptor kind/state/scanner/quarantine/size, ACL/download/AEAD/whole digest, before/after head 검사를 바꾸지 않는다.
2. Source와 Result를 같은 역할로 취급하거나 기존 Source-only guard를 변경하지 않는다. 이 경로는 처음부터 원래 provider의 **sealed Result read** 계약을 사용한다. bytes를 바꾸어 dedup identity를 우회하지 않는다.
3. actual downloaded bytes와 actual digest, provider-owned document ID로 unchanged `ImportedSourcePackage`→`ImportedDocumentForms`를 실행한다. caller synthetic map/state/IR가 원본을 대신하지 않는다. 원래 native package/canonical graph/source anchor/legacy failed verdict/opaque guards도 그대로 적용된다.
4. source snapshot, 실제 imported graph, receipt를 private immutable/non-deserializable object가 소유한다. 현재 head/generation/artifact/whole bytes와 scope에 결합되며 artifact 쓰기 capability가 없다.
5. fresh verification은 먼저 cached scope와 현재 provider의 tenant/subject/project/branch/document 전체를 비교한다. 매번 실제 서비스를 재호출해 ACL/descriptor/AEAD/head를 확인하고 source 전체와 imported whole graph/observations/receipt를 재구성한다. artifact/bytes만 같더라도 head advance는 old snapshot을 무효화한다.
6. policy 결합도 **fresh service verification 이후** P69의 명시적 typed policy field만 입력받는다. original envelope/ordered anchor/type/default/domain/group/budget 검사를 재사용한다. 실제 source의 ACL을 확인한 것은 caller 정책의 권위·외부 검증기 실행·native default 관측이 아니다.
7. bound policy verification은 fresh downloaded bytes에서 source/policy/state/graph 전체를 다시 비교한다. cached import 성공을 이후의 권한으로 재사용하지 않는다. 이미 허용된 이전 read가 반환한 메모리 데이터를 revocation이 소급 삭제한다고 주장하지 않는다.
8. 모든 P67/P68/P69 partial markers와 unqualified security state를 유지한다. original product full-document context는 계속 Projection으로 거부한다. generic provider-authenticated contexts나 marker 제거가 full importer/issuer 증명이 아니다.

## 검증과 변경 범위

- original provider root 및 original test root는 module declarations만 추가한다. 전체 원본을 archive하고 complete declaration inverse를 검사한다. old functions/assertions/native readers/domain/Cargo.lock/dependencies를 바꾸지 않는다.
- locked actual source/output10/8uniqueSHA/case-누적50forms를 실제 service APIs의 AES-GCM ingest/download, descriptor/ACL 및 sealed revision read를 통해 읽는다. 결과는 독립 original direct import/whole graph/observations/complete policy state/receipt와 exact해야 한다.
- service metadata/revision repositories는 **in-memory adapters**, scanner verdict·opaque sealed revision metadata·keys는 **explicit test fixtures**이다. actual package bytes와 실제 crypto/ACL/service checks를 사용하지만 PostgreSQL durability, real scanner, external issuer, execution manifest 또는 authoritative policy provider evidence가 아니다.
- fresh ACL 철회/head advance/AEAD tamper/wrong artifact kind/unverified quarantine/bad package, cached scope의 document/branch/project/subject/tenant 대체, stale policy/no-form/privacy 및 full-product rejection을 검사한다.
- 테스트 중 artifact ingest는 fixture setup의 prior Source+Result 두 개뿐이다. 새 APIs의 서비스 효과는 original read audits뿐이며, source/result/IR ingest·node sealing·CAS·manifest·key claim·publication을 수행하지 않는다. fixture prior Source는 아직 synthetic이므로 actual previous-result→next committed input chain 증거가 아니다.
- before/after head reads는 atomic CAS, lock/fence, 동시성 또는 ACL race-free execution이 아니다. durable actual Source/Result/IR lineage와 authority/lifecycle/복구/동시성/whole qualification/current native admission은 남는다.
- no-form source는 실제 body/None native binding을 보존하며 policy attestation은 원래 `NoForms` 거부다. 실제 저장된 table/field/note 등 미완성 의미가 full importer로 승격되지 않는다.
- COM/Hwp/UI/접근 허용창·DB/container 생성·trust/security/config 변경·dependency 추가·stage/commit/push·P10 없이 구현/검증한다. 실패·원본·private 증거를 보존한다. Goal ACTIVE/P09 Gate OPEN/native INPUT_CHANGED/full34 NOT_RUN/0green.
