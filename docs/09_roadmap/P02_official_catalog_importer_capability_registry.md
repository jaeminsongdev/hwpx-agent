# P02 — Official Catalog Importer·Capability Registry

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P01`

## 목표

Official Catalog Importer·Capability Registry를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P02-01` | SourceRecord schema | 도움말/PDF/XSD/runtime 항목의 공통 record를 정의한다. | `source-record schema` | sample records validate |
| `P02-02` | Help extractor | 메뉴·상세 도움말을 구조화한다. | `help records` | 원문 locator 보존 |
| `P02-03` | Automation extractor | Action/Parameter/Object/Event 자료를 구조화한다. | `automation records` | 필드 타입·설명·source hash 보존 |
| `P02-04` | OWPML extractor | XSD/패키지 part/element/attribute를 색인한다. | `schema records` | namespace/version coverage |
| `P02-05` | 정규화·중복 후보 | label/input/output/scope 기반 candidate를 생성한다. | `candidate graph` | 자동 병합 오탐 review |
| `P02-06` | Semantic capability review | 후보를 stable capability와 scope/support에 매핑한다. | `reviewed catalog` | official item 100% disposition |
| `P02-07` | Binding model | target build action/method/parameter binding schema를 구현한다. | `binding registry types` | schema/codegen pass |
| `P02-08` | Runtime probe tool | default ParameterSet·실행 effect·modal을 탐사한다. | `probe CLI` | disposable fixture에서 trace 생성 |
| `P02-09` | Registry signing·drift | signed registry와 build-to-build diff를 만든다. | `signed registry/drift report` | tamper and drift tests |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P02-01` 산출물 `source-record schema` 존재, 검증: sample records validate.
- [x] `P02-02` 산출물 `help records` 존재, 검증: 원문 locator 보존.
- [x] `P02-03` 산출물 `automation records` 존재, 검증: 필드 타입·설명·source hash 보존.
- [x] `P02-04` 산출물 `schema records` 존재, 검증: namespace/version coverage.
- [x] `P02-05` 산출물 `candidate graph` 존재, 검증: 자동 병합 오탐 review.
- [x] `P02-06` 산출물 `reviewed catalog` 존재, 검증: official item 100% disposition.
- [x] `P02-07` 산출물 `binding registry types` 존재, 검증: schema/codegen pass.
- [ ] `P02-08` 산출물 `probe CLI` 존재, 검증: disposable fixture에서 trace 생성.
- [ ] `P02-09` 산출물 `signed registry/drift report` 존재, 검증: tamper and drift tests.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
