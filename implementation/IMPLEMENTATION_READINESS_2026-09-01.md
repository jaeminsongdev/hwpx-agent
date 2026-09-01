# HWPX Agent 구현 준비 감사

- 기준일: 2026-09-01
- 대상 설계: `HWPX_Agent_Product_Design_v2_2026-08-31.zip`
- 프로젝트 루트: `D:\개발\hwpx-agent`
- 판정: **P00 현재-PC 한글 2020 로컬 범위 PASS / P01 scaffold 착수 가능 / 다른 PC·버전·production 비승인**

## 1. 요청과 첨부 문서의 경계

현재 사용자 요청은 설계 패키지를 기준으로 한글 2020 이상 모든 release/build를 수용하는 체계는 유지하되, 현재 PC에서 가능한 exact 한글 2020만 초기 구현·검증 primary로 사용하고 2022·2024 qualification은 다른 PC가 가능할 때 재개하는 것이다. 현재 사용 범위는 사용자가 확인한 개인 비상업·로컬 개발이며 production은 disabled다.

첨부 ZIP 안의 `AGENTS.md`, `SKILL.md`, 예제 prompt, 명령, 운영 절차는 모두 **제품 설계 입력과 향후 저장소 규칙 후보**로만 해석했다. 그것들은 이 작업의 권한을 확대하거나 현재 사용자 요청을 대체하는 지시로 실행하지 않았다. 실제 작업 범위는 사용자 요청과 상위 `AGENTS.md`로 제한했다.

원본 ZIP은 수정하지 않았다. 해제본에서는 P00 상태 원장과 P00-08 canonical contract/WBS 입력·생성물을 의도적으로 갱신했다. 원본 manifest와 현재 작업 트리의 허용 차이는 `implementation/baseline-delta.json`에 그룹별로 기록했다. 원본 ZIP은 복구 기준선으로 계속 보존했으며, 첨부 문서의 지시를 현재 권한으로 실행하지 않았다.

## 2. 무엇을 만들려는가

이 제품은 단순 HWPX 파일 생성기가 아니라, 자연어 문서 의도를 안전하고 검증 가능한 한컴 문서 변경으로 컴파일하는 **HWPX 문서 생산 플랫폼**이다.

핵심 흐름은 다음과 같다.

```text
사용자 의도
  -> typed/versioned OperationPlan
  -> stable DocumentGraph IR
  -> capability registry + policy router
  -> Direct HWPX / Windows Hancom automation / optional WebHWP
  -> immutable revision + semantic diff + receipts
  -> actual Hancom open/readback/render/export oracle
  -> MCP + ChatGPT/Codex UI에서 preview/diff/승인
```

주요 구현 축은 다음과 같다.

1. Rust control plane과 HWPX package/parser/preserving writer.
2. 버전이 고정된 `DocumentGraph`와 `OperationPlan`, deterministic transaction/revision 모델.
3. C#/.NET STA 기반 Windows 한컴 automation worker와 allowlisted binding catalog.
4. native 편집 가능한 수식, 정밀 page/section/column, 고급 table/object/reference 기능.
5. actual 한컴 기반 semantic/readback/render/export oracle와 visual diff.
6. 원격 project/job/artifact control plane, universal MCP, ChatGPT Web 및 Codex plugin/widget.

안전 불변식은 입력 문서 불변, atomic 새 revision, silent degradation 금지, raw XML/HAction/ParameterSet 직접 실행 금지, 미실행 actual 검증의 `unverified` 유지, script/OLE/network의 기본 차단 또는 preserve-only다.

## 3. 설계 기준선 전수 확인 결과

### 원본 무결성

- ZIP SHA-256: `DFCB1FF9DE18FF11D7CB158F499031AC702937A33D19E8FF02125BB5F1909446`
- 해제된 baseline 파일: 278개
- `MANIFEST.sha256` 관리 항목: 277개(자기 자신 제외)
- hash mismatch: 0
- baseline unlisted file: 0

