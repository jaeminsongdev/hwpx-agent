# 필드·양식·주석·참조 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `필드·양식·주석·참조` 영역 53개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## REF-001 — 필드 입력

- **Semantic capability:** `ref.field_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-002 — 사용자 정의 필드

- **Semantic capability:** `ref.field_user`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-003 — 누름틀/클릭 안내 필드

- **Semantic capability:** `ref.field_click_here`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-004 — 날짜/시간 코드

- **Semantic capability:** `ref.field_date_time`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-005 — 파일 이름 필드

- **Semantic capability:** `ref.field_filename`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-006 — 쪽 번호 필드

- **Semantic capability:** `ref.field_page_number`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-007 — 구역 번호 필드

- **Semantic capability:** `ref.field_section_number`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-008 — 개체 번호 필드

- **Semantic capability:** `ref.field_object_number`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-009 — 필드 결과 새로 고침

- **Semantic capability:** `ref.field_update`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-010 — 필드 결과 잠금

- **Semantic capability:** `ref.field_lock`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

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

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-011 — 텍스트 양식 개체

- **Semantic capability:** `ref.form_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-012 — 체크 상자

- **Semantic capability:** `ref.form_checkbox`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-013 — 라디오 단추

- **Semantic capability:** `ref.form_radio`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-014 — 콤보 상자

- **Semantic capability:** `ref.form_combo`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-015 — 목록 상자

- **Semantic capability:** `ref.form_list`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-016 — 명령 단추

- **Semantic capability:** `ref.form_button`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-017 — 날짜 양식

- **Semantic capability:** `ref.form_date`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-018 — 양식 개체 속성

- **Semantic capability:** `ref.form_properties`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-019 — 양식 탭 순서

- **Semantic capability:** `ref.form_tab_order`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-020 — 양식 데이터 연결

- **Semantic capability:** `ref.form_data_binding`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-021 — 각주 넣기

- **Semantic capability:** `ref.footnote_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-022 — 미주 넣기

- **Semantic capability:** `ref.endnote_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-023 — 각주/미주 모양

- **Semantic capability:** `ref.note_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-024 — 각주↔미주 변환

- **Semantic capability:** `ref.note_convert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-025 — 주석 저장하기

- **Semantic capability:** `ref.note_export`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-026 — 숨은 설명

- **Semantic capability:** `ref.hidden_explanation`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

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

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-027 — 메모 넣기

- **Semantic capability:** `ref.comment_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-028 — 메모 모양

- **Semantic capability:** `ref.comment_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-029 — 메모 보이기/숨기기

- **Semantic capability:** `ref.comment_show_hide`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

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

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-030 — 메모 해결 처리

- **Semantic capability:** `ref.comment_resolve`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-031 — 책갈피 넣기

- **Semantic capability:** `ref.bookmark_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-032 — 책갈피 지우기

- **Semantic capability:** `ref.bookmark_delete`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-033 — 하이퍼링크 넣기

- **Semantic capability:** `ref.hyperlink_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-034 — 하이퍼링크 편집

- **Semantic capability:** `ref.hyperlink_edit`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-035 — 상호 참조 넣기

- **Semantic capability:** `ref.crossref_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-036 — 상호 참조 새로 고침

- **Semantic capability:** `ref.crossref_update`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-037 — 제목 차례 표시

- **Semantic capability:** `ref.toc_mark`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-038 — 차례 표시 숨기기

- **Semantic capability:** `ref.toc_hide_mark`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-039 — 차례 만들기

- **Semantic capability:** `ref.toc_create`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-040 — 차례 새로 고침

- **Semantic capability:** `ref.toc_update`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-041 — 색인 표시

- **Semantic capability:** `ref.index_mark`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-042 — 색인 만들기

- **Semantic capability:** `ref.index_create`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-043 — 참고 문헌 관리

- **Semantic capability:** `ref.bibliography_manage`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-044 — 인용 삽입

- **Semantic capability:** `ref.citation_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-045 — 참고 문헌 목록 생성

- **Semantic capability:** `ref.bibliography_generate`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-046 — 메일 머지 필드 넣기

- **Semantic capability:** `ref.mailmerge_field`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-047 — 메일 머지 만들기

- **Semantic capability:** `ref.mailmerge_generate`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-048 — 캡션 번호 체계

- **Semantic capability:** `ref.caption_sequence`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-049 — 날짜/시간 형식

- **Semantic capability:** `ref.date_time_format`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-050 — 파일 이름 문자열 넣기

- **Semantic capability:** `ref.file_name_literal`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-051 — 교정 부호 넣기

- **Semantic capability:** `ref.correction_mark`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-052 — 자료 연결

- **Semantic capability:** `ref.data_link`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REF-053 — 깨진 참조 검사

- **Semantic capability:** `ref.reference_validate`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `FieldNode/FormControlNode/Notes/References`
- **Selector:** `ReferenceFieldOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {
      "type": "string"
    },
    "value": {},
    "properties": {
      "type": "object",
      "additionalProperties": true
    },
    "target": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.

**Desktop automation:** 필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `field_readback` — Execute the `field_readback` validator defined in the target profile and attach its evidence artifact.
- `reference_update` — Execute the `reference_update` validator defined in the target profile and attach its evidence artifact.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `REFERENCE_TARGET_MISSING`, `FIELD_NAME_CONFLICT`, `REFERENCE_CYCLE`, `FIELD_REFRESH_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

