# 검토·비교·이력 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `검토·비교·이력` 영역 20개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## REVIEW-001 — 변경 내용 추적 켜기/끄기

- **Semantic capability:** `review.track_enable`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-002 — 변경 내용 표시 설정

- **Semantic capability:** `review.track_display`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `workstation.control` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-003 — 검토자별 변경 필터

- **Semantic capability:** `review.track_filter_author`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `workstation.control` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-004 — 변경 내용 보호

- **Semantic capability:** `review.track_protect`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-005 — 선택 변경 내용 적용

- **Semantic capability:** `review.track_accept_one`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-006 — 선택 변경 내용 취소

- **Semantic capability:** `review.track_reject_one`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-007 — 모든 변경 적용

- **Semantic capability:** `review.track_accept_all`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-008 — 모든 변경 취소

- **Semantic capability:** `review.track_reject_all`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-009 — 검토자 이름 설정

- **Semantic capability:** `review.reviewer_name`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-010 — 문서 이력 관리

- **Semantic capability:** `review.document_history`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-011 — 문서 비교

- **Semantic capability:** `review.document_compare`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-012 — 비교 결과 병합

- **Semantic capability:** `review.document_merge_review`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-013 — 메모 작성자/시간

- **Semantic capability:** `review.comment_author`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-014 — 이전/다음 메모

- **Semantic capability:** `review.comment_navigation`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `workstation.control` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-015 — 메모 삭제

- **Semantic capability:** `review.comment_delete`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-016 — 모든 메모 삭제

- **Semantic capability:** `review.comment_delete_all`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-017 — 교정 부호 표시

- **Semantic capability:** `review.correction_marks_show`
- **분류:** `workstation_ui` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `session_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `workstation.control` / `P11`
- **IR 위치:** `N/A`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-018 — 검토 내역 보고서

- **Semantic capability:** `review.revision_export`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P11`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `change_readback` — Execute the `change_readback` validator defined in the target profile and attach its evidence artifact.
- `save_reopen` — Save in target Hancom, close, reopen, and compare semantic snapshot.
- `visual_diff` — Execute the `visual_diff` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-019 — 제품 semantic diff

- **Semantic capability:** `review.semantic_diff`
- **분류:** `artifact_semantics` / `DIRECT_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P04`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `diff_golden` — Execute the `diff_golden` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## REVIEW-020 — 제품 revision DAG

- **Semantic capability:** `review.revision_graph`
- **분류:** `artifact_semantics` / `DIRECT_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `direct_hwpx`
- **권한·단계:** `review.accept` / `P04`
- **IR 위치:** `ReviewState/ChangeSpan/CommentNode`
- **Selector:** `ReviewSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "action": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "note": {
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

1. ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** 공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.

**Desktop automation:** Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `diff_golden` — Execute the `diff_golden` validator defined in the target profile and attach its evidence artifact.
- **오류:** `REVIEW_ITEM_NOT_FOUND`, `REVIEW_STATE_CONFLICT`, `TRACKING_UNAVAILABLE`, `COMPARE_FAILED`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P04`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

