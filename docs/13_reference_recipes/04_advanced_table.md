# 병합·반복 머리행·수식 표

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

표 grid를 만든 뒤 직사각형 병합, 반복 머리행, 상대 수식을 원자적으로 적용한다. 병합 전 비어 있지 않은 셀 내용 처리와 formula reference 이동을 반드시 명시한다.

## 실행 예제

`specs/examples/recipes/04_advanced_table.json` 참조.

## 구현자가 확인할 것

1. JSON Schema validation.
2. capability route와 target binding.
3. dry-run semantic/layout diff.
4. atomic revision.
5. 요청된 validation evidence.
