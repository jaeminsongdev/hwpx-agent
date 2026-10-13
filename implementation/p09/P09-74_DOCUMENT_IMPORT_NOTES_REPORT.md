# P09-74 실제 원본의 각주·미주 본문 가져오기

- 상태: **actual source Note body/marker COMPONENT PASS / numbering·render·full importer·product·native·P09 Gate OPEN**.
- 정책: [P09-74_DOCUMENT_IMPORT_NOTES_POLICY.md](P09-74_DOCUMENT_IMPORT_NOTES_POLICY.md).
- 경계: P09 Gate OPEN/Goal ACTIVE/no P10. 접근허용 금지에 따라 Hangul/COM/UI/native dispatcher를 실행하지 않았다.

## 구현

기존 `ImportedDocumentStructure`의 실제 source-backed paragraph/run/text/table/opaque mapper를 각주·미주의 실제 subList에도 적용한다. 원래 opaque wrapper node/common/properties/resources와 원문 paragraph ControlRef는 유지하고 source_note_id 링크 및 실제 Note table만 추가한다. 관찰에는 실제 marker/body/source paragraph/wrapper anchors와 native_kind/실제로 존재하는 attributes를 연결한다. instId는 실제 원본의 양의 정수로 읽으며 native 전역·지속 identity로 주장하지 않는다. 같은 instId의 다른 위치는 다른 source-local logical ID를 갖는다. 없던 번호/flag/default를 생성하지 않는다.

section의 모든 실제 HP note marker를 최종 관찰 집합과 대조한다. 잘못된 wrapper/parent/namespace/속성/빈 body/number bound, 숨겨진 미표현 note 및 nested note는 거부한다. 기존 source/domain depth/node/note 한도를 유지한다. rich table body 및 table cell 내부 note를 실제 flow에 연결하고, Note body의 기존 forms/fields/meaning overlay 순회를 추가한다. 이 순회 추가는 임의 native form-in-note/catalog 지원의 새로운 한글 acceptance가 아니다.

실제 P26 저장 C01은 suffixChar를 literal 문자 대신 decimal WCHAR 토큰으로 기록한다. 새 **source-only** envelope는 bounded decimal WCHAR 또는 single BMP literal을 raw observed attribute 그대로 보존한다. rendered character 변환, 모호성 선택, 번호 계산은 하지 않는다. surrogate/out-of-u16/control/multi-character counterexamples를 거부한다. 기존 `note_projection`/plain-text/typed lowering parser는 그대로다. P26 native 실패를 성공으로 바꾸지 않았다.

원래 Reference table은 canonical ID 순서이며 source field 관찰은 source 순서다. P73 위치 zip은 여러 필드에서 이 순서가 다르면 실제 source를 거부할 수 있었다. actual reference ID lookup으로 연결하도록 국소 수정했다. Note 안의 24 DATE 필드는 순서 차이를 실제로 입증하고 Unsupported 의미를 유지하며, 12 서로 다른 HTTPS 필드는 자기 source reference의 URI에 정확히 연결된다. original parameters/namespace/parser/graph guards는 변경하지 않았다. URI 열기·승인·DATE/수식 평가·destination resolution을 수행하지 않았다.

## 실제 입력과 독립 소비

원본 P24 generated3와 원본 P26 saved3/reopened3, 총9개 whole HWPX를 immutable manifest/native receipt의 size/SHA로 읽었다. 각주6+미주6=12개 marker/body anchors를 실제 source에서 resolve했다. 기존 Source→body/forms→ranges→meanings 및 forms/final whole fresh verify를 수행했다.

- actual probe build: `12dc02`; executable5323264 bytes/SHA `b303c3509ffa9a66e19c05b0b7949e147b227d5fa847e86c29a5ac3d0a602b82`.
- 독립 프로세스 `c7af8d`/`2a4763`: 각각 exit0, 전체 metadata payload 동일; lanes generated3/saved3/reopened3, note12/foot6/end6.
- 원본 P26 receipt SHA `a03e6461d94010d7b1ccfbf9eecdb8e1d06389f3a690363e7b414d4cda9f2347`의 top/각 case `failed_semantic_non_green`/green0을 재확인했다.

기존 stored actual provider에서 동일9개 source의 direct/stored whole graph 및 note observations equality/fresh verify를 확인했다. original head 및 artifact.ingested2가 유지된다. 실제 Result ACL revoke, production AEAD fixture tamper, head advance는 fresh/cached 읽기를 거부한다. tenant/subject/project/branch/document scope 변경은 기존 모델의 cached verify 및 fresh bound field derivation 모두 Binding으로 거부한다. 독립적으로 권한 있는 provider의 신규 읽기는 기존 모델 재사용과 별개이며 이 테스트로 정식 source-document lineage를 증명하지 않는다.

