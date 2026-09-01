# P19 — Production Deployment·License·Submission

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P18`

## 목표

Production Deployment·License·Submission를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P19-01` | Production infra | control plane/storage/queue/Windows pool를 배포한다. | `production environment` | smoke/health pass |
| `P19-02` | License evidence | Automation/WebHWP/font/provider 계약을 production config에 연결한다. | `signed license bundle` | scope matches deployment |
| `P19-03` | Identity/secrets/domain | OAuth, secrets, domains, TLS, rotation을 설정한다. | `security config` | rotation/failover test |
| `P19-04` | Privacy/terms/support | 정책 문서, support channel, data handling disclosure를 확정한다. | `public metadata` | legal review |
| `P19-05` | Canary | internal/workspace tenant로 제한 출시한다. | `canary report` | SLO/error/feedback threshold |
| `P19-06` | Rollback | service/image/registry/binding/widget를 함께 rollback한다. | `rollback runbook/evidence` | full rollback drill |
| `P19-07` | Plugin submission | manifest, screenshots, test account, review notes를 제출한다. | `submission package` | review checklist pass |
| `P19-08` | Quota/billing | 필요 시 job class/worker cost/billing guardrail을 구현한다. | `quota/billing config` | abuse/cost tests |
| `P19-09` | GA gate | production smoke, incident contacts, G7를 승인한다. | `1.0 release` | signed release notes |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P19-01` 산출물 `production environment` 존재, 검증: smoke/health pass.
- [ ] `P19-02` 산출물 `signed license bundle` 존재, 검증: scope matches deployment.
- [ ] `P19-03` 산출물 `security config` 존재, 검증: rotation/failover test.
- [ ] `P19-04` 산출물 `public metadata` 존재, 검증: legal review.
- [ ] `P19-05` 산출물 `canary report` 존재, 검증: SLO/error/feedback threshold.
- [ ] `P19-06` 산출물 `rollback runbook/evidence` 존재, 검증: full rollback drill.
- [ ] `P19-07` 산출물 `submission package` 존재, 검증: review checklist pass.
- [ ] `P19-08` 산출물 `quota/billing config` 존재, 검증: abuse/cost tests.
- [ ] `P19-09` 산출물 `1.0 release` 존재, 검증: signed release notes.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
