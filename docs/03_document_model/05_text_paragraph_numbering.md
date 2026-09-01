# 텍스트·문단·번호 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## ParagraphNode

```text
ParagraphNode
 ├─ paragraph_style_ref + direct_properties
 ├─ numbering_state
 ├─ inlines[]
 ├─ controls[]
 └─ layout_constraints
```

inline types:

- `TextRun`, `Tab`, `LineBreak`, `SoftHyphen`, `NonBreakingSpace`
- `InlineEquation`, `FieldRef`, `BookmarkBoundary`, `HyperlinkSpan`
- `AnnotationAnchor`, `ChangeSpan`, `Ruby/AdditionalText`
- `InlineObjectRef`, `CharacterOverlap`

## text semantics

- Unicode NFC를 기본으로 하되 source byte/char boundaries가 중요한 경우 원형을 provenance에 보존한다.
- locale, language tag, bidi direction, spellcheck exclusion을 run에 둘 수 있다.
- hard paragraph break와 soft line break를 구분한다.
- 제어 문자와 조판 부호는 typed node로 다룬다.

## numbering

- paragraph number, bullet, outline은 별도 definition과 instance state로 분리한다.
- level 0..N, number format, prefix/suffix, restart rule, start value, alignment, spacing, linked paragraph style을 저장한다.
- “새 번호로 시작”은 page/object/note/outline domain별 restart control로 표현한다.
- 문단 수준 증가/감소는 level operation이며 텍스트 삽입으로 흉내 내지 않는다.

## 문단 첫 글자 장식과 문단 띠

drop cap은 characters/lines/distance/style을 갖는 paragraph decoration이다. paragraph band는 배경/테두리/너비/anchor와 함께 별도 node 또는 paragraph decoration으로 표현한다.

## search normalization

찾기/바꾸기는 literal, regex, case, whole word, Unicode normalization, language, style/property predicate, control type predicate를 지원한다. 치환 전에 matched node IDs와 context를 dry-run으로 반환한다.
