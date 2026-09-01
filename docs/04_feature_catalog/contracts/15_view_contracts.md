# 보기·작업환경 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `보기·작업환경` 영역 47개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## VIEW-001 — 화면 확대/축소

- **Semantic capability:** `view.zoom`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-002 — 쪽 윤곽 보기

- **Semantic capability:** `view.page_outline`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-003 — 조판 부호 표시

- **Semantic capability:** `view.show_layout_marks`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-004 — 문단 부호 표시

- **Semantic capability:** `view.show_paragraph_marks`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-005 — 교정 부호 표시

- **Semantic capability:** `view.show_correction_marks`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-006 — 투명 선 표시

- **Semantic capability:** `view.show_transparent_lines`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-007 — 그림 표시/숨기기

- **Semantic capability:** `view.show_images`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-008 — 메모 보이기/숨기기

- **Semantic capability:** `view.show_comments`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-009 — 메모 안내선

- **Semantic capability:** `view.comment_guides`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-010 — 메모 내용 보기

- **Semantic capability:** `view.comment_content_pane`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-011 — 한자 발음 표시

- **Semantic capability:** `view.hanja_pronunciation`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-012 — 한자 발음 설정

- **Semantic capability:** `view.hanja_pronunciation_settings`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-013 — 격자 보기

- **Semantic capability:** `view.grid_view`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-014 — 격자 설정

- **Semantic capability:** `view.grid_settings`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-015 — 그리기 안내선

- **Semantic capability:** `view.drawing_guides`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-016 — 개체 이동 안내선

- **Semantic capability:** `view.move_guides`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-017 — 개체 이동 안내선 설정

- **Semantic capability:** `view.move_guide_settings`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-018 — 문서 보기 색

- **Semantic capability:** `view.document_view_color`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-019 — 기본 도구 상자

- **Semantic capability:** `view.toolbar_default`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-020 — 서식 도구 상자

- **Semantic capability:** `view.toolbar_format`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-021 — 사용자 도구 상자

- **Semantic capability:** `view.toolbar_customize`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-022 — 쪽 모양 작업 창

- **Semantic capability:** `view.pane_page_shape`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-023 — 빠른 실행 작업 창

- **Semantic capability:** `view.pane_quick_run`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-024 — 스타일 작업 창

- **Semantic capability:** `view.pane_styles`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-025 — 책갈피 작업 창

- **Semantic capability:** `view.pane_bookmarks`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-026 — 개요 보기 작업 창

- **Semantic capability:** `view.pane_outline`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-027 — 스크립트 작업 창

- **Semantic capability:** `view.pane_script`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-028 — 번역 작업 창

- **Semantic capability:** `view.pane_translation`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-029 — 양식 개체 속성 작업 창

- **Semantic capability:** `view.pane_form_properties`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-030 — 클립보드 작업 창

- **Semantic capability:** `view.pane_clipboard`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-031 — 사전 검색 작업 창

- **Semantic capability:** `view.pane_dictionary`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-032 — 태그 이름 작업 창

- **Semantic capability:** `view.pane_tag_names`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-033 — 문서 탭

- **Semantic capability:** `view.document_tabs`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-034 — 상황 선

- **Semantic capability:** `view.status_bar`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-035 — 가로 이동 막대

- **Semantic capability:** `view.horizontal_scroll`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-036 — 세로 이동 막대

- **Semantic capability:** `view.vertical_scroll`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-037 — 가로 눈금자

- **Semantic capability:** `view.horizontal_ruler`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-038 — 세로 눈금자

- **Semantic capability:** `view.vertical_ruler`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-039 — 편집 화면 나누지 않음

- **Semantic capability:** `view.split_none`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-040 — 가로로 나누기

- **Semantic capability:** `view.split_horizontal`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-041 — 세로로 나누기

- **Semantic capability:** `view.split_vertical`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-042 — 가로 세로 나누기

- **Semantic capability:** `view.split_both`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-043 — 창 가로 배열

- **Semantic capability:** `view.arrange_horizontal`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-044 — 창 세로 배열

- **Semantic capability:** `view.arrange_vertical`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-045 — 창 겹치게 배열

- **Semantic capability:** `view.arrange_cascade`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-046 — 모두 아이콘으로

- **Semantic capability:** `view.minimize_all`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## VIEW-047 — 열린 창 목록

- **Semantic capability:** `view.window_list`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `WorkstationViewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "enabled": {
      "type": "boolean"
    },
    "value": {},
    "persist_scope": {
      "enum": [
        "session",
        "user_profile"
      ]
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `WORKSTATION_SESSION_REQUIRED`, `WINDOW_NOT_FOUND`, `UI_CAPABILITY_UNAVAILABLE`, `SESSION_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