새 note profile/scope 각각은 다른 partial marker 없이도 full product context를 거부한다. 기존 partial/security guards는 그대로다. metadata/revision/blob/scanner/keys/sealed baseline은 **in-memory fixtures**, 새 PG/실제 scanner·policy issuer/native/product acceptance가 아니다. 정상 READ audit 외 ingest/CAS/seal/publication은 없다. 두 head reads는 atomic lock/CAS/idempotency가 아니다.

## 검증

| 검증 | 실제 결과 |
|---|---|
| 새 package note tests | bb6073:11 PASS; 원본 속성/anchors/wrapper/no default/identity/hidden·nested 거부/whole fresh/24 DATE/12 HTTPS/no-note/rich table/WCHAR/privacy |
| 새 stored service tests | d2b248:5 PASS/50 filtered, 타깃 실행; actual9 equality/fresh/ACL/AEAD/head/scope5/partial marker |
| current CLI+whole package | 3a2b3d→bb2268→8e3ca2:100 targets/CLI117+package884=1001 PASS/failed0/ignored0/filtered0 |
| original domain public | ca1bee:form_control8+form_input_public15=23 PASS |
| domain document graph | b8cc0a:9 PASS; named total1033 |
| strict lib/tests | d7e3a7→0481ee:four crates `-D warnings` PASS |
| strict actual example | d04593:`-D warnings` PASS |
| recursive format check | a5e51b:13 entry sources와 하위 modules PASS |
| source preservation | 54efd3와 원장 갱신 후8b3e9a:prior2040/original1551/51047460 bytes/native75 exact;28 original graph origin mappings/Hwp0 |
| eight code inverses | 222bbe:이번 note addition/traversal/source-order correction 제거 시 eight whole pre-change files raw-exact |

원본 ZipWriter seek-limit negative test diagnostics는 예상된 테스트 출력으로 보존하고 숨기지 않았다. 지정 Rust 검증은 whole workspace/Python/whole original qualification CLI replay/current admission/native tests를 대체하지 않는다.

## 실패·보존과 다음 경계

`source-archive/p09-74-pre-source-notes/`에 기존 code8+PLANS 원본120 lines를 whole-copy/SHA로 보존했다. 새 compile/lint/literal-only actual saved failure와 inverse-reader newline/syntax 실패, 새 scope5 oracle의 잘못된 독립 read 기대를 별도로 보존했다. 총23 archive files=pre-change9+failed/intermediate14다. 실패 원장의 원래 exit/failure 상태를 유지한다. 새 scope test만 원래 fresh bound/cached 계약에 맞췄고 production authorization/기존 assertions/guards/skips는 바꾸지 않았다.

P73 source423 중414개는 unchanged다. 이번 국소 추가·수정 외 8개 코드의 전체 역복원이 exact이며 P73 영수증/원본 입력, original1551-file graph/native75, 사용자 dirty worktree/원본 HWPX/비밀정보/기존 DB/dependencies/Cargo.lock을 보존했다. stage/commit/push/삭제·이동/보호 설정·trust 변조/COM/한글창/접근허용은 하지 않았다. XML/본문/URI/parameters/전체 로그는 보고서·영수증에 출력하지 않는다.

다음 실제 개발은 다른 field/reference/comment/catalog/security 의미 및 평가·정책·승인, 정식 committed Source/Result/IR input lineage/issuer/ExecutionManifest/publication/idempotency/IR lifecycle/concurrency/crash/recovery다. P73 HTTPS/formula AST 및 P71 actual PG/file form evidence는 historical scope로 그대로 보존한다. note source 성공으로 full importer/native 번호·body/style/render/direct differential을 승격하지 않는다.

P62 16fde8 root cause는 UNRESOLVED이며 current admission은 INPUT_CHANGED_RE_ADMISSION_REQUIRED다. full34 NOT_RUN/0green/P09 Gate OPEN/Goal ACTIVE/no P10/prompts를 유지한다.

- [actual consumer](evidence/p09-74-document-import-notes.actual-consumer.v1.json)
- [Rust regression](evidence/p09-74-document-import-notes.rust-regression.v1.json)
- [실패 원장](evidence/p09-74-document-import-notes.initial-failures.v1.json)
- [source progress](evidence/p09-74-document-import-notes.source-progress.v1.json)
- [final audit](evidence/p09-74-document-import-notes.final-audit.v1.json)
