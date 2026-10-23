# P09-109 authenticated persisted rich comment additive binding

원래 P94 저장 댓글 route와 P108 caller-complete body preparation은 변경하지 않는다.
새 child module은 기존 서비스·sealed source/IR readers·stored complete state decoder·
strict request 및 P108 final compiler를 연결한다. source/IR/body selectors나 기존 body
override, 새 artifact ingest/head commit/publication capability는 추가하지 않는다.

실제 다운로드한 complete caller IR의 metadata 문자열에서만 existing body inventory를
읽는다. canonical outer graph와 별도로 inner typed JSON의 exact canonical equality를
검사한다. private DTO 외에 public prepared receipt/body에는 Deserialize를 추가하지 않는다.
원래 full graph limits와 protection/partial guards, P108 body validation/budgets를 유지한다.
source 및 IR은 fresh independent ACL/AEAD/head/scanner로 재검증되며 memory candidate만
제공한다. storage 검증을 native author/time/state/source import 또는 durable SQL로 승격하지 않는다.

각 original parent의 whole preimage를 보존하며 source/test module declaration만 추가한다.
기존 함수/test bodies/helper visibility와 원래 낮은 graph ceilings를 바꾸지 않는다.
새 실패 source/실행 파일은 보존하며 과거 native/SQL 실패 원장이나 기본 matrix_drift를 지우지 않는다.
전체 P09 Gate는 OPEN, P10은 시작하지 않는다. actual source metadata/coordinates의
positive evidence가 없는 부분은 계속 미검증이다. PLANS.md를 재생성하지 않는다.
