# P09-73 실제 원본의 HTTPS 목적지·표 수식 AST 가져오기

- 상태: **source-derived HTTPS target/table formula AST COMPONENT PASS / evaluation·approval·full importer·input lineage·product·native·P09 Gate OPEN**.
- 정책: [P09-73_DOCUMENT_IMPORT_FIELD_SEMANTICS_POLICY.md](P09-73_DOCUMENT_IMPORT_FIELD_SEMANTICS_POLICY.md).
- P72의 immutable actual source/body/forms/ranges에서 실제 HTTPS target과 표 수식 AST/owner/dimensions를 가져온다. caller URI/formula/graph를 입력으로 받지 않으며, label/cache로 목적지나 계산 결과를 추측하지 않는다.

## 실제 구현과 남은 의미

`document_import/fields/semantics.rs`와 실제 저장 서비스의 `field_ranges/semantics.rs`를 연결했다. typed observations와 원래 FieldNode/reference properties의 source_derived_meaning을 추가하며, 원래 header/end/parameters/anchors/parent/inline positions/common/body/table/grid/resources/opaque/security는 그대로다. 추가 의미와 두 metadata markers를 제거하면 원래 전체 field graph와 같다는 검사를 실행했다.

HTTPS source-only bridge는 기존 hyperlink validate_parameters의 정확한 six-parameter profile을 재사용한다. 원본 expanded namespace와 native escaped-colon Command/Path/Prop/Category/TargetType/DocOpenType를 확인하고 기존 domain target shape 검사를 적용한다. 목적지는 데이터일 뿐 external approval, approved target-node identity, network/URL 열기 또는 signed execution 권위를 만들지 않는다. Reference.target_node_id는 여전히 None이며, HTTPS라는 사실을 내부 문서 node가 해석됐다는 뜻으로 바꾸지 않는다.

표 수식은 실제 fieldBegin에서 nearest source table/direct owning cell/grid를 찾는다. 원래 field envelope, Command/Formula/ResultFormat/LastResult, visible cache parity, canonical grammar와 owner/dimensions 검사를 그대로 사용한다. exact SUM(LEFT)은 기존 left-prefix 규칙을, 나머지는 기존 canonical AST 규칙을 적용한다. readback의 unowned digest나 전체 table formula count를 꾸며 만들지 않고 실제 dimensions/FormulaCell만 반환한다. 캐시는 Unverified 또는 지원 profile의 Absent이며, 계산·검산·native 재계산은 하지 않았다.

나머지13 field kinds는 Unsupported로 명시해 원본 range/parameters와 함께 남긴다. supported HTTPS/FORMULA가 원래 profile에 맞지 않으면 error로 거부하며 느슨한 parser/opaque 성공으로 우회하지 않는다. DATE/상호참조/책갈피 등의 의미와 notes/catalog/security 전체 importer는 아직 미완료다.

recognized field별 source XML element work를 누적해 hard8,000,000을 넘으면 전체 Limit으로 거부한다. source XML bytes는 crate-private immutable callback으로만 읽고 공개 raw XML action/writable buffer를 추가하지 않았다. 기존 source/parser/domain limits를 유지했다.

## 실행 증거

| 검사 | 실제 결과와 범위 |
|---|---|
| actual17 | historical captured HTTPS1 + P06 generated/saved table formula16; source-derived HTTPS target1/FormulaCell AST16/unsupported0 |
| 독립 current-exe processes | 34988c/9562db, exit0; actual17의 source/form/range/meaning whole fresh reconstruction 및 전체 metadata receipts exact |
| current CLI/package lib/tests | 023619/c211d1/264c2f/8588cb/7c2036, terminal exit0;99 targets, CLI112+package873=985 PASS, failed/ignored/filtered0 |
| original domain public | a39ecd, form_control8+form_input_public15=23 PASS; named total1008 |
| 신규 검사 | package11 + stored-service6 =17; 기존991 +17 =1008, 신규1008 기능이 아님 |
| strict lint | four-crate lib/tests7a528f 및 actual example9789a4 `-D warnings` PASS; allow/skip 없음 |
| format | 1f8c1a, recursive rustfmt check PASS |
| whole original inverses | 10d2d0 및 final audit, eight code files의 additive bridges/declarations/partial guard/test visibility만 제거하면 whole pre-change bytes/SHA exact |
| 이전 증거·원본 보존 | cc73c9 및 final audit, prior1588 pins/original1551 files·51,047,460 bytes/27 original-graph origin mappings/native75 exact |

