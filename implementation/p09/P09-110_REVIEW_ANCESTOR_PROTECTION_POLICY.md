# P09-110 — 실제 댓글 상위 표·셀의 관측된 보호 검사

## 요구사항과 범위

P09~P20 전체 목표와 P09 선행 Gate를 유지한다. 댓글/MEMO/hiddenComment를 감싼
MAIN 표·셀의 실제 보호 속성을 댓글 경계 때문에 무시해서는 안 된다.
실제 원본을 읽는 기존 hwpx-package 편집 경로를 수정한다. 새 임의의 XML 입력,
작업 권한, 보호 정책 또는 원본 작성자/시간/상태를 만들어 내지 않는다.

## 변경 계약

1. 기존 selected-to-review-body 검사와 정확한 자손 선택을 그대로 유지한다.
2. 그 검사 뒤 실제 review body에서 같은 XML 문서 root까지 상위 요소를 검사한다.
   기존과 동일한 `hp:tc/@protect`, `hp:tbl/@lock`, 그 표의 직접 자식 `hp:sz/@protect`
   규칙만 사용한다. 다른 namespace의 속성이나 알 수 없는 보호 의미를 추정하지 않는다.
3. 공통 `lower_body_target`에서도 선택 위치에서 root까지 검사한다. 전체 댓글 본문
   편집이 개별 문단·셀 편집의 보호 검사를 우회할 수 없다.
4. 실제 source/marker/path 검증 뒤, NoChange/목표 값 검사/patch/writer보다 먼저 보호를
   검사한다. 다른 원본은 여전히 Source 오류가 우선한다.
5. 기존 상위 속성의 0/false 허용 검사는 바꾸지 않는다. 더 강한 원래 importer의
   native boolean/필수 속성 검사를 약화하지 않는다. 원래 importer가 거부한 false나
   누락 속성을 성공 출력으로 세지 않는다. 미관측 속성은 전체 보호 허용 증거가 아니다.

재귀 호출은 review body != XML root일 때 root를 종료점으로 한 번만 추가된다.
실제 XML의 기존 parent chain과 유한 parser 예산을 이용하며 caller offset/ID를 받지 않는다.
원래 출력의 package ID/스타일/opaque/예산/readback/외부 영역 byte 보존 검사는 그대로다.

## 검증과 원본 보존

새 자식 테스트 파일은 기존 support fixture와 native package builder를 사용한다.
원래 테스트 본문을 복사하거나 접근 제한을 풀지 않는다. 기존 부모 3개를 전체 byte로
사전 보존하고, 정확한 guard/module 추가만 제거한 결과가 사전 원본과 같은지 검사한다.
수정 전 실제 보호 우회, 최초 테스트 compile 오류, 강한 기존 validator와 충돌한 fixture,
그 실패 실행 파일을 보존한다. 실패/반복 실행/중복 포함 함수는 최종 통과 수에 더하지 않는다.

core package가 변경되었으므로 이전 P106 실행 파일을 현재 코드 검증으로 재사용하지 않는다.
새 target에서 관련 package 17개 및 product 경로 3개 suite를 새로 빌드하고 실행한다.
전체 과거 qualification 또는 모든 저장된 실행 파일을 재실행했다는 주장은 하지 않는다.

## 완료로 승격하지 않는 경계

이 수정은 관측된 원본 상위 보호의 fail-closed 경로를 강화하는 것이다.
full native protection/author/time/state/coordinates, full comment source mapping,
실제 SQL 내구 통합, trusted issuer/atomic 실행·publication 및 P09 Gate 증거가 아니다.
최소 6개 큰 잔여 묶음을 차감하지 않는다. Native34 NOT_RUN,
INPUT_CHANGED_RE_ADMISSION_REQUIRED, P26 failed_semantic_non_green,
P62/P84_SQL UNRESOLVED, P09/A12/A13 OPEN/green0/product false/no P10을 유지한다.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/
삭제·이동 없이 진행하며 PLANS.md 삭제 상태와 사용자 dirty/private/원본·실패 증거를 보존한다.
