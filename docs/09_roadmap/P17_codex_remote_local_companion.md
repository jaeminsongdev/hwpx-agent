# P17 — Codex Remote·Local Companion

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P15`

## 목표

Codex Remote·Local Companion를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P17-01` | Codex package | manifest, remote app, skills/agents/commands를 구성한다. | `Codex bundle` | package validation |
| `P17-02` | Remote workflow | 동일 MCP project/create/edit/validate를 검증한다. | `remote E2E` | Web project resume |
| `P17-03` | Local daemon | workspace-confined local service와 health/config를 구현한다. | `local daemon` | sandbox tests |
| `P17-04` | Local MCP config | optional `.mcp.json`과 startup/auth를 구현한다. | `local companion config` | fresh install smoke |
| `P17-05` | Local file/Git | fixture/materialize/output/diff/commit helper를 구현한다. | `local workflow` | path traversal/large file tests |
| `P17-06` | Project sync | local mirror, pull/push/checkpoint를 구현한다. | `sync CLI` | offline/online transition |
| `P17-07` | Conflict handling | rebase/branch/manual merge와 stale head UI를 구현한다. | `conflict resolver` | concurrent Web/Codex tests |
| `P17-08` | Approvals | shell/automation/external side effect approval policy를 구현한다. | `approval policy` | denied-by-default tests |
| `P17-09` | Handoff/evals | AGENTS/handoff와 task eval corpus를 완성한다. | `Codex evidence` | remote/local parity |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P17-01` 산출물 `Codex bundle` 존재, 검증: package validation.
- [ ] `P17-02` 산출물 `remote E2E` 존재, 검증: Web project resume.
- [ ] `P17-03` 산출물 `local daemon` 존재, 검증: sandbox tests.
- [ ] `P17-04` 산출물 `local companion config` 존재, 검증: fresh install smoke.
- [ ] `P17-05` 산출물 `local workflow` 존재, 검증: path traversal/large file tests.
- [ ] `P17-06` 산출물 `sync CLI` 존재, 검증: offline/online transition.
- [ ] `P17-07` 산출물 `conflict resolver` 존재, 검증: concurrent Web/Codex tests.
- [ ] `P17-08` 산출물 `approval policy` 존재, 검증: denied-by-default tests.
- [ ] `P17-09` 산출물 `Codex evidence` 존재, 검증: remote/local parity.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
