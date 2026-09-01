# 스타일 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 계층

1. `FontFaceResource`
2. `CharacterStyle`
3. `ParagraphStyle`
4. `NumberingStyle` / `BulletStyle` / `OutlineStyle`
5. `TableStyle` / `CellStyle`
6. `ObjectStyle`
7. `NamedStyle` — 글자 또는 문단 스타일과 다음 스타일을 묶음
8. direct formatting override

## CharacterStyle

- 언어별 font slots: Hangul, Latin, Hanja, Japanese, other, symbol, user-defined.
- font family/fallback list/face metadata.
- size, relative size, bold, italic.
- underline type/style/color, strike-through variants.
- outline, shadow, emboss, engrave, superscript/subscript.
- text color, shade, border/background.
- character scale(장평), spacing(자간), baseline offset.
- kerning and compression flags where supported.
- hidden/protected/track-change annotations.

## ParagraphStyle

- alignment: left/right/center/justify/distribute.
- left/right margin, first-line indent/hanging indent.
- line spacing modes and value.
- before/after spacing.
- tab stops and leader.
- border/background, paragraph band.
- keep with next, keep lines, widow/orphan, page break before.
- snap-to-grid, line-break/word-break policies.
- numbering/bullet/outline reference and level.

## named style rules

- internal stable id와 localized display name을 분리한다.
- imported style의 영문 이름/식별 특성을 source metadata로 보존한다.
- style dedup은 모든 effective properties가 동일하고 의미 이름 충돌이 없을 때만 한다.
- template surgical mode에서는 사용하지 않는 스타일도 삭제하지 않는다.

## font policy

- server는 font file을 사용자에게 제공하지 않는다.
- target profile에는 설치 font inventory와 checksum을 기록한다.
- 요청 font가 없으면 fail, approved fallback, render-only substitution 중 정책을 선택한다.
- substitution은 validation warning과 render evidence에 표시한다.
