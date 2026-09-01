# Capability Registry와 백엔드 라우팅

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Capability key

모든 사용자 기능은 안정된 이름을 갖는다. 예:

- `page.paper_preset`
- `page.column_config_equal`
- `table.merge_cells`
- `eq.insert_native`
- `ref.crossref_insert`
- `review.track_accept_one`
- `export.pdf`

공개 key는 한/글 메뉴명이나 HAction 이름과 분리한다.

## Registry record

각 record는 다음을 포함한다.

```yaml
capability_id: table.merge_cells
scope_class: artifact_semantics
support_level: HYBRID
preferred_backend: direct_hwpx
fallback_backends: [desktop_automation]
version_constraints:
  hancom_product: Hangul
  builds: [target-build-id]
operation_schema_ref: '#/$defs/TableMergeCells'
permissions: [document.write]
risk_flags: [layout_reflow]
bindings:
  direct_hwpx: {lowerer: table_merge_v2}
  desktop_automation: {registry_key: hwp2024.table.merge_cells}
validation: [semantic_reopen, hancom_open, render_diff]
fixtures: [tbl_merge_2x2, tbl_merge_nonrect_reject]
```

## 라우팅 알고리즘

1. 입력 operation을 JSON Schema로 검증한다.
2. 대상 artifact의 format, encryption, signatures, unknown parts, generator version을 inspect한다.
3. target Hancom build와 requested fidelity를 정한다.
4. 각 operation의 capability record를 조회한다.
5. 모든 operation을 한 backend transaction으로 처리할 수 있는지 계산한다.
6. 불가능하면 안전한 job DAG로 분할한다. 예: direct edit → Hancom normalize → oracle render.
7. signature invalidation, encryption, external links, macro/OLE 등 정책 위반을 평가한다.
8. dry-run에서 선택된 route, 예상 변경 part, 보존 수준, 위험, 검증 계획을 사용자에게 반환한다.
9. 승인 후 execution receipt를 만들고 immutable revision으로 commit한다.

## route 우선순위

1. deterministic하고 보존 가능한 `DirectHWPXBackend`.
2. 기능 의미는 직접 작성 가능하지만 layout 정규화가 필요하면 `HYBRID`.
3. proprietary 또는 app behavior가 필요한 `DesktopAutomationBackend`.
4. 기관이 WebHWP를 보유하고 그 API가 적합하면 `WebHWPBackend`.
5. 기능을 안전하게 수행할 수 없으면 실패하고 지원 수준을 보고한다.

## capability completeness lint

- 대상 도움말/Action catalog/ParameterSet catalog의 모든 항목이 registry source record에 연결돼야 한다.
- 모든 registry record는 schema, backend, phase, test, evidence 중 빈 값이 없어야 한다.
- runtime binding이 없는 `AUTOMATION_FULL` 항목은 GA blocker다.
- menu-only 기능은 `workstation_ui`로 등록하되 문서 artifact 기능과 분리한다.
