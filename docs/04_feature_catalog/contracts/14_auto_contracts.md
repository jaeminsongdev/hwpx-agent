# 스크립트·자동화·이벤트 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `스크립트·자동화·이벤트` 영역 25개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## AUTO-001 — HwpObject 생성·종료

- **Semantic capability:** `auto.hwpobject_lifecycle`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-002 — 오토메이션 문서 열기·저장

- **Semantic capability:** `auto.document_open_save`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-003 — allowlisted Action 실행

- **Semantic capability:** `auto.action_execute`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  },
  "required": [
    "binding_id",
    "parameters"
  ]
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-004 — ParameterSet 생성·검증

- **Semantic capability:** `auto.parameterset_build`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-005 — ParameterArray 생성·검증

- **Semantic capability:** `auto.parameterarray_build`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-006 — 커서 위치 읽기·이동

- **Semantic capability:** `auto.cursor_position`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-007 — 선택 범위 API

- **Semantic capability:** `auto.selection_api`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-008 — 본문 텍스트 추출

- **Semantic capability:** `auto.text_extract`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-009 — 컨트롤 열거

- **Semantic capability:** `auto.control_enumerate`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-010 — 컨트롤 속성 읽기·수정

- **Semantic capability:** `auto.control_properties`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-011 — 이벤트 핸들러 등록

- **Semantic capability:** `auto.event_subscribe`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-012 — 메시지/대화상자 정책

- **Semantic capability:** `auto.messagebox_policy`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-013 — 파일 경로 보안 승인 모듈

- **Semantic capability:** `auto.file_path_security`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-014 — 스크립트 매크로 정의

- **Semantic capability:** `auto.macro_define`
- **분류:** `editor_workflow` / `DISABLED_BY_POLICY` / 위험 `critical` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `macro.execute` / `P11`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "macro_id": {
      "type": "string"
    },
    "script": {
      "type": "string"
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Denied by default policy. Enabling requires a separate security ADR, tenant allowlist, and explicit confirmation.

### 검증·오류·완료 기준

- `policy_negative_test` — Execute the `policy_negative_test` validator defined in the target profile and attach its evidence artifact.
- `trusted_mode_e2e` — Execute the `trusted_mode_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-015 — 스크립트 매크로 중지

- **Semantic capability:** `auto.macro_stop`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-016 — 스크립트 매크로 실행

- **Semantic capability:** `auto.macro_run`
- **분류:** `editor_workflow` / `DISABLED_BY_POLICY` / 위험 `critical` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `macro.execute` / `P11`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "macro_id": {
      "type": "string"
    },
    "script": {
      "type": "string"
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Denied by default policy. Enabling requires a separate security ADR, tenant allowlist, and explicit confirmation.

### 검증·오류·완료 기준

- `policy_negative_test` — Execute the `policy_negative_test` validator defined in the target profile and attach its evidence artifact.
- `trusted_mode_e2e` — Execute the `trusted_mode_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-017 — 매크로 기록 기반 action 발견

- **Semantic capability:** `auto.macro_record_discovery`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-018 — 예상치 못한 modal 탐지

- **Semantic capability:** `auto.modal_watchdog`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-019 — 한/글 프로세스 회수·재시작

- **Semantic capability:** `auto.process_recycle`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-020 — 빌드별 기능 runtime probe

- **Semantic capability:** `auto.runtime_probe`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-021 — WebHWP HwpCtrl lifecycle

- **Semantic capability:** `auto.webhwp_ctrl`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `webhwp` → fallback `desktop_automation`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `webhwp_contract` — Execute the `webhwp_contract` validator defined in the target profile and attach its evidence artifact.
- `conformance` — Execute the `conformance` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-022 — WebHWP Action 실행

- **Semantic capability:** `auto.webhwp_action`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `webhwp` → fallback `desktop_automation`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `webhwp_contract` — Execute the `webhwp_contract` validator defined in the target profile and attach its evidence artifact.
- `conformance` — Execute the `conformance` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-023 — WebHWP 이벤트

- **Semantic capability:** `auto.webhwp_events`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `webhwp` → fallback `desktop_automation`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `webhwp_contract` — Execute the `webhwp_contract` validator defined in the target profile and attach its evidence artifact.
- `conformance` — Execute the `conformance` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-024 — 배치 자동화

- **Semantic capability:** `auto.batch_automation`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## AUTO-025 — action/parameter 실행 trace

- **Semantic capability:** `auto.automation_trace`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P10`
- **IR 위치:** `BackendExecutionRequest/CapabilityBinding`
- **Selector:** `AutomationSessionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "binding_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "additionalProperties": true
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300000
    },
    "expected_dialog_policy": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `worker_integration` — Execute the `worker_integration` validator defined in the target profile and attach its evidence artifact.
- `state_probe` — Execute the `state_probe` validator defined in the target profile and attach its evidence artifact.
- `timeout_recovery` — Execute the `timeout_recovery` validator defined in the target profile and attach its evidence artifact.
- **오류:** `AUTOMATION_BINDING_NOT_FOUND`, `AUTOMATION_PARAMETER_INVALID`, `AUTOMATION_TIMEOUT`, `AUTOMATION_MODAL_BLOCKED`, `AUTOMATION_PROCESS_CRASH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

