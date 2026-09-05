# P16 — ChatGPT Web Plugin·Widget

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P15`

## 목표

ChatGPT Web Plugin·Widget를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P16-01` | Official docs lock | release 시점 plugin/Apps SDK 문서와 examples를 다시 고정한다. | `OpenAI source lock` | manifest/UI requirements reviewed |
| `P16-02` | Universal package | plugin manifest, registered app mapping, assets를 구성한다. | `plugin bundle` | package validation |
| `P16-03` | Skills | 9개 workflow skill을 실제 tool names와 동기화한다. | `skills package` | trigger/negative eval |
| `P16-04` | Widget shell | MCP Apps bridge, resource URI, theme/locale를 구현한다. | `React widget` | bridge lifecycle tests |
| `P16-05` | Project/revision UI | project open, history, checkpoint, conflict 화면을 구현한다. | `continuity UI` | Web↔Codex E2E |
| `P16-06` | Plan/diff UI | capability route, risk, semantic diff, warnings를 구현한다. | `dry-run UI` | high-risk confirmation tests |
| `P16-07` | Preview/job UI | page thumbnails, validation badges, progress/cancel을 구현한다. | `preview UI` | large job tests |
| `P16-08` | Upload/download | input file/asset와 artifact output flow를 구현한다. | `file flow` | size/type/ACL tests |
| `P16-09` | CSP/a11y/E2E | exact domains, keyboard, screen reader, developer-mode flow를 검증한다. | `web release evidence` | create/edit/validate/resume/download green |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P16-01` 산출물 `OpenAI source lock` 존재, 검증: manifest/UI requirements reviewed.
- [ ] `P16-02` 산출물 `plugin bundle` 존재, 검증: package validation.
- [x] `P16-03` 산출물 `skills package` 존재, 검증: trigger/negative eval.
- [ ] `P16-04` 산출물 `React widget` 존재, 검증: bridge lifecycle tests.
- [ ] `P16-05` 산출물 `continuity UI` 존재, 검증: Web↔Codex E2E.
- [ ] `P16-06` 산출물 `dry-run UI` 존재, 검증: high-risk confirmation tests.
- [ ] `P16-07` 산출물 `preview UI` 존재, 검증: large job tests.
- [ ] `P16-08` 산출물 `file flow` 존재, 검증: size/type/ACL tests.
- [ ] `P16-09` 산출물 `web release evidence` 존재, 검증: create/edit/validate/resume/download green.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
