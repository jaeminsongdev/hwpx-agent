# P09-111 — 관측된 보호를 우회하는 삭제·내용 교체 수정

## 실제 제품 경로 변경

기존 structural review 삭제에는 ancestor 보호 검사 자체가 없었다. 또한 문단/셀/본문을
통째로 교체하면 그 안의 보호된 표·셀을 없앨 수 있었다. 원래 actual-source selector와
출력 경로에서 두 문제를 수정했다. 새 공개 API, request/DB schema 변경은 없다.

공통 private mutation guard는 P110 ancestor 검사를 그대로 호출한 뒤 실제 선택 subtree
안의 tc protect/tbl lock/직접 자식 sz protect를 동일한 기존 규칙으로 검사한다.
삭제는 paired_targets가 고른 실제 begin/end/direct/ctrl wrapper 전체를 검사하고 하나라도
보호되면 artifact 생성 전에 Selection으로 거부한다. 기존 Source 우선순위와 foreign/
nested review/singleton wrapper/ID/style/opaque/finite budget/readback 검사는 그대로다.
검사는 indexed XML 선형 순회이며 각 descendant마다 ancestor를 중복 탐색하지 않는다.
이건 코드 복잡도 설명이지 실제 한글 실행 성능 측정은 아니다.

## 최종 회귀 검증

helper 정리 이후 현재 code를 새 target에서 다시 빌드하고 실행했다. 이전 P110 실행 파일이나
lint 전 초기 executable을 현재 변경된 code의 최종 결과로 대체하지 않았다.

| 범위 | 최종 실행 |
| --- | --- |
| hwpx-package 관련 17 suite | 198 통과 |
| comment_operation | 16 통과 |
| form_stored_provider | 167 통과 |
| stored_comment_provider | 24 통과 |
| 합계 | 405 통과 / 실패·ignored 0 |
| 고유 함수 | 중복 23회 제외 382개, 중복 함수15개 |
| 신규 regression | 8개; 기존 14개와 함께 cell suite22 통과 |
| 신규 evidence Python | 9개 통과 |
| package17 strict lint / 신규 Rust 단독 fmt / 전체 diff check | 통과 |
| 원래 current-source component 검사 | 15개 검증 / green0 |

신규 regression은 두 review kind의 MAIN ancestor 3flag, 삭제되는 body의 표·셀 3flag,
문단 통째 교체, 보호 nested table을 포함한 outer cell 교체, whole body에서 values/writer
이전 차단, Source/foreign 선택 우선순위를 검증했다. 보호된 peer가 있는 문서에서도 다른
실제 문단은 편집 가능하며, MEMO 삭제는 잠긴 hidden peer와 MAIN 및 모든 다른 part를
byte-exact로 보존한다. 실제 anchor/spans로 예상된 expanded package 전체를 비교하고
다시 import했다. 새로운 권한이나 native 작성자/시간/상태 값을 만들지 않는다.

## 실제 실패와 수정 과정

원래 P110 production code와 신규 fixture로 실행한 첫 suite는 16 통과/6 실패였다.
6개는 실제 보호 누락이며 fixture의 부정확한 기대값으로 바꾸지 않았다. 그 test source와
실패 executable을 별도 보존했다. 첫 guard의 focused22 및 package/product 초기405는
통과했으나 strict lint는 큰 함수 두 개의 101/100, 102/100 line ceiling으로 실패했다.
경고 억제/검사 약화 대신 공통 mutation helper와 delete target helper로 분리했고,
현재 최종 code로 전체405와 strict lint를 다시 실행했다. 반복/초기 실행을 합산하지 않는다.
lint 당시 source3개 및 당시 executable21개도 진단 inventory로 보존했다.

첫 evidence 생성기는 완전한 읽기 본문을 얻지 못했는데 빈 입력을 처리해 신규 checker/test가
각 1 byte로 생성됐다. 크기·내용 검사로 발견했다. 그 빈 파일 둘은 진단 archive에 남겼으며
빈 Python의 exit0/무출력은 검증 성공으로 세지 않는다. 읽기 완료/크기 확인 뒤 새 checker를
작성하고 실제 Python9 및 이전 전체 source audit/parent inverse를 수행했다.
원래 파일/guards를 빈 script로 대체하지 않았고, 당시 읽기 handle 상세 원인은 미확정이다.

첫 current manifest 검사에서는 checker의 정책/보고서 경로에 이전 P09-110 번호가 남아
current_group_coverage_drift로 거부됐다. 실패 checkpoint와 당시 변경될 source6개를
whole byte로 별도 보존하고 경로만 실제 P09-111로 고쳤다. 선언한 신규 source가 실제
존재하고 현재 단계 문서 경로인지 검사하는 테스트도 추가했다. scope/guard를 줄이지 않았다.

원래 default conformance는 `matrix_drift`/exit1 그대로다. current-source-v2 component15
통과가 그 실패 해소나 native/full protection/product/Gate PASS를 의미하지 않는다.

## 보존과 현재 원장

이전 source971 중967 unchanged + 변경된 부모4 whole preimage를 검증했다. 본문 한 call의
정확한 private helper 교체, 새 helper/호출/module 추가만 역변환한 전체 byte가 원본과 같다.
이전 raw pin1806과 실행 파일306을 보존했고 원래 이전 audit을 exact preimage view로 검증했다.
현재 source980/delta13/추가 archive17/predecessor2/current executable43이다.
현재 executable43 = 최종 test20 + 미실행 CLI1 + pre-lint 진단21 + 수정 전 실패1이며
진단 파일 전부를 최종 통과로 세지 않는다. 모든 과거 qualification/실행 파일을 재실행한
주장은 하지 않는다. 각 byte/SHA256, 명령/session/terminal chunk와 실제 test inventory는
`evidence/p09-111-review-mutation-protection.*.v1.json`에 분리 기록한다.

## 미완료와 다음 경계

공용 memoPr 서식은 section-wide 참조이며 실제 protection/cascade 범위가 미확정이다.
이번에는 확인만 하고 보호 의미를 추정해 style API를 바꾸지 않았다. 보호 검사의 원본
관측 범위가 보완됐지만 full native/document protection/issuer/atomic execution은 미완료다.
metadata/coordinates, full comment/rich Flow/compiler/source mapping, durable integration,
fields/Date/external/document 의미, trusted protection/atomic publication, actual P84 SQL
원인·회귀의 최소6 큰 잔여 묶음은 유지한다. 실제 native 검증은 별도다.
P09/A12/A13 OPEN/green0, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED/product false/no P10을 유지한다.
전체 P09~P20 목표 active. 한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·
commit·push/삭제·이동 없이 진행했다. HEAD/사용자 dirty/private/원본·실패 증거와 PLANS
삭제 상태를 보존했다.
