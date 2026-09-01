# P13 — Validation·Hancom Oracle·Render

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P02,P10`

## 목표

Validation·Hancom Oracle·Render를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P13-01` | Validation model | pass/fail/unverified/skipped evidence와 invalidation을 구현한다. | `validation-core` | state transition tests |
| `P13-02` | Package/schema validators | ZIP/XML/XSD/relationship/reference 검사를 구현한다. | `L1/L2 validators` | malformed corpus |
| `P13-03` | Semantic snapshot | 문서 의미 canonical snapshot과 feature comparator를 구현한다. | `snapshot engine` | determinism tests |
| `P13-04` | Hancom open oracle | fresh target process open/repair/error evidence를 구현한다. | `L5 oracle` | known corrupt fixtures |
| `P13-05` | Save/reopen oracle | save, close, fresh reopen, snapshot compare를 구현한다. | `L6 oracle` | format-specific suite |
| `P13-06` | Render service | page PDF/image, font substitution, bounds metadata를 생성한다. | `render oracle` | page count/bounds tests |
| `P13-07` | Visual diff | affected region, text/table/equation/object thresholds를 구현한다. | `visual diff tool` | golden image suite |
| `P13-08` | Export validator | PDF/DOCX/HWP/image/text reopen/loss를 검증한다. | `export validators` | conversion matrix |
| `P13-09` | Evidence store/report | 환경 digest, artifact refs, freshness와 dashboard를 구현한다. | `evidence service` | tamper/invalidation tests |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P13-01` 산출물 `validation-core` 존재, 검증: state transition tests.
- [ ] `P13-02` 산출물 `L1/L2 validators` 존재, 검증: malformed corpus.
- [ ] `P13-03` 산출물 `snapshot engine` 존재, 검증: determinism tests.
- [ ] `P13-04` 산출물 `L5 oracle` 존재, 검증: known corrupt fixtures.
- [ ] `P13-05` 산출물 `L6 oracle` 존재, 검증: format-specific suite.
- [ ] `P13-06` 산출물 `render oracle` 존재, 검증: page count/bounds tests.
- [ ] `P13-07` 산출물 `visual diff tool` 존재, 검증: golden image suite.
- [ ] `P13-08` 산출물 `export validators` 존재, 검증: conversion matrix.
- [ ] `P13-09` 산출물 `evidence service` 존재, 검증: tamper/invalidation tests.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