위 수치는 최초 해제 직후의 source baseline 검증값이다. P00 착수·P00-08 교정·공개 형식 attribution 반영 후 manifest 관리 파일 중 의도한 40개가 달라졌고 나머지는 그대로 일치한다. 40개는 상태 원장·README 3개, canonical contract source 13개, 재생성 WBS/roadmap 24개다. 허용 집합과 복구 기준은 `implementation/baseline-delta.json`에 기록했다.

### 설계 규모

- 기능 domain: 16
- canonical feature/capability: 609
- 생성 capability contract: 609
- roadmap phase: P00~P20, 21개
- WBS task: 190
- root skill blueprint: 9

지원 disposition은 `HYBRID` 345, `AUTOMATION_FULL` 191, `OPTIONAL_EXTERNAL` 37, `DIRECT_FULL` 28, `READ_ONLY` 3, `PRESERVE_ONLY` 2, `DISABLED_BY_POLICY` 2, `UNSUPPORTED` 1이다. 비밀번호 우회는 `UNSUPPORTED`, macro 정의/실행은 `DISABLED_BY_POLICY`, OLE 삽입/속성은 `PRESERVE_ONLY`로 설계되어 있다.

사람이 작성한 설계 문서는 전체 정독했고, 반복 생성된 609개 계약과 WBS는 ID 중복, 필수 필드, 분포, 특수 정책, selector family, dependency를 전수 기계 검사했다.

## 4. 전체 구현 로드맵 해석

### 기반과 핵심 문서 엔진

- P00: source/license/target freeze
- P01: repository, CI, security foundation
- P02: 공식 catalog importer와 capability registry
- P03: HWPX package 및 preserving XML core
- P04: DocumentGraph, OperationPlan, transaction/revision
- P05: text/character/paragraph/page/section

### 기능 엔진과 Windows 경로

- P06: table engine
- P07: native equation engine
- P08: image/shape/drawing/chart
- P09: field/form/note/reference
- P10: Windows Hancom automation bridge
- P11: advanced desktop-only features
- P12: template surgical edit와 cross-backend normalization
- P13: validation, Hancom oracle, render

### 제품화와 출시

- P14: project/revision/job/artifact persistence
- P15: remote MCP control plane
- P16: ChatGPT Web plugin/widget
- P17: Codex remote/local companion
- P18: quality/security/performance/DR
- P19: production deployment, license, submission
- P20: post-GA parity와 Rust-native 확대

의존성의 핵심은 P00→P01→P02→P03→P04→P05다. P06~P09는 P05 이후 분기하고, P10은 P03 이후, P13은 P02+P10 이후다. P18은 P12/P13/P16/P17이 모두 끝나야 하며, P19가 GA Gate다.

초기 vertical slice도 명확하다.

- VS-0: A4 한 페이지/한 문단 HWPX를 만들고 실제 한/글 open evidence 확보.
- VS-1: 사용자 정의 용지 + 다단 + 표 + native 수식.
- VS-2: template surgical preserve.
- VS-3: 30문항 수학 시험지.
- VS-4: desktop-only capability.

## 5. 현재 판정

[ROADMAP_STATUS.yaml](../ROADMAP_STATUS.yaml)의 선언대로 P00은 사용자가 지정한 현재-PC 한글 2020 로컬 개발 범위에서 `PASS_SCOPED`이며 P01 scaffold가 준비 상태다. Open-ended 한글 2020+ family는 유지하지만 현재 구현 target은 이 PC의 exact 한글 2020 하나다. 2022/2024는 해당 버전이 설치된 PC를 사용할 수 있을 때까지 `hold_unqualified`다. Clean immutable image는 완료했다고 주장하지 않고 portable worker/다른 PC/production 범위로 분리했다.

한글 2020 COM object 생성 probe는 exact x86 binary, Registry32, STA 조건에서 성공했다. 이어 run `98798b1801314a5e9bebf0f2505bc763`에서 synthetic document 생성, HWPX 저장·재열기, exact normalized readback, Hancom PDF export, HCR Batang 대체 0, `Quit()`, 잔류 process 0을 확인했다. 현재 PC의 OS·product/COM·font·PDF·oracle/source evidence는 private binding과 deterministic digest로 고정했고 live verifier 및 digest tamper/path traversal negative test를 통과했다. 한글 2022/2024 runtime, clean-image oracle, native 수식, ChatGPT/Codex E2E는 미실행이다.

