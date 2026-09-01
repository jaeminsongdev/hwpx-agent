# P07 — Native Equation Engine

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P05`

## 목표

Native Equation Engine를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P07-01` | MathAst | semantic nodes, source spans, normalization/hash를 구현한다. | `math AST crate` | canonicalization property tests |
| `P07-02` | LaTeX adapter | 지원 문법·macro limits·ambiguity를 구현한다. | `LaTeX parser` | Tier A/negative corpus |
| `P07-03` | MathML adapter | namespace/content/presentation subset을 구현한다. | `MathML parser` | round-trip corpus |
| `P07-04` | EqEdit parser/compiler | target dialect precedence/symbol/escape를 구현한다. | `EqEdit module` | AST↔script property tests |
| `P07-05` | Direct native lowerer | equation control/script/style/layout를 HWPX에 생성한다. | `direct equation writer` | native object inspection |
| `P07-06` | Automation binding | native equation insertion/edit/readback을 연결한다. | `equation bindings` | target action probes |
| `P07-07` | Layout estimator | inline baseline/object extent와 render-required state를 구현한다. | `equation layout module` | baseline/ink-box visual tests |
| `P07-08` | Tier corpus | A/B/C와 legacy preserve fixture를 구축한다. | `equation corpus` | A 100%, B target |
| `P07-09` | Editor smoke | double-click edit→token 변경→save/reopen을 자동/수동 증거화한다. | `oracle evidence` | silent fallback 0 |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P07-01` 산출물 `math AST crate` 존재, 검증: canonicalization property tests.
- [ ] `P07-02` 산출물 `LaTeX parser` 존재, 검증: Tier A/negative corpus.
- [ ] `P07-03` 산출물 `MathML parser` 존재, 검증: round-trip corpus.
- [ ] `P07-04` 산출물 `EqEdit module` 존재, 검증: AST↔script property tests.
- [ ] `P07-05` 산출물 `direct equation writer` 존재, 검증: native object inspection.
- [ ] `P07-06` 산출물 `equation bindings` 존재, 검증: target action probes.
- [ ] `P07-07` 산출물 `equation layout module` 존재, 검증: baseline/ink-box visual tests.
- [ ] `P07-08` 산출물 `equation corpus` 존재, 검증: A 100%, B target.
- [ ] `P07-09` 산출물 `oracle evidence` 존재, 검증: silent fallback 0.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
