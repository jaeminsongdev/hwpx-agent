# P12 — Template Surgical Edit·Cross-backend Normalization

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P06,P07,P08,P09,P11`

## 목표

Template Surgical Edit·Cross-backend Normalization를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P12-01` | Template analyzer | slots/styles/sections/controls/unknown/protection을 inventory한다. | `TemplateSnapshot` | real/synthetic template corpus |
| `P12-02` | TemplateContract | fillable/immutable/repeating regions와 allowed operation을 생성한다. | `contract generator` | schema and human review |
| `P12-03` | Surgical edits | field/slot/stable ID 기반 patch와 untouched policy를 구현한다. | `template editor` | byte/token preservation |
| `P12-04` | Style mapping | semantic styles를 existing style IDs에 map하고 conflict를 처리한다. | `style mapper` | no unintended style duplication |
| `P12-05` | Unknown/OLE handling | opaque extension/active content 영향 분석과 quarantine을 구현한다. | `preservation/security report` | malicious template tests |
| `P12-06` | Cross-backend normalization | direct/automation output을 semantic snapshot으로 조정한다. | `normalizer` | differential fixtures |
| `P12-07` | Document merge/split | section/style/resource/reference collision을 처리한다. | `transform engine` | multi-document tests |
| `P12-08` | Exam engine | question/score/choice/answer/keep/split rule를 구현한다. | `ExamPlan compiler` | 30-question fixture |
| `P12-09` | VS-2/VS-3 | 학교 양식과 수학 시험지를 end-to-end 완성한다. | `vertical evidence` | Hancom save/reopen/visual pass |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P12-01` 산출물 `TemplateSnapshot` 존재, 검증: real/synthetic template corpus.
- [ ] `P12-02` 산출물 `contract generator` 존재, 검증: schema and human review.
- [ ] `P12-03` 산출물 `template editor` 존재, 검증: byte/token preservation.
- [ ] `P12-04` 산출물 `style mapper` 존재, 검증: no unintended style duplication.
- [ ] `P12-05` 산출물 `preservation/security report` 존재, 검증: malicious template tests.
- [ ] `P12-06` 산출물 `normalizer` 존재, 검증: differential fixtures.
- [ ] `P12-07` 산출물 `transform engine` 존재, 검증: multi-document tests.
- [ ] `P12-08` 산출물 `ExamPlan compiler` 존재, 검증: 30-question fixture.
- [ ] `P12-09` 산출물 `vertical evidence` 존재, 검증: Hancom save/reopen/visual pass.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
