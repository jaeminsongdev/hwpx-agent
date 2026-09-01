# 그림·도형·글상자·차트·OLE 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 공통 ObjectProperties

- anchor: character/paragraph/page/paper.
- positioning: inline/floating, reference frame, x/y offsets.
- size, aspect lock, rotation, flip.
- wrap: in-front/behind/square/tight/top-bottom/inline 등 target-supported modes.
- margins, caption, protection.
- z-order, group id, visibility, printable.
- alt text/title/description.

## ImageNode

embedded/linked resource, MIME, original dimensions, crop rectangle, scale, color adjustments, transparency, border, shadow/reflection/glow/soft edge, clipping, replacement text. linked images are not fetched unless allowlisted; embed is default.

## ShapeNode

line, arrow, rectangle, rounded rectangle, ellipse, arc, polygon, freeform, connector, callout, basic symbols. geometry, control points, line cap/join/dash/arrows, fill solid/gradient/pattern/image, shadow and effects를 표현한다.

## TextBoxNode

내부 FlowContainer, padding, vertical alignment, text direction, auto-size, linked flow, shape properties를 갖는다.

## WordArtNode

text, warp preset, character style, fill/line/effect, transform를 갖는다. Direct HWPX 지원이 불완전한 경우 automation route를 사용한다.

## ChartNode

chart type, series, categories, data table, axes, legends, labels, title, styles, number formats, linked/embedded data provenance를 포함한다. 차트 engine의 실제 데이터 구조가 version-sensitive이면 automation 생성 후 IR snapshot을 읽는다.

## OLE/Multimedia

- 기본 support는 `PRESERVE_ONLY` 또는 `AUTOMATION_FULL`.
- 임베디드 binary를 실행하지 않는다.
- 새 OLE 삽입은 허용된 CLSID/application allowlist와 관리자 권한이 필요하다.
- multimedia는 artifact package 보존과 미리보기 metadata까지만 기본 제공한다.
