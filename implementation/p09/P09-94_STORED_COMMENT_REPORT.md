# P09-94 저장된 댓글 변경 준비 결과

원래 StoredFormProvider의 sealed-result/IR 읽기를 원래 다섯 댓글 변경 준비와 연결했다.
저장된 source/IR의 인증·snapshot freshness와 compiler 결속 단계이며 native 댓글 import,
HWPX lowering, 실제 SQL 통합 또는 full comment/P09 Gate 완료가 아니다.

## 변경과 검증

- 신규 제품 module: crates/product-cli/src/form_stored_provider/comments.rs.
- 기존 provider에는 module 선언 한 줄만 추가했다. 기존 full_document.rs의 IrSnapshot,
  두 필드와 reader는 부모 module 범위 pub(super) 가시성만 부여했다. 원래 guard body는
  그대로이며 두 파일의 전체 원문을 보관하고 정확한 역변환을 확인했다.
- 신규16 + 기존 stored form/import/policy125 + form/full-document18 + P93 댓글8 +
  원래 댓글 모델10 = **Rust 177 PASS**, ignored/failed 0.
- 신규16에서 원래 다섯 positive 준비의 graph/plan/receipt를 기존 compiler와 전체 비교했다.
  두 artifact의 권한 철회·재부여, quarantine, 독립 ciphertext 변조, head advance,
  실제 IR download 도중 head 변경, 다른 문서/actor/tenant/read scope, 세 binding digest,
  kind/media, canonical/duplicate/unknown/oversized/missing state, partial/protected IR,
  complete view 및 logical insertion 거부를 확인했다. 준비/검증은 ingest/commit하지 않는다.
- strict clippy, 신규 source/test format 및 git diff --check PASS. 기존 검사와 지문 고정
  실행 파일은 덮어쓰지 않고 target/p09-94-regression에서 회귀 검사를 빌드했다.
- 원래 current-source component conformance 15개 PASS; green0/P09 OPEN이다.
  그 qualifier는 원래 component 범위이며 신규 stored product module의 전체 acceptance가 아니다.
  기본 conformance FAIL:matrix_drift는 원래 실패로 남아 있다.

신규 positive는 명시적인 synthetic storage-only bytes와 complete caller IR를 썼다.
ArtifactService/RevisionService 및 실제 AES-GCM 코드는 실행했으나 repository는 in-memory이고
scanner/actor/key/commit metadata는 fixture다. 저장된 package hash로 source-native 댓글
작성자/시간/visibility/resolution/body/좌표가 검증됐다고 주장하지 않는다.

## 실패와 보존

첫 새 테스트는 DocumentGraphDraft의 없는 security 필드 때문에 compile 실패했다.
그 당시 새 source/test/support 4개 전체를 보관하고 원래 security_state 이름으로 수정했다.
strict 검사에서 nested if, 불필요 lifetime, semicolon 지적을 수정했고 검사 완화는 없다.
보존 감사 초안의 predecessor 선택이 P92에 남아 기대 개수 검사에 실패했으며, P93로
정확히 지정한 후 동일한 hash/coverage 조건으로 다시 확인했다. product/source drift가 아니었다.

P93 raw 지문1,126개는 정확히 보존했다. 소스782개 중780개가 같고 바뀐 부모2개는
정확한 whole preimage로 보존된다. P59~P93 지문 선언15,598개, 최초 원본소스1,551개/
51,047,460 bytes 및 native 원본75개를 현재 bytes 또는 정확한 whole 보관본에서 확인했다.
과거 qualification 전체를 재실행한 것은 아니다. P93의 과거 실행 파일46개도 보존했다.
원래 CommentBuilder/compiler/importer/full-IR admission 및 original tests를 수정하지 않았다.

## 다음 실제 제품 경계

native/source metadata와 현재 실제 capture에서 확인 가능한 MEMO·본문 의미를 먼저 조사하고,
지원 증거가 있는 tuple만 기존 importer/assembly와 HWPX lowering에 연결해야 한다.
없는 author/time/state/style/좌표는 unavailable/unverified로 유지한다. durable 저장소 제품
통합, trusted issuer/atomic execution/publication, 미지원 field/Date/external validation,
나머지 P09 기능 검증, P84 SQL 간헐 원인 및 P09 Gate도 남는다.

P93 remaining에 완료된 항목/중복/숫자 key가 섞인 과거 표현은 수정하지 않았다.
이번 checkpoint는 준비 경로 완료와 native/제품 미완료를 별도 필드로 기록한다.
접근허용 없는 잔여는 최소6 큰 묶음이라는 조사 결과이지 정확한 전체 세부 작업 개수가 아니다.
이 단계 완료만으로 그 전체 묶음 하나가 모두 끝났다고 계산하지 않는다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62 UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; full native34 NOT_RUN; green0.
full_comment_product_acceptance=false, p09_complete=false, product_complete=false,
P10_new_implementation=false, goal_status=active. 한글/UI/접근허용/SQL/설치/설정/commit/push 없음.
root PLANS.md는 사용자 삭제 상태를 유지했다.

정책: P09-94_STORED_COMMENT_POLICY.md. 증거: evidence/p09-94-stored-comments.*.json.
