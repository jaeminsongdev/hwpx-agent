# Native 한컴 수식 엔진 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## source adapter

한 요청에는 `latex`, `mathml`, `eqedit`, `ast` 중 하나만 허용한다. LaTeX 전체 언어를 지원한다고 주장하지 않고 support table로 허용 문법을 버전화한다. 사용자 macro는 별도 expansion sandbox에서 제한 깊이·토큰 수를 적용한다.

## MathAst

모든 node는 semantic type, children, source span, optional style hint를 갖는다. 공백·brace·명령어 차이와 무관한 canonical form을 만든다. 곱셈 생략, unary minus, 함수 적용, 미분 기호 등 모호성이 있는 입력은 parser가 confidence와 후보를 반환한다.

```rust
enum MathNode {
    Number(String), Identifier(String), Text(String), Symbol(SymbolId),
    Apply { op: MathOp, args: Vec<NodeId> },
    Fraction { numerator: NodeId, denominator: NodeId },
    Script { base: NodeId, sub: Option<NodeId>, sup: Option<NodeId> },
    Root { degree: Option<NodeId>, radicand: NodeId },
    Delimited { left: Delimiter, body: NodeId, right: Delimiter },
    Matrix { rows: Vec<Vec<NodeId>>, kind: MatrixKind },
    Cases(Vec<(NodeId, Option<NodeId>)>),
    Aligned(Vec<AlignedLine>),
}
```

## EqEdit compiler

- AST node별 명시적 lowering rule과 precedence table을 둔다.
- target profile별 EqEdit dialect/escape/symbol mapping을 분리한다.
- compiler output을 문자열 snapshot만으로 시험하지 않고 readback parser로 semantic compare한다.
- unsupported node는 fail-closed. 유사 기호나 plain text로 몰래 대체하지 않는다.

## native equation lowerer

Direct path는 equation control/object, script, font/size/color, inline/display baseline, object extent/anchor를 생성한다. Automation path는 native equation insertion binding을 사용한다. 두 경로 모두 output package 안에 native equation object가 존재하는지 검사한다.

## 크기 계산

수식 object extent를 임의 상수로 두지 않는다. 우선순위:

1. target Hancom automation readback/render bounds.
2. 검증된 layout estimator와 font metrics.
3. conservative provisional extent + `render_required`.

provisional 결과는 visual verified로 표시하지 않는다.

## semantic round-trip

```text
input AST A
 -> compile EqEdit E
 -> insert native object
 -> save/reopen
 -> read EqEdit E'
 -> parse AST B
 -> normalize A/B
 -> semantic equality + style/layout assertions
```

같은 의미의 다른 EqEdit 표현은 허용하되 AST가 달라지면 실패한다.

## conformance corpus

- Tier A: 고교 수학 전 범위, 함수/극한/미분/적분/벡터/수열/집합.
- Tier B: matrix/determinant/cases/aligned/multi-integral/complex delimiters.
- Tier C: legacy scripts, uncommon typography, controlled macro cases.
- property test: random AST → compile → parse round-trip.
- negative: unsupported macro, malformed MathML, excessive nesting, ambiguous syntax.
- target oracle: double-click edit, one token change, save/reopen.

## 완료 기준

- Tier A semantic round-trip 100%, silent approximation 0.
- inline baseline과 block spacing visual thresholds 통과.
- legacy equation unknown script는 preserve mode에서 손실 없음.
- 수식이 이미지/텍스트로 변환된 경우 capability receipt가 실패 상태를 반환.
