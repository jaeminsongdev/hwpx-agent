# P09-87 원본 댓글 본문 읽기 결과

## 결과

실제 HWPX 원본의 hiddenComment/subList와 MEMO field/subList 본문을 읽는 경로를 추가하고 기존 authenticated artifact reader에 연결했다. 별도 importer나 댓글 의미 모델을 만들지 않고 기존 source/field collector/body Mapper/domain validator를 재사용했다. 관측 본문은 main text나 complete CommentState로 승격하지 않는다.

신규 Rust5개, parent6개의 제한된 변경이다. source-preserving MEMO envelope, 실제 parameter anchor 선택, module declarations 및 새 partial profile/scope 거부만 추가했다. parent6개의 raw whole preimage를 보관했고 새 변경 제거 inverse 및 원래 parameters/settings 검사 재사용을 확인했다. 원본 HWPX는 재작성하지 않았다.

## 현재 소스 검증

최종 소스에서 Rust274 tests가 통과했다. 신규20은 아래 집계에 포함되므로 추가로 합산하지 않는다.

- package10 targets119: text_flow12, source10, structure14, forms10, fields12, field_semantics11, notes11, bookmarks10, form_policies14, review15.
- product4 targets144: stored_provider117, stored_product_request8, form_value_operation18, policy_bound_form_import1. 신규 stored-review5는117에 포함된다.
- 원래 domain comment-model public10/private plan tamper1:11. combined command가 뒤 Python validator에서 실패했지만 두 Rust 실행은 각각0/PASS다.

새 검사는 실제 marker/body/end/parameter anchors, original paired fields, hidden direct/wrapped controls, body/cache 분리, 실제 속성·문단/table/cell/Unicode/run/unknown XML 구조, 별도 문단의 동일 native ID와 distinct source identity, whole-source drift, budgets, malformed/nested/unrepresented 구조 거부 및 redacted Debug를 확인했다. 없는 본문이나 author/time/state를 default로 만들지 않았다.

stored path에서는 원래 encrypted ArtifactService read와 whole direct reader graph/관측/receipt가 일치했다. ACL 철회, AEAD 변조, head 변경, provider scope5 대체를 거부하고, malformed body 및 새 partial marker 각각의 full-document 거부를 확인했다. ingest 수2 fixture baseline과 head가 유지돼 새 publication은 없었다. fixture actor/scanner/metadata를 실제 외부 인증·issuer 증거로 세지 않는다.

5 crate lib/tests/examples strict lint, 신규 Rust5개 개별 format, diff check가 통과했다. 기존 parameters 검사 본문과 settings denial은 그대로 재사용했다. subtree 검사 범위를 줄였지만 전체 제품 성능 합격은 주장하지 않는다.

## 실제 원본과 공식 구조의 한계

고정된36 actual input을 fresh 재검증해 원본·기존 그래프를 보존했다. counts-only 진단에서 memoShapeIDRef44, memo style records0, MEMO ranges0, hiddenComment0이었다. 따라서 이 corpus는 기존 원본 회귀 증거이며 신규 댓글 본문·author/time의 positive native acceptance가 아니다.

한컴 고정 commit1453388472c703a4b299a0834f425cdac16644b9의 [hiddenComment](https://github.com/hancom-io/hwpx-owpml-model/blob/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/hiddenComment.cpp)와 [fieldBegin](https://github.com/hancom-io/hwpx-owpml-model/blob/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/fieldBegin.cpp) local raw/UTF8 CRLF-to-LF 지문을 원래 source qualification과 대조했다. BOM은 보존해 해시했다. subList 구조는 확인되지만 author/time/표시/해결 의미 연결은 여전히 미검증이다.

MEMO metaTag 및 body 안의 중첩 field/review/note/bookmark는 거부하고 미지원으로 남긴다. parameters-only/empty MEMO를 본문 있는 댓글로 세지 않으며 원래 MEMO meaning Unsupported도 유지한다. full comment insert/style/show/resolve/delete를 완료했다고 말하지 않는다.

## 실패 및 기존 비녹색 상태

초기 reader compile의 없는 hex dependency/attribute getter 및 lifetime 오류, 새 test의 없는 Properties::get, 신규 importer 길이198/100, 기존 bind에 새 guard를 넣은 뒤108/100와101/100 lint 실패를 별도 보존했다. 신규 부분을 수정·분리하고 원래 settings 검사를 재사용했으며 lint 경고 허용이나 budget/guard 약화는 하지 않았다. 실패 소스5개를 whole archive로 보관했다.

기존 P09 conformance validator는 matrix_drift로 실패했다. 원래 comment validator는 implementation_digest로 실패했고 Python5 tests 중4 PASS/1 FAIL이다. 실제 canonical 비교에서 comment_model.rs와 그 tests는 원래 지문 그대로이며 lib.rs만 과거 지문과 다르다. lib.rs는 P86 current source와도 동일해서 이번 변경이 만든 drift가 아니다. 오래된 source qualification/matrix를 수정해서 PASS로 만들지 않았다.

P59~P86 declared pins9681, original source1551 files/51047460 bytes, native originals75를 현재 raw bytes 또는 whole archives로 확인했다. P86 source603 중597은 동일하고6 parent는 exact preimages로 보존됐다. 모든 과거 qualification을 재실행한 것은 아니다. P86 policy-product/P85 registration/과거 assembly executable3개도 그대로 보존했고 P87 PostgreSQL 재실행 증거로 세지 않는다.

## 남은 작업과 Gate

댓글 author/time·스타일·표시·해결의 실제 연결과 저장·재열기 검증, 나머지 원본 의미 및 full-document admission/issuer/atomic execution/publication, source re-admission, native 의미·render/differential, P09 Gate가 남아 있다. 기존 P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN을 유지한다.

한글/COM/UI/접근 허용, 운영·trust DB, stage/commit/push는 실행하지 않았다. root PLANS.md 부재 유지. P09 Gate/A12/A13 OPEN, 목표 active, P10 새 구현 없음.
