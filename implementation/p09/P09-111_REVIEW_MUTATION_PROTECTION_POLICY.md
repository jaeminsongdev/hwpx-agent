# P09-111 — 삭제·교체의 관측된 보호 범위

## 원래 제품 요구와 변경 범위

P09~P20 전체 목표와 P09 선행 Gate를 유지한다. 기존 review 출력이 보호된 MAIN 조상을
무시하거나, 선택한 컨테이너를 삭제/교체하면서 안의 보호된 표·셀을 지워서는 안 된다.
기존 actual-source deletion/body/paragraph/cell 출력 경로를 보완한다. 작성자/시간/상태,
공용 서식의 미확정 보호 의미, native 실행·publication 허가를 만들어 내지 않는다.

## 실제 mutation 검사

- P110의 원래 ancestor 검사 전체를 공통 mutation 검사에서 먼저 호출한다.
- 이어 실제 선택 element의 원본 outer span 안에 포함되는 indexed XML element를 검사한다.
  `hp:tc/@protect`, `hp:tbl/@lock`, 표의 직접 자식 `hp:sz/@protect`에 대해서만
  원래 observed flag 규칙을 재사용한다. caller XML/offset/ID나 새 의미 추정은 없다.
- whole body/paragraph/cell 공유 출력은 공통 검사 뒤 기존 read/values/patch/writer로 간다.
  선택 영역 밖의 보호된 peer는 지우거나 변경하지 않으므로 subtree 검사에서 제외한다.
- 삭제는 paired_targets가 실제로 선택한 모든 wrapper에 대해 동일한 검사를 수행한다.
  MEMO begin과 end 중 하나라도 보호되어 있으면 모든 삭제를 거부한다. hiddenComment의
  실제 direct/ctrl wrapper, bodyless MEMO, foreign/stale source 규칙은 그대로 유지한다.
- 원래 전체 part의 ID/style/opaque/budget/readback/byte preservation 검사를 바꾸지 않는다.
  Source 검증이 먼저이며 보호 거부는 Selection이고 부분 artifact를 반환하지 않는다.

검사에는 실제 XML index를 한 번 선형 순회한다. 원본을 clone하거나 각 자손마다 전체
ancestor chain을 반복 탐색하지 않는다. 기존 parser의 finite 예산을 유지한다.
이건 algorithm 범위 설명이지 실제 native 성능 측정/허가가 아니다.

## 코드 정리와 검증 보존

신규 guard 때문에 처음 strict lint에서 원래 큰 출력 함수 두 개의 line ceiling을 넘었다.
경고를 허용하거나 검사 규칙을 낮추지 않는다. ancestor+subtree 검사를 공통 private 함수로
모으고, 삭제의 모든 target 검사를 private helper로 나눠 original function limits를 지킨다.
원래 source 4개 whole preimage와 정확한 선언된 추가/교체 inverse를 비교한다.
원래 native flag 규칙이나 user-owned assertions/visibility는 변경하지 않는다.
수정 전 6개 보호 우회 회귀의 실제 실패와 lint 당시 source/executable을 보존한다.
새 evidence checker의 첫 읽기 출력 누락으로 생성된 빈 파일도 진단 자료로 보존하고,
빈 Python의 exit0은 검증 통과로 사용하지 않는다. 크기·내용과 실제 테스트 실행을 확인한다.

현재 core가 바뀌었으므로 새 target에서 관련 package17/product3 suite를 새로 빌드한다.
최종 helper 정리 이후 다시 실행하며 초기 성공/실패/반복/중복 포함 함수를 추가 합산하지 않는다.

## 미완료와 금지 경계

공용 memoPr 서식은 section-wide source 참조이며 native protection/cascade 범위가
미확정이다. 이번 확인만으로 새 보호 의미를 부여하거나 스타일 API를 변경하지 않는다.
관측된 mutation 보호와 full native/document protection acceptance를 구분한다.
metadata/coordinates, full comment/rich Flow/compiler/source mapping, durable integration,
fields/Date/external/document 의미, trusted issuer/보호/atomic execution/publication,
actual P84 SQL 원인·회귀의 최소6 큰 잔여 묶음은 계속 남는다.
P09/A12/A13 OPEN/green0, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, product false/no P10을 유지한다.
전체 목표 active. 한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/
삭제·이동 없이 진행한다. 사용자 dirty/private/원본·실패 증거와 PLANS 삭제 상태를 보존한다.
