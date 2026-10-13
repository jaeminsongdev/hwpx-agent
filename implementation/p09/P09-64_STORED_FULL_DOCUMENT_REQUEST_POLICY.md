# P09-64 저장된 전체 문서 IR 제품 요청 연결 정책

- 범위: `crates/product-cli`의 실제 제품 라이브러리에서 기존 strict 요청을 저장된 전체 문서 IR 준비 경로로 연결한다.
- 새 API: `form_product_request::stored_full_document::StoredFullDocumentProductFormRequest::prepare_json`.
- 기존 `hwpx-agent.product-form-request/v1` envelope/parser/limits/duplicate-key rejection을 그대로 재사용한다. caller graph/artifact/path/approval/lease/ExecutionManifest 필드를 추가하지 않는다.
- 새 receipt profile은 `hwpx-agent.product-stored-full-document-form-request/v1`이다. 기존 inventory-only receipt/profile/검증 기대값을 바꾸거나 역사 증거를 재서명하지 않는다.

## 필수 경로와 불변식

1. 원래 parser를 통과하기 전 서비스 읽기나 audit 추가가 없어야 한다.
2. provider의 실제 project/document/current head/source package SHA와 요청이 일치해야 한다.
3. 원래 `StoredFormProvider::prepare_full_document_json`을 호출한다. IR은 현재 sealed node의 `full_document_ir` 연결로만 선택한다.
4. source와 IR 각각의 실제 artifact service ACL/state/AEAD/digest 검증, canonical IR/전체 graph/package 결속, 원래 atomic form compiler와 full-graph compiler를 모두 유지한다.
5. 준비된 요청 재검증은 fresh source/head/IR/access/map/policies 검증 후 요청의 canonical/scoped digest, whole-graph plan ID/base revision/document identity를 다시 대조한다. 여러 head read는 lock이나 atomic CAS가 아니다.
6. IR 누락/잘못된 kind/media/세 digest/noncanonical JSON/보호된 graph/다른 document/inventory projection은 거부한다. inventory-only 경로로 fallback하지 않는다.
7. 기존 real signed authority는 검증 뒤에만 조회한다. 현재 route는 unqualified여서 거부하며 VS0 권한을 양식 경로에 사용하지 않는다.
8. 후보 HWPX/target graph/compiled plan은 메모리 준비 결과다. artifact ingest/stream initialization/idempotency key claim/CAS/ExecutionManifest/publication을 하지 않는다. 정상 artifact READ audit는 추가된다.

## 증거 범위

새 tests는 기존 locked HWPX 4개 사례와 private captured fixture, 기존 scanner/crypto/revision fixture를 재사용한다. 실제 ArtifactService/RevisionService/compiler를 호출하지만 metadata/blob/revision 저장소는 **in-memory**, scanner/keys와 caller whole graph는 **synthetic test-only**다.

따라서 source/component 요청 연결은 검증할 수 있으나 actual PostgreSQL+LocalEncryptedBlobStore 조합, 실제 native whole-document importer/provenance, 외부 issuer/ExecutionManifest/idempotent publication, IR lifecycle/native semantics/render/direct differential/P09 Gate를 증명하지 않는다. 기존 P63 DB PASS를 이 새 요청 경로의 DB PASS로 재사용하지 않는다.

원래 assertions/guards/receipts와 변경 전 전체 bytes를 보존한다. 기존 3개 파일의 변경은 module export, 두 helper의 sibling visibility, 새 test module 선언뿐이며 나머지 텍스트를 대조한다. 원장 변경은 P64 상태와 다음 경계에 한정한다. 실패 소스도 보존한다.

접근 허용창, Hwp COM/UI/native dispatcher, trust/security/config 변경, git stage/commit/push, 기존 DB 또는 사용자 원본 정리는 금지한다. P09 Gate가 닫히기 전 P10 새 구현을 시작하지 않는다.
