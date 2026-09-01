# MASTER ROADMAP — 설계에서 1.0과 전 기능 패리티까지

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## Phase map

| Phase | 목표 | 선행 |
|---|---|---|
| P00 | Source·License·Target Freeze | 없음 |
| P01 | Repository·CI·Security Foundation | P00 |
| P02 | Official Catalog Importer·Capability Registry | P01 |
| P03 | HWPX Package·Preserving XML Core | P02 |
| P04 | DocumentGraph·OperationPlan·Transactions | P03 |
| P05 | Text·Character·Paragraph·Page·Section | P04 |
| P06 | Table Engine | P05 |
| P07 | Native Equation Engine | P05 |
| P08 | Images·Shapes·Drawing·Charts | P05 |
| P09 | Fields·Forms·Notes·References | P05 |
| P10 | Windows Hancom Automation Bridge | P03 |
| P11 | Advanced Desktop Features | P06,P07,P08,P09,P10 |
| P12 | Template Surgical Edit·Cross-backend Normalization | P06,P07,P08,P09,P11 |
| P13 | Validation·Hancom Oracle·Render | P02,P10 |
| P14 | Projects·Revisions·Jobs·Artifacts | P04 |
| P15 | Remote MCP Control Plane | P14 |
| P16 | ChatGPT Web Plugin·Widget | P15 |
| P17 | Codex Remote·Local Companion | P15 |
| P18 | Quality·Security·Performance·DR | P12,P13,P16,P17 |
| P19 | Production Deployment·License·Submission | P18 |
| P20 | Post-GA Parity·Rust-native Expansion | P19 |

## 주요 병렬화

```text
P00→P01→P02→P03→P04→P05
                    ├→P06 Table ─┐
                    ├→P07 Eq ────┤
                    ├→P08 Object ┤→P12 Template/Normalize
                    └→P09 Ref ───┘
          P03→P10 Automation→P11 Advanced ─┘
          P02+P10→P13 Oracle
          P04→P14 State→P15 MCP→P16 Web
                                └→P17 Codex
P12+P13+P16+P17→P18→P19→P20
```

## 우선순위 수정의 핵심

v1의 Python MVP부터 시작하는 순서를 폐기했다. **공식 source/라이선스/대상 build → capability catalog → preserving package core → semantic IR/transaction**을 먼저 고정해야 뒤에서 “기능이 된다”는 주장을 검증할 수 있다. Windows automation은 후반 부가 기능이 아니라 P10의 정식 backend이고, oracle은 P13에서 모든 핵심 기능의 release 근거를 만든다.

## 마일스톤

- **M1 Core-safe**: P00–P04.
- **M2 Authoring-complete**: P05–P09.
- **M3 Hancom-full-path**: P10–P13.
- **M4 Product-service**: P14–P17.
- **M5 Release-grade**: P18–P19.
- **M6 Continuous parity**: P20.

## phase 공통 완료 조건

- code + tests + docs + registry + evidence가 같은 change set.
- 새 capability는 operation schema, permission, backend binding, negative tests 포함.
- 다음 phase의 API를 추정 구현하지 않고 ADR을 기록.
- handoff와 `CURRENT_STATE.md`, `ROADMAP_STATUS.yaml` 갱신.

## 구현 작업 수

`WORK_BREAKDOWN_STRUCTURE.csv`에는 총 **190개** 실행 task가 있다. 각 phase 문서는 task별 구현 내용·산출물·검증·hard gate를 포함한다.

## 권장 첫 구현 경로

`P00 → P01 → P02 → P03 → P04 → P05`를 완료한 뒤 `P06/P07`을 우선 병렬 수행하여 표·자유 문서 크기·native 수식의 VS-1을 만든다. 동시에 `P10` Windows worker를 시작하고, VS-1이 실제 한/글 oracle을 통과한 뒤 P08/P09/P11/P12를 확장한다. 서비스와 앱은 P14/P15/P16/P17에서 붙인다.

## 지원 표기 규칙

phase task가 끝났더라도 capability는 target-profile evidence가 없으면 `implemented_unverified`다. 마케팅/사용자 응답에서 “지원”으로 표시하려면 registry status `verified`와 required evidence freshness가 모두 충족돼야 한다.
