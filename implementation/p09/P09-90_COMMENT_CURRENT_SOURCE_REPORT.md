# P09-90 댓글 현재 소스 검증 결과

명시적 현재 소스 검증 모드를 원래 댓글 계약 검사에 연결했다.
comment-model/v1 API와 REF-026..REF-030 5개 기능의 원래 검사 범위는 그대로다.
현재 모드만 컴포넌트 PASS이고, P09 Gate와 실제 한글 제품 검증은 완료되지 않았다.

## 변경 및 검증

- 원래 검사 파일 1개에 명시적 프로필 선택과 추가 검증만 연결했다.
  원래 전체 소스로 되돌리는 정확한 역변환과 전체 원본 보관본을 확인했다.
- 새 검증 도우미는 불변 v2 기록 및 32개 raw 파일, 권위 문서 4개와 공식 소스
  17개의 실제 바이트를 확인한다. 공식 경로 접두사 불일치로 발생한 초기 실패를
  보관하고, 동일한 17개 지문에 접두사를 정확히 적용하는 방식으로 수정했다.
  불변 증거나 과거 잠금을 바꾸어 통과시키지 않았다.
- 원래 Rust 댓글 검사: 11/11 PASS, 공개 10개 + 내부 계획 변조 1개.
  현재 모드 Python 검사: 22/22 PASS, 세부 사례 71개.
  원래 계약·상태·소유권 검사 유지, 파일 변조/누락, 실행 파일 변조/누락,
  raw 줄바꿈 변조, 공식 소스 17개 각각의 변조, 상태 승격과 잘못된 경로를 확인했다.
- 보관된 과거 검사와 현재 기본 검사의 반환 결과는 모든 항목이 동일하다.
  두 검사 모두 fail:implementation_digest이며, 원래 Python 검사는 4 PASS / 1 FAIL이다.
  원래 검사와 검증 기록을 수정하지 않았다.
- 기존 검사 15개: 2 PASS / 13 FAIL. 댓글의 새 현재 모드 PASS는 별도 결과이지
  기존 실패 13개를 지운 결과가 아니다. 다른 실패 프로필의 재검증과 전체 conformance
  연결은 남아 있다. conformance: fail:matrix_drift.
- Python 구문 검사와 git diff --check PASS. 한글·네트워크·실제 SQL은 실행하지 않았다.

## 보존

P59~P89에 선언된 원본 파일 잠금 11,978개 항목, 최초 전체 소스 1,551개
(51,047,460 bytes), native 증거 75개를 실제 지문으로 확인했다.
P89의 소스 636개는 모두 바뀌지 않았다. 이번 수정 대상 원래 검사 파일은
P89의 636개 목록 밖에 있었으며, 최초 전체 소스의 원본과 이번 전체 보관본으로
보존을 확인했다. 이 목록 차이로 발생한 첫 보존 검사 실패도 기록에 남겼다.

이전 P89의 Rust 334개 검사·실제 36개 자료 결과는 보존했지만 이번에 전부 재실행한
결과로 집계하지 않는다. 이번 실제 Rust 재실행은 댓글 11개뿐이다.
사용자 변경, P00~P08/P17 원본, 실패/native 기록과 삭제된 루트 PLANS.md 상태를 유지했다.
stage/commit/push/install/설정/운영 DB 변경과 접근 허용 창 실행은 하지 않았다.

## 남은 제품 작업 및 Gate

원래 전체 P09 댓글 삽입/스타일/표시/해결 제품 경로, native 작성자/시각/상태/
스타일 매핑과 대상 한글 검증, 원래 source conformance의 현재 구현 재검증,
MEMO metaTag/중첩 본문 및 지원되지 않는 필드 의미, source-bound 전체 문서
제품 작업·신뢰 발급자·원자적 실행/공개 권한은 미완료다. P11 댓글 삭제는 제외한다.
P84 SQL 간헐 실패 원인은 UNRESOLVED이고, 과거 SQL 통과를 이번 증거로 승격하지 않는다.

P09/A12/A13=OPEN, P26=failed_semantic_non_green, P62=UNRESOLVED,
native admission=INPUT_CHANGED_RE_ADMISSION_REQUIRED, full native34=NOT_RUN.
native_author_time_binding=false, native_visibility_resolution_binding=false,
full_comment_product_acceptance=false, p09_complete=false, product_complete=false,
P10_new_implementation=false, goal_status=active.

정책: P09-90_COMMENT_CURRENT_SOURCE_POLICY.md.
실행 기록과 전체 지문: evidence/p09-90-comment-current-source.*.json.
