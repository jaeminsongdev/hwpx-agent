# OperationPlan v2

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 목적

OperationPlan은 자연어 의도를 deterministic하고 검증 가능한 편집 transaction으로 바꾼다. public MCP는 이 plan을 직접 또는 간접 생성하며 backend 세부 action을 포함하지 않는다.

## 구조

```json
{
  "schema":"hwpx-agent.operation-plan/v2",
  "base_revision":"rev_...",
  "target_profile":"hangul-2024-build-x",
  "edit_mode":"surgical_preserve",
  "operations":[...],
  "preconditions":[...],
  "validation_plan":["package","semantic","hancom_open","render"],
  "failure_policy":"atomic",
  "idempotency_key":"..."
}
```

## selector

- `by_id`: stable logical node id.
- `by_bookmark` / `by_field_name` / `by_style`.
- `by_structural_path`: section/block/table/cell path.
- `by_text`: exact/regex with occurrence and context.
- `by_semantic_role`: title, question, answer, caption.
- `by_control_type`.
- `by_page_position`는 최후 수단이며 layout oracle가 필요.

selector는 0개 또는 다수 match일 때 기본 실패한다. `expected_matches`와 ambiguity policy를 명시한다.

## operation family

- document/metadata/settings.
- insert/delete/replace/move/wrap/copy.
- character/paragraph/style/numbering.
- page/section/column/header-footer/master/page number.
- table structure/style/formula.
- equation insert/replace/edit.
- image/shape/textbox/chart/OLE.
- field/form/note/reference.
- review/protection/accessibility.
- search/transform/import/merge.
- export/render/print are document mutation과 별도 job output.

## precondition

- node exists and type matches.
- text/style/property equals expected value.
- document not encrypted/signed or explicit override granted.
- required font/resource/capability available.
- current revision equals expected.

## dry-run output

resolved targets, capability route, backend DAG, touched parts, estimated pages, signature/protection impact, fallback/degradation, required confirmation, validation plan, cost/resource class를 반환한다.

## 원자성

`failure_policy=atomic`이 기본이다. `best_effort`는 서로 독립된 batch export 등에만 허용하고 각 operation result를 개별 표시한다.