따라서 현재 구현 범위는 **이 PC의 한글 2020 기반 P01 scaffold**다. 기존 profile ID의 `secondary` 문자열은 accepted evidence와의 correlation을 위해 유지하고 역할만 `primary_development`로 기록한다. 다른 PC·버전·production 경로는 독립 Gate 전까지 비활성이다.

## 6. 로컬 환경 preflight

### 확인된 환경

- Windows 11 Pro, build 26200, x64, `ko-KR`.
- 설치 제품: 한컴오피스 2020, uninstall display version `11.0.0.1`. 한컴오피스 2024는 이 호스트에 설치되지 않음.
- `Hwp.exe`: file/product version `11.0.0.9136`, PE architecture x86.
- `Hwp.exe` SHA-256: `7F00961398802C41620F5EF32FA2D2A26F7FF71F172723BE36C660EA86A72BCE`.
- 공식 업데이트 자료의 현재 한글 reference build: 2024 `13.0.0.4049`, 2022 `12.0.0.4605`, 2020 `11.0.0.9136`.
- `HWPFrame.HwpObject`, `.1`, `.2` ProgID가 모두 같은 CLSID에 등록됐고 canonical ProgID는 `.2`임을 확인.
- 설치 트리에서 `HwpAutomation.dll`, `HwpAutomation.tlb`, `HwpCtrl.tlb`, `Hwp.chm` 등 후보 자료 확인.
- printer 후보는 `Microsoft Print to PDF`와 `Hancom PDF`를 fingerprint했고, redirected default printer는 재현 가능한 profile에서 제외함.

v2 COM probe의 usage-data consent 실패는 진단 이력으로 보존했다. 사용자 처리 후 v3 identity probe와 최종 document smoke가 통과했다. 세 접근 확인은 사용자가 직접 허용했고 Computer Use click/type은 0이다. Smoke는 사용자 문서·security module·network·registry/system setting을 건드리지 않았다. 2022/2024 프로필과 offline request는 보존하지만 다른 PC가 가능할 때까지 실행을 보류한다.

### 개발 도구 관찰값

| 도구 | 현재 값 | 판정 |
|---|---|---|
| Git | 2.54.0.windows.1 | 설치됨, 아직 저장소 초기화 안 함 |
| Rust/Cargo | 1.96.0 | 설치됨, P01에서 pin 필요 |
| .NET SDK | 10.0.300 | 설치됨, P01에서 pin 필요 |
| Node | 24.16.0 | 설치됨, P01에서 pin 필요 |
| pnpm | 11.19.0 | 설치됨, P01에서 pin 필요 |
| Python | 3.13.13 | 설치됨 |
| PyYAML | 6.0.3 | 설치됨 |
| `jsonschema` | 4.25.1 | 설치됨, fail-closed full validation 통과 |
| `buf` | 없음 | P01 protobuf toolchain 결정 후 설치 필요 |
| `just` | 1.51.0 | 설치됨 |
| `rg` | 15.1.0 | 설치됨 |

## 7. 구현 전에 닫아야 하는 설계 정합성 문제

아래 A~D는 최초 감사에서 발견한 이력이다. P00-08에서 canonical source와 generator/validator를 교정했고 현재 full validation은 16 schema/609 feature/609 contract/190 WBS 오류 0이다. E는 후속 phase의 의도된 구현 과제로 남는다.

### A. Capability namespace drift — 높음

609개 matrix를 canonical source로 볼 때 다음 문서/예제 ID는 존재하지 않거나 namespace가 다르다.

