# P09-93 댓글 전체 호출자 IR 변경 준비 결과

제품 라이브러리에 기존 CommentBuilder의 다섯 작업을 실제 full-IR view 변경과 원래
OperationPlanCompiler에 연결했다. 이 결과는 호출자 제공 완전한 typed IR의 준비 경로이며,
actual source-backed comment import, HWPX lowering 또는 native/제품 Gate 완료가 아니다.

## 구현과 검증

REF-026 숨은 설명, REF-027 삽입, REF-028 스타일, REF-029 표시/숨김, REF-030 해결 상태를
모두 원래 typed request/plan/build로 처리한다. root ordered state와 section/style/review view의
전체 일치를 확인하고 실제 graph node/section 경로로 compile한다. 해당 view만 변경하며
나머지 문서·notes·settings·references·resources·opaque 값은 보존한다. 원래 getter·plan·검사와
full-IR admission을 변경하지 않았다. 기존 lib.rs에는 공개 module 선언 1줄만 추가했다.

신규8 + 기존 form/full-document18 + 원래 comment model10 = Rust36 PASS.
신규 검사에서 다섯 positive 준비와 전체 문서 보존, stale state/flow/package/revision/graph,
missing/extra/conflicting view, 실제 다른 section 대상, duplicate/unknown/over-limit JSON,
보호/서명/암호화 및 partial importer marker 거부, P11 delete 거부와 route denial을 확인했다.
작성자나 댓글 없는 합법적인 style/hidden 준비도 검사하되 실제 작성자를 생성하지 않았다.
strict clippy와 새2file format 및 git diff --check PASS.

현재 component/source conformance 원래15개도 PASS이며 green0/P09 OPEN을 유지한다.
그 source 검사의 qualifier는 원래 component 범위이며 이번 새 제품 module의 전체 acceptance가 아니다.
baseline 회귀는 별도 target/p09-93-regression에서 빌드하여 과거 실행 파일을 보존했다.
section/node 및 ID/JSON index를 한 번 구성하여 per-entry whole graph clone과 반복 catalog 검색을 제거했다.
구조적 개선이며 성능 acceptance나 benchmark PASS를 주장하지 않는다.

## 발견한 실패와 수정

초기 컴파일의 local function shadow/moved array 오류를 수정하고 초기 전체 source를 보관했다.
첫6개 검사 중2개가 실패했다. 원래 Graph가 review catalog를 ID별 정렬하므로 새 댓글 삽입 순서를
그 catalog에 강제하면 잘못 거부했고, negative 사례 하나는 이미 동일한 target을 다시 썼다.
원래 catalog 의미는 유지하고 표시 순서는 정확한 root component state로 결속했다.
negative는 actual component 순서/다른 section target 변조를 검사하도록 고쳤고, catalog 순서만
바꾼 동일 문서가 합법적으로 canonicalize되는 사례를 추가했다. 실패 당시 module/test 전체도 보관했다.
엄격 검사에서 too_many_lines/needless_borrow/fixture literal-pattern 지적을 수정했다.
prod lint나 original guard를 약화하지 않았다.

## 보존과 남은 실제 제품 경로

P92 지문1109개는 lib.rs 1개만 변경되었고 그 정확한 전체 preimage가 보관되어 있다.
P92 소스774개 중773개가 그대로이며 lib.rs 전체 byte inverse를 확인했다. 실제 native 증거와
원래 source/qualifier/tests/failed evidence를 유지했다. PLANS 부재, 한글/UI/접근 허용/SQL 실행 없음.
P59~P92 지문 선언14,633개와 최초 소스1,551개/51,047,460 bytes/native 원본75개도
현재 파일 또는 정확한 전체 보관본에서 확인했다. 과거 qualification 전부를 재실행한 것은 아니다.

현재 source-native 작성자/시간/visibility/resolution/body binding은 여전히 unavailable/unverified다.
prepared route는 항상 거부되며 caller IR을 인증된 source/native 상태나 publication 권한으로
바꾸지 않는다. typed state에 포함된 작성자/시간은 explicit synthetic caller fixtures만 검사했다.
native run/inline 좌표 의미도 검증하지 않았다. source capture와 실제 header/body/MEMO lowering,
authenticated persistence/provider, trusted issuer/atomic execution/publication, 한글 저장·재열기/
렌더링/차이 비교 및 P09의 나머지 기능 검증은 남는다. 실제 node가 없는 style 목표는 Anchor 거부다.

다음은 원래 저장소 artifact/revision 읽기 경로와 이 prepared comment binding을 결속하고,
native/source가 미확인인 상태는 계속 거부하는 것이다. 이후 actual comment HWPX lowering은
실제 source/metadata 증거가 있는 경우에만 연결한다. P09 Gate 전 P10 구현을 시작하지 않는다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62 UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; full native34 NOT_RUN.
full_comment_product_acceptance=false, p09_complete=false, product_complete=false,
P10_new_implementation=false, goal_status=active.

정책: P09-93_COMMENT_PRODUCT_POLICY.md. 실행·실패·보존·전체 지문: evidence/p09-93-comment-product.*.json.
