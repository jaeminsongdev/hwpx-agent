# Native Equation 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 원칙

수식은 이미지가 아니라 한/글에서 더블클릭해 편집할 수 있는 native equation object여야 한다. 입력은 LaTeX, MathML, EqEdit, Math AST 중 하나를 받되 canonical representation은 versioned `MathAst`다.

## pipeline

```text
source → parser/adapter → MathAst → normalize → semantic validation
       → EqEdit compiler → native equation lowerer → HWPX/automation
       → reopen/readback → semantic compare → render/oracle
```

## AST node

- literal: number, identifier, text, symbol.
- arithmetic/relation/logical/set operations.
- fraction, power, subscript, root.
- function call, trig/log/exp, accents, vectors.
- delimiters, absolute/norm, over/under braces.
- limits, sum, product, integral, derivative.
- matrix, determinant, cases, aligned lines.
- binomial, permutations/combinations, set builder.
- typography directives limited to semantic-safe subset.

## source provenance

원본 source, parser version, normalization version, AST hash, EqEdit compiler version, emitted script를 receipt에 저장한다. 기존 equation을 수정할 때는 readback script와 parsed AST를 모두 보존한다.

## layout properties

inline/display, baseline, width/height, font/size, line thickness, color, object margins, caption, numbering, anchor/wrap을 표현한다.

## 실패 정책

- 미지원 LaTeX는 `EQUATION_LATEX_UNSUPPORTED`.
- parser ambiguity는 후보를 반환하고 사용자/skill이 선택.
- text 또는 image fallback은 명시적으로 요청된 export-only 모드 외에는 금지.
- EqEdit compile 성공만으로 verified가 아니다. 실제 native object, reopen, editor smoke가 필요하다.

## conformance tiers

- Tier A: 고교 수학 전체와 일반 과학 기호.
- Tier B: 행렬, cases, aligned, 복합 집합/논리, 다중 적분.
- Tier C: 사용자 정의 매크로, 드문 typography, legacy EqEdit 특수 문법.

Tier A는 semantic round-trip 100%, Tier B는 99% 이상, silent approximation 0을 요구한다.