actual probe executable SHA: `f0f32a2bdc8f44680d6e67492e74ce21fcf5d20dd836f248f8f5c1ebd81c653d`. 최초 c44cea actual run은 추가 관찰이며, 최종 두 독립 process proof는 위34988c/9562db다.

synthetic HTTPS entities/tuple mismatch/HTTP·script URI/foreign namespace/unsupported DATE/nested parent/whole graph inverse/fresh drift/finite work denial와 actual corpus17을 구분했다. derived synthetic bad-format table은 원본 ZIP을 메모리에서 별도 재작성해 검사한 것이며 원본 파일은 그대로다. LastResult를 계산값으로 받아들이지 않고 기존 format guard가 거부했다. original ZIP writer limit negative-test diagnostics는 그대로 보존했으며 quiet regression의 terminal result와 counts는 모두 PASS다.

## 저장 서비스와 권위 경계

stored import는 원래 ranges.verify를 먼저 수행하고, cached verify는 원래 서비스 검사 및 fresh authenticated source read로 whole source/body/forms/ranges/meanings를 재구성한다. original scope5/head/ACL/scanner/quarantine/AEAD/digest checks 및 마지막 head 확인을 유지했다. 두 checked reads는 atomic lock/CAS/idempotency가 아니다.

실제 captured Result bytes의 stored/direct whole graph·observations·receipt equality, fresh verify, unchanged head/ingest count와 receipt/debug privacy가 통과했다. Result ACL revoke, 실제 production AES-GCM fixture tamper, head advance, tenant/subject/project/branch/document substitutions 모두 fresh/cached 의미 접근을 거부했다. 정상 READ audit는 그대로 추가된다. 새 semantic profile/scope 각각은 predecessor markers가 없어도 full product context를 독립적으로 Projection으로 거부한다.

이번 metadata/revision/blob/scanner/keys/sealed baseline은 in-memory fixtures이며 새 PG field acceptance가 아니다. P71 actual PostgreSQL/file form-import 증거는 해당 historical scope 그대로 보존한다. artifact ingest/CAS/seal/publication, external approval/issuer/ExecutionManifest를 실행하지 않았다.

## 실패와 보존

nine whole pre-change originals(PLANS 포함)는 `source-archive/p09-73-pre-field-semantics/`에 보존했다. eight inverse-checked code files와 PLANS의 whole120 lines다. 기존 parser/service/SQL/tests/guards/assertions/expected values/locks/production dependencies를 변경하거나 skip하지 않았다. new child exports/helper access 및 additive partial guard/test-only fixture visibility만 연결했다.

initial compile의 error conversion/Boolean variant/explicit bounded constructors, test compile의 없는 graph getter, synthetic HTTPS Command 형식, 잘못된 new module relative path, test expect/let-chain lint, duplicate fixture loading과 intermediate command construction을 보존했다. eight failure/intermediate source files와 [실패 원장](evidence/p09-73-document-import-field-semantics.initial-failures.v1.json)에 당시 오류·수정 범위를 남겼다. original parameters validator를 느슨하게 바꿔 fixture를 통과시키지 않았다.

원본 actual HWPX/private/native evidence/user dirty worktree/기존 DB는 삭제·이동·수정하지 않았다. DB/container/package dependency를 만들거나 설치하지 않았으며 Hangul/COM/UI/native dispatcher/접근허용창/trust·security·config mutation/stage·commit·push도 실행하지 않았다. URL/parameters/formula AST/cache/graph/XML/비밀정보·전체 로그는 보고서와 receipts에 출력하지 않는다.

## 기록과 다음 경계

- [actual consumer](evidence/p09-73-document-import-field-semantics.actual-consumer.v1.json)
- [Rust regression](evidence/p09-73-document-import-field-semantics.rust-regression.v1.json)
- [source progress](evidence/p09-73-document-import-field-semantics.source-progress.v1.json)
- [final audit](evidence/p09-73-document-import-field-semantics.final-audit.v1.json)

다음은 다른 field/reference/note/catalog/security 의미, 실제 계산 및 정책·외부 승인 계약, actual committed Source/Result/IR·previous-result input lineage, 정식 issuer/ExecutionManifest/publication/idempotency/IR lifecycle/concurrency/crash/recovery다. full current workspace/Python/whole original qualification CLI replay/current admission은 이번 지정 Rust/component 증거와 별개다.

P62 16fde8 원인은 UNRESOLVED다. native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green/P09 Gate OPEN/Goal ACTIVE/no P10를 유지한다. 접근허용 금지 상태에서는 native 실행을 하지 않는다.
