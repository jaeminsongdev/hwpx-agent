# HWPX Agent 통합 구현 플레이북

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

이 파일은 v2 문서 세트를 실제 구현 순서로 압축한 실행 지침이다. 세부 타입·기능·테스트는 링크된 문서를 normative source로 사용한다.

## 1. 최종 제품의 정의

동일한 remote project를 ChatGPT Web과 Codex가 열고, 자연어 요청을 versioned `OperationPlan`으로 변환하여 HWPX를 생성·편집·검증·내보낸다. 표, exact 문서 크기/여백/구역/다단, native 수식은 초기 수직 슬라이스의 필수 기능이다. 장기적으로 한/글 대상 build의 모든 기능을 capability registry에서 누락 없이 분류하고, 직접 HWPX·Windows Automation·WebHWP·외부 provider 중 검증된 경로로 실행한다.

## 2. Source of Truth 순서

1. `target-profile.yaml`, `source-lock.json`, signed capability registry.
2. JSON Schema/protobuf contracts.
3. `DocumentGraph` + `OperationPlan` + immutable revision.
4. backend receipts와 validation evidence.
5. `FEATURE_COVERAGE_MATRIX.csv`, WBS, ADR, handoff.
6. 채팅 기록과 UI local state는 source of truth가 아니다.

## 3. v1에서 바뀐 핵심

- Python authoring 우선이 아니라 Rust direct HWPX + C#/.NET Windows worker의 capability-driven 구조다.
- “문단/표/그림/수식 일부”가 아니라 16개 영역 609개 baseline 기능과 609개 구현 계약을 둔다.
- “HWPX가 열림”이 아니라 semantic readback, 실제 한/글 open/save/reopen, render/export evidence를 구분한다.
- roadmap은 P00~P20, 실행 task는 `WORK_BREAKDOWN_STRUCTURE.csv`의 190개다.

## 4. 읽기 순서

1. `EXECUTIVE_REVIEW_AND_DELTA.md`
2. `docs/02_architecture/01_system_architecture.md`
3. `docs/02_architecture/02_capability_routing.md`
4. `docs/03_document_model/01_document_graph_ir.md`
5. `docs/03_document_model/11_operation_plan.md`
6. `docs/12_implementation_guides/03_hwpx_package_and_preserving_editor.md`
7. `docs/12_implementation_guides/07_windows_automation_worker.md`
8. `FEATURE_COVERAGE_MATRIX.md`
9. `docs/04_feature_catalog/17_contract_usage.md`
10. `docs/09_roadmap/00_master_roadmap.md`

## 5. 구현 아키텍처

```text
ChatGPT Web / Codex remote / Codex local
        -> semantic skills + 18 public MCP tools
        -> Rust MCP control plane
        -> auth/policy/project/job/artifact services
        -> OperationPlan compiler + CapabilityRouter
           |-> DirectHWPXBackend (Rust)
           |-> Windows Hancom Agent -> C#/.NET STA worker
           |-> optional WebHWP/external provider
        -> Validation/Oracle/Render
        -> immutable artifact + revision DAG + evidence
```

LLM은 XML, HAction, ParameterSet 이름을 만들지 않는다. public operation은 stable capability ID만 사용한다.

## 6. 기능 하나의 구현 절차

```text
feature row 선택
 -> capability contract 확인
 -> target binding/source evidence 확인
 -> selector/args Rust type 및 schema 생성
 -> negative fixture부터 작성
 -> direct 또는 automation implementation
 -> semantic readback
 -> package/reopen/oracle/render 검증
 -> registry status와 evidence commit
 -> MCP에서는 기존 OperationPlan으로 노출
```

기계 판독 원본은 `specs/capability-contracts.generated.json`이다. 영역별 상세는 `docs/04_feature_catalog/contracts/`에 있다.

## 7. 먼저 완성할 수직 슬라이스

### VS-0: Hello HWPX

P00~P04. A4 문서 한 문단을 direct writer로 만들고 새 revision과 actual Hancom open evidence를 생성한다.

### VS-1: 표·자유 문서 크기·native 수식

P05~P07 + P10/P13의 최소 oracle. exact custom mm, 여백, 1/2단, 병합/스타일 표, LaTeX→native equation, Web/Codex artifact flow를 완성한다. 사용자의 필수 요구를 처음으로 end-to-end 충족하는 gate다.

### VS-2: 기존 양식 보존

