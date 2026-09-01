# 필드·양식 개체·주석·참조 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## FieldNode

- date/time, filename/path, document properties.
- user field, mail merge field, click-here placeholder.
- page/section/object/note number.
- formula/conditional field where supported.
- field code, display result, update policy, locked state를 분리한다.

## FormControlNode

text input, checkbox, radio, combo/list, button, date control 등 target-supported controls. name, value, default, validation, tab order, enabled/locked, script reference를 모델링한다. script execution은 별도 보안 권한이다.

## notes

- footnote/endnote: numbering format/restart/position/separator/style/content.
- hidden explanation: anchor와 hidden content.
- comment/memo: author/time/body/anchor/resolved/display properties.
- correction mark: type, anchor, metadata.

## references

- bookmark: named range/control anchor.
- hyperlink: internal bookmark, document, URL, email 등 type; external open policy 별도.
- cross-reference: target id, display kind, update state.
- caption: object type, sequence id, label, number, placement.
- TOC: source levels/styles, leader/page number options, generated range.
- index: entries/subentries/ranges, generated index settings.
- bibliography: source records, citation nodes, style, generated list.

## update semantics

동적 필드와 참조는 `preserve_cached`, `recompute_direct`, `recompute_automation`, `freeze_text` 정책을 선택한다. 기본은 의미를 보존하고 automation oracle에서 명시적으로 update한다.

## mail merge

데이터 source는 문서와 분리된 encrypted artifact이며 schema, row count, merge fields, output mode(single/multiple documents), PII policy를 갖는다. 출력마다 provenance와 source row ID hash를 기록한다.
