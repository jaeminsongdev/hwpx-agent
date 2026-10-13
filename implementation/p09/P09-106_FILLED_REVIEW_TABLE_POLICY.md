# P09-106 새 댓글 표의 셀 내용 출력 정책

## 원래 제품 경로의 실제 조합

P09-103 원본·native template context, P09-104 실제 빈 표 출력,
P09-100 실제 셀의 typed paragraph 출력과 원래 whole-package writer/readback을 조합한다.
호출자는 신규 표의 행·열 좌표와 명시적 TextFlow 문단만 제공한다. 원본 셀 ID,
XML, source offset, native author/time/state, full-Flow hash나 승인 비트를 받지 않는다.

원래 context/profile/ID/style/protection/writer 검사를 바꾸거나 빠뜨리지 않는다.
각 셀 출력 직후 실제 결과 전체를 original source/forms/review importer로 다시 읽고,
실제 생성된 표의 좌표에서 새 source anchor를 구한다. 앞선 출력의 stale anchor는
재사용하지 않는다. 내부 원본 문단 위치는 context의 실제 source anchor에서만 도출한다.
셀 탐색은 직접 자식 row/cell/address 순회이며 nested outer table의 셀을 선택하지 않는다.
중복 native cell address나 모호한 생성 표 선택은 거부한다.

## 제한·결정성·증거

입력은 비어 있지 않은 최대128 수정 셀, 셀별 비어 있지 않은 문단,
합계512 문단/원래 writer가 만든 typed XML8MiB 이하다. 원래 더 엄격한 cell-body
한도와 실제 요청 geometry, native style/ID/보호/출력 한도는 출력 시 다시 검사한다.
동일 셀 좌표의 중복은 거부하며 canonical 좌표 순서로 정렬해 결과가 입력 순서에
의존하지 않게 한다. 어느 셀에서 실패해도 부분 artifact를 반환하지 않는다.

receipt의 blank_creation은 명시적 **중간 빈 표** 증거다. 그 output/grid/state hash를
최종 채워진 표의 whole native state 증거로 바꾸지 않는다. final_package_sha256과
cell_output_chain_sha256, 채운 셀·문단 수는 별도로 기록한다.
각 original cell output의 선택 외 전체 내용 보존과 fresh whole reimport를 조합해
geometry/수정하지 않은 셀/나머지 expanded package parts의 정확성을 유지한다.
with_verified_bytes는 최종 immutable artifact의 무결성 확인일 뿐 접근권한이 아니다.
객체 Debug는 redacted이고 receipt에는 입력 본문이나 비밀정보를 넣지 않는다.

## 아직 미완료인 전체 목표

P09-105 stored table 경로는 여전히 빈 표 출력만 연결돼 있다. 이번 package API는
아직 그 저장 서비스에 연결되지 않았으며 full rich Flow/comment compiler/insertion,
author/time/state/caret, 전체 opaque ID closure 및 문서 보호 의미의 완성이 아니다.
필드·날짜의 native parameter/locale/timezone은 검증되지 않았으므로 추측하지 않는다.
durable SQL/실제 P84 SQL 원인, trusted issuer, atomic execution/publication,
native save/reopen/render/differential/P09 Gate는 이번 증거가 입증하지 않는다.

최소6개 큰 잔여 묶음은 그대로다. native34 NOT_RUN/green0,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
INPUT_CHANGED_RE_ADMISSION_REQUIRED, P09/A12/A13 OPEN, no P10/full product false다.
전체 P09~P20 목표 active. 한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/
stage·commit·push/삭제·이동을 하지 않는다. 삭제된 root PLANS.md는 재생성하지 않는다.
