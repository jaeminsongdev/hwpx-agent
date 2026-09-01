# P00 — Source·License·Target Freeze

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`없음`

## 목표

Source·License·Target Freeze를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P00-01` | 대상 제품 기준선 | primary/secondary 한/글 제품, edition, exact build, locale, bitness를 결정한다. | `target-profile.yaml 초안` | 제품 정보와 runtime probe가 일치 |
| `P00-02` | Windows 이미지 기준선 | OS build, interactive session 방식, patch policy, image digest를 고정한다. | `windows-image decision` | 깨끗한 이미지에서 설치/실행 smoke |
| `P00-03` | 글꼴·프린터 기준선 | 필수 font set, embedding 권리, 기본/시험용 printer profile을 확정한다. | `font-printer manifest` | font substitution 0인 기준 fixture |
| `P00-04` | 공식 자료 수집 | HWPX/OWPML, Help, ActionTable, ParameterSetTable, Automation, Event, WebHWP 자료를 수집한다. | `source archive inventory` | 모든 파일 URL/date/hash 기록 |
| `P00-05` | Source lock | 원본 checksum, parser rights, 보관 위치, version을 source-lock에 기록한다. | `source-lock.json` | 재다운로드/내부 원본 hash 일치 |
| `P00-06` | Automation 라이선스 | 개인 연구, 사내, 상업 서비스, 서버/VM 범위별 승인 조건을 확인한다. | `license-decision.md` | 법무/사업/기술 승인 서명 |
| `P00-07` | WebHWP·외부 provider 라이선스 | WebHWP, 변환, OCR, 번역, 서명, 폰트 조건을 분리한다. | `provider-license matrix` | 미승인 provider disabled |
| `P00-08` | 기능 baseline 승인 | 609개 baseline과 completeness 방법을 review한다. | `feature-baseline report` | 누락/중복/비기능 분류 review 완료 |
| `P00-09` | P00 gate | 모든 blocker와 미결정을 ROADMAP_STATUS에 반영한다. | `P00 evidence bundle` | 다음 phase 시작 승인 |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P00-01` 산출물 `target-profile.yaml 초안` 존재, 검증: 제품 정보와 runtime probe가 일치.
- [ ] `P00-02` 산출물 `windows-image decision` 존재, 검증: 깨끗한 이미지에서 설치/실행 smoke.
- [ ] `P00-03` 산출물 `font-printer manifest` 존재, 검증: font substitution 0인 기준 fixture.
- [ ] `P00-04` 산출물 `source archive inventory` 존재, 검증: 모든 파일 URL/date/hash 기록.
- [ ] `P00-05` 산출물 `source-lock.json` 존재, 검증: 재다운로드/내부 원본 hash 일치.
- [ ] `P00-06` 산출물 `license-decision.md` 존재, 검증: 법무/사업/기술 승인 서명.
- [ ] `P00-07` 산출물 `provider-license matrix` 존재, 검증: 미승인 provider disabled.
- [ ] `P00-08` 산출물 `feature-baseline report` 존재, 검증: 누락/중복/비기능 분류 review 완료.
- [ ] `P00-09` 산출물 `P00 evidence bundle` 존재, 검증: 다음 phase 시작 승인.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
