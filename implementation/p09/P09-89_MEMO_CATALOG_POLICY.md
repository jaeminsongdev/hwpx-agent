# P09-89 기존 카탈로그의 메모 모양·절 참조 연결 정책

원래 P09-04 Comments의 메모 모양 제품 경로에 필요한 source binding을 기존 ImportedDocumentCatalog에 추가한다. 이 작업은 메모 모양 변경 기능, full CommentState, native semantic acceptance를 대체하지 않는다.

## 기존 경로 재사용

- original catalog의 ImportedCatalogKind에 MemoProperty를 추가한다. 같은 definitions/index/style graph에 실제 header refList/memoProperties/memoPr를 넣는다. 별도 문서 importer나 style graph를 만들지 않는다.
- 원래 immutable source와 children/element/attribute/number/anchor resolver를 재사용한다. itemCnt/duplicate/native ID/bounded style count를 검사하고 원래 graph validator를 실행한다.
- native MemoShapeType와 unsigned converter를 근거로 width는 실제 unsigned integer, lineWidth는 원래 enum ordinal0..15만 읽는다. 원래 lineType18개/memoType4개 및 color none 또는 six-hex 형태를 검사한다. source token/extra namespace attributes는 그대로 보관한다. C++ constructor defaults를 적용하지 않는다.
- memoPr child 또는 비공백 본문은 이 closed source subset에서 거부한다. native style mutation/렌더 의미를 검증한 것은 아니다.
- original source spine과 graph sections를 순서/ID로 결속하고 secPr의 명시적 memoShapeIDRef를 읽는다. duplicate secPr, malformed reference를 거부한다.
- NoExplicitReference, UnresolvedMissingDefinition, Resolved는 구별한다. header에 정의가 없는 zero reference도 실제 unresolved로 남기며 기본 Style을 만들지 않는다.
- 실제 resolved 관계만 source_memo_shape_catalog로 원래 section graph에 연결한다. source section anchor/attributes/reference/binding sidecar를 whole fresh catalog verify에 포함한다.
- 원래 assembly getter로 같은 memo uses를 제공한다. 실제 MEMO body는 source marker가 속한 section ID만 참조하고, hidden explanation에 메모 스타일을 추정하지 않는다. section 속성을 댓글마다 복제하지 않는다.
- original stored catalog/assembly service 소스는 바꾸지 않는다. 원래 before-after ACL/quarantine/AEAD/head/scope 및 full fresh reconstruction을 새 branch도 사용한다. cached getter는 execution authority가 아니다.

## 보존과 판정

원래 font/security/settings/formula/review assembly, original combine/receipt guards/exact oracle은 유지한다. actual36에 memoPr0/explicit memo refs44가 있다는 사실을 현재 reader로 검증하고 기존 그래프를 보존한다. positive memo definitions는 원래 builder의 in-memory synthetic source만 사용한다.

334 current Rust tests 및 strict5crate lint/신규5file nonrecursive format을 검증한다. 실패 source4개와 original parent4개의 whole preimages를 보관한다. 원래 comment/conformance 실패는 갱신해서 숨기지 않는다.

이 결과는 paragraph/run 및 section source 관계이며 per-comment native shape/state acceptance, author/time/visibility/resolution, original comment mutation/lowering, trusted issuer, atomic execution/publication, native save/reopen/render의 증거가 아니다. P11 comment_delete 소유권을 바꾸지 않는다. P09 Gate/A12/A13 OPEN, P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN 유지. PLANS.md는 사용자 삭제 상태를 유지한다.
