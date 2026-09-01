# 표 모델과 구현 규격

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 구조

```text
TableNode
 ├─ rows[]
 │   └─ cells[]
 │       ├─ grid_span / row_span
 │       ├─ properties
 │       └─ content: FlowContainer
 ├─ column_grid[]
 ├─ table_properties
 ├─ caption
 └─ formula_graph
```

logical grid는 병합 전 좌표를 유지한다. 병합 셀은 master cell과 covered coordinates를 명확히 구분한다.

## TableProperties

- width mode: absolute, percent, fit-content, fit-page.
- position/anchor/wrap/inline.
- left/right/top/bottom outer margins.
- border/fill, cell spacing.
- page split policy, row split policy, repeat header rows.
- alignment, text flow, caption, table id/name.
- auto-resize and fixed row/column constraints.

## CellProperties

- width/height/min/max, padding.
- horizontal/vertical alignment, text direction.
- border per side, diagonal lines, fill/gradient/image.
- protected/editable state.
- number format, formula, result cache.
- content overflow/shrink/fit policy.

## 구조 연산

- insert/delete rows/columns.
- merge rectangular cells only; non-rectangular request fails.
- split cell by rows/columns with content distribution policy.
- equalize width/height.
- split/join table.
- transpose/flip where backend supports.
- string↔table conversion with delimiter/quote/escape schema.
- nested table insertion.

## 계산식

`FormulaAst`를 사용하여 SUM, AVG, PRODUCT, arithmetic, cell/range refs, relative/absolute refs를 표현한다. backend 수식 문자열은 compiler가 생성한다. 계산 결과는 source formula와 cached result를 분리하며, oracle save 후 readback을 검증한다.

## 페이지 분할

- `allow`, `avoid_row`, `avoid_table`, `required_keep` 정책.
- header repeat가 켜진 경우 split fragment마다 동일 header가 렌더되는지 확인.
- 셀 내부 긴 문단·수식·그림의 split/overflow를 검사.
- 표 전체를 무리하게 다음 쪽으로 보내 빈 페이지를 만들 경우 layout warning을 낸다.

## 테스트 필수 조합

병합+배경+대각선, 반복 머리행+여러 쪽, 셀 수식+숫자 형식, 세로쓰기 셀, 중첩 표, 캡션, inline/floating table, 1×1/최대 크기 경계, 수천 행 성능을 포함한다.
