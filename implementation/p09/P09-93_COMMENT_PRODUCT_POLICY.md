# P09-93 댓글 전체 호출자 IR 변경 준비 정책

원래 CommentBuilder/CommentRequest와 OperationPlanCompiler, 기존 full-IR admission을 사용하여
REF-026~030의 다섯 작업을 제품 라이브러리의 준비 경로에 연결한다. CommentBuilder를 교체하거나
별도 native importer를 만들지 않는다. caller-qualified IR와 실제 HWPX/native 증거는 분리한다.

## 완전한 상태와 문서 결속

완전한 ordered sections/authors/styles/hidden explanations/comments 및 모든 payload/protection/
opaque 지문을 원래 모델로 검증한다. 문서의 root complete state와 모든 section/style/review
view가 정확히 일치해야 한다. 다른 review/style entry는 보존하고 marked extra/missing/conflicting
view를 거부한다. 원래 Graph의 review catalog는 ID 순으로 canonicalize되며 표시 순서는 root
complete component state에 결속한다. catalog 순서를 표시 순서로 재정의하지 않는다.

실제 graph의 section/node를 대상으로 원래 compiler를 실행한다. 신규 삽입은 explicit caller
anchor와 같은 section의 실제 node가 필요하다. 이 binding은 native run/inline 좌표의 mapping
자격을 주장하지 않는다. 스타일 변경은 참조 댓글과 해당 style을 쓰는 section을 포함한다.
선택할 실제 node가 없는 경우 Anchor error로 거부하며 임의 실행 anchor를 생성하지 않는다.
유한한 원래 모델/graph/selector/compiler 제한을 유지한다.

## 변경과 권한 경계

root complete state, 해당 review entry JSON, 해당 memo-style view 외의 원래 문서
본문·notes·settings·resources·references·opaque 영역을 바꾸지 않는다.
source package identity/graph/revision/state/request/flow/typed plan/compiled plan/target를 재검증한다.
서명·암호화·보호 graph 및 기존 partial importer marker는 원래 full-IR admission에서 거부한다.

작성자/시간/상태는 명시적 caller typed state일 뿐 실제 native metadata mapping은 미검증이다.
actual importer의 absent/unknown 값을 채워서 이 경로로 승격하지 않는다.
PreparedCommentOperation에는 deserializer나 mutable plan/receipt가 없으며 현재 product route는
전체 재검증 뒤에도 RouteUnqualified로 거부한다. 실제 HWPX lowering, authenticated provider,
issuer/atomic execution/publication, installed Hangul semantics/save/reopen/render는 별도 필수 작업이다.
receipt는 native_author_time_state_verified/hwpx_lowered/execution_authority_verified=false다.
P11 comment_delete는 표현하지 않는다.

## 보존

기존 lib.rs는 module 선언 1줄만 추가하며 수정 전 전체 바이트와 역변환을 보존한다.
초기 컴파일/테스트 실패와 whole failed sources를 보존한다. 기존 original model/tests/compiler/
importer/admission/qualification/matrix는 수정하지 않는다. 기존 회귀 실행 파일을 덮어쓰지 않도록
baseline 검사 빌드를 target/p09-93-regression에 격리한다.
한글/COM/UI/접근 허용/실제 SQL/운영·trust DB/설치·설정/commit·push는 실행하지 않는다.
PLANS.md를 재생성하지 않는다. P09 Gate OPEN, P10 새 구현 없음, 목표 active.
