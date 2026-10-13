# P09-72 실제 원본의 필드 범위 importer 정책

## 목표

원래 immutable Source→body→observed forms 모델 위에 실제 paragraph-local fieldBegin/fieldEnd 범위를 연결한다. 기존 모델과 parser/parameter-envelope/stack/header/budget 검사 및 TEST policy binder를 변경하지 않는다. 실제 원본을 갖는 `ImportedDocumentForms`만 입력으로 받고, caller graph/map/숫자-ID identity/임의 path/정책/계산 결과는 받지 않는다.

새 모델은 필드 시작의 기존 exact-source 객체만 typed FieldNode로 바꾸고 실제 Reference table에 연결한다. 원래 paragraph inline·run·text/style·table/cell·나머지 객체·resource·opaque bag·security qualification을 유지한다. end 객체도 원래 source 그대로 보존한다. field source anchor는 실제 시작·끝 marker 위치이고, node common의 원래 control-wrapper anchor도 유지한다. source-local reference handle은 cross-revision persistent/native identity가 아니다.

## 범위·의미·실패 조건

- 원래 paragraph reader의 시작·끝 ID/stack/중첩/type/header/parameter envelope 검사를 재사용한다. field가 포함된 attributed 또는 mixed control wrapper는 성공으로 생략하지 않는다. body graph에 표현되지 않은 section native field는 `Unrepresented`로 거부한다.
- 실제 시작 ID는 paragraph-local pairing에만 사용한다. 다른 문단의 동일 native ID는 source-bound 서로 다른 logical references가 된다. source spine/element 순서로 관찰 목록을 정렬하며 normalized graph의 attached-table 순서를 원본 XML 순서로 가정하지 않는다.
- range는 원래 문단의 inline 위치 구간이며, 중첩별 캐시 텍스트를 복사하지 않는다. 실제 header/end attrs의 존재와 원문 semantic 값만 보존하고 missing editable/dirty/name/default를 만들지 않는다.
- parameter subtree는 exact source anchor로 연결하고 아직 해석되지 않은 것으로 유지한다. cached DATE/FORMULA 값의 계산 정확성, hyperlink URI/crossref destination, native/persistent identity, note/reference 전체 의미, 실행 권위는 승인하지 않는다. Reference.target_node_id는 원본 시작 위치를 목적지로 가장하지 않고 None이다.
- 실제 marker/header/native type에 source binding을 갖지만 native numeric field ID의 모든 의미나 paragraph를 가로지르는 field를 지원 완료한 것으로 부르지 않는다. 미지원 범위는 원래 parser 또는 새 source binding에서 거부한다.
- source/field model은 private immutable/non-deserializable이고 fresh source에서는 원래 whole package/form/body 및 파생 전체 graph/observations/receipt를 재구성해 비교한다.

## 저장 서비스·제품 경계

`StoredImportedDocumentForms::import_field_ranges`와 새 snapshot verify는 기존 fresh_source를 먼저 호출한다. scope5/head/ACL/quarantine/descriptor/scanner/AEAD/digest/whole source를 다시 검사한 뒤 실제 field graph를 만들고 head를 다시 확인한다. 정상 READ audit 외 ingest/CAS/seal/publication write는 없다. 두 head reads는 atomic lock/CAS/idempotency가 아니다.

새 partial profile/scope 두 marker는 각각 독립적으로 FullDocumentFormContext에서 Projection으로 거부해야 한다. 기존 여섯 partial markers나 security-state qualifier를 지워서 새 range import를 full product로 승인하지 않는다.

## 검증·보존

synthetic nested/header/default absence/hidden fields/attributed wrappers/namespace-bound source positions/anchor forgery/fresh drift와 실제 historical hyperlink1+generated/saved table16을 구분한다. 실제 원본17에서 독립 fresh processes의 전체 receipts를 비교하고, 서비스 fixture에서는 source ACL/AEAD/head/scope5/ingest absence/partial denial/privacy를 확인한다. 이는 새로운 licensed native 실행이나 실제 PG field acceptance가 아니다.

테스트 fixture 생성에 기존 workspace zip의 CLI dev-dependency 한 줄 및 대응 lock entry만 추가한다. production dependencies와 기존 패키지 writer/parser/SQL/service bodies를 변경하지 않는다. 실제 backend의 P71 증거는 그대로 historical scope로 보존하고 새 fixture-service field 검증으로 재승인하지 않는다.

일곱 whole pre-change originals 및 새 compile/lint/test 실패 당시 sources를 보존한다. declarations/새 Projection block/zip dev-dependency만 제거한 inverse가 whole 원문과 같아야 한다. original tests/locks/guard/assertion/skip를 수정하거나 삭제하지 않는다.

whole original qualification CLI replay/current admission·실제 new Source/Result/IR input lineage·정식 정책/issuer/publication/lifecycle·complete note/reference/catalog/security 의미·P62 원인·native/render/differential/P09 Gate는 별도 OPEN이다. Goal ACTIVE/no P10/한글·COM·UI·접근 허용창 금지를 유지한다.
