# P15 — Remote MCP Control Plane

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P14`

## 목표

Remote MCP Control Plane를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P15-01` | Auth/tenant | OAuth/OIDC identity, tenant mapping, service tokens를 구현한다. | `auth middleware` | negative/expiry tests |
| `P15-02` | Public tool schemas | 18 tool input/output와 annotations를 확정한다. | `MCP descriptors` | schema snapshots |
| `P15-03` | Handlers | auth→schema→policy→job/service 호출→structured result를 구현한다. | `MCP handlers` | contract tests |
| `P15-04` | Async job UX | job IDs, progress, cancel, terminal receipt를 구현한다. | `job MCP tools` | long-running E2E |
| `P15-05` | Artifact delivery | attachment/signed URL, range, expiry를 구현한다. | `artifact_get` | ACL/expiry tests |
| `P15-06` | Error mapping | internal errors를 stable public envelope로 map한다. | `error catalog` | no secret leakage |
| `P15-07` | Rate limit/quotas | tenant/user/capability/job class 제한을 구현한다. | `quota service` | burst/fairness tests |
| `P15-08` | Telemetry | tool/job/backend/capability SLI와 trace correlation을 구현한다. | `dashboards` | sample trace complete |
| `P15-09` | Inspector/staging | MCP Inspector와 staging HTTPS E2E를 자동화한다. | `staging evidence` | all tools green |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P15-01` 산출물 `auth middleware` 존재, 검증: negative/expiry tests.
- [x] `P15-02` 산출물 `MCP descriptors` 존재, 검증: schema snapshots.
- [x] `P15-03` 산출물 `MCP handlers` 존재, 검증: contract tests.
- [x] `P15-04` 산출물 `job MCP tools` 존재, 검증: long-running E2E.
- [x] `P15-05` 산출물 `artifact_get` 존재, 검증: ACL/expiry tests.
- [ ] `P15-06` 산출물 `error catalog` 존재, 검증: no secret leakage.
- [ ] `P15-07` 산출물 `quota service` 존재, 검증: burst/fairness tests.
- [ ] `P15-08` 산출물 `dashboards` 존재, 검증: sample trace complete.
- [ ] `P15-09` 산출물 `staging evidence` 존재, 검증: all tools green.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
