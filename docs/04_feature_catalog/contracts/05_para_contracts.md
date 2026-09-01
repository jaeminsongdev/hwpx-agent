# 문단·탭·목록·스타일 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `문단·탭·목록·스타일` 영역 45개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## PARA-001 — 왼쪽 정렬

- **Semantic capability:** `para.align_left`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-002 — 오른쪽 정렬

- **Semantic capability:** `para.align_right`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-003 — 가운데 정렬

- **Semantic capability:** `para.align_center`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-004 — 양쪽 정렬

- **Semantic capability:** `para.align_justify`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-005 — 배분 정렬

- **Semantic capability:** `para.align_distribute`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-006 — 문단 왼쪽 여백

- **Semantic capability:** `para.margin_left`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-007 — 문단 오른쪽 여백

- **Semantic capability:** `para.margin_right`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-008 — 첫 줄 들여쓰기

- **Semantic capability:** `para.first_line_indent`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-009 — 내어쓰기

- **Semantic capability:** `para.hanging_indent`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-010 — 줄 간격 비율

- **Semantic capability:** `para.line_spacing_percent`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-011 — 고정 줄 간격

- **Semantic capability:** `para.line_spacing_fixed`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-012 — 최소 줄 간격

- **Semantic capability:** `para.line_spacing_minimum`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-013 — 글자 기준 줄 간격

- **Semantic capability:** `para.line_spacing_font_based`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-014 — 문단 위 간격

- **Semantic capability:** `para.space_before`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-015 — 문단 아래 간격

- **Semantic capability:** `para.space_after`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-016 — 문단 테두리

- **Semantic capability:** `para.paragraph_border`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-017 — 문단 배경

- **Semantic capability:** `para.paragraph_background`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-018 — 탭 위치

- **Semantic capability:** `para.tab_stop`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-019 — 탭 채움선

- **Semantic capability:** `para.tab_leader`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-020 — 다음 문단과 함께

- **Semantic capability:** `para.keep_with_next`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-021 — 문단 줄 함께 유지

- **Semantic capability:** `para.keep_lines`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-022 — 외톨이줄 방지

- **Semantic capability:** `para.widow_orphan`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-023 — 문단 앞 쪽 나누기

- **Semantic capability:** `para.page_break_before`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-024 — 문서 격자에 맞춤

- **Semantic capability:** `para.snap_grid`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-025 — 낱말/줄 나눔 규칙

- **Semantic capability:** `para.word_break`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-026 — 문단 첫 글자 장식

- **Semantic capability:** `para.drop_cap`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-027 — 문단 띠

- **Semantic capability:** `para.paragraph_band`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-028 — 글머리표 적용/해제

- **Semantic capability:** `para.bullet_apply`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-029 — 글머리표 모양 정의

- **Semantic capability:** `para.bullet_definition`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-030 — 문단 번호 적용/해제

- **Semantic capability:** `para.numbering_apply`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-031 — 문단 번호 모양 정의

- **Semantic capability:** `para.numbering_definition`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-032 — 문단 번호 새로 시작

- **Semantic capability:** `para.number_restart`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-033 — 개요 적용/해제

- **Semantic capability:** `para.outline_apply`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-034 — 개요 번호 모양

- **Semantic capability:** `para.outline_definition`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-035 — 한 수준 증가

- **Semantic capability:** `para.outline_level_up`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-036 — 한 수준 감소

- **Semantic capability:** `para.outline_level_down`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-037 — 스타일 적용

- **Semantic capability:** `para.named_style_apply`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-038 — 스타일 추가

- **Semantic capability:** `para.named_style_create`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-039 — 스타일 편집

- **Semantic capability:** `para.named_style_edit`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-040 — 스타일 삭제

- **Semantic capability:** `para.named_style_delete`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-041 — 스타일 순서 변경

- **Semantic capability:** `para.named_style_reorder`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-042 — 스타일 가져오기

- **Semantic capability:** `para.style_import`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-043 — 스타일 내보내기

- **Semantic capability:** `para.style_export`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-044 — 스타일마당 적용

- **Semantic capability:** `para.style_gallery`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## PARA-045 — 다음 문단 스타일 지정

- **Semantic capability:** `para.next_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `ParagraphStyle/NumberingStyle/NamedStyle`
- **Selector:** `ParagraphRangeSelector`

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
    "merge_mode": {
      "enum": [
        "replace",
        "merge"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.

**Desktop automation:** ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- `style_count` — Execute the `style_count` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PARAGRAPH_NOT_FOUND`, `LIST_REFERENCE_INVALID`, `STYLE_CONFLICT`, `LAYOUT_CONSTRAINT_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

