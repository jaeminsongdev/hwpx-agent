# P09-91 원래 컴포넌트 현재 소스 검증 결과

원래 검사 12개에 명시적 현재 소스 검증을 연결했다. 기존 댓글 현재 모드와
원래 양식 HWPX/자동 번호 검사 2개를 합쳐 원래 15개 영역에 현재 소스 검증
경로가 마련됐다. 이는 원래 15개 기본 검사가 모두 PASS라는 뜻이 아니다.
전체 conformance와 실제 P09 제품 Gate는 여전히 완료되지 않았다.

## 구현 및 실제 검사

- 원래 검사 조건·소유권·native 경계는 유지하고 현재 구현 지문 선택과 추가
  불변 증거 검증만 연결했다. 검사 파일 12개 전체의 정확한 역변환을 실제 확인했다.
- 기본 모드와 보관된 원래 검사 결과는 모든 항목이 같다. 기본 검사 15개는
  2 PASS / 13 FAIL을 유지한다. 원래 Python 검사 12개 모듈은 47 PASS / 12 FAIL,
  0 ERROR이며 원래 테스트는 수정하지 않았다.
- 새 현재 모드 12개는 실제 저장소에서 PASS. 현재 모드 Python 검사 19/19 PASS,
  세부 사례 183개. 과거 댓글 현재 모드 검사도 22/22 PASS로 재실행했다.
- Rust 검사 137/137 PASS: domain 공개 93 + domain 내부 전체 18 + HWPX 공개 23
  + HWPX 내부 3. 이 중 이번 12개 원래 컴포넌트의 직접 범위는 128개이고,
  나머지 9개는 함께 실행된 domain 내부 검사다. Rust 소스/테스트는 이번에 수정하지 않았다.
- 불변 증거는 raw 파일 172개와 공식 실제 소스 68개 및 실행 파일 14개를 확인한다.
  현재 출력은 별도 validation/v2로 구분하며 과거 출력 버전을 함께 남긴다.

## 발견한 문제와 수정

보조 참조의 공식 지문은 BOM을 제외한 값이고 다른 원래 공식 지문은 BOM을 포함했다.
로컬 실제 파일 9개 모두의 BOM과 양쪽 계산 방식을 확인했다. 원래 지문이나 파일을
수정하지 않고 family별 정확한 방식을 명시했으며, 전체 원본 바이트 잠금은 유지했다.

초기 171개 파일 기록에는 하이퍼링크 공개 API 파일이 빠져 있었다.
실제 저장소 모드는 통과했지만 격리된 복사본에서 원래 public_export 검사가 실패했다.
이 실패와 초기 기록/도우미/테스트 전체 3개를 보관하고 공개 API의 실제 바이트를
추가한 172개 기록으로 다시 검증했다. 검사 조건을 제거하지 않았다.
원본 보관본 생성 시 추가됐던 EOF 줄바꿈도 전체 지문 검사에서 발견하여 제거했고,
수정 후 15개 전체 보관본의 원래 크기와 SHA-256이 정확히 같은 것을 확인했다.

## 보존과 남은 작업

P59~P90 원본 잠금 12,779개 선언 항목, 최초 전체 소스 1,551개(51,047,460 bytes),
native 증거 75개를 실제 지문으로 확인했다. P90의 소스 647개는 모두 변하지 않았다.
Python 구문 검사와 git diff --check PASS. 한글/접근 허용 창/실제 SQL은 실행하지 않았다.
사용자 변경과 삭제된 루트 PLANS.md 상태를 유지했고 commit/push/install/설정 변경도 없다.

원래 conformance는 fail:matrix_drift이다. 다음은 버전이 구분된 현재 컴포넌트 증거를
원래 conformance 실행 경로에 연결하고 원래 REF 53개/소유권/P11 보류/native 미검증을
유지하는 것이다. 해당 연결 이후에도 전체 댓글/문서 제품 경로와 원래 P09의 나머지
기능 의미·대상 한글 저장/재열기/렌더링/차이 비교·신뢰 발급자·원자적 실행 등은 필요하다.
P84 SQL 간헐 실패 원인은 여전히 UNRESOLVED이며 과거 SQL 통과를 이번 증거로 승격하지 않는다.

P09/A12/A13=OPEN, P26=failed_semantic_non_green, P62=UNRESOLVED,
native admission=INPUT_CHANGED_RE_ADMISSION_REQUIRED, full native34=NOT_RUN.
native_executed=false, full_comment_product_acceptance=false, p09_complete=false,
product_complete=false, P10_new_implementation=false, goal_status=active.

정책: P09-91_COMPONENT_CURRENT_SOURCE_POLICY.md.
전체 지문·실행·초기 실패·보존 기록: evidence/p09-91-component-current-source.*.json.
