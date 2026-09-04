# P14 — Projects·Revisions·Jobs·Artifacts

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P04`

## 목표

Projects·Revisions·Jobs·Artifacts를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P14-01` | Metadata schema | tenant/project/revision/checkpoint/job/artifact/idempotency DB를 설계한다. | `DB migrations` | migration/rollback tests |
| `P14-02` | Artifact store | content hash, encryption, ACL, quarantine, signed URL을 구현한다. | `artifact service` | cross-tenant denial |
| `P14-03` | Revision CAS | immutable DAG와 expected head commit을 구현한다. | `revision service` | race/conflict tests |
| `P14-04` | History/checkpoints | semantic diff cursor, labels, branches를 구현한다. | `history API` | DAG/query tests |
| `P14-05` | Job state machine | enqueue/lease/stage/execute/validate/commit 상태를 구현한다. | `job service` | invalid transition tests |
| `P14-06` | Worker lease/fencing | capability/profile matching, lease expiry, fencing token을 구현한다. | `scheduler` | late worker commit rejection |
| `P14-07` | Idempotency/reconciliation | request hash, timeout outcome, retry policy를 구현한다. | `idempotency module` | duplicate side-effect tests |
| `P14-08` | Cancel/cleanup | safe cancellation, orphan artifact, temp cleanup을 구현한다. | `cleanup worker` | fault injection |
| `P14-09` | Retention/local mirror | purge/legal hold와 Codex project-state mirror를 구현한다. | `retention/sync service` | delete and conflict tests |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P14-01` 산출물 `DB migrations` 존재, 검증: migration/rollback tests.
- [x] `P14-02` 산출물 `artifact service` 존재, 검증: cross-tenant denial.
- [x] `P14-03` 산출물 `revision service` 존재, 검증: race/conflict tests.
- [x] `P14-04` 산출물 `history API` 존재, 검증: DAG/query tests.
- [x] `P14-05` 산출물 `job service` 존재, 검증: invalid transition tests.
- [x] `P14-06` 산출물 `scheduler` 존재, 검증: late worker commit rejection.
- [x] `P14-07` 산출물 `idempotency module` 존재, 검증: duplicate side-effect tests.
- [x] `P14-08` 산출물 `cleanup worker` 존재, 검증: fault injection.
- [ ] `P14-09` 산출물 `retention/sync service` 존재, 검증: delete and conflict tests.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
