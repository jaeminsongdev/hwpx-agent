# P20 — Post-GA Parity·Rust-native Expansion

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P19`

## 목표

Post-GA Parity·Rust-native Expansion를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P20-01` | Source/build watcher | Hancom/OpenAI 문서·build 변화를 감시한다. | `change feed` | scheduled diff runs |
| `P20-02` | Catalog delta | 새 source를 import하고 coverage drift를 review한다. | `delta registry` | official item disposition |
| `P20-03` | Binding re-probe | 새 build의 automation binding을 재검증한다. | `binding bundle` | target canary green |
| `P20-04` | Direct backend expansion | 사용량/안정성 높은 automation capability를 Rust direct로 이전한다. | `new direct capabilities` | differential parity |
| `P20-05` | WebHWP expansion | 라이선스가 있는 환경에서 browser/server route를 추가한다. | `WebHWP bindings` | cross-backend tests |
| `P20-06` | Schema migration | IR/OperationPlan/project/binding migration을 제공한다. | `migrators` | N-1 compatibility |
| `P20-07` | Deprecation | removed/renamed capability와 target build sunset을 운영한다. | `deprecation notices` | no silent break |
| `P20-08` | Performance/cost | queue, storage, render, worker 효율을 지속 개선한다. | `optimization report` | no correctness regression |
| `P20-09` | Parity release cadence | 분기/빌드별 matrix와 evidence report를 발행한다. | `parity release` | signed report |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P20-01` 산출물 `change feed` 존재, 검증: scheduled diff runs.
- [ ] `P20-02` 산출물 `delta registry` 존재, 검증: official item disposition.
- [ ] `P20-03` 산출물 `binding bundle` 존재, 검증: target canary green.
- [ ] `P20-04` 산출물 `new direct capabilities` 존재, 검증: differential parity.
- [ ] `P20-05` 산출물 `WebHWP bindings` 존재, 검증: cross-backend tests.
- [ ] `P20-06` 산출물 `migrators` 존재, 검증: N-1 compatibility.
- [ ] `P20-07` 산출물 `deprecation notices` 존재, 검증: no silent break.
- [ ] `P20-08` 산출물 `optimization report` 존재, 검증: no correctness regression.
- [ ] `P20-09` 산출물 `parity release` 존재, 검증: signed report.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
