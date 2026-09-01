# 레이아웃·표·시각 회귀 테스트

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 구조 측정

- paper width/height/orientation/margins.
- section and column spans.
- page count and paragraph page assignment.
- table row/column grid, merged ranges, widths/heights.
- object bounds/anchor/z-order/wrap.
- header/footer/master page region.
- overflow/clipping/split events.

## visual diff

페이지를 동일 Hancom build·font inventory·DPI로 rasterize한다. 전체 pixel diff만 쓰지 않고:

- text baseline/line box shift.
- table border topology.
- equation bounding box/baseline.
- image/object bounds.
- page break and column flow.
- allowed dynamic regions(date/page field 등).

## 허용치

허용치는 capability/fixture별로 기록한다. 기본값을 넓게 잡아 실패를 숨기지 않는다. page break, missing glyph, table border, equation structure 차이는 tolerance 0에 가깝게 둔다.

## 시험지 특화

- 문항 번호와 첫 문단 분리 금지.
- 선택지 block split policy.
- 그림/표/수식과 참조 문장 keep-together.
- 문항 겹침·잘림·빈 열·비정상 widow.
- 정답지 번호/배점/정답 cardinality 일치.
