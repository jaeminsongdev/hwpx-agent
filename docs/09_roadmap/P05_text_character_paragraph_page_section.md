# P05 — Text·Character·Paragraph·Page·Section

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P04`

## 목표

Text·Character·Paragraph·Page·Section를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P05-01` | Text flow reader/writer | run, tab, line break, field boundary를 parse/lower한다. | `text module` | Unicode/run-boundary corpus |
| `P05-02` | Character styles | 언어별 font slots, 크기, 장평, 자간, 효과, 색을 구현한다. | `char style lowerer` | style dedup/readback |
| `P05-03` | Paragraph styles | 정렬, 간격, 들여쓰기, border/fill, keep를 구현한다. | `para style lowerer` | layout/semantic tests |
| `P05-04` | Tabs | default/custom tab, leader, decimal tab을 구현한다. | `tab model` | target readback fixtures |
| `P05-05` | Lists·numbering | 글머리표/문단번호/개요/재시작/연속성을 구현한다. | `list engine` | sequence and nesting tests |
| `P05-06` | Page setup | preset/custom mm, orientation, margins, gutter를 구현한다. | `PageSetup lowerer` | impossible layout negative tests |
| `P05-07` | Sections·columns | section break, equal/custom columns, gaps/separator/balance를 구현한다. | `section/column engine` | multi-section render tests |
| `P05-08` | Header/footer/page number | variants, restart, fields, master page 연결을 구현한다. | `header/footer module` | odd/even/first-page fixtures |
| `P05-09` | VS-1 layout | custom paper+2단+styles 문서를 E2E 생성한다. | `layout vertical slice` | Hancom save/reopen/render pass |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P05-01` 산출물 `text module` 존재, 검증: Unicode/run-boundary corpus.
- [x] `P05-02` 산출물 `char style lowerer` 존재, 검증: style dedup/readback.
- [x] `P05-03` 산출물 `para style lowerer` 존재, 검증: layout/semantic tests.
- [x] `P05-04` 산출물 `tab model` 존재, 검증: target readback fixtures.
- [x] `P05-05` 산출물 `list engine` 존재, 검증: sequence and nesting tests.
- [x] `P05-06` 산출물 `PageSetup lowerer` 존재, 검증: impossible layout negative tests.
- [x] `P05-07` 산출물 `section/column engine` 존재, 검증: multi-section render tests.
- [x] `P05-08` 산출물 `header/footer module` 존재, 검증: odd/even/first-page fixtures.
- [x] `P05-09` 산출물 `layout vertical slice` 존재, 검증: Hancom save/reopen/render pass.
- [x] 새 capability/contract/schema에 migration과 negative test가 있다.
- [x] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [x] source artifact를 in-place로 수정한 경로가 없다.
- [x] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

Authoritative scoped Gate decision: `implementation/p05/P05_GATE_REPORT.md`. P05는 현재 PC의
정품 한글 2020 개인·비상업·로컬 개발 범위에서 완료됐으며, P06만 동일 범위로 승인한다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
