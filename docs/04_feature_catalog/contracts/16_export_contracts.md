# 인쇄·내보내기·접근성 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `인쇄·내보내기·접근성` 영역 34개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## EXPORT-001 — 인쇄 미리 보기

- **Semantic capability:** `export.print_preview`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `read_only`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `workstation.control` / `P12`
- **IR 위치:** `N/A`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-002 — 인쇄 범위

- **Semantic capability:** `export.print_range`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-003 — 부수·한 부씩 인쇄

- **Semantic capability:** `export.print_copies`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-004 — 양면 인쇄

- **Semantic capability:** `export.print_duplex`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-005 — 모아 찍기/N-up

- **Semantic capability:** `export.print_nup`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-006 — 용지에 맞춤·확대축소

- **Semantic capability:** `export.print_scaling`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-007 — 프린터 용지 공급

- **Semantic capability:** `export.print_paper_source`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-008 — 인쇄 워터마크

- **Semantic capability:** `export.print_watermark`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-009 — 메모/변경 내용 인쇄

- **Semantic capability:** `export.print_comments`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-010 — 개체 인쇄 여부

- **Semantic capability:** `export.print_object_visibility`
- **분류:** `external_service` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `external_side_effect`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `print.execute` / `P12`
- **IR 위치:** `PrintJob`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "printer_profile_id": {
      "type": "string"
    },
    "page_range": {
      "type": "string"
    },
    "copies": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9999
    },
    "duplex": {
      "enum": [
        "off",
        "long_edge",
        "short_edge"
      ]
    },
    "n_up": {
      "type": "integer",
      "minimum": 1,
      "maximum": 64
    },
    "scaling": {
      "type": "object",
      "additionalProperties": true
    },
    "watermark": {
      "type": "object",
      "additionalProperties": true
    },
    "spool_only": {
      "type": "boolean"
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-011 — PDF 내보내기

- **Semantic capability:** `export.export_pdf`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "pdf"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-012 — PDF 품질·글꼴·책갈피 옵션

- **Semantic capability:** `export.export_pdf_options`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "pdf_options"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-013 — 태그된 PDF 내보내기

- **Semantic capability:** `export.export_pdf_tagged`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "pdf_tagged"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-014 — 쪽별 이미지 내보내기

- **Semantic capability:** `export.export_page_images`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "page_images"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-015 — 선택 영역 이미지

- **Semantic capability:** `export.export_selection_image`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "selection_image"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-016 — 텍스트 내보내기

- **Semantic capability:** `export.export_text`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "text"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-017 — HTML 내보내기

- **Semantic capability:** `export.export_html`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "html"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-018 — XML 내보내기

- **Semantic capability:** `export.export_xml`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "xml"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-019 — RTF 내보내기

- **Semantic capability:** `export.export_rtf`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "rtf"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-020 — DOCX 내보내기

- **Semantic capability:** `export.export_docx`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "docx"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-021 — HWP 내보내기

- **Semantic capability:** `export.export_hwp`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "hwp"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-022 — HWPX 내보내기

- **Semantic capability:** `export.export_hwpx`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "hwpx"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-023 — 문서 제목 지정

- **Semantic capability:** `export.access_document_title`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-024 — 문서 기본 언어

- **Semantic capability:** `export.access_language`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-025 — 그림/개체 대체 텍스트

- **Semantic capability:** `export.access_alt_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-026 — 표 머리글 지정

- **Semantic capability:** `export.access_table_headers`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-027 — 읽기 순서

- **Semantic capability:** `export.access_reading_order`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-028 — 제목/개요 구조

- **Semantic capability:** `export.access_heading_structure`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-029 — 의미 있는 링크 텍스트

- **Semantic capability:** `export.access_link_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-030 — 색 대비 검사

- **Semantic capability:** `export.access_contrast_check`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-031 — 문서 접근성 검사

- **Semantic capability:** `export.access_document_checker`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-032 — DAISY 내보내기

- **Semantic capability:** `export.daisy_export`
- **분류:** `artifact_semantics` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_accessibility_review` — Execute the `manual_accessibility_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-033 — 점자 문서 변환

- **Semantic capability:** `export.braille_export`
- **분류:** `artifact_semantics` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "destination": {
      "type": "object",
      "additionalProperties": true
    },
    "printer_profile_id": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_contract` — Execute the `provider_contract` validator defined in the target profile and attach its evidence artifact.
- `manual_accessibility_review` — Execute the `manual_accessibility_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EXPORT-034 — 내보낸 파일 재열기·검증

- **Semantic capability:** `export.export_validation`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.export` / `P12`
- **IR 위치:** `ExportPlan/AccessibilityMetadata`
- **Selector:** `ExportOrPrintSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "format": {
      "const": "validation"
    },
    "page_range": {
      "type": "string"
    },
    "options": {
      "type": "object",
      "additionalProperties": true
    },
    "output_name": {
      "type": "string"
    },
    "loss_policy": {
      "enum": [
        "fail_on_loss",
        "report_loss",
        "best_effort_explicit"
      ]
    }
  },
  "required": [
    "format"
  ]
}
```

### 실행 절차

1. 원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.

**Desktop automation:** 한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `export_open` — Open the exported format with the designated validator and record loss report.
- `page_metrics` — Execute the `page_metrics` validator defined in the target profile and attach its evidence artifact.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- `accessibility_scan` — Execute the `accessibility_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `EXPORT_FORMAT_UNSUPPORTED`, `EXPORT_LOSS_POLICY_BLOCKED`, `PRINT_PROFILE_NOT_FOUND`, `EXPORT_REOPEN_FAILED`, `SPOOL_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P12`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