P12. TemplateContract, named slots, surgical patch, untouched byte/token report, Hancom save/reopen/visual diff.

### VS-3: 30문항 시험지

ExamPlan, question keep/split, 표/그림/수식, 배점 검증, 정답지, 페이지 split report.

### VS-4: Desktop-only 기능

HWP 변환, 검토/비교, 차트, 필드 갱신, PDF/인쇄, 보안/외부 기능.

## 8. 표·문서 크기·수식 구현 핵심

### 문서 크기

`page.paper_preset`과 `page.paper_custom(width_mm,height_mm)`를 분리한다. orientation·여백·gutter·header/footer·column width를 정적으로 검사한다. colloquial 종이 이름은 exact mm 후보를 먼저 제시한다.

### 표

TableGrid와 CellSpanMap을 canonical로 하고, 병합/분할/행열 이동 전에 invariant와 FormulaAst 참조를 갱신한다. repeat header와 page split은 renderer/한글 oracle로 검증한다.

### 수식

LaTeX/MathML/EqEdit/AST → MathAst → normalize → EqEdit compiler → native object → readback → AST compare → editor smoke. 이미지 fallback은 기본 금지다.

## 9. 편집 모드

- `normalized_authoring`: 새 문서. 일관된 스타일/ID/패키지 생성.
- `surgical_preserve`: 기존 양식. 필요한 token/part만 변경하고 unknown을 보존.
- `native_automation`: 한/글 편집기 의미 또는 고유 변환이 필요한 기능.

planner가 mode를 정하고, operation 중간에 임의 변경하지 않는다.

## 10. Windows worker 핵심

C#/.NET STA worker가 HwpObject와 COM event/message pump를 담당한다. Rust와는 protobuf만 공유한다. action은 signed target binding에서만 실행한다. unknown modal, timeout, process crash는 fail-closed이며 output reconciliation 전 재실행하지 않는다. 원본은 read-only staging이고 output은 새 경로다.

## 11. 검증과 지원 표기

- `pass`: 실제 필요한 검증이 성공.
- `fail`: assertion 불일치.
- `unverified`: 필요한 환경/worker가 없어 수행하지 못함.
- `skipped_by_policy`: 정책상 수행하지 않음.

`implemented_unverified`를 사용자에게 “완전 지원”으로 표시하지 않는다. target build 또는 binding/compiler/schema가 바뀌면 관련 evidence를 무효화한다.

## 12. ChatGPT Web과 Codex

public tool 18개는 사용자 intent 단위다. 609개 기능은 `OperationPlan.operations[].capability_id`로 표현한다. ChatGPT widget은 project/revision, dry-run, semantic diff, preview, validation, job progress, download를 제공한다. Codex local companion은 `.mcp.json` local bridge와 Git/fixture 도구를 추가하되 remote project head를 묵시적으로 덮지 않는다.

## 13. 개발 시작 명령 순서(개념)

```text
1. P00 target/source/license files 작성
2. monorepo bootstrap + schema/proto codegen
3. catalog importer로 signed registry 생성
4. package reader/preserving tokenizer/property tests
5. DocumentGraph/OperationPlan/transaction
6. VS-0
7. page/text + table + equation 병렬
8. Windows Agent/STA worker + oracle
9. VS-1
10. template/exam/advanced desktop
11. project/job/MCP
12. Web/Codex apps
13. security/performance/DR + production
```

실제 task는 `WORK_BREAKDOWN_STRUCTURE.csv`를 순서대로 처리한다.

## 14. PR 완료 기준

- contract/schema/type.
- permission/risk/fallback.
- implementation.
- happy/boundary/negative/preservation/security tests.
- semantic readback.
- required target evidence.
- registry/status/docs/handoff.

하나라도 없으면 capability는 완료가 아니다.

## 15. 즉시 시작할 첫 작업

P00-01부터 P00-09를 실행한다. primary target 한/글 exact build와 상업 automation 범위가 확정되지 않으면 구현 자체는 research branch에서 진행할 수 있으나 production capability 상태는 disabled/unverified로 유지한다. 그 다음 P01-01 monorepo와 P02 source importer를 시작한다.

## 16. 예제

- `docs/13_reference_recipes/01_custom_page_table_equation.md`
- `docs/13_reference_recipes/02_two_column_math_exam.md`
- `docs/13_reference_recipes/03_surgical_template_fill.md`
- `docs/13_reference_recipes/04_advanced_table.md`
- `docs/13_reference_recipes/05_native_equation_edit.md`
