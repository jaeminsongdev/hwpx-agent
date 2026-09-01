# 사용자 정의 문서 크기 + 표 + 수식

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

정확한 mm 단위 용지와 여백을 지정하고 표와 native 수식을 함께 만드는 최소 수직 예다. 실제 서비스에서는 빈 문서의 `sec-1`, `p-title` 등 logical ID를 document skeleton compiler가 먼저 만든다.

핵심 검증은 body area 양수, 표 폭 overflow 없음, equation AST round-trip, target Hancom save/reopen, page render다.

## 실행 예제

`specs/examples/recipes/01_custom_page_table_equation.json` 참조.

## 구현자가 확인할 것

1. JSON Schema validation.
2. capability route와 target binding.
3. dry-run semantic/layout diff.
4. atomic revision.
5. 요청된 validation evidence.
