# P09 — Fields·Forms·Notes·References

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 2026-10-23 phase 경계 명확화

현재 실행 목록은 [P09 경계·잔여 원장](../../implementation/p09/P09_SCOPE_AND_REMAINING.md)을
따른다. 이는 기존 필수 검증을 제거하거나 Gate를 완료 처리하는 변경이 아니다.

- 기능별 소유권은 `FEATURE_COVERAGE_MATRIX.csv`와 개별 계약을 따른다. 아래9개 WBS
  제목만으로 검색19개를 제외하지 않으며 P09 검색19+참조46=65기능을 유지한다.
- `P09-08`의 참고문헌 관리/목록 생성 실행은 REF-043/045의 P11 소유이고, P09는
  REF-044 인용 삽입과 그 실제 field/readback·자료 권한/format 증거를 마감한다.
- `P09-09`의 preview/batch output/label 생성 실행은 REF-047/P11 소유다. P09는
  REF-046 필드의 자료/열 결속·삽입·표시/저장/readback·개인정보/권한 검증을 마감한다.
- 독립 상호참조 새로고침 REF-036·차례 새로고침 REF-040은 P11 소유다. P09 기능의
  초기 생성 결과·필수 평가·결과 보존·저장/재열기 검증까지 제외하는 것은 아니다.
- P10/P13 범용 worker/oracle 구축과 P14/P15 전체 저장/job/원격 서비스,
  P18 전역 RC/DR, P19 운영 배포·장기 secrets 관리는 각 단계 소유다. P09가 사용하는
  로컬 제품 경로·정확한 현재 원본/권한/head/owner·원본 보존·자원 보호·실제 결과
  검증은 계속 필수다. 기존 범용 모듈을 재사용하되 운영 완성 전체를 P09에 합치지 않는다.
- 잔여31묶음(F16/S8/C7)은 완료 근거를 닫을 작업 단위다. 미구현 기능31개나
  테스트91개의 대체 집계가 아니다. P09/A12/A13 OPEN·P10 새 구현 보류를 유지한다.

아래 원 WBS와 hard gate는 이 기능 소유권 해석 및 실제 required evidence와 함께 읽는다.

## 선행 조건

`P05`

## 목표

Fields·Forms·Notes·References를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P09-01` | Field core | named field, date/file/page/section/object result와 lock/update를 구현한다. | `field engine` | field readback |
| `P09-02` | Form controls | text/check/radio/combo/list/date properties와 tab order를 구현한다. | `form model` | input/protection fixtures |
| `P09-03` | Notes | footnote/endnote insert/style/convert/export를 구현한다. | `note engine` | section-specific tests |
| `P09-04` | Comments | insert/style/show/resolve/delete를 구현한다. | `comment model` | author/time/readback |
| `P09-05` | Bookmark/hyperlink | target names, external link policy, edit/delete를 구현한다. | `link/reference module` | dangling/external tests |
| `P09-06` | Cross reference | target graph와 update를 구현한다. | `crossref engine` | rename/update tests |
| `P09-07` | TOC/index | mark/create/update/hide와 numbering linkage를 구현한다. | `TOC/index engine` | multi-level corpus |
| `P09-08` | Citation/bibliography | citation source and generated list를 구현/automation 연결한다. | `citation adapter` | provider/format evidence |
| `P09-09` | Mail merge/labels | data schema, preview, batch output, label layout를 구현한다. | `merge engine` | record count/privacy tests |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P09-01` 산출물 `field engine` 존재, 검증: field readback.
- [ ] `P09-02` 산출물 `form model` 존재, 검증: input/protection fixtures.
- [ ] `P09-03` 산출물 `note engine` 존재, 검증: section-specific tests.
- [ ] `P09-04` 산출물 `comment model` 존재, 검증: author/time/readback.
- [ ] `P09-05` 산출물 `link/reference module` 존재, 검증: dangling/external tests.
- [ ] `P09-06` 산출물 `crossref engine` 존재, 검증: rename/update tests.
- [ ] `P09-07` 산출물 `TOC/index engine` 존재, 검증: multi-level corpus.
- [ ] `P09-08` 산출물 `citation adapter` 존재, 검증: provider/format evidence.
- [ ] `P09-09` 산출물 `merge engine` 존재, 검증: record count/privacy tests.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
