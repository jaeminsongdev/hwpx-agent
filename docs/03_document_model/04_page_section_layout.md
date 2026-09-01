# 쪽·구역·레이아웃 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## SectionProperties

```text
paper: preset | custom(width,height)
orientation: portrait | landscape
binding: single | facing | top
margins: top/bottom/left/right/header/footer/gutter
text_direction: horizontal | vertical_latin_upright | vertical_latin_sideways
columns: count, widths, gap, separator, direction, balance
page_border_background
master_page_refs
header_footer_policy
page_numbering / object_numbering / note_numbering
line_numbering
grid / baseline / default_tab
first_page_suppression
empty_line_pullup
```

## 적용 범위

용지·다단·바탕쪽·각주/미주 모양 등은 구역 범위를 가진다. operation은 `document`, `current_section`, `section_ids`, `from_anchor_new_section` 중 하나를 반드시 명시한다.

## paper preset

A/B/국판/46배판 등 preset은 이름뿐 아니라 target profile의 exact dimensions로 resolve한다. 사용자 정의 크기는 width/height를 직접 저장하며 workstation에 등록된 사용자 preset 이름에 의존하지 않는다.

## 머리말/꼬리말·바탕쪽

- 홀수/짝수/첫 쪽/양쪽 적용을 모델링한다.
- section별 master page와 header/footer variant를 둔다.
- “현재 쪽만 감추기”는 해당 page context의 suppression control로 표현한다.
- page number field는 표시 형식, 위치, 시작값, 숨김 규칙을 포함한다.

## 다단

균등 단과 사용자 너비 단을 모두 표현한다. `ColumnDefinition`은 width/gap, separator style, flow direction, balance behavior를 갖는다. 단 설정 나누기는 새로운 column layout span을 생성하며 section break와 구분한다.

## 레이아웃 검증

- content width/height 음수 금지.
- 여백+gutter가 paper bounds를 넘으면 reject.
- 표/개체의 available area와 wrap 계산.
- rendered page count, first baseline, footer/header collision, orphan/widow, clipped object를 측정한다.
