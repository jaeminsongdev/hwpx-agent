# P08 — Images·Shapes·Drawing·Charts

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P05`

## 목표

Images·Shapes·Drawing·Charts를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P08-01` | Asset pipeline | MIME sniff/hash/dedup/relationship/size limit을 구현한다. | `asset store adapter` | malformed media tests |
| `P08-02` | Image insert | embed/link, crop, resolution, alt text를 구현한다. | `image lowerer` | reopen/render |
| `P08-03` | Geometry·anchor·wrap | 좌표/size/rotation/anchor/text wrap을 구현한다. | `object geometry module` | page/paragraph anchor fixtures |
| `P08-04` | Basic shapes | line/rectangle/ellipse/text box/freeform을 구현한다. | `shape lowerer` | property/readback tests |
| `P08-05` | Appearance | line/fill/gradient/pattern/shadow/transparency/effects를 구현한다. | `effect model` | visual diff |
| `P08-06` | Composition | group/ungroup/z-order/align/distribute/connector를 구현한다. | `object graph operations` | graph invariant tests |
| `P08-07` | Charts | type/data/series/axis/legend/title/style automation bindings을 구현한다. | `chart adapter` | target readback/export |
| `P08-08` | OLE/media policy | opaque preserve, blocked activation, inventory를 구현한다. | `active-content policy` | security corpus |
| `P08-09` | Object conformance | 58 capability와 asset/render thresholds를 닫는다. | `object report` | required matrix green |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P08-01` 산출물 `asset store adapter` 존재, 검증: malformed media tests.
- [ ] `P08-02` 산출물 `image lowerer` 존재, 검증: reopen/render.
- [ ] `P08-03` 산출물 `object geometry module` 존재, 검증: page/paragraph anchor fixtures.
- [ ] `P08-04` 산출물 `shape lowerer` 존재, 검증: property/readback tests.
- [ ] `P08-05` 산출물 `effect model` 존재, 검증: visual diff.
- [ ] `P08-06` 산출물 `object graph operations` 존재, 검증: graph invariant tests.
- [ ] `P08-07` 산출물 `chart adapter` 존재, 검증: target readback/export.
- [ ] `P08-08` 산출물 `active-content policy` 존재, 검증: security corpus.
- [ ] `P08-09` 산출물 `object report` 존재, 검증: required matrix green.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
