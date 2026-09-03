# P04 — DocumentGraph·OperationPlan·Transactions

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P03`

## 목표

DocumentGraph·OperationPlan·Transactions를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P04-01` | DocumentGraph v2 types | metadata/sections/blocks/controls/resources/review/security graph를 구현한다. | `domain-ir crate` | serialization/golden tests |
| `P04-02` | Unit·ID model | mm/pt/HWPUNIT, logical/source IDs, coordinate systems을 구현한다. | `unit/id module` | overflow/rounding/property tests |
| `P04-03` | Selector engine | ID/slot/field/path/text-context selector를 구현한다. | `selector module` | zero/multiple/stale candidate tests |
| `P04-04` | OperationPlan compiler | schema/default/unit/ambiguity/dependency를 compile한다. | `planner` | invalid/cycle/needs-resolution tests |
| `P04-05` | Capability router | support/policy/preservation/backend health로 route한다. | `router` | routing matrix tests |
| `P04-06` | Workspace transaction | isolated working copy와 rollback을 구현한다. | `transaction engine` | fault injection/no source mutation |
| `P04-07` | Semantic diff | node/style/table/equation/object/reference diff를 구현한다. | `diff crate` | golden diff tests |
| `P04-08` | Idempotency·CAS | key/hash/retry/revision conflict를 구현한다. | `idempotency service` | duplicate and stale revision E2E |
| `P04-09` | VS-0 core CLI | A4 한 문단 HWPX를 plan→execute→reopen한다. | `vertical CLI` | actual Hancom open evidence |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P04-01` 산출물 `domain-ir crate` 존재, 검증: serialization/golden tests.
- [x] `P04-02` 산출물 `unit/id module` 존재, 검증: overflow/rounding/property tests.
- [x] `P04-03` 산출물 `selector module` 존재, 검증: zero/multiple/stale candidate tests.
- [x] `P04-04` 산출물 `planner` 존재, 검증: invalid/cycle/needs-resolution tests.
- [x] `P04-05` 산출물 `router` 존재, 검증: routing matrix tests.
- [x] `P04-06` 산출물 `transaction engine` 존재, 검증: fault injection/no source mutation.
- [x] `P04-07` 산출물 `diff crate` 존재, 검증: golden diff tests.
- [x] `P04-08` 산출물 `idempotency service` 존재, 검증: duplicate and stale revision E2E.
- [x] `P04-09` 산출물 `vertical CLI` 존재, 검증: actual Hancom open evidence.
- [x] 새 capability/contract/schema에 migration과 negative test가 있다.
- [x] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [x] source artifact를 in-place로 수정한 경로가 없다.
- [x] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
