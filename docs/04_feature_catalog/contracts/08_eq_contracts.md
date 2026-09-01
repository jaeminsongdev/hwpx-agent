# 수식 — 기능별 구현 계약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 문서는 `수식` 영역 34개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.

## EQ-001 — native 한컴 수식 삽입

- **Semantic capability:** `eq.insert_native`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source"
  ],
  "properties": {
    "source": {
      "oneOf": [
        {
          "type": "object",
          "required": [
            "latex"
          ],
          "properties": {
            "latex": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "mathml"
          ],
          "properties": {
            "mathml": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "eqedit"
          ],
          "properties": {
            "eqedit": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "ast"
          ],
          "properties": {
            "ast": {
              "type": "object",
              "additionalProperties": true
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "display": {
      "enum": [
        "inline",
        "block"
      ]
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "unsupported_policy": {
      "const": "fail_closed"
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-002 — 기존 native 수식 편집

- **Semantic capability:** `eq.edit_native`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source"
  ],
  "properties": {
    "source": {
      "oneOf": [
        {
          "type": "object",
          "required": [
            "latex"
          ],
          "properties": {
            "latex": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "mathml"
          ],
          "properties": {
            "mathml": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "eqedit"
          ],
          "properties": {
            "eqedit": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "ast"
          ],
          "properties": {
            "ast": {
              "type": "object",
              "additionalProperties": true
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "display": {
      "enum": [
        "inline",
        "block"
      ]
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "unsupported_policy": {
      "const": "fail_closed"
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-003 — LaTeX 입력

- **Semantic capability:** `eq.latex_input`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source"
  ],
  "properties": {
    "source": {
      "oneOf": [
        {
          "type": "object",
          "required": [
            "latex"
          ],
          "properties": {
            "latex": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "mathml"
          ],
          "properties": {
            "mathml": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "eqedit"
          ],
          "properties": {
            "eqedit": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "ast"
          ],
          "properties": {
            "ast": {
              "type": "object",
              "additionalProperties": true
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "display": {
      "enum": [
        "inline",
        "block"
      ]
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "unsupported_policy": {
      "const": "fail_closed"
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-004 — MathML 입력

- **Semantic capability:** `eq.mathml_input`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source"
  ],
  "properties": {
    "source": {
      "oneOf": [
        {
          "type": "object",
          "required": [
            "latex"
          ],
          "properties": {
            "latex": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "mathml"
          ],
          "properties": {
            "mathml": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "eqedit"
          ],
          "properties": {
            "eqedit": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "ast"
          ],
          "properties": {
            "ast": {
              "type": "object",
              "additionalProperties": true
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "display": {
      "enum": [
        "inline",
        "block"
      ]
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "unsupported_policy": {
      "const": "fail_closed"
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-005 — EqEdit 원문 입력

- **Semantic capability:** `eq.eqedit_input`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source"
  ],
  "properties": {
    "source": {
      "oneOf": [
        {
          "type": "object",
          "required": [
            "latex"
          ],
          "properties": {
            "latex": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "mathml"
          ],
          "properties": {
            "mathml": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "eqedit"
          ],
          "properties": {
            "eqedit": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "ast"
          ],
          "properties": {
            "ast": {
              "type": "object",
              "additionalProperties": true
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "display": {
      "enum": [
        "inline",
        "block"
      ]
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "unsupported_policy": {
      "const": "fail_closed"
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-006 — Math AST 입력

- **Semantic capability:** `eq.ast_input`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source"
  ],
  "properties": {
    "source": {
      "oneOf": [
        {
          "type": "object",
          "required": [
            "latex"
          ],
          "properties": {
            "latex": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "mathml"
          ],
          "properties": {
            "mathml": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "eqedit"
          ],
          "properties": {
            "eqedit": {
              "type": "string"
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "required": [
            "ast"
          ],
          "properties": {
            "ast": {
              "type": "object",
              "additionalProperties": true
            }
          },
          "additionalProperties": false
        }
      ]
    },
    "display": {
      "enum": [
        "inline",
        "block"
      ]
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "unsupported_policy": {
      "const": "fail_closed"
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-007 — 인라인 수식

- **Semantic capability:** `eq.inline`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-008 — 독립 수식

- **Semantic capability:** `eq.display`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-009 — 분수·중첩 분수

- **Semantic capability:** `eq.fraction`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-010 — 지수·아래첨자

- **Semantic capability:** `eq.power_subscript`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-011 — 제곱근·n제곱근

- **Semantic capability:** `eq.root`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-012 — 괄호·절댓값·노름

- **Semantic capability:** `eq.delimiter`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-013 — 등식·부등식·관계

- **Semantic capability:** `eq.relation`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-014 — 극한

- **Semantic capability:** `eq.limit`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-015 — 미분 표기

- **Semantic capability:** `eq.derivative`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-016 — 정적분·부정적분·다중적분

- **Semantic capability:** `eq.integral`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-017 — 합·곱 기호

- **Semantic capability:** `eq.sum_product`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-018 — 삼각·로그·지수 함수

- **Semantic capability:** `eq.function`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-019 — 그리스 문자·기호

- **Semantic capability:** `eq.greek_symbols`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-020 — 벡터·윗기호

- **Semantic capability:** `eq.vector_accent`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-021 — 행렬·행렬식

- **Semantic capability:** `eq.matrix`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-022 — 경우 나누기

- **Semantic capability:** `eq.cases`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-023 — 여러 줄 정렬

- **Semantic capability:** `eq.aligned`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-024 — 이항계수·조합

- **Semantic capability:** `eq.binomial`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-025 — 집합·논리식

- **Semantic capability:** `eq.sets_logic`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-026 — 수식 안 텍스트

- **Semantic capability:** `eq.text_in_math`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-027 — 수식 글꼴·크기

- **Semantic capability:** `eq.font_size`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-028 — 수식 색

- **Semantic capability:** `eq.color`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-029 — 인라인 기준선

- **Semantic capability:** `eq.baseline`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-030 — 수식 개체 크기·여백

- **Semantic capability:** `eq.object_size`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-031 — 수식 캡션·번호

- **Semantic capability:** `eq.caption_number`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ast_fragment"
  ],
  "properties": {
    "ast_fragment": {
      "type": "object",
      "additionalProperties": true
    },
    "replace_target_path": {
      "type": "string"
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-032 — EqEdit readback·semantic 비교

- **Semantic capability:** `eq.roundtrip_readback`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `read_only`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source": {
      "type": "object",
      "additionalProperties": true
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "layout": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-033 — 수식 편집기 재편집 smoke

- **Semantic capability:** `eq.editor_smoke`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source": {
      "type": "object",
      "additionalProperties": true
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "layout": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

## EQ-034 — legacy EqEdit script 보존

- **Semantic capability:** `eq.legacy_script_preserve`
- **분류:** `artifact_semantics` / `HYBRID` / 위험 `medium` / 변경성 `artifact_mutation`
- **기본 경로:** `direct_hwpx` → fallback `desktop_automation`
- **권한·단계:** `document.write` / `P07`
- **IR 위치:** `EquationNode/MathAst`
- **Selector:** `EquationOrInsertionSelector`

### 입력 계약

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source": {
      "type": "object",
      "additionalProperties": true
    },
    "style": {
      "type": "object",
      "additionalProperties": true
    },
    "layout": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### 실행 절차

1. 입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.
2. Create an isolated working copy or session; never mutate the source artifact in place.
3. Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.
4. Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.

**Direct HWPX:** native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.

**Desktop automation:** EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.

**Fallback:** Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.

### 검증·오류·완료 기준

- `native_object` — Execute the `native_object` validator defined in the target profile and attach its evidence artifact.
- `eqedit_readback` — Execute the `eqedit_readback` validator defined in the target profile and attach its evidence artifact.
- `semantic_compare` — Execute the `semantic_compare` validator defined in the target profile and attach its evidence artifact.
- `hancom_editor_smoke` — Execute the `hancom_editor_smoke` validator defined in the target profile and attach its evidence artifact.
- `render_diff` — Render affected pages and compare geometry/text/object diff within the feature threshold.
- **오류:** `EQUATION_SOURCE_AMBIGUOUS`, `EQUATION_LATEX_UNSUPPORTED`, `EQEDIT_COMPILE_FAILED`, `NATIVE_EQUATION_READBACK_MISMATCH`, `CAPABILITY_UNAVAILABLE_FOR_TARGET`, `PERMISSION_DENIED`, `REVISION_CONFLICT`, `VALIDATION_FAILED`
- **릴리스:** `P07`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.

