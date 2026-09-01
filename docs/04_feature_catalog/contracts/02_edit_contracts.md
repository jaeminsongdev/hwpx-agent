# 편집·선택·클립보드 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `편집·선택·클립보드` 영역 28개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## EDIT-001 — 되돌리기

- **Semantic capability:** `edit.undo`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-002 — 다시 실행

- **Semantic capability:** `edit.redo`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-003 — 오려 두기

- **Semantic capability:** `edit.cut`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-004 — 복사하기

- **Semantic capability:** `edit.copy`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-005 — 붙이기

- **Semantic capability:** `edit.paste`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-006 — 골라 붙이기

- **Semantic capability:** `edit.paste_special`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-007 — 모양 복사

- **Semantic capability:** `edit.format_painter`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-008 — 선택 내용 지우기

- **Semantic capability:** `edit.delete`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-009 — 조판 부호 지우기

- **Semantic capability:** `edit.delete_layout_marks`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-010 — 모두 선택

- **Semantic capability:** `edit.select_all`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-011 — 텍스트 범위 선택

- **Semantic capability:** `edit.select_text_range`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-012 — 문단 선택

- **Semantic capability:** `edit.select_paragraph`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-013 — 개체/컨트롤 선택

- **Semantic capability:** `edit.select_control`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-014 — 표 셀 범위 선택

- **Semantic capability:** `edit.select_table_cell_range`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-015 — 커서 이동

- **Semantic capability:** `edit.move_cursor`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-016 — 찾아가기

- **Semantic capability:** `edit.go_to`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-017 — 정렬

- **Semantic capability:** `edit.sort`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-018 — 고치기/속성 편집

- **Semantic capability:** `edit.edit_properties`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-019 — OLE 연결 관리

- **Semantic capability:** `edit.ole_link_manage`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-020 — OLE 개체 속성

- **Semantic capability:** `edit.ole_properties`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-021 — 클립보드 내용 확인

- **Semantic capability:** `edit.clipboard_inspect`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-022 — 텍스트로 복사

- **Semantic capability:** `edit.copy_as_text`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-023 — 그림으로 복사

- **Semantic capability:** `edit.copy_as_image`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- `undo_smoke` — Execute the `undo_smoke` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-024 — 블록 이동

- **Semantic capability:** `edit.move_block`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-025 — 블록 복제

- **Semantic capability:** `edit.duplicate_block`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-026 — 컨트롤 삭제

- **Semantic capability:** `edit.delete_control`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-027 — 컨트롤 교체

- **Semantic capability:** `edit.replace_control`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EDIT-028 — 다중 편집 transaction

- **Semantic capability:** `edit.transaction_multi_edit`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `OperationPlan/selectors`
- **Selector:** `RangeControlOrCursorSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "content": {},
    "mode": {
      "type": "string"
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `selector_tests` — Execute the `selector_tests` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SELECTOR_NOT_FOUND`, `RANGE_STALE`, `EDIT_PRECONDITION_FAILED`, `TRANSACTION_ABORTED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

