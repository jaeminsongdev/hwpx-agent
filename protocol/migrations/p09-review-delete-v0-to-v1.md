# 기존 원본 review 삭제 출력 v0 → v1

## 기존 상태

P09-97 기존 review body 교체와 P09-96 memo style 출력, 원래5개 caller-owned typed comment
연산과 full-IR compiler는 그대로다. 기존 source observation의 author/time/state/protection은
unverified이고 current product route는 unqualified다.

## 추가 API

- ImportedDocumentReviewBodies::lower_delete(fresh, marker, WriterLimits)
- StoredImportedReviewBodies::prepare_delete(provider, marker, WriterLimits, now)
- immutable ReviewDeleteOutput/ReviewDeleteReceipt 및 PreparedStoredReviewDelete
- 원래 검증을 반복하는 verify/with_verified_bytes; 항상 거부하는 require_current_product_route

새 receipt는 기존 observed review의 structural deletion에 한정한다. source/output 전체
package 및 observations digests, deleted subtree count, changed part1, exact outside bytes와
명시적인 native/protection/execution unqualified flags를 기록한다. caller XML·author/time
기본값·경로·비밀정보는 받거나 receipt에 노출하지 않는다.

## 호환과 거부

기존 operation enum/schema/capability/contract/registry는 변경하지 않는다.
review.comment_delete/all의 P11 지정과 required native validators도 변경하지 않는다.
오래된 source/foreign 또는 body/end anchor/삭제 후 old anchor, 잘못된 envelope, 원래
nested payload, patch/ID/writer/readback 실패는 출력을 승인하지 않는다.
stored ACL/AEAD/head drift는 cached bytes callback 전에 거부한다.

이번 변경을 소스 삭제·보호 해제·native acceptance·전체 compiler integration으로 적용하면 안 된다.
새 package가 원본을 덮어쓰지 않으며 새 product revision을 자동 발행하지 않는다.
P09 Gate OPEN, native34 NOT_RUN/green0, 실제SQL 미실행, P10 미시작을 유지한다.

## 증거

P09-98 정책/보고서 및 evidence/p09-98-review-delete.*.v1.json 참조.
P09-97 snapshot/validator는 고정된 과거 증거로 보존하고 현재 P98 audit를 별도로 실행한다.
