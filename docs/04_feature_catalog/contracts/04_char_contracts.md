# 글자 모양·문자 입력 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `글자 모양·문자 입력` 영역 41개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## CHAR-001 — 언어별 글꼴 지정

- **Semantic capability:** `char.font_slots`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-002 — 글꼴 지정

- **Semantic capability:** `char.font_family`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-003 — 글꼴 대체 목록

- **Semantic capability:** `char.font_fallback`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-004 — 글자 크기

- **Semantic capability:** `char.font_size`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "size_pt"
  ],
  "properties": {
    "size_pt": {
      "type": "number",
      "minimum": 1,
      "maximum": 4096
    },
    "relative": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-005 — 장평

- **Semantic capability:** `char.character_scale`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-006 — 자간

- **Semantic capability:** `char.character_spacing`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-007 — 진하게

- **Semantic capability:** `char.bold`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-008 — 기울임

- **Semantic capability:** `char.italic`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-009 — 밑줄

- **Semantic capability:** `char.underline`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-010 — 밑줄 모양·색

- **Semantic capability:** `char.underline_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-011 — 취소선

- **Semantic capability:** `char.strike`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-012 — 이중 취소선

- **Semantic capability:** `char.double_strike`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-013 — 외곽선

- **Semantic capability:** `char.outline`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-014 — 그림자

- **Semantic capability:** `char.shadow`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-015 — 양각

- **Semantic capability:** `char.emboss`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-016 — 음각

- **Semantic capability:** `char.engrave`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-017 — 위 첨자

- **Semantic capability:** `char.superscript`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-018 — 아래 첨자

- **Semantic capability:** `char.subscript`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-019 — 글자 색

- **Semantic capability:** `char.text_color`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-020 — 형광펜/강조색

- **Semantic capability:** `char.highlight`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-021 — 글자 테두리

- **Semantic capability:** `char.char_border`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-022 — 글자 배경

- **Semantic capability:** `char.char_background`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-023 — 기준선 위치

- **Semantic capability:** `char.baseline_offset`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-024 — 커닝

- **Semantic capability:** `char.kerning`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-025 — 숨은 글자

- **Semantic capability:** `char.hidden_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-026 — 선택 글자 보호

- **Semantic capability:** `char.protected_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-027 — 글자 스타일 적용

- **Semantic capability:** `char.char_style_apply`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-028 — 글자 스타일 해제

- **Semantic capability:** `char.char_style_clear`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-029 — 글자 겹치기

- **Semantic capability:** `char.character_overlap`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-030 — 덧말 넣기

- **Semantic capability:** `char.additional_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-031 — 문자표 문자 입력

- **Semantic capability:** `char.special_character`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-032 — 한자 입력

- **Semantic capability:** `char.hanja_input`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-033 — 한자 단어 등록

- **Semantic capability:** `char.hanja_register`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-034 — 한자 부수/총획 입력

- **Semantic capability:** `char.hanja_radical`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-035 — 한자 새김 입력

- **Semantic capability:** `char.hanja_meaning`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-036 — 날짜/시간 문자열

- **Semantic capability:** `char.date_time_literal`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-037 — 묶음 빈칸

- **Semantic capability:** `char.nonbreaking_space`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-038 — 조건부 하이픈

- **Semantic capability:** `char.soft_hyphen`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-039 — 문자 언어 지정

- **Semantic capability:** `char.language_tag`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-040 — 양방향 문자 방향

- **Semantic capability:** `char.bidi_direction`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## CHAR-041 — 맞춤법 검사 제외

- **Semantic capability:** `char.spellcheck_exclude`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P05`
- **IR 위치:** `CharacterStyle/TextRun`
- **Selector:** `TextRangeSelector`

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
        "merge",
        "toggle"
      ]
    }
  }
}
```

### 실행 절차

1. 대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.

**Desktop automation:** 대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `font_probe` — Execute the `font_probe` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `TEXT_RANGE_INVALID`, `FONT_UNAVAILABLE`, `STYLE_CONFLICT`, `VALUE_OUT_OF_RANGE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P05`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