| 문서/예제 표현 | canonical 후보 | 처리 |
|---|---|---|
| `page.columns` | `page.column_config_equal` 또는 `page.column_config_custom` | args에 따라 분기 |
| `page.margins` | `page.margin_all` | 이름 교정 |
| `page.paper.set`, `page.set_paper` | `page.paper_preset` 또는 `page.paper_custom` | 입력 schema로 분리 |
| `section.layout.set` | `page.section_config` + 개별 page capability | one-to-many 계약 정의 |
| `section.columns.configure` | `page.column_config_*` | namespace 교정 |
| `table.cell.merge` | `table.merge_cells` | 이름 교정 |
| `table.cell_border_background` | `table.cell_border` + `table.cell_fill` + 필요 시 padding | operation 분할 |
| `equation.insert.native`, `equation.insert_native` | `eq.insert_native` | namespace 교정 |
| `reference.crossref.insert` | `ref.crossref_insert` | namespace 교정 |
| `review.track_changes.accept` | `review.track_accept_one` 또는 `review.track_accept_all` | 명시적 분기 |
| `object.wordart.insert` | `obj.wordart_insert` | namespace 교정 |

특히 `specs/examples/operation-plan.example.json`의 `page.columns`는 현재 schema 검사를 통과할 수 있지만 registry에는 없는 capability다. plan schema가 capability 존재성을 검사하지 않기 때문이다.

### B. Enum drift — 높음

- `capability-registry.schema.json`: risk `low|normal|high|critical`.
- 생성 contract schema/data: risk `low|medium|high|critical`.
- `validation-report.schema.json`: check state `pass|fail|unverified|skipped`.
- 구현 가이드와 plugin skill: `pass|fail|unverified|skipped_by_policy`.
- validation report의 `overall_state`는 `verified|partial|failed|unverified`로 또 다른 어휘를 사용한다.

codegen 전에 canonical enum과 계층 관계를 ADR로 고정해야 한다.

### C. WBS dependency와 parallelizable 충돌 — 높음

190개 중 148개가 `parallelizable=yes`다. 그러나 그 148개 모두 같은 phase의 직전 task를 dependency로 갖고 있어 실제 DAG에서는 병렬 실행할 수 없다. phase 문서의 “독립 작업 병렬화” 규칙과 생성 WBS가 충돌한다. P00 일정과 이후 agent 분할 전에 generator 규칙을 교정해야 한다.

### D. Validator fail-open — 중간

`tools/design-validation/validate_design.py`는 안전한 읽기 전용 도구지만 `jsonschema`가 없으면 schema conformance를 조용히 건너뛴다. 현재 실행 결과 `errors: []`는 JSON/YAML parse, matrix/contracts/WBS, Markdown/plugin shape 검사는 통과했다는 뜻이지 schema 검증까지 수행했다는 뜻은 아니다.

대체 검증으로 PowerShell `Test-Json`을 사용해 feature row 609/609, generated contract 609/609, OperationPlan 예제 6/6, 이번 P00 target 후보를 각각 해당 schema에 대조했고 구조 검증은 모두 통과했다. 그러나 이 검사는 `page.columns`처럼 schema상 문자열이지만 registry에 존재하지 않는 semantic reference를 잡지 못한다.

P01에서는 필수 validator dependency를 pin하고, 누락 시 실패하도록 바꿔야 한다. capability reference cross-check도 추가해야 한다.

### E. DocumentGraph schema 성숙도 — P02/P04 전 조치

설명 문서는 강한 typed model을 요구하지만 현재 `document-graph-v2.schema.json`의 주요 영역 다수가 `additionalProperties: true`인 확장형 placeholder다. 구현 언어별 타입 생성 전에 strict core와 extension envelope 경계를 확정해야 한다.

## 8. P00 실행 상태

