# 수식 적합성 테스트

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Tier

- **A**: 사칙, 분수, 첨자, 근호, 절댓값, 함수, 극한, 미분 표기, 적분, 합/곱, 관계, 그리스 문자, 벡터.
- **B**: 행렬, 경우 나누기, 조합, 집합, 다행 정렬, 중첩 구문.
- **C**: 한/글 EqEdit 특화 옵션, 극단적 중첩, 사용자 기호/확장.

## pipeline assertions

1. input parser result.
2. normalized Math AST hash.
3. EqEdit compiler output.
4. native equation object existence.
5. package reopen script readback.
6. semantic AST equivalence.
7. real Hancom open.
8. equation editor edit smoke.
9. save/reopen semantic equivalence.
10. render baseline/size comparison.

## property tests

- AST pretty-print/parse idempotency.
- commutative normalization은 사용하지 않아 원래 표현 순서를 보존.
- delimiter balance.
- matrix dimensions.
- superscript/subscript nesting bounds.
- unicode/Greek symbol mapping.
- font/style separation from equation semantics.

## 실패 정책

unsupported LaTeX는 error. plain text 또는 이미지 fallback은 사용자가 명시적으로 `render_only`를 선택한 별도 capability에서만 허용하며 native 수식 성공으로 집계하지 않는다.
