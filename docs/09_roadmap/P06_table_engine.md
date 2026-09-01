# P06 — Table Engine

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P05`

## 목표

Table Engine를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P06-01` | Grid/span invariant | slot→master cell, rectangular span model을 구현한다. | `TableGrid` | property tests |
| `P06-02` | Create/insert/delete | 표·행·열 생성과 삽입/삭제를 구현한다. | `table operations` | boundary/index tests |
| `P06-03` | Merge/split | content preservation policy와 span 변환을 구현한다. | `merge/split engine` | nonrectangular/conflict tests |
| `P06-04` | Cell formatting | margin, border/fill, alignment, direction, protection을 구현한다. | `cell style lowerer` | readback/render tests |
| `P06-05` | Sizing·autofit | fixed/min/preferred width와 body constraints solver를 구현한다. | `layout solver` | overflow and font metric tests |
| `P06-06` | FormulaAst | 수식, 상대/절대 참조, 캐시, number format을 구현한다. | `formula engine` | row/column move reference tests |
| `P06-07` | Pagination | repeat header, row/page split, caption, keep를 구현한다. | `table pagination validator` | boundary page suite |
| `P06-08` | Inspect/select | stable table/cell selector와 snapshot을 구현한다. | `table inspector` | merged/nested selector tests |
| `P06-09` | Direct/automation differential | 61 capability를 target binding과 비교한다. | `table conformance report` | required matrix green |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P06-01` 산출물 `TableGrid` 존재, 검증: property tests.
- [ ] `P06-02` 산출물 `table operations` 존재, 검증: boundary/index tests.
- [ ] `P06-03` 산출물 `merge/split engine` 존재, 검증: nonrectangular/conflict tests.
- [ ] `P06-04` 산출물 `cell style lowerer` 존재, 검증: readback/render tests.
- [ ] `P06-05` 산출물 `layout solver` 존재, 검증: overflow and font metric tests.
- [ ] `P06-06` 산출물 `formula engine` 존재, 검증: row/column move reference tests.
- [ ] `P06-07` 산출물 `table pagination validator` 존재, 검증: boundary page suite.
- [ ] `P06-08` 산출물 `table inspector` 존재, 검증: merged/nested selector tests.
- [ ] `P06-09` 산출물 `table conformance report` 존재, 검증: required matrix green.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
