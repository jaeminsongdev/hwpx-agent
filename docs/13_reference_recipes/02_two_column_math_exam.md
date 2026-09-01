# A3 2단 수학 시험지

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

A3 세로 2단 시험지의 page/column/table/equation operation 예다. ExamPlan compiler가 문항 노드와 keep policy를 만든 뒤 이 layout operation을 적용한다.

최종 검증에는 문항 분리 보고서, 표 쪽 나눔, 수식 semantic round-trip, 실제 한/글 렌더가 필요하다.

## 실행 예제

`specs/examples/recipes/02_two_column_math_exam.json` 참조.

## 구현자가 확인할 것

1. JSON Schema validation.
2. capability route와 target binding.
3. dry-run semantic/layout diff.
4. atomic revision.
5. 요청된 validation evidence.
