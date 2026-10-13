# P09-72 실제 원본의 필드 범위 가져오기

- 상태: **actual source-backed paragraph-local field ranges COMPONENT PASS / 계산·목적지 해석·전체 importer·제품 실행·native·P09 Gate OPEN**.
- 정책: [P09-72_DOCUMENT_IMPORT_FIELDS_POLICY.md](P09-72_DOCUMENT_IMPORT_FIELDS_POLICY.md).
- 실제 immutable Source→body→forms 위에 원본 `fieldBegin`/`fieldEnd`의 범위, 중첩 관계, 정확한 source anchors를 연결했다. 원본 파라미터는 보존하되 계산 결과나 참조 목적지를 만들지 않는다.
- 새 서비스 snapshot은 원래 scope/head/ACL/quarantine/scanner/AEAD/digest 검사를 통과한 actual source에서만 파생한다. 기존 실제 PG/file backend의 P71 증거와 이번 in-memory service fixture 검증은 별도 범위다.

## 구현과 보존 경계

`crates/hwpx-package/src/document_import/fields.rs`는 실제 source의 시작·끝 ID를 paragraph-local pairing에만 쓰고, 서로 다른 문단에서 같은 native ID가 관찰되면 source-bound references를 구분한다. 중첩의 parent reference와 원래 inline 위치를 보존한다. missing editable/dirty/name/default를 채우지 않으며 `Reference.target_node_id=None`은 아직 목적지가 해석되지 않았다는 뜻이다.

필드 시작의 기존 exact-source 객체만 typed `FieldNode`로 바꾸고, 시작 node의 원래 common/wrapper anchor 및 끝 객체를 유지한다. 본문 text/run/style, table/cell/grid, 나머지 객체, resources, opaque bags, security qualification은 unchanged다. 전체 inverse graph 복구 및 fresh source 재구성으로 검사한다. 관찰 목록은 normalized graph의 attached-table 순서가 아니라 원본 spine part/element 위치로 정렬한다.

원래 paragraph parser의 field header/type/stack/parameter-envelope/budget 거부를 유지한다. attributed/mixed wrapper나 body graph에 표현되지 않은 section field를 성공으로 생략하지 않는다. section 밖의 원본 parts도 보존하지만 지원 완료한 body fields로 가장하지 않는다. source-local handles는 persistent/native identity가 아니다.

`StoredImportedDocumentForms::import_field_ranges`와 cached snapshot verify는 원래 fresh source check와 whole source/form/field 재구성을 사용한다. 정상 READ audit 외 ingest/CAS/seal/publication write는 없다. 두 head reads는 atomic lock이나 idempotency가 아니다. 새 partial profile/scope 각각은 독립적으로 full product context에서 Projection으로 거부된다.

기존 production dependencies는 unchanged다. 기존 workspace ZIP의 CLI test-only dev-dependency 한 줄 및 대응 lock entry만 추가했다. 기존 parser/service/SQL bodies, original tests/guards/expected values/skip는 수정하거나 삭제하지 않았다.

## 현재 실행 증거

| 검사 | 결과와 정확한 범위 |
|---|---|
| 실제 원본 consumer | historical captured hyperlink1 + P06 generated/saved table16, 총17 packages/17 ranges; FORMULA16/HYPERLINK1, parameterized17, actual nested0 |
| 독립 fresh processes | 3e5bb5, 수정 후 executable로 두 child processes의 전체 metadata receipts exact; 원본 begin/end anchors resolve 및 whole fresh reconstruction PASS |
| current CLI/package lib/tests | 8fa15f/9898a9/62c8fb, exit0; 98 targets, CLI106 + package862 =968 PASS, failed/ignored/filtered0 |
| original domain public suites | 26d34a, form_control8 + form_input_public15 =23 PASS |
| 신규 검사 | package12 + stored-service7 =19; 기존972 + 신규19 = named991 PASS |
| strict lint | c348a7, four-crate lib/tests와 새 actual example `-D warnings` PASS; allow/skip 없음 |
| format | 10d09f, rustfmt recursive check PASS |
| whole original inverse | 9f28e6 및 최종 보존 검사, 아래 six original source files byte/SHA exact |
| unchanged predecessor source | 49f16e, P71 declared source401 중 seven authorized originals 외394 byte/SHA exact |
| 원본·이전 증거 | e29925 및 최종 audit, prior1150 declared pins / original1551 files·51,047,460 bytes /24 archived origins /native75 exact |

