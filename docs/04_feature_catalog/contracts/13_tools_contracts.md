# 도구·언어·외부 서비스 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `도구·언어·외부 서비스` 영역 23개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## TOOLS-001 — 맞춤법 검사

- **Semantic capability:** `tools.spellcheck`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "source_locale": {
      "type": "string"
    },
    "target_locale": {
      "type": "string"
    },
    "mode": {
      "type": "string"
    },
    "consent_token": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "provider"
  ]
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-002 — 문법/문장 교정

- **Semantic capability:** `tools.grammarcheck`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "source_locale": {
      "type": "string"
    },
    "target_locale": {
      "type": "string"
    },
    "mode": {
      "type": "string"
    },
    "consent_token": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "provider"
  ]
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-003 — 한컴 사전

- **Semantic capability:** `tools.dictionary_hancom`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "source_locale": {
      "type": "string"
    },
    "target_locale": {
      "type": "string"
    },
    "mode": {
      "type": "string"
    },
    "consent_token": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "provider"
  ]
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-004 — 한자 사전

- **Semantic capability:** `tools.dictionary_hanja`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "source_locale": {
      "type": "string"
    },
    "target_locale": {
      "type": "string"
    },
    "mode": {
      "type": "string"
    },
    "consent_token": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "provider"
  ]
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-005 — 유의어/반의어 사전

- **Semantic capability:** `tools.dictionary_thesaurus`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "source_locale": {
      "type": "string"
    },
    "target_locale": {
      "type": "string"
    },
    "mode": {
      "type": "string"
    },
    "consent_token": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "provider"
  ]
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-006 — 번역

- **Semantic capability:** `tools.translation`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "source_locale": {
      "type": "string"
    },
    "target_locale": {
      "type": "string"
    },
    "mode": {
      "type": "string"
    },
    "consent_token": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "required": [
    "provider"
  ]
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-007 — 빠른 교정 내용 관리

- **Semantic capability:** `tools.quick_correct_content`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-008 — 빠른 교정 동작

- **Semantic capability:** `tools.quick_correct_behavior`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-009 — 입력어 자동 실행

- **Semantic capability:** `tools.input_auto_execute`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-010 — 빠른 교정 효과음

- **Semantic capability:** `tools.quick_correct_sound`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-011 — 한컴 애셋

- **Semantic capability:** `tools.hancom_assets`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-012 — 문서 찾기

- **Semantic capability:** `tools.document_search`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_or_ui_probe` — Execute the `provider_or_ui_probe` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-013 — 프레젠테이션 실행

- **Semantic capability:** `tools.presentation_run`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-014 — 프레젠테이션 설정

- **Semantic capability:** `tools.presentation_settings`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-015 — 프레젠테이션 범위

- **Semantic capability:** `tools.presentation_range`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-016 — 글자판 바꾸기

- **Semantic capability:** `tools.keyboard_change`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-017 — 글자판 보기

- **Semantic capability:** `tools.keyboard_view`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-018 — 언어 선택 사항

- **Semantic capability:** `tools.language_options`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-019 — 글자판 자동 변경

- **Semantic capability:** `tools.keyboard_auto_change`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-020 — COM 추가 기능 설정

- **Semantic capability:** `tools.com_addins`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-021 — 사용자 설정

- **Semantic capability:** `tools.customize_ui`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-022 — 환경 설정

- **Semantic capability:** `tools.preferences`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## TOOLS-023 — 스킨 설정

- **Semantic capability:** `tools.skin`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ToolSessionOrDocumentSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "provider": {
      "type": "string"
    },
    "locale": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "consent_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `workstation_state_probe` — Execute the `workstation_state_probe` validator defined in the target profile and attach its evidence artifact.
- **오류:** `PROVIDER_UNAVAILABLE`, `CONSENT_REQUIRED`, `LOCALE_UNSUPPORTED`, `EXTERNAL_RESULT_UNVERIFIED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

