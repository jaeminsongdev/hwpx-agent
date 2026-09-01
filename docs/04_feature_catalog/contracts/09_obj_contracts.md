# 그림·도형·개체·차트 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `그림·도형·개체·차트` 영역 58개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## OBJ-001 — 도형 삽입

- **Semantic capability:** `obj.shape_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-002 — 그림 삽입

- **Semantic capability:** `obj.image_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "asset_ref"
  ],
  "properties": {
    "asset_ref": {
      "$ref": "artifact-ref.schema.json"
    },
    "link_mode": {
      "enum": [
        "embed",
        "link",
        "package_relationship"
      ]
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "alt_text": {
      "type": "string"
    },
    "mime_type": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-003 — 그리기마당 개체 삽입

- **Semantic capability:** `obj.drawing_gallery`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-004 — 스크린 샷 삽입

- **Semantic capability:** `obj.screenshot_insert`
- **분류:** `artifact_semantics` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_oracle` — Execute the `provider_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-005 — 그림에서 글자 가져오기

- **Semantic capability:** `obj.ocr_image_text`
- **분류:** `artifact_semantics` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_oracle` — Execute the `provider_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-006 — 차트 삽입

- **Semantic capability:** `obj.chart_insert`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-007 — 글상자 삽입

- **Semantic capability:** `obj.textbox_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-008 — 멀티미디어 삽입

- **Semantic capability:** `obj.multimedia_insert`
- **분류:** `artifact_semantics` / `OPTIONAL_EXTERNAL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `external_connector`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.

### 검증·오류·완료 기준

- `provider_oracle` — Execute the `provider_oracle` validator defined in the target profile and attach its evidence artifact.
- `manual_e2e` — Execute the `manual_e2e` validator defined in the target profile and attach its evidence artifact.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-009 — 글맵시 삽입

- **Semantic capability:** `obj.wordart_insert`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-010 — 그리기 개체 삽입

- **Semantic capability:** `obj.drawing_object_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-011 — OLE 개체 삽입

- **Semantic capability:** `obj.ole_insert`
- **분류:** `artifact_semantics` / `PRESERVE_ONLY` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "asset_ref"
  ],
  "properties": {
    "asset_ref": {
      "$ref": "artifact-ref.schema.json"
    },
    "link_mode": {
      "enum": [
        "embed",
        "link",
        "package_relationship"
      ]
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "alt_text": {
      "type": "string"
    },
    "mime_type": {
      "type": "string"
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Opaque data is retained byte/token-equivalently; creation or semantic editing is rejected.

### 검증·오류·완료 기준

- `binary_preservation` — Execute the `binary_preservation` validator defined in the target profile and attach its evidence artifact.
- `security_scan` — Execute the `security_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-012 — 양식 개체 삽입

- **Semantic capability:** `obj.form_object_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-013 — 개체 캡션 넣기

- **Semantic capability:** `obj.caption_insert`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-014 — 문단 띠 개체

- **Semantic capability:** `obj.paragraph_band_object`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-015 — 개체 위치

- **Semantic capability:** `obj.position`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-016 — 개체 크기

- **Semantic capability:** `obj.size`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-017 — 글자/문단/쪽 기준점

- **Semantic capability:** `obj.anchor`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-018 — 개체 주위 글 배치

- **Semantic capability:** `obj.wrap`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-019 — 개체 여백·캡션

- **Semantic capability:** `obj.margin_caption`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-020 — 선 모양·색·두께·화살표

- **Semantic capability:** `obj.line_style`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-021 — 단색 채우기

- **Semantic capability:** `obj.fill_solid`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-022 — 그라데이션 채우기

- **Semantic capability:** `obj.fill_gradient`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-023 — 무늬 채우기

- **Semantic capability:** `obj.fill_pattern`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-024 — 그림 채우기

- **Semantic capability:** `obj.fill_image`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-025 — 글상자 내부 여백·정렬

- **Semantic capability:** `obj.textbox_properties`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-026 — 개체 그림자

- **Semantic capability:** `obj.shadow`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-027 — 그림 반사

- **Semantic capability:** `obj.reflection`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-028 — 네온/광선

- **Semantic capability:** `obj.glow`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-029 — 옅은 테두리

- **Semantic capability:** `obj.soft_edge`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-030 — 그림 확대·축소·해상도

- **Semantic capability:** `obj.image_properties`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-031 — 그림 자르기

- **Semantic capability:** `obj.crop`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-032 — 개체 회전

- **Semantic capability:** `obj.rotate`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-033 — 개체 뒤집기

- **Semantic capability:** `obj.flip`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-034 — 투명도

- **Semantic capability:** `obj.transparency`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "x_mm": {
      "type": "number"
    },
    "y_mm": {
      "type": "number"
    },
    "width_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "height_mm": {
      "type": "number",
      "exclusiveMinimum": 0
    },
    "rotation_deg": {
      "type": "number"
    },
    "anchor": {
      "enum": [
        "character",
        "paragraph",
        "page",
        "section"
      ]
    },
    "wrap": {
      "type": "string"
    },
    "crop": {
      "type": "object",
      "additionalProperties": true
    },
    "opacity": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "minProperties": 1
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-035 — 밝기·대비·색조 보정

- **Semantic capability:** `obj.color_adjust`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-036 — 개체 묶기

- **Semantic capability:** `obj.group`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-037 — 개체 풀기

- **Semantic capability:** `obj.ungroup`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-038 — 맨 앞/뒤·앞/뒤로

- **Semantic capability:** `obj.z_order`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-039 — 개체 맞춤

- **Semantic capability:** `obj.align`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-040 — 개체 간격 동일하게

- **Semantic capability:** `obj.distribute`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-041 — 연결선

- **Semantic capability:** `obj.connector`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-042 — 자유형 도형

- **Semantic capability:** `obj.freeform`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-043 — 도형 점 편집

- **Semantic capability:** `obj.shape_edit_points`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-044 — 가로세로 비율 유지

- **Semantic capability:** `obj.aspect_lock`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

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

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-045 — 개체 보호

- **Semantic capability:** `obj.object_protect`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

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

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-046 — 인쇄 여부

- **Semantic capability:** `obj.printable`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

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

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-047 — 대체 텍스트

- **Semantic capability:** `obj.alt_text`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-048 — 개체 하이퍼링크

- **Semantic capability:** `obj.object_hyperlink`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P08`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `resource_integrity` — Execute the `resource_integrity` validator defined in the target profile and attach its evidence artifact.
- `semantic_reopen` — Reparse output into DocumentGraph and compare requested postconditions.
- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `object_bounds` — Execute the `object_bounds` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P08`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-049 — 차트 종류

- **Semantic capability:** `obj.chart_type`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-050 — 차트 데이터

- **Semantic capability:** `obj.chart_data`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-051 — 계열 설정

- **Semantic capability:** `obj.chart_series`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-052 — 축 설정

- **Semantic capability:** `obj.chart_axis`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-053 — 범례

- **Semantic capability:** `obj.chart_legend`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-054 — 데이터 레이블

- **Semantic capability:** `obj.chart_labels`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-055 — 차트 제목

- **Semantic capability:** `obj.chart_title`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-056 — 차트 스타일

- **Semantic capability:** `obj.chart_style`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-057 — OLE 속성

- **Semantic capability:** `obj.ole_properties`
- **분류:** `artifact_semantics` / `PRESERVE_ONLY` / 위험 `high` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `없음`
- **권한·단계:** `automation.use` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Opaque data is retained byte/token-equivalently; creation or semantic editing is rejected.

### 검증·오류·완료 기준

- `binary_preservation` — Execute the `binary_preservation` validator defined in the target profile and attach its evidence artifact.
- `security_scan` — Execute the `security_scan` validator defined in the target profile and attach its evidence artifact.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## OBJ-058 — 글맵시 속성

- **Semantic capability:** `obj.wordart_properties`
- **분류:** `artifact_semantics` / `AUTOMATION_FULL` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `desktop_automation` → fallback `direct_hwpx`
- **권한·단계:** `document.write` / `P11`
- **IR 위치:** `DrawingNode/ImageNode/ShapeNode/TextBoxNode/ChartNode/EmbeddedObjectNode`
- **Selector:** `ObjectOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "asset_ref": {
      "type": "object",
      "additionalProperties": true
    },
    "geometry": {
      "type": "object",
      "additionalProperties": true
    },
    "properties": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.

**Desktop automation:** Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.

**Fallback:** Requires an available target-matched licensed worker; no semantic approximation by the direct backend.

### 검증·오류·완료 기준

- `hancom_open` — Open the artifact in the target Hancom build and record success/error evidence.
- `property_readback` — Execute the `property_readback` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `OBJECT_NOT_FOUND`, `ASSET_UNSUPPORTED`, `OBJECT_GEOMETRY_INVALID`, `RELATIONSHIP_BROKEN`, `RENDER_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P11`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

