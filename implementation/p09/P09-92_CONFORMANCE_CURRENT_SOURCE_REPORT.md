# P09-92 원래 conformance 현재 소스 연결 결과

원래 conformance 검사에 명시적 현재 소스 모드를 연결했다. 실제 저장소와 격리된
복사본 모두 원래 15개 하위 검사를 실행하고 현재 소스/컴포넌트 검증을 통과했다.
이는 실제 한글 또는 P09 제품 Gate 통과가 아니다. 원래 기본 모드의 matrix_drift는 유지한다.

## 변경과 검증

원래 builder는 수정하지 않았다. 현재 builder의 정확한 출력을 별도 v2 wrapper로
보관하고 원래 validator의 기존 조건을 실행한다. REF 53개/P09 46개/P11 보류 7개,
summary, 모든 non-component 행 정보는 과거와 같다. REF-021/022/031/032/033/034의
세 HWPX adapter 소스 지문만 기존 구현 변경을 반영한다. Green 0개를 유지한다.

현재 모드는 override와 upstream skip을 거부한다. qualification의 실제 242개 파일
전체 바이트를 잠그며, 원래 15개 검사 결과의 버전·증거·non-native 상태까지 확인한다.
도우미/새 테스트는 순환 지문을 피하여 최종 source-progress에 별도 결속한다.

- 새 Python 19/19 PASS. 실제 저장소와 owned clone의 전체 15개 경로,
  owner/target/fixture/contract/qualification/공식 소스/실행 파일/기존 검사 변조 거부를 포함한다.
  세부 subcase 수는 이번에 별도 집계하지 않았다.
- 양식 HWPX 6 + 자동 번호 8 = Rust 14/14 PASS. Rust 소스와 테스트는 수정하지 않았다.
- 원래 Python 9개: 8 PASS / 0 FAIL / 1 ERROR(matrix_drift). 기존 테스트를 수정하지 않았다.
- 현재 CLI PASS, 원래 기본 CLI FAIL:matrix_drift. 기본 실패를 필터링하지 않았다.
- Python 구문 3개 및 git diff --check PASS.

## 초기 실패와 보존

처음 240개 지문으로 만든 owned clone은 자동 번호 원래 검사에서 qualification_fixture_path로
실패했다(18개 중 1 FAIL). 원래 검사가 실제로 읽는 P05 PAGE DIGIT HWPX 원본과 근거 문서가
누락되어 있었다. 초기 qualification/helper/tests 전체 3개와 실패를 보존하고,
두 원본 전체 바이트를 추가한 242개 기록으로 재검증했다. 조건을 제거하거나 파일을 재생성하지 않았다.
이 원본은 과거 lexical shape 증거이며 현재 한글 또는 객체 번호 의미 증거가 아니다.

수정 전 원래 validator 전체 13,557 bytes와 SHA-256 및 전체 텍스트 역변환 일치를 확인했다.
P59~P91의 13,682개 지문 선언, 최초 전체 소스 1,551개/51,047,460 bytes,
native 원본 75개를 현재 파일 또는 정확한 전체 보관본으로 확인했다.
P91 현재 소스 732개는 모두 그대로다. 과거 qualification 전체를 재실행했다는 뜻은 아니다.
한글/접근 허용/실제 SQL/설치/설정/commit/push는 실행하지 않았으며 루트 PLANS.md는 없다.

## 남은 제품 작업과 다음 경계

현재 source conformance 연결은 끝났다. 원래 full-document 댓글/문서 제품 경로에서
insert/style/show/resolve mutation/lowering와 qualified author/time/state 의미,
fields/notes/references/TOC/citation/mailmerge의 원래 제품 검증, source re-admission,
실제 대상 한글 저장·재열기·렌더링·차이 비교, 신뢰 발급자/원자적 실행/출판 및
P09 Gate는 남았다. comment_delete는 원래 P11 소유다.

다음 안전한 구현 단계는 기존 CommentBuilder와 source-bound catalog/assembly를 사용하는
댓글 mutation/lowering의 원래 제품 경로를 조사하여 실제 근거가 있는 변경부터 연결하는 것이다.
native 의미가 없는 필드는 unavailable을 유지하고 별도 importer나 추측 기본값을 만들지 않는다.
사용자의 접근 허용 금지 경계를 계속 유지한다. P10 새 구현으로 넘어가지 않는다.

P09/A12/A13 OPEN, P26 failed_semantic_non_green, P62 UNRESOLVED,
native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED, full native34 NOT_RUN.
full_comment_product_acceptance=false, p09_complete=false, product_complete=false,
P10_new_implementation=false, goal_status=active.

정책: P09-92_CONFORMANCE_CURRENT_SOURCE_POLICY.md.
초기 실패·실행·전체 지문·보존·최종 검사: evidence/p09-92-conformance-current-source.*.json.
