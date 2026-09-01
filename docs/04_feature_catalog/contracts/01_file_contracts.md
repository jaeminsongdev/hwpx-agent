# 파일·문서 수명주기 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `파일·문서 수명주기` 영역 41개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## FILE-001 — 빈 새 문서 만들기

- **Semantic capability:** `file.new_document`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-002 — 새 탭 만들기

- **Semantic capability:** `file.new_tab`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `workstation.control` / `P10`
- **IR 위치:** `N/A`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-003 — 문서마당/템플릿으로 새 문서

- **Semantic capability:** `file.new_from_template`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-004 — 문서 시작 도우미

- **Semantic capability:** `file.new_wizard`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `workstation.control` / `P10`
- **IR 위치:** `N/A`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-005 — HWPX 불러오기

- **Semantic capability:** `file.open_hwpx`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-006 — HWP 바이너리 불러오기

- **Semantic capability:** `file.open_hwp`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-007 — RTF·DOCX·TXT 등 지원 형식 불러오기

- **Semantic capability:** `file.open_other`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-008 — 파일 형식 자동 판별

- **Semantic capability:** `file.detect_format`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-009 — 현재 형식 저장

- **Semantic capability:** `file.save`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-010 — 다른 이름/형식으로 저장

- **Semantic capability:** `file.save_as`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-011 — 자동 저장·복구본 처리

- **Semantic capability:** `file.autosave_recovery`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `project_state_service`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `ProjectState/RecoveryPolicy`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `recovery_fixture` — Crash/restart the worker under a controlled fixture and verify recovery artifact selection.
- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-012 — 문서 닫기

- **Semantic capability:** `file.close_document`
- **분류:** `editor_workflow` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P10`
- **IR 위치:** `N/A`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `session_state_probe` — Read current workstation state through the target binding and compare requested value.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P10`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-013 — 문서 정보 읽기·수정

- **Semantic capability:** `file.document_info`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-014 — 사용자 정의 문서 속성

- **Semantic capability:** `file.document_properties`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-015 — 문서 끼워 넣기

- **Semantic capability:** `file.insert_document`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-016 — 여러 문서 병합

- **Semantic capability:** `file.merge_documents`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-017 — 문서 분할

- **Semantic capability:** `file.split_document`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-018 — 손상 HWPX 패키지 진단·복구

- **Semantic capability:** `file.package_repair`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-019 — XML 서식 만들기

- **Semantic capability:** `file.xml_form_create`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-020 — XML 서식마당

- **Semantic capability:** `file.xml_form_gallery`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-021 — XML 문서 불러오기

- **Semantic capability:** `file.xml_import`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-022 — XML 문서 저장하기

- **Semantic capability:** `file.xml_export`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-023 — PDF를 오피스 문서로 변환

- **Semantic capability:** `file.pdf_import`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-024 — 그림을 오피스 문서로 변환

- **Semantic capability:** `file.image_ocr_import`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-025 — PDF로 저장

- **Semantic capability:** `file.pdf_export`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-026 — 모바일 최적화 문서로 저장

- **Semantic capability:** `file.mobile_export`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-027 — 한컴독스 저장·연동

- **Semantic capability:** `file.hancom_docs`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-028 — DAISY로 저장

- **Semantic capability:** `file.daisy_export`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-029 — DAISY 스타일 가져오기

- **Semantic capability:** `file.daisy_style_import`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-030 — 문서 전체 점자로 변환

- **Semantic capability:** `file.braille_document`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-031 — 선택 글자 점자로 변환

- **Semantic capability:** `file.braille_selection`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-032 — 점자 변환 설정

- **Semantic capability:** `file.braille_settings`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external_service.use` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-033 — CCL 표시 넣기

- **Semantic capability:** `file.ccl_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-034 — 공공누리 표시 넣기

- **Semantic capability:** `file.kogl_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P04`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `schema` — Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-035 — 편지 보내기(본문)

- **Semantic capability:** `file.send_mail_body`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external.invoke` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-036 — 편지 보내기(첨부)

- **Semantic capability:** `file.send_mail_attachment`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external.invoke` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-037 — 웹 브라우저로 보내기

- **Semantic capability:** `file.send_browser`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `external_side_effect`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external.invoke` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-038 — 웹 서버로 올리기

- **Semantic capability:** `file.upload_web_server`
- **분류:** `external_service` / `OPTIONAL_EXTERNAL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `external_connector` → fallback `없음`
- **권한·단계:** `external.invoke` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-039 — 미리 보기

- **Semantic capability:** `file.preview`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `workstation.control` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-040 — 인쇄

- **Semantic capability:** `file.print`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P11`
- **IR 위치:** `PrintJob`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## FILE-041 — 일괄 형식 변환

- **Semantic capability:** `file.batch_convert`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DocumentGraph.metadata/settings`
- **Selector:** `DocumentOrProjectSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "input_artifact_id": {
      "type": "string"
    },
    "format": {
      "type": "string"
    },
    "output_name": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.

**Desktop automation:** 버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `export_open` — Open the exported format with the designated validator and record loss report.
- **오류:** `FILE_FORMAT_UNSUPPORTED`, `FILE_PACKAGE_INVALID`, `FILE_CONVERSION_LOSS`, `ARTIFACT_CHECKSUM_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

