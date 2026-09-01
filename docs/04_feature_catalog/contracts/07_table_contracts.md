# 표·셀·계산 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `표·셀·계산` 영역 61개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## TABLE-001 — 표 만들기

- **Semantic capability:** `table.create`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "rows",
    "columns"
  ],
  "properties": {
    "rows": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "columns": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1024
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "column_widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "row_heights_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "style_id": {
      "type": "string"
    },
    "initial_cells": {
      "type": "array",
      "items": {
        "type": "array"
      }
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-002 — 표 그리기

- **Semantic capability:** `table.draw`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-003 — 표 지우개

- **Semantic capability:** `table.eraser`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-004 — 문자열을 표로

- **Semantic capability:** `table.text_to_table`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-005 — 표를 문자열로

- **Semantic capability:** `table.table_to_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-006 — 표 데이터로 차트 만들기

- **Semantic capability:** `table.chart_from_table`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-007 — 표/셀 속성

- **Semantic capability:** `table.properties`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-008 — 각 셀마다 테두리/배경 적용

- **Semantic capability:** `table.cell_border_each`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-009 — 하나의 셀처럼 테두리/배경 적용

- **Semantic capability:** `table.cell_border_unified`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-010 — 표 나누기

- **Semantic capability:** `table.split_table`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "rows": {
      "type": "integer",
      "minimum": 1
    },
    "columns": {
      "type": "integer",
      "minimum": 1
    },
    "direction": {
      "enum": [
        "horizontal",
        "vertical"
      ]
    },
    "preserve_content": {
      "enum": [
        "concatenate",
        "first",
        "distribute",
        "reject_if_multiple"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-011 — 표 붙이기

- **Semantic capability:** `table.join_table`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "rows": {
      "type": "integer",
      "minimum": 1
    },
    "columns": {
      "type": "integer",
      "minimum": 1
    },
    "direction": {
      "enum": [
        "horizontal",
        "vertical"
      ]
    },
    "preserve_content": {
      "enum": [
        "concatenate",
        "first",
        "distribute",
        "reject_if_multiple"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-012 — 줄 추가

- **Semantic capability:** `table.insert_rows`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "index",
    "count"
  ],
  "properties": {
    "index": {
      "type": "integer",
      "minimum": 0
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "inherit_format_from": {
      "enum": [
        "before",
        "after",
        "none"
      ]
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-013 — 칸 추가

- **Semantic capability:** `table.insert_columns`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "index",
    "count"
  ],
  "properties": {
    "index": {
      "type": "integer",
      "minimum": 0
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "inherit_format_from": {
      "enum": [
        "before",
        "after",
        "none"
      ]
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-014 — 줄 지우기

- **Semantic capability:** `table.delete_rows`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "index",
    "count"
  ],
  "properties": {
    "index": {
      "type": "integer",
      "minimum": 0
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "inherit_format_from": {
      "enum": [
        "before",
        "after",
        "none"
      ]
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-015 — 칸 지우기

- **Semantic capability:** `table.delete_columns`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "index",
    "count"
  ],
  "properties": {
    "index": {
      "type": "integer",
      "minimum": 0
    },
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000
    },
    "inherit_format_from": {
      "enum": [
        "before",
        "after",
        "none"
      ]
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-016 — 셀 나누기

- **Semantic capability:** `table.split_cell`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-017 — 셀 합치기

- **Semantic capability:** `table.merge_cells`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "rows": {
      "type": "integer",
      "minimum": 1
    },
    "columns": {
      "type": "integer",
      "minimum": 1
    },
    "direction": {
      "enum": [
        "horizontal",
        "vertical"
      ]
    },
    "preserve_content": {
      "enum": [
        "concatenate",
        "first",
        "distribute",
        "reject_if_multiple"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-018 — 셀 높이 같게

- **Semantic capability:** `table.equal_row_height`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-019 — 셀 너비 같게

- **Semantic capability:** `table.equal_column_width`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-020 — 표마당/표 스타일

- **Semantic capability:** `table.table_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-021 — 표 뒤집기/전치

- **Semantic capability:** `table.transpose`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-022 — 블록 합계

- **Semantic capability:** `table.block_sum`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "enabled"
  ],
  "properties": {
    "enabled": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-023 — 블록 평균

- **Semantic capability:** `table.block_average`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "enabled"
  ],
  "properties": {
    "enabled": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-024 — 블록 곱

- **Semantic capability:** `table.block_product`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "enabled"
  ],
  "properties": {
    "enabled": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-025 — 가로 합계

- **Semantic capability:** `table.horizontal_sum`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-026 — 세로 합계

- **Semantic capability:** `table.vertical_sum`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-027 — 가로 평균

- **Semantic capability:** `table.horizontal_average`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-028 — 세로 평균

- **Semantic capability:** `table.vertical_average`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-029 — 가로 곱

- **Semantic capability:** `table.horizontal_product`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-030 — 세로 곱

- **Semantic capability:** `table.vertical_product`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-031 — 계산식 입력

- **Semantic capability:** `table.formula`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "formula": {
      "type": "string"
    },
    "formula_ast": {
      "type": "object",
      "additionalProperties": true
    },
    "recalculate": {
      "type": "boolean"
    },
    "cache_policy": {
      "enum": [
        "update",
        "preserve",
        "clear"
      ]
    }
  },
  "anyOf": [
    {
      "required": [
        "formula"
      ]
    },
    {
      "required": [
        "formula_ast"
      ]
    }
  ]
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-032 — 1,000단위 구분 쉼표 넣기

- **Semantic capability:** `table.thousands_add`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-033 — 1,000단위 구분 쉼표 빼기

- **Semantic capability:** `table.thousands_remove`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-034 — 표 위치·정렬

- **Semantic capability:** `table.position`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-035 — 표 크기

- **Semantic capability:** `table.width_height`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-036 — 글자처럼 취급/떠 있는 표

- **Semantic capability:** `table.inline_floating`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-037 — 표 주위 글 배치

- **Semantic capability:** `table.wrap`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-038 — 표 바깥 여백

- **Semantic capability:** `table.outer_margin`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-039 — 셀 안 여백

- **Semantic capability:** `table.cell_padding`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-040 — 셀 가로/세로 정렬

- **Semantic capability:** `table.cell_alignment`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-041 — 셀 글자 방향

- **Semantic capability:** `table.cell_text_direction`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-042 — 제목 줄 자동 반복

- **Semantic capability:** `table.repeat_header`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "enabled"
  ],
  "properties": {
    "enabled": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-043 — 쪽 경계 표 나눔

- **Semantic capability:** `table.allow_page_split`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "enabled"
  ],
  "properties": {
    "enabled": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-044 — 행 쪼개짐 정책

- **Semantic capability:** `table.row_split_policy`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-045 — 셀 보호/편집 가능

- **Semantic capability:** `table.cell_protection`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "enabled"
  ],
  "properties": {
    "enabled": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-046 — 셀 면별 테두리

- **Semantic capability:** `table.cell_border`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-047 — 셀 대각선

- **Semantic capability:** `table.cell_diagonal`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-048 — 셀 배경색·무늬·그림

- **Semantic capability:** `table.cell_fill`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-049 — 셀 숫자 형식

- **Semantic capability:** `table.number_format`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-050 — 행 최소 높이

- **Semantic capability:** `table.row_min_height`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-051 — 열 고정 너비

- **Semantic capability:** `table.column_fixed_width`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-052 — 내용에 맞춤

- **Semantic capability:** `table.autofit_content`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-053 — 쪽 너비에 맞춤

- **Semantic capability:** `table.autofit_page`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-054 — 중첩 표

- **Semantic capability:** `table.nested_table`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-055 — 표 캡션

- **Semantic capability:** `table.caption`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-056 — 표 데이터 정렬

- **Semantic capability:** `table.sort_cells`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-057 — 표 자동 채우기

- **Semantic capability:** `table.auto_fill`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-058 — 자동 채우기 내용 정의

- **Semantic capability:** `table.auto_fill_series`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "formula": {
      "type": "string"
    },
    "style_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-059 — 상대 셀 참조

- **Semantic capability:** `table.formula_relative_ref`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "formula": {
      "type": "string"
    },
    "formula_ast": {
      "type": "object",
      "additionalProperties": true
    },
    "recalculate": {
      "type": "boolean"
    },
    "cache_policy": {
      "enum": [
        "update",
        "preserve",
        "clear"
      ]
    }
  },
  "anyOf": [
    {
      "required": [
        "formula"
      ]
    },
    {
      "required": [
        "formula_ast"
      ]
    }
  ]
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-060 — 절대 셀 참조

