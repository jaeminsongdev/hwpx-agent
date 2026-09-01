# DocumentGraph IR v2

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 목적

`DocumentGraph`는 LLM, MCP, direct HWPX, Windows automation, WebHWP 사이의 **유일한 의미 계약**이다. HWPX numeric IDs, XML namespace, HAction/ParameterSet 이름, COM 객체는 IR에 들어오지 않는다.

## 최상위 구조

```text
DocumentGraph
 ├─ schema_version / document_id / source_profile
 ├─ metadata / security_state / accessibility
 ├─ settings / resource_catalog / style_catalog
 ├─ sections[]
 │   ├─ section_properties
 │   ├─ master_pages[]
 │   ├─ headers_footers[]
 │   └─ body: FlowContainer
 ├─ notes: footnotes/endnotes/comments
 ├─ references: bookmarks/fields/crossrefs/toc/index/bibliography
 ├─ review: change_sets/history
 └─ opaque_preservation_bag
```

`FlowContainer.children`은 다음 node를 포함한다.

- `ParagraphNode`
- `TableNode`
- `DrawingNode`
- `ChartNode`
- `EquationNode`(display)
- `EmbeddedObjectNode`
- `FormControlNode`
- `PageBreakNode`, `ColumnBreakNode`, `SectionBreakNode`
- `MasterPageRefNode`, `HiddenExplanationNode`, `ParagraphBandNode`

## 공통 node 필드

```json
{
  "node_id": "logical stable id",
  "node_type": "paragraph",
  "source_anchor": {"part":"section0.xml","opaque_id":"..."},
  "style_refs": [],
  "layout_hints": {},
  "semantics": {},
  "provenance": {"created_by":"user|import|automation"},
  "preserve": {"unknown_attributes":true}
}
```

## 안정 ID

- `node_id`는 문서 revision 사이에서 가능한 한 유지한다.
- 새 문서는 UUIDv7 또는 deterministic content seed로 생성한다.
- template import에서는 source part/path/opaque ID를 바탕으로 stable mapping을 만든다.
- HWPX 내부 ID가 재할당되더라도 logical ID는 변경하지 않는다.
- selector와 diff는 logical ID를 우선하고 text/structural anchor를 보조로 사용한다.

## partial IR

대형 문서는 전체 graph를 매번 모델에 반환하지 않는다. `DocumentSnapshot`은 outline, section summaries, node handles, style/resource summaries를 제공하고, `document_inspect`에서 필요한 범위만 materialize한다.

## round-trip contract

1. Direct parser는 알려진 의미를 typed IR로 올린다.
2. 알 수 없는 XML/part/attribute는 opaque bag과 source anchor로 보존한다.
3. 수정되지 않은 subtree는 가능한 한 원본 bytes 또는 canonical token stream을 재사용한다.
4. 수정된 subtree만 lowerer가 재생성한다.
5. relationship와 referenced resource closure를 재검증한다.
6. semantic snapshot과 source preservation report를 함께 출력한다.

## 구현 완료 기준

- 모든 feature catalog의 `document_ir` 값이 특정 node/property path에 연결됨.
- 1,000페이지 문서의 outline-only inspect가 전체 graph materialize 없이 동작.
- logical ID가 open-save-open 및 direct↔automation round-trip에서 안정적으로 유지되거나 명시된 remap receipt를 생성.
