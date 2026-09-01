# 대표 OperationPlan 예제

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## A3 가로 시험지와 2단 설정

```json
{
  "schema_version":"hwpx-agent.operation-plan/v2",
  "mode":"normalized_authoring",
  "operations":[
    {"op_id":"op-1","capability_id":"page.paper_preset","selector":{"section_ids":["sec-1"]},"args":{"preset":"A3","orientation":"landscape"}},
    {"op_id":"op-2","depends_on":["op-1"],"capability_id":"page.margin_all","selector":{"section_ids":["sec-1"]},"args":{"top":{"value":12,"unit":"mm"},"bottom":{"value":12,"unit":"mm"},"left":{"value":14,"unit":"mm"},"right":{"value":14,"unit":"mm"}}},
    {"op_id":"op-3","depends_on":["op-2"],"capability_id":"page.column_config_equal","selector":{"section_ids":["sec-1"]},"args":{"count":2,"equal_width":true,"gap":{"value":8,"unit":"mm"},"separator":"none"}}
  ],
  "postconditions":["layout.no_overflow","hancom.open","render.pages"]
}
```

## 6×8 표 생성, 셀 병합, 너비 지정

```json
{
  "operations":[
    {"op_id":"t1","capability_id":"table.create","selector":{"after_node_id":"p-10"},"args":{"rows":6,"columns":8,"width_mode":"explicit","column_widths_mm":[15,15,20,20,20,20,15,15],"logical_id":"tbl-score"}},
    {"op_id":"t2","depends_on":["t1"],"capability_id":"table.merge_cells","selector":{"table_id":"tbl-score","rect":{"r1":0,"c1":0,"r2":0,"c2":7}},"args":{}},
    {"op_id":"t3","depends_on":["t2"],"capability_id":"table.cell_border","selector":{"table_id":"tbl-score","range":"A1:H6"},"args":{"border":{"style":"solid","width_pt":0.4}}},
    {"op_id":"t4","depends_on":["t3"],"capability_id":"table.cell_padding","selector":{"table_id":"tbl-score","range":"A1:H6"},"args":{"padding_mm":1.5}}
  ]
}
```

## 편집 가능한 native 수식

```json
{
  "operations":[
    {
      "op_id":"e1",
      "capability_id":"eq.insert_native",
      "selector":{"paragraph_id":"q-17-body","offset":24},
      "args":{
        "display":"inline",
        "source":{"kind":"latex","value":"\\lim_{x\\to 0} \frac{\sin x}{x}=1"},
        "fallback":"fail_closed",
        "logical_id":"eq-q17-1"
      }
    }
  ],
  "postconditions":["equation.native_object","equation.semantic_roundtrip","hancom.equation_editor_smoke"]
}
```

## 학교 템플릿의 이름·날짜만 채우기

```json
{
  "mode":"surgical_preserve",
  "template_contract_id":"tpl-contract-2026-001",
  "operations":[
    {"op_id":"f1","capability_id":"ref.field_user","selector":{"field_name":"student_name"},"args":{"value":"홍길동"}},
    {"op_id":"f2","capability_id":"ref.field_date_time","selector":{"field_name":"exam_date"},"args":{"value":"2026-09-01","format":"yyyy. M. d."}}
  ],
  "preservation":{"untouched_parts":"byte_preserve","unknown_xml":"preserve","styles":"no_gc"}
}
```

## 기존 문서의 모든 본문 글꼴 바꾸기

먼저 `document_inspect(styles)`로 font slots와 적용 범위를 확인한 뒤 `document_plan`이 언어별 font slot을 명시한다. 단순 문자열 치환으로 font table을 바꾸면 수식·개체·외국어 슬롯을 손상할 수 있으므로 금지한다.

## 안전한 실패 예

- target build에서 `chart.3d_wall` binding이 검증되지 않음 → `CAPABILITY_UNVERIFIED_FOR_TARGET`.
- 암호 문서인데 password credential 없음 → `DOCUMENT_CREDENTIAL_REQUIRED`.
- 수식 parser가 지원하지 않는 LaTeX macro → `EQUATION_LATEX_UNSUPPORTED`.
- 병합 셀 범위가 비직사각형 → `TABLE_MERGE_RANGE_INVALID`.
- 서명된 문서 수정이 서명을 무효화함 → dry-run 경고 후 명시적 `allow_signature_invalidation=true` 필요.