- **Semantic capability:** `table.formula_absolute_ref`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "formula": {
      "type": "string"
    },
    "formula_ast": {
      "type": "object",
      "additionalProperties": true
    },
    "recalculate": {
      "type": "boolean"
    },
    "cache_policy": {
      "enum": [
        "update",
        "preserve",
        "clear"
      ]
    }
  },
  "anyOf": [
    {
      "required": [
        "formula"
      ]
    },
    {
      "required": [
        "formula_ast"
      ]
    }
  ]
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TABLE-061 — 계산 결과 캐시 갱신

- **Semantic capability:** `table.formula_cache`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P06`
- **IR 위치:** `TableNode/CellProperties/FormulaAst`
- **Selector:** `TableCellSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "formula": {
      "type": "string"
    },
    "formula_ast": {
      "type": "object",
      "additionalProperties": true
    },
    "recalculate": {
      "type": "boolean"
    },
    "cache_policy": {
      "enum": [
        "update",
        "preserve",
        "clear"
      ]
    }
  },
  "anyOf": [
    {
      "required": [
        "formula"
      ]
    },
    {
      "required": [
        "formula_ast"
      ]
    }
  ]
}
```

### 실행 절차

1. 논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.

**Desktop automation:** Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `formula_readback` — Read table formula and cached result; compare normalized FormulaAst.
- `page_split` — Assert row/cell/page split and repeat-header behavior on boundary fixtures.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TABLE_NOT_FOUND`, `CELL_RANGE_INVALID`, `MERGE_CONFLICT`, `FORMULA_INVALID`, `TABLE_LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P06`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

