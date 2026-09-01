# 보안·보호·개인정보 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `보안·보호·개인정보` 영역 24개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## SEC-001 — 문서 열기 암호 설정

- **Semantic capability:** `sec.open_password_set`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-002 — 문서 암호 변경

- **Semantic capability:** `sec.open_password_change`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-003 — 문서 암호 해제

- **Semantic capability:** `sec.open_password_remove`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-004 — 배포용 문서로 저장

- **Semantic capability:** `sec.distribution_save`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-005 — 배포용 문서 편집

- **Semantic capability:** `sec.distribution_edit`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-006 — 배포용 문서 암호 변경/해제

- **Semantic capability:** `sec.distribution_password`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-007 — 선택 글자 보호

- **Semantic capability:** `sec.protect_selection`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-008 — 개인정보 찾아서 보호

- **Semantic capability:** `sec.privacy_find_protect`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-009 — 개인정보 보호 해제

- **Semantic capability:** `sec.privacy_unprotect`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-010 — 개인정보 보호 암호 변경

- **Semantic capability:** `sec.privacy_password_change`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-011 — 문서 보안 설정

- **Semantic capability:** `sec.document_security_settings`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-012 — 편집 제한

- **Semantic capability:** `sec.edit_restriction`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-013 — 개체 보호

- **Semantic capability:** `sec.object_protection`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-014 — 양식 입력만 허용

- **Semantic capability:** `sec.form_protection`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-015 — 전자서명 상태 확인

- **Semantic capability:** `sec.signature_inspect`
- **분류:** `security_control` / `READ_ONLY` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.read` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Inspection only. Any mutation request is rejected.

### 검증·오류·완료 기준

- `signature_state` — Execute the `signature_state` validator defined in the target profile and attach its evidence artifact.
- `policy` — Execute the `policy` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-016 — 수정 시 서명 무효화 경고

- **Semantic capability:** `sec.signature_invalidation`
- **분류:** `security_control` / `READ_ONLY` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.read` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Inspection only. Any mutation request is rejected.

### 검증·오류·완료 기준

- `signature_state` — Execute the `signature_state` validator defined in the target profile and attach its evidence artifact.
- `policy` — Execute the `policy` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-017 — 승인된 외부 서명 연동

- **Semantic capability:** `sec.digital_sign`
- **분류:** `security_control` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `external_signing_service` → fallback `없음`
- **권한·단계:** `security.modify` / `P19`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `signature_verify` — Execute the `signature_verify` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P19`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-018 — 개인정보/메타데이터 제거

- **Semantic capability:** `sec.sanitize_metadata`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-019 — 스크립트 매크로 보안 설정

- **Semantic capability:** `sec.macro_security`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-020 — 외부 링크 차단/허용 정책

- **Semantic capability:** `sec.external_link_policy`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-021 — 암호 문서 열기

- **Semantic capability:** `sec.encrypted_open`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-022 — 보호 상태 유지 복제

- **Semantic capability:** `sec.protected_copy`
- **분류:** `security_control` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `security.modify` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `negative_auth` — Execute the `negative_auth` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `protection_state` — Execute the `protection_state` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-023 — 문서 보안 요소 감사

- **Semantic capability:** `sec.security_audit`
- **분류:** `security_control` / `READ_ONLY` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.read` / `P11`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string"
    },
    "policy_id": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "confirmation_token": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.

**Desktop automation:** 보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.

**Fallback:** Inspection only. Any mutation request is rejected.

### 검증·오류·완료 기준

- `signature_state` — Execute the `signature_state` validator defined in the target profile and attach its evidence artifact.
- `policy` — Execute the `policy` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEC-024 — 암호·보호 우회

- **Semantic capability:** `sec.password_bypass`
- **분류:** `security_control` / `UNSUPPORTED` / 위험 `critical` / 변경성 `artifact_mutation`
- **기본 경로:** `` → fallback `없음`
- **권한·단계:** `security.modify` / `N/A`
- **IR 위치:** `SecurityState/ProtectionSpan`
- **Selector:** `SecurityTargetSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "secret_ref": {
      "type": "string",
      "description": "Secret manager reference; plaintext secrets are forbidden."
    },
    "protection_policy": {
      "type": "object",
      "additionalProperties": true
    },
    "allow_copy": {
      "type": "boolean"
    },
    "allow_print": {
      "type": "boolean"
    },
    "confirmation_token": {
      "type": "string"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Return CAPABILITY_UNSUPPORTED with target-profile evidence; do not approximate.

### 검증·오류·완료 기준

- `policy_negative_test` — Execute the `policy_negative_test` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SECURITY_POLICY_DENIED`, `SECRET_REFERENCE_INVALID`, `PROTECTED_DOCUMENT`, `SIGNATURE_WOULD_INVALIDATE`, `SECURITY_STATE_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `N/A`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

