# P11 — Advanced Desktop Features

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P06,P07,P08,P09,P10`

## 목표

Advanced Desktop Features를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P11-01` | HWP import/export | binary HWP와 office formats를 automation 변환한다. | `format adapter` | loss/reopen report |
| `P11-02` | Track changes | enable/display/filter/accept/reject/protect를 연결한다. | `review bindings` | change list readback |
| `P11-03` | Compare/history | 문서 비교·병합·한/글 이력 기능을 구현한다. | `compare adapter` | known-diff fixtures |
| `P11-04` | Chart advanced | chart editing/export behavior를 완성한다. | `chart binding bundle` | visual/readback |
| `P11-05` | Print/PDF | print profiles, PDF options, tagged PDF를 구현한다. | `print/export adapter` | spool/export reopen |
| `P11-06` | External tools | spell/dictionary/translation/assets/provider flow를 구현한다. | `provider adapters` | consent/license/offline tests |
| `P11-07` | Workstation UI | 보기/창/도구상자 session capabilities를 구현한다. | `UI bindings` | session state probe |
| `P11-08` | Advanced security | password/distribution/protection/signature inspection을 연결한다. | `security bindings` | clean-worker audit |
| `P11-09` | Accessibility | alt text, headings, table headers, reading order/checker를 구현한다. | `accessibility suite` | checker and tagged export |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P11-01` 산출물 `format adapter` 존재, 검증: loss/reopen report.
- [ ] `P11-02` 산출물 `review bindings` 존재, 검증: change list readback.
- [ ] `P11-03` 산출물 `compare adapter` 존재, 검증: known-diff fixtures.
- [ ] `P11-04` 산출물 `chart binding bundle` 존재, 검증: visual/readback.
- [ ] `P11-05` 산출물 `print/export adapter` 존재, 검증: spool/export reopen.
- [ ] `P11-06` 산출물 `provider adapters` 존재, 검증: consent/license/offline tests.
- [ ] `P11-07` 산출물 `UI bindings` 존재, 검증: session state probe.
- [ ] `P11-08` 산출물 `security bindings` 존재, 검증: clean-worker audit.
- [ ] `P11-09` 산출물 `accessibility suite` 존재, 검증: checker and tagged export.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
