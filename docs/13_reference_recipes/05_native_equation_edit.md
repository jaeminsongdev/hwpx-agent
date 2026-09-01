# 기존 native 수식 편집

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

수식 logical ID로 기존 equation을 선택하고 MathAst/EqEdit round-trip을 거쳐 수정한다. output은 다시 native equation이어야 하며 editor smoke까지 완료해야 release-grade다.

## 실행 예제

`specs/examples/recipes/05_native_equation_edit.json` 참조.

## 구현자가 확인할 것

1. JSON Schema validation.
2. capability route와 target binding.
3. dry-run semantic/layout diff.
4. atomic revision.
5. 요청된 validation evidence.