실제 consumer executable SHA: `32c8ba418875cc17409a6d37178806c53d09e12a5bd9aaba74103146285cf57e`. 수정 전 fresh pair7de7c7와 이전 verbose/truncated regression은 최종 current proof로 재사용하지 않았다.

991은 지정한 Rust 회귀 검사 수이며 신규991 기능, workspace 전체, Python, whole original qualification CLI, 실제 field PG acceptance 또는 제품/native/Gate PASS가 아니다. all15 field types의 관찰, nested fields, source order, malformed headers, absent defaults, anchor forgery, hidden fields, scope/ACL/head/AEAD 거부는 synthetic/service fixture와 actual package 증거를 구분한다.

actual17에서는 parameter 값·URI·XML·graph·원본 전체 로그를 출력하지 않고 counts/hashes/qualification metadata만 저장했다. DATE/FORMULA 평가 정확성, hyperlink/crossref 목적지, native 실행은 검사하지 않았다. 실제 nested fields가17개 원본에서 발견됐다는 주장도 하지 않는다.

## 실패와 원본 보존

whole pre-change originals seven files는 `source-archive/p09-72-pre-field-ranges/`에 보존했다. `document_import.rs`, production/test `actual_import.rs`, `full_document.rs`, CLI `Cargo.toml`, `Cargo.lock`, P71 whole `PLANS.md`다. six code/config inverses는 additive declarations/Projection block/test dependency만 제거하면 whole 원문 bytes/SHA와 같다. PLANS는 이전120 lines 전체를 별도 보존하고 현재 행만 동기화한다.

초기 새 소스의 E0597 rebuild lifetime, strict lint helper/closure, attributed-wrapper fixture, nested test module path, CLI ZIP dev-dependency compile 실패는 당시 whole sources로 남겼다. 검토에서 발견한 attached-table field 순서 문제는 수정 전 소스를 보존하고 source part/element 정렬 및 회귀 검사를 추가했다. 뒤따른 unused-mut lint도 실패 당시 소스를 보존했다. 총 eight failed/intermediate source files는 immutable archive에 있고 상세는 [initial failures](evidence/p09-72-document-import-fields.initial-failures.v1.json)에 남긴다. 실패 당시 기대값을 삭제하거나 original parser rejection을 우회하지 않았다.

원본 actual HWPX, 과거 native receipts, 사용자 dirty changes, 기존 DB, trust/security/config를 변경·삭제·이동하지 않았다. 이번에는 DB/container를 생성하지 않았으며 Hangul/COM/UI/native dispatcher/접근허용창, stage/commit/push를 실행하지 않았다.

## 증거 파일과 다음 경계

- [actual consumer](evidence/p09-72-document-import-fields.actual-consumer.v1.json): actual17와 두 fresh processes의 metadata evidence.
- [Rust regression](evidence/p09-72-document-import-fields.rust-regression.v1.json): 실행 command와98 target별 counts, 신규19와 named991의 범위.
- [source progress](evidence/p09-72-document-import-fields.source-progress.v1.json): 현재 declared source와 원본/실패 archive/predecessor receipts의 raw bytes/SHA. 이것은 current whole admission을 대체하지 않는다.
- [final audit](evidence/p09-72-document-import-fields.final-audit.v1.json): frozen declared pins/원본/수정 범위/PLANS/Hwp absence 재검사.

다음 구현은 exact parameter의 field-specific 의미와 destinations/evaluation, note/reference/catalog/security 전체 importer, actual committed Source/Result/IR·previous-result input lineage다. TEST policy/scanner/keys/issuer를 실제 권위로 승격하지 않는다. 정식 ExecutionManifest/publication/idempotency, IR lifecycle/concurrency/crash/recovery도 남아 있다.

whole original qualification CLI replay/current source admission은 별도 OPEN이며, 이전 P62 16fde8 원인은 UNRESOLVED다. native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green/P09 Gate OPEN/Goal ACTIVE/no P10를 유지한다. 접근허용 금지 동안 native 실행은 하지 않는다.
