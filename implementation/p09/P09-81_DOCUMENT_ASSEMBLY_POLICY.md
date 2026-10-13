# P09-81 같은 원본의 모델·글꼴·보안·페이지 설정·수식 sidecar 통합 정책

## 제품 방향과 범위

완전한 문서 가져오기(A12)의 실제 누락을 줄인다. 기존 catalog에서 분기했던 font graph와 security → section-settings graph를 같은 immutable source에서 함께 만들고, 정확한 source formula evaluation sidecar도 같은 객체로 보존한다. 새 `ImportedDocumentAssembly`와 인증된 저장 서비스의 `import_document_assembly`가 그 경로다. 단순한 수치 합산이나 문서상의 PASS 선언은 구현을 대신하지 않는다.

현재 정보가 완전하지 않은 importer를 완전한 importer로 승인하지 않는다. 미지원 필드 의미, 댓글 의미 양성 증거, 전체 settings/font availability/native security, 실제 policy/scanner/issuer/manifest, persisted lineage/publication/lifecycle 및 native acceptance는 별도 미완료 요구사항이다. A12와 P09 Gate는 OPEN이다.

## 동일 원본과 보존

- 모든 branch는 하나의 non-deserializable `ImportedDocumentCatalog`에서 생성한다. caller가 임의 graph/receipt/source branch를 조합하는 API를 제공하지 않는다.
- 원래 source/catalog/body/field/note/bookmark/font/page/column/active inventory/math reader와 한계는 그대로 사용한다. 오류를 성공 fallback, 기본값 또는 생략으로 바꾸지 않는다.
- font graph에서 styles와 정확한 두 marker를 제외한 전체 draft가 원래 catalog와 동일해야 한다. security/settings graph의 styles는 원래 catalog와 동일해야 하며, 다르면 덮어쓰지 않고 거부한다.
- 통합 graph의 styles만 font graph에서 가져온다. settings/security의 나머지 모든 필드는 원래 그대로 유지한다. 다섯 통합 marker만 제거하고 원래 styles를 되돌리면 전체 settings graph가 동일해야 한다.
- source package SHA, catalog graph SHA, security → settings graph SHA, meanings → formula SHA chain을 모두 확인한다. 다른 document identity 또는 metadata key 중복은 거부한다.
- original typed font definitions/links, section settings, complete active inventory/control/resource/native-form bindings, formula values/cell anchors와 각 원래 receipt를 전부 보존한다.
- 수식 결과는 typed sidecar이며 graph에는 그 sidecar digest만 연결한다. native cached text/body/AST 또는 원본 패키지를 덮어쓰지 않는다. 원래 canonical numeric inputs와 exact math 실패는 그대로 거부한다.

## 인증과 실행 권위

- 저장 서비스는 기존 전체 catalog 검증을 통합 생성 전에 수행하고, source/ACL/AEAD/head/scope/quarantine 검증을 이후에도 수행한다. cached verify는 fresh authenticated bytes로 전체 graph/모든 typed sidecar/inventory/receipt를 재구성하고 마지막 source checkpoint를 유지한다.
- tenant/subject/project/branch/document/read scope 변경을 거부한다. 반복 읽기를 atomic CAS 또는 보유 DB lock으로 주장하지 않는다. 새 ingest/head write/publication/issuer route는 없다.
- 원래 active inventory의 여섯 activation kind는 모두 거부한다. blocked/quarantined/review-required 상태와 native security `NotAssessed`를 보존한다.
- assembly profile/scope 각각 독립적으로 full-document context 승격을 거부한다. 완전한 importer/Gate가 닫힌 것으로 세지 않는다.
- Debug는 redacted이며 receipts에는 실제 본문/글꼴 이름/수식 값/개인정보/인증 값을 기록하지 않는다.

## 검증 증거와 사용자 경계

잠긴 역사적 실제36개는 원본 그대로 검사하며 파생 negative 사례는 메모리에서만 생성한다. 전체 graph inverse와 모든 typed branch equality를 확인한다. 현재 source regression과 원본 보존 audit는 별도 evidence에 기록한다. 실패 snapshot/기록과 오래된 frozen guards를 보존한다.

한글/COM/UI/native dispatcher/접근허용 실행은 금지된 상태를 유지한다. root `PLANS.md`는 사용자의 명시적 삭제 지시에 따라 재생성하지 않는다. 단계 보고서와 evidence만 동기화한다. P10 새 구현은 하지 않는다.
