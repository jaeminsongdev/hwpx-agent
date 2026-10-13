# P09-92 원래 conformance 현재 소스 연결 정책

원래 `reference_conformance.build_matrix`를 변경하지 않고 그 현재 출력의 별도
v2 wrapper를 원래 conformance 검사에 연결한다. 명시적 `--current-source-v2`
모드만 현재 기록을 사용한다. 기본 모드와 과거 matrix·qualification·문서·테스트는
동결하며 `matrix_drift`를 숨기거나 과거 결과를 현재 PASS로 바꾸지 않는다.

## 검증 경계

- 원래 53 REF, P09 소유 46개/P11 보류 7개, required fixture·target·privacy 및
  모든 no-green 검사 조건을 유지한다. 현재 원래 생성기와 기록의 출력이 정확히 같아야 한다.
- 현재 qualification 242개 파일 전체 바이트와 크기를 확인한다. 도우미가 qualification
  자체의 지문도 고정한다. helper/테스트는 최종 source-progress에서 별도로 결속한다.
- 원래 15개 하위 검사를 같은 순서로 실제 실행한다. 13개는 P90/P91 명시적 현재 모드,
  양식 HWPX/자동 번호 2개는 수정하지 않은 기존 검사다. 출력 버전·증거·non-native
  상태도 확인하며 skip, override, unknown profile 및 manufactured PASS를 거부한다.
- 원래 P05 PAGE DIGIT fixture/근거 문서는 whole-byte source 증거일 뿐이다.
  이를 현재 한글/객체 번호 의미 검증으로 승격하지 않는다. 원본을 다시 생성하지 않는다.
- 새 native/제품 authority를 만들어내지 않는다. 실제 한글 저장·재열기·렌더링·차이 비교,
  author/time/state 의미, 신뢰 발급자, 원자적 실행/출판 및 전체 P09 Gate는 별도다.

## 보존과 승인 경계

수정 전 원래 validator 전체와 초기 실패 profile 3개를 raw byte archive로 보존한다.
원래 validator 전체의 역변환 일치를 확인하고, 사용자 변경·native 증거·과거 실패를 유지한다.
이 단계는 한글/COM/UI/접근 허용·실제 SQL·운영/trust DB·설치/설정·commit/push를 실행하지 않는다.
사용자가 삭제한 루트 PLANS.md를 재생성하지 않는다.

P09/A12/A13 OPEN, P26 failed_semantic_non_green, P62 UNRESOLVED,
native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED, full native34 NOT_RUN,
product_complete=false, P10_new_implementation=false, goal_status=active.
