# 찾기·치환·텍스트 변환 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `찾기·치환·텍스트 변환` 영역 25개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## SEARCH-001 — 일반 문자열 찾기

- **Semantic capability:** `search.find_literal`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "include_hidden": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-002 — 정규식 찾기

- **Semantic capability:** `search.find_regex`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "include_hidden": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-003 — 글자/문단 모양 조건 찾기

- **Semantic capability:** `search.find_style`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "include_hidden": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-004 — 개체/필드/조판 부호 찾기

- **Semantic capability:** `search.find_control`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "include_hidden": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-005 — 다시 찾기

- **Semantic capability:** `search.find_next`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "include_hidden": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-006 — 문자열 찾아 바꾸기

- **Semantic capability:** `search.replace_literal`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "replacement"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_replacements": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "preview_only": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-007 — 정규식 찾아 바꾸기

- **Semantic capability:** `search.replace_regex`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "replacement"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_replacements": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "preview_only": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-008 — 서식 찾아 바꾸기

- **Semantic capability:** `search.replace_style`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "replacement"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_replacements": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "preview_only": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-009 — 특정 컨트롤 치환

- **Semantic capability:** `search.replace_control`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "replacement"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_replacements": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "preview_only": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-010 — 쪽/구역/문단/개체 찾아가기

- **Semantic capability:** `search.find_by_page`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "include_hidden": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-011 — 한글을 한자로 바꾸기

- **Semantic capability:** `search.convert_hanja`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `language_oracle` — Execute the `language_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_review` — Execute the `manual_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-012 — 한자를 한글로 바꾸기

- **Semantic capability:** `search.convert_hangul`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `language_oracle` — Execute the `language_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_review` — Execute the `manual_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-013 — 대문자/소문자 바꾸기

- **Semantic capability:** `search.case_convert`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-014 — 전각/반각 바꾸기

- **Semantic capability:** `search.full_half_width`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-015 — 일어 바꾸기

- **Semantic capability:** `search.japanese_convert`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `language_oracle` — Execute the `language_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_review` — Execute the `manual_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-016 — 간체/번체 바꾸기

- **Semantic capability:** `search.simplified_traditional`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `language_oracle` — Execute the `language_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_review` — Execute the `manual_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-017 — 로마자로 바꾸기

- **Semantic capability:** `search.romanize`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `language_oracle` — Execute the `language_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_review` — Execute the `manual_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-018 — 외래어 표기 변환

- **Semantic capability:** `search.foreign_word_notation`
- **분류:** `editor_workflow` / `OPTIONAL_EXTERNAL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `language_oracle` — Execute the `language_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_review` — Execute the `manual_review` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-019 — 개인정보 바로 바꾸기

- **Semantic capability:** `search.personal_info_replace_direct`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-020 — 개인정보 찾아서 바꾸기

- **Semantic capability:** `search.personal_info_find_replace`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-021 — 텍스트/문단 정렬

- **Semantic capability:** `search.sort_text`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-022 — Unicode 정규화

- **Semantic capability:** `search.normalize_unicode`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-023 — 공백·탭·줄바꿈 정규화

- **Semantic capability:** `search.normalize_whitespace`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "query": {
      "type": "string"
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "direction": {
      "enum": [
        "forward",
        "backward",
        "all"
      ]
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-024 — 폰트 일괄 대체

- **Semantic capability:** `search.replace_fonts`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "replacement"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_replacements": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "preview_only": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## SEARCH-025 — 스타일 일괄 대체

- **Semantic capability:** `search.replace_styles`
- **분류:** `editor_workflow` / `DIRECT_FULL` / 위험 `low` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P09`
- **IR 위치:** `OperationPlan/SearchSelector`
- **Selector:** `SearchScopeSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "query",
    "replacement"
  ],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "replacement": {
      "type": "string"
    },
    "regex": {
      "type": "boolean"
    },
    "case_sensitive": {
      "type": "boolean"
    },
    "whole_word": {
      "type": "boolean"
    },
    "style_filter": {
      "type": "object",
      "additionalProperties": true
    },
    "max_replacements": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100000
    },
    "preview_only": {
      "type": "boolean"
    }
  }
}
```

### 실행 절차

1. 정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.

**Desktop automation:** 한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.

**Fallback:** No implicit automation dependency. Fail if direct capability preconditions are not met.

### 검증·오류·완료 기준

- `match_set` — Execute the `match_set` validator defined in the target profile and attach its evidence artifact.
- `semantic_diff` — Execute the `semantic_diff` validator defined in the target profile and attach its evidence artifact.
- `reopen` — Execute the `reopen` validator defined in the target profile and attach its evidence artifact.
- **오류:** `SEARCH_PATTERN_INVALID`, `SEARCH_SCOPE_INVALID`, `REPLACEMENT_LIMIT_EXCEEDED`, `RANGE_STALE`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P09`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