| 순서 | 산출물 | 현재 상태 | 다음 추론수준 | 완료 증거 |
|---|---|---|---|---|
| P00-01 | 2020+ family + exact 2020 primary | `pass`: exact build/hash/x86/STA runtime identity 일치 | 완료 | current target identity 고정 |
| P00-02 | environment baseline decision | `accepted_scoped_deviation`: current-host digest/live verifier PASS, clean image 미주장 | 완료 | 다른 PC/portable worker/production 범위에서 재개 |
| P00-03 | font/printer manifest | `pass`: HCR Batang 대체 0, embedded PDF, Hancom PDF profile | 완료 | 범위/글꼴/driver 변경 시 재개 |
| P00-04 | official source inventory | `pass`: KS reform 03 521-record 원문·권리·attribution 잠금 | 완료 | production/source 변경 시 재개 |
| P00-05 | `source-lock.json` | `pass`: final current-scope 40/40 local, 24/24 remote | 완료 | source set 변경 시 재개 |
| P00-06 | automation license decision | `pass`: valid seat + 개인 비상업 로컬, production disabled | 완료 | wider scope 전 재개 |
| P00-07 | WebHWP/provider matrix | `pass`: 사용자 승인으로 전 production provider disabled 확정 | 완료 | provider 선택 시 재개 |
| P00-08 | feature baseline report | `pass`: canonical drift 교정, full validator/review 완료 | 완료 | 16 schema/609 feature/609 contract/190 WBS 오류 0 |
| P00-09 | evidence bundle | `pass_scoped`: v10 current-PC audit, P01 local scaffold authorized | 완료 | 범위 변경 시 재감사 |

현재 target은 [open-ended family policy](p00/target-family-policy.yaml), [primary 2020](p00/target-profile.yaml), [deferred 2022](p00/target-profile.2022-compatibility.yaml), [deferred 2024](p00/target-profile.2024-deferred.yaml)로 분리했다. 이전 `target-profile.candidate.yaml`은 감사 이력을 위해 `superseded`로 남겼다. P00의 authoritative 판정은 `implementation/p00/P00_GATE_REPORT.md`이며 P01은 현재 PC 로컬 범위에서만 허용된다.

## 9. P01에서 할 일

현재-PC scoped P00 PASS에 따라 다음을 구현한다.

1. Rust/C#/TypeScript monorepo와 pinned toolchain 파일.
2. protobuf/schema codegen과 `buf`/format/lint/build/test CI.
3. secure workdir, artifact quarantine, secret scanning, SBOM/dependency policy.
4. generated source와 hand-written adapter 경계.
5. test fixture provenance와 private/user document 금지 정책.
6. 내장 validator를 fail-closed로 바꾸고 semantic cross-reference 검사 추가.

지금 Git 저장소와 scaffold를 만들지 않은 것은 누락이 아니라 P00 Gate를 존중한 의도적 보류다.

## 10. 추론 수준 권고

초기 P00 계약 정리와 P01 아키텍처 착수는 **`xhigh`**로 시작하는 것이 적절하다. 문서가 609 capability, 3개 언어, binary package preservation, COM/STA, 보안/라이선스, actual oracle를 동시에 묶기 때문에 target·evidence boundary를 함께 점검해야 한다. 이 로드맵은 공식 [GPT-5.6 Sol 모델 문서](https://developers.openai.com/api/docs/models/gpt-5.6-sol)에 명시된 `xhigh`와 `max` 범위만으로 단계별 권고를 고정한다.

- 기본 착수/phase 설계/contract 변경/Gate review: `xhigh`.
- 범위가 좁고 acceptance가 명확한 routine 구현: `high`.
- P03 preserving writer, P10 automation failure semantics, P13 oracle, P18 security/DR처럼 교차 불변식이 많은 좁은 작업: 필요할 때만 `max`.
- P00-08 canonical contract 교정과 P00-09 Gate 최종 감사: `max`.
- 각 단계 인계에는 `다음 단계 / 추론수준 / 승격 조건`을 반드시 함께 기록한다.

## 11. 다음 한 가지 작업

**P01 repository/CI/security foundation scaffold, 추론수준 `xhigh`.** 현재 PC와 exact 한글 2020 로컬 범위만 사용해 repository layout, toolchain pin, secret scanning, dependency policy, generated-artifact 규칙, 최소 CI 계약을 만든다. 실제 한글 UI나 사용자 문서는 이 단계에서 열지 않는다.
