# P09-88 원래 문서 조립 경로의 review body 연결 정책

P09-87의 실제 source reader를 기존 ImportedDocumentAssembly에 연결한다. 별도 문서 importer, 별도 field stack, 호출자가 공급한 그래프나 허위 네이티브 metadata를 도입하지 않는다.

## 구현 범위

- 원래 immutable catalog → fonts/security/settings/formula 조립을 그대로 수행한 뒤 review branch를 추가한다. 원래 combine 함수와 기존 receipt-chain guard는 변경하지 않는다.
- 이미 catalog에 묶인 원래 ImportedDocumentFields를 crate-private import_bound_fields로 재사용한다. document/source/provenance/form-graph 동일성을 먼저 검증한다. 원래 public review import도 같은 helper를 사용한다.
- AssembledReviewBody는 원래 observation 전체와 source body의 catalog-bound Flow 및 paragraph/run catalog uses를 함께 보관한다. 원래 catalog attach binder와 원래 graph validator만 사용한다.
- source hidden/MEMO 본문을 일반 본문·표시용 cache로 합치지 않는다. body=None도 그대로 유지한다. source attributes/anchors/native-unverified 표시를 보존한다.
- named/paragraph/character style references는 원래 header catalog로 해석한다. 없는 style reference와 malformed body는 전체 assembly 실패이며 opaque 성공으로 바꾸지 않는다. 여기서 연결하는 것은 본문 paragraph/run style이고 네이티브 MEMO-box style acceptance가 아니다.
- source receipt/원래 field graph/review graph/raw observations/typed catalog sidecar digest를 모두 결속한다. 전체 AssemblyState의 fresh reconstruction으로 graph/sidecar/receipt 변조를 거부한다.
- body bytes는 기존 8MiB bounded streaming serialization으로 항목별 계산하고 배열 punctuation까지 checked aggregate budget을 적용한다. 전체 prefix를 매번 재직렬화하지 않는다. 최종 전체 digest와 fresh verify는 별도로 실행한다.
- body가 없는 기존 실제 문서36개의 반환 graph는 이전 exact oracle 그대로 유지한다. validation용으로 typed body를 붙인 disposable graph는 반환·저장·publish하지 않는다.
- 기존 stored catalog→assembly 서비스는 수정하지 않는다. 새 branch도 원래 ACL/quarantine/AEAD/head/scope before-after fresh read와 whole assembly verify를 자동으로 통과해야 한다. cached getter 자체는 현재 실행 권한이 아니다.

## 제품 권한 및 Gate

현재는 partial import이다. author/time/visibility/resolution/native MEMO-box style, full CommentState, full-document operation admission, issuer, atomic lease, native edit/save/reopen/render 및 publish 권한을 제공하지 않는다. MEMO semantic meaning은 여전히 Unsupported이며 기존 partial-marker denial/activation denial을 약화하지 않는다. comment_delete 소유권은 원래 P11이다.

P09 Gate/A12/A13 OPEN, P26 failed_semantic_non_green, P62 UNRESOLVED, native INPUT_CHANGED_RE_ADMISSION_REQUIRED, full native34 NOT_RUN을 유지한다. P10 새 구현은 금지한다.

## 검증과 보존

원래 builder의 in-memory synthetic positive body/style fixtures를 실제 reader와 원래 authenticated service에 넣는다. 실제 캡처 원본은 고치지 않는다. 현재 source/package/private/service/domain regression289개와 strict5crate lint 및 신규5file nonrecursive format을 수행한다. 원래 comment/conformance validator 실패는 별도로 기록한다.

변경 parent3개의 whole raw preimages와 초기 lint source3개를 보존한다. 기존 원본1551/native75 및 P59~P87 declared pin10427을 현재 파일 또는 whole archive로 검증한다. PLANS.md는 사용자의 명시적 삭제 상태로 유지한다.
