# 쪽·구역·다단·머리말 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `쪽·구역·다단·머리말` 영역 50개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## PAGE-001 — 용지 종류 preset

- **Semantic capability:** `page.paper_preset`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "preset"
  ],
  "properties": {
    "preset": {
      "enum": [
        "A3",
        "A4",
        "A5",
        "B4_ISO",
        "B4_JIS",
        "B5_ISO",
        "B5_JIS",
        "LETTER",
        "LEGAL",
        "TABLOID",
        "USER_PROFILE"
      ]
    },
    "orientation": {
      "enum": [
        "portrait",
        "landscape"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-002 — 사용자 정의 용지 크기

- **Semantic capability:** `page.paper_custom`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "width_mm",
    "height_mm"
  ],
  "properties": {
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0,
      "maximum": 2000
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0,
      "maximum": 2000
    },
    "orientation": {
      "enum": [
        "portrait",
        "landscape"
      ]
    },
    "name": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-003 — 용지 세로/가로 방향

- **Semantic capability:** `page.orientation`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-004 — 상하좌우 여백

- **Semantic capability:** `page.margin_all`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top_mm": {
      "type": "number",
      "minimum": 0
    },
    "bottom_mm": {
      "type": "number",
      "minimum": 0
    },
    "left_mm": {
      "type": "number",
      "minimum": 0
    },
    "right_mm": {
      "type": "number",
      "minimum": 0
    },
    "header_mm": {
      "type": "number",
      "minimum": 0
    },
    "footer_mm": {
      "type": "number",
      "minimum": 0
    },
    "gutter_mm": {
      "type": "number",
      "minimum": 0
    },
    "gutter_side": {
      "enum": [
        "left",
        "right",
        "top",
        "inside"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-005 — 머리말/꼬리말 거리

- **Semantic capability:** `page.margin_header_footer`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top_mm": {
      "type": "number",
      "minimum": 0
    },
    "bottom_mm": {
      "type": "number",
      "minimum": 0
    },
    "left_mm": {
      "type": "number",
      "minimum": 0
    },
    "right_mm": {
      "type": "number",
      "minimum": 0
    },
    "header_mm": {
      "type": "number",
      "minimum": 0
    },
    "footer_mm": {
      "type": "number",
      "minimum": 0
    },
    "gutter_mm": {
      "type": "number",
      "minimum": 0
    },
    "gutter_side": {
      "enum": [
        "left",
        "right",
        "top",
        "inside"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-006 — 제본 여백

- **Semantic capability:** `page.gutter`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "top_mm": {
      "type": "number",
      "minimum": 0
    },
    "bottom_mm": {
      "type": "number",
      "minimum": 0
    },
    "left_mm": {
      "type": "number",
      "minimum": 0
    },
    "right_mm": {
      "type": "number",
      "minimum": 0
    },
    "header_mm": {
      "type": "number",
      "minimum": 0
    },
    "footer_mm": {
      "type": "number",
      "minimum": 0
    },
    "gutter_mm": {
      "type": "number",
      "minimum": 0
    },
    "gutter_side": {
      "enum": [
        "left",
        "right",
        "top",
        "inside"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-007 — 한쪽 제본

- **Semantic capability:** `page.binding_single`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-008 — 맞쪽 제본

- **Semantic capability:** `page.binding_facing`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-009 — 위로 넘기기 제본

- **Semantic capability:** `page.binding_top`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-010 — 가로/세로 글자 방향

- **Semantic capability:** `page.text_direction`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-011 — 쪽 테두리

- **Semantic capability:** `page.page_border`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-012 — 쪽 배경색

- **Semantic capability:** `page.page_background_color`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "color"
  ],
  "properties": {
    "color": {
      "oneOf": [
        {
          "type": "string",
          "pattern": "^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$"
        },
        {
          "type": "object",
          "additionalProperties": true
        }
      ]
    },
    "theme_role": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-013 — 쪽 배경 그림

- **Semantic capability:** `page.page_background_image`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-014 — 바탕쪽

- **Semantic capability:** `page.master_page`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-015 — 홀짝/첫 쪽 바탕쪽

- **Semantic capability:** `page.master_page_variant`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-016 — 머리말 넣기

- **Semantic capability:** `page.header_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-017 — 꼬리말 넣기

- **Semantic capability:** `page.footer_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-018 — 홀수/짝수/첫 쪽 머리말·꼬리말

- **Semantic capability:** `page.header_footer_variants`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-019 — 쪽 번호 매기기

- **Semantic capability:** `page.page_number_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-020 — 쪽 번호 모양·위치

- **Semantic capability:** `page.page_number_format`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-021 — 쪽 번호 새로 시작

- **Semantic capability:** `page.page_number_restart`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-022 — 그림/표/수식 번호 새로 시작

- **Semantic capability:** `page.object_number_restart`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-023 — 현재 쪽 요소 감추기

- **Semantic capability:** `page.hide_current_page`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-024 — 줄 번호 표시

- **Semantic capability:** `page.line_number_enable`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-025 — 줄 번호 간격·시작·구역 설정

- **Semantic capability:** `page.line_number_config`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-026 — 쪽 나누기

- **Semantic capability:** `page.page_break`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-027 — 단 나누기

- **Semantic capability:** `page.column_break`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-028 — 균등 다단 설정

- **Semantic capability:** `page.column_config_equal`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-029 — 사용자 너비 다단

- **Semantic capability:** `page.column_config_custom`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-030 — 단 사이 간격

- **Semantic capability:** `page.column_gap`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-031 — 단 구분선

- **Semantic capability:** `page.column_separator`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-032 — 단 진행 방향

- **Semantic capability:** `page.column_direction`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-033 — 마지막 쪽 단 균형

- **Semantic capability:** `page.column_balance`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-034 — 단 설정 나누기

- **Semantic capability:** `page.column_layout_break`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "count": {
      "type": "integer",
      "minimum": 1,
      "maximum": 32
    },
    "equal_width": {
      "type": "boolean"
    },
    "widths_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "exclusiveMinimum": 0
      }
    },
    "gaps_mm": {
      "type": "array",
      "items": {
        "type": "number",
        "minimum": 0
      }
    },
    "separator": {
      "type": "object",
      "additionalProperties": true
    },
    "direction": {
      "enum": [
        "left_to_right",
        "right_to_left"
      ]
    },
    "balance_last_page": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-035 — 구역 설정

- **Semantic capability:** `page.section_config`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-036 — 구역 나누기

- **Semantic capability:** `page.section_break`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-037 — 구역별 용지

- **Semantic capability:** `page.section_paper_override`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-038 — 구역별 번호 체계

- **Semantic capability:** `page.section_numbering`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-039 — 구역별 각주/미주 모양

- **Semantic capability:** `page.section_note_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-040 — 구역별 바탕쪽

- **Semantic capability:** `page.section_master`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-041 — 원고지 설정

- **Semantic capability:** `page.manuscript_paper`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-042 — 라벨 문서 만들기

- **Semantic capability:** `page.label_document`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-043 — 라벨 새 쪽 추가

- **Semantic capability:** `page.label_new_page`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-044 — 쪽 지우기

- **Semantic capability:** `page.delete_page`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-045 — 문서 격자/원고지 그리드

- **Semantic capability:** `page.page_grid`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-046 — 기본 탭 간격

- **Semantic capability:** `page.default_tab`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-047 — 빈 줄 끌어올림

- **Semantic capability:** `page.empty_line_pullup`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-048 — 첫 쪽 다르게

- **Semantic capability:** `page.first_page_special`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-049 — 새 구역 홀수/짝수 쪽 시작

- **Semantic capability:** `page.page_start_side`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PAGE-050 — 구역 내 단 구간

- **Semantic capability:** `page.section_columns_span`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `SectionProperties/MasterPage/HeaderFooter`
- **Selector:** `SectionOrPageSelector`

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
    "apply_scope": {
      "enum": [
        "section",
        "selected_sections",
        "whole_document",
        "from_here"
      ]
    }
  }
}
```

### 실행 절차

1. section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.

**Desktop automation:** PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `SECTION_NOT_FOUND`, `PAPER_SIZE_INVALID`, `MARGIN_EXCEEDS_PAPER`, `LAYOUT_OVERFLOW`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

