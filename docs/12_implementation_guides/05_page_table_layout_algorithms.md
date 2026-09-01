# 문서 크기·쪽·다단·표 레이아웃 알고리즘

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 단위와 종이 규격

public API는 `mm`, `pt`, `deg`, ratio를 사용한다. HWPUNIT 변환은 하나의 checked module에서 수행하며 반올림 mode와 원래 값의 provenance를 저장한다. preset은 이름만 저장하지 않고 target profile이 해석한 exact width/height도 receipt에 기록한다.

## PageSetup 검증

```text
paper width/height > 0
printable text width = paper - left - right - gutter
printable text height = paper - top - bottom - header/footer constraints
columns total width + gaps <= text width
header/footer distance does not invert body region
object anchors and table preferred widths fit or produce explicit overflow plan
```

구역마다 PageSetup이 다를 수 있으므로 “문서 전체” 요청도 실제로는 section selector를 펼쳐 operation 여러 개로 만든다.

## 사용자 정의 크기

`page.paper_custom`은 width/height mm를 필수로 받고 orientation은 결과 치수와 중복 충돌하지 않게 정규화한다. 프린터 종속 가능성은 artifact 저장 가능성과 실제 인쇄 가능성을 분리해 보고한다.

## 다단

`ColumnLayout`은 count, equal/custom widths, gaps, separator, direction, balance policy를 가진다. custom width의 합이 본문 폭을 넘으면 자동 축소하지 않고 `LAYOUT_OVERFLOW`를 반환한다. 단 구간은 section 전체와 구간 control을 구분한다.

## 표 내부 모델

```text
TableGrid
  rows[]
  columns[]
  slots[row][col] -> master_cell_id
Cell
  row_span, col_span
  content_block_ids
  margins, border_fill, vertical_alignment
  formula_ast, cached_value, number_format
TableLayout
  width mode, anchor, wrap, page split, repeat header
```

병합은 직사각형 slot 집합만 허용한다. 병합 전 각 master cell 내용을 어떤 순서로 보존할지 `preserve_content`가 없으면 여러 비어 있지 않은 셀에 대해 실패한다.

## 행·열 삽입/삭제

1. 대상 인덱스와 병합 span 교차 여부를 계산한다.
2. span 확장/축소 또는 split 정책을 명시한다.
3. 수식 상대/절대 참조를 FormulaAst 기준으로 이동한다.
4. row/column style inheritance source를 결정한다.
5. grid invariant를 확인한다.
6. direct lowering 또는 automation 실행 후 readback한다.

## 자동 맞춤

자동 맞춤은 단순 평균 분배가 아니다.

- 최소 폭: 셀 여백 + unbreakable token/object minimum.
- 선호 폭: 글꼴 metric 기반 줄바꿈 비용.
- 제약: merged span, fixed column, page/body width.
- 목적함수: overflow 최소화, row height 증가 최소화, 기존 폭 변화 최소화.

결과는 approximate layout plan이며 실제 한/글 renderer의 page/line break를 oracle로 확인한다. font가 없으면 verified가 아니다.

## 페이지 분할

표/행의 split policy, repeat header, keep-with-next, caption, footnote가 함께 영향을 준다. boundary fixture는 페이지 끝 1줄 전/정확히 경계/1줄 후, merged cell, nested table, long equation/image를 포함한다.

## 필수 시험지 acceptance

- A3/A4/B4/custom mm, 세로/가로, 1단/2단.
- 30문항 표/수식 혼합 문서에서 문항 번호와 본문이 의도치 않게 분리되지 않음.
- 반복 머리행과 셀 병합이 저장·재열기·PDF export 후 보존.
- 쪽 수와 주요 bounding box가 target Hancom oracle과 tolerance 내 일치.
