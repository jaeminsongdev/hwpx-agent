# 학교 양식 보존 채우기

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

템플릿을 전체 재생성하지 않고 field/table stable selector로 필요한 부분만 바꾼다. `untouched_parts=byte_preserve`, `unknown_xml=preserve`, `styles=no_gc`가 핵심이다.

## 실행 예제

`specs/examples/recipes/03_surgical_template_fill.json` 참조.

## 구현자가 확인할 것

1. JSON Schema validation.
2. capability route와 target binding.
3. dry-run semantic/layout diff.
4. atomic revision.
5. 요청된 validation evidence.
