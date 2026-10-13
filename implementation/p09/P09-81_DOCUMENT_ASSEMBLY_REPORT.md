# P09-81 동일 원본 문서 모델·글꼴·보안·설정·수식 통합

## 결과와 완료 경계

P09의 실제 문서 가져오기 경로에서 분리되었던 font graph와 security → section-settings graph를 하나의 source-bound 모델로 연결했다. 원래 field meanings 기반 exact formula 결과와 cell source bindings도 같은 객체에 보존한다. 저장 서비스에서 `StoredImportedCatalog::import_document_assembly`로 같은 경로를 사용할 수 있다.

이 단계는 실제 통합 코드의 추가이지 A12 전체 importer 또는 제품/P09 Gate 완료가 아니다. partial profile/scope와 full-context 승격 거부를 유지한다. 미지원 field meanings, comments 양성 의미 증거, 전체 settings/native security/font availability, authoritative policy/scanner/issuer/manifest, 실제 persisted lineage/commit/publication/lifecycle 및 native46 acceptance는 여전히 남아 있다. P10 새 구현은 하지 않았다.

## 구현과 보존

- 새 source assembly/저장 서비스 경로와 independent whole-output oracle, actual36 probe, package·service tests를 추가했다. 새 코드7개와 원래 parent4개에 제한된다.
- 같은 immutable catalog에서 각 원래 importer를 실행한다. 서로 다른 원본에서 온 caller graph/receipt를 합치는 API는 없다.
- font branch의 전체 non-style/non-marker 영역이 원래 catalog와 같고, security/settings branch의 styles가 원래 catalog와 같아야 한다. conflict나 metadata key 중복을 last-writer-wins로 덮어쓰지 않는다.
- font styles 및 marker만 settings/security graph에 연결한다. 나머지 본문·참조·notes/bookmarks·resources·opaque bag·security·settings 전체는 그대로 유지한다. 원래 component의 typed sidecars와 receipts를 전부 유지한다.
- 수식 결과는 별도 typed values/cell anchors이고 graph에는 digest만 연결한다. native cache/body/AST를 덮어쓰지 않는다. noncanonical/nonnumeric/missing dependency는 원래 evaluator 오류 그대로 거부한다.
- fresh 검증은 원래 전체 source/catalog와 모든 통합 graph/sidecar/inventory/receipt를 재구성한다. 저장 서비스의 원래 ACL/AEAD/head/quarantine/five-scope/read-scope 검사는 전후 유지한다. atomic CAS/issuer/persistence/publication 권위로 세지 않는다.
- activation6종은 원래 inventory에서 모두 거부한다. assembly profile와 scope 각각만 남겨도 full-document context 승격이 거부된다.

## 실제 source 검증

기존 P77에 잠긴 실제36개를 그대로 읽었다. 이전 실제26개의 prefix identity도 그대로 확인했다. 새 파생 numeric/font/page/formula/invalid reader 사례는 메모리에서만 생성했다.

두 개의 독립 probe 실행 결과가 동일했다. whole graph inverses36, font definitions504, character-language font links1771, section settings44, native-form security bindings50, formula values16, formula cell source bindings128이다. 새 source 소비 결과는 `evidence/p09-81-document-assembly.actual-consumer.v1.json`에 저장했다. 이는 역사적 입력 소비 검증이며 새 native save/reopen 또는 render PASS가 아니다.

Focused service tests4 및 새 package integration tests4가 각각 통과했다. private cache/conflict tests2도 통과했다. 이10개는 이후 전체 회귀 결과에 포함되며 추가로 이중 합산하지 않는다. 현재5개 관련 crate의 libs/tests/examples strict lint가 통과했다. 신규7개 파일만 formatting 검사했고 parent4개 전체 inverse는 정확히 원래 텍스트로 되돌아간다.

현재 hwpx-package + hwpx-agent-cli 전체 오프라인 locked 회귀가 exit0으로 끝났다. hwpx-package934/95targets + hwpx-agent-cli151/12targets =1085/107targets이며 failed/ignored/filtered는0이다. 신규10개는 이 합계에 포함돼 있다. 단일 quiet 전체 실행의 모든 target별 결과를 보존했고 출력 누락이나 재실행·필터 제외는 없다. 마지막 결과와 모든 target별 합계는 `evidence/p09-81-document-assembly.source-regression.v1.json`에 기록했다. 이것은 관련 두 package의 libs/tests 회귀이며 domain-ir 전체 test 재실행, native 검증 또는 모든 제품 Gate PASS가 아니다.

## 원본과 실패 기록

P59–P80의 source/archive/predecessor pin entries5688, original graph files1551/51047460 bytes, native originals75를 각각 원래 해시로 확인했다. 이전 P80 source522 중518개는 현재 그대로이고 변경 parent4개는 `source-archive/p09-81-pre-document-assembly`에 전체 원문과 해시를 보존했다. whole-text inverses4도 일치했다. 오래된 complete-source qualification CLI/Gate 자체를 재실행하거나 새 PASS로 승격한 것은 아니다.

초기 dev-dependency hex 호출, 새 clone/semicolon lint, 원래 helper에 맞지 않은 파생 formula input, LF 원문에 CRLF를 가정한 parent 재적용, read-only preservation selector의 P79/P80 선택 오류를 수정하고 실패 기록/snapshot을 보존했다. focused name filter가 integration target을0개 실행한 결과는 integration PASS로 세지 않고, 이후 unfiltered 새 target4개를 통과시켰다. 원래 readers/검사/threshold/fixtures/frozen receipts를 약화하지 않았다.

## 현재 제품 경계와 다음 작업

현재 admission은 `INPUT_CHANGED_RE_ADMISSION_REQUIRED`, full native34 queue는 `NOT_RUN/0 green`, P26 semantic failure와 P62 unresolved 상태는 그대로다. 이 단계는 A12에서 모델 branch 누락을 줄였지만 A12 전체 완료나 작업46개 완료로 계산하지 않는다. 다음에는 실제 importer의 나머지 의미/설정 요구와 authority·lineage 연결을 계속 다뤄야 한다.

사용자 지시대로 root `PLANS.md`는 부재이고 재생성하지 않았다. 원래 복구 archive는 그대로다. 한글/COM/UI/native dispatcher/접근허용은 실행하지 않았다. stage/commit/push, 시스템·trust 설정 변경 및 원본 삭제는 하지 않았다. 전체 목표는 active이고 P09 Gate는 OPEN이다.
