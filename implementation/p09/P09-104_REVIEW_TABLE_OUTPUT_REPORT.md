# P09-104 실제 메모 빈 표 출력 보고서

## 실제 진척

P09-103이 준비한 실제 원본 위치와 blank native template에서 새 표가 들어간
완성 HWPX bytes를 출력하는 ReviewTableCreationContext::lower_table을 구현했다.
메모·숨김 설명의 2×3 nonuniform 표, 1×1 경계, 기존 메모 표 셀 내부의 2×2 새 표를
원래 renderer/writer/importer로 생성·재읽기했다. 두 whole source archives를 재검증하고
실제 대상 review와 table grid/state, 그 외 expanded parts/section bytes를 대조한다.

최초 nested output은 template wrapper p900과 기존 outer p900의 중복으로
원래 package ID validator에서 거부됐다. closed code id_index_validation_failed를
보존한 뒤, 교체되는 실제 빈 문단의 ID를 그대로 이어 쓰도록 수정했다.
zero는 실제 selected source의 native sentinel일 때만 사용한다.
수정 뒤 nested positive와 unrelated duplicate negative를 모두 통과했다.
원래 ID guards/public create builder/full-Flow 조건은 변경하지 않았다.

전체 rich comment/compiler/Flow/stored execution 연결은 아직 아니다.
동일 header의 원래 template만 지원하며 header reconciliation/opaque ID closure나
native layout/visual fitting/한글 저장·재열기를 완료했다고 주장하지 않는다.

## 검증

- 최종 scoped Rust 326 PASS, failed/ignored0: package159 + product167.
- package159 = 원래 이전138 + reused native8 + P103context7 + 신규 output6.
  신규6: memo/hidden 실제2×3 deterministic output와 exact preservation/paragraph ID 유지,
  1×1 및 요청 치수 변경, 두 whole sources drift/geometry/writer bounds,
  다른 section native table-ID 충돌, 기존 review cell nested actual output,
  다른 문단 duplicate ID의 원래 package guard 거부.
- product: original comment8 + encrypted in-memory stored form/import143 + stored comment16.
  actual SQL/운영 DB acceptance가 아니다. 마지막 library 수정 후 다시 실행했다.
- Python8 PASS: whole prior read-view/inverse와 inventory/bytes/qualification tamper tests.
- package/product scoped strict lint PASS, 신규 Rust3 scoped format와 전체 diff check PASS.
- 원래 current-source component validator15 PASS/green0/OPEN.
  원래 default conformance FAIL:matrix_drift는 유지했다.
- 정확한 commands/sessions/terminal chunks/tested source/executable pins는
  evidence/p09-104-review-table-output.source-regression.v1.json에 기록한다.

## 실패 보존

최초 original writer API 추측에 의한 compile failure, derivative ZIP mimetype 순서 오류
18PASS/1FAIL, 함수 길이/borrow/style lint failures, nested19PASS/1FAIL Patch,
closed code diagnostic0PASS/1FAIL, unbound namespace wrapper17PASS/3FAIL,
original helper arity compile failure, private identity accessor compile failure를 남겼다.
원래 helper/private API/validator를 넓히지 않고 정확한 original APIs와 admitted whole
template namespace 분석, public raw spans를 사용해 수정했다. lint allow/검사 제거는 없다.

실패 executable은 initial target/fixed target 및 별도 diagnostic/unbound-wrapper copy로
보존했다. 수정된 실행은 별도 nested-fixed target이다. 중간 성공 실행 파일이 같은
target에서 후속 빌드로 대체된 경우 그 중간 파일까지 별도 보존했다고 주장하지 않는다.
잘못된 --source-profile current-source-v2 호출은 source_profile_unknown으로 거부됐으며
정확한 --current-source-v2 호출을 다시 실행했다. 실패를 Gate PASS로 바꾸지 않았다.

## 전체 보존과 잔여 목표

이전900 source/evidence entries 중896개 exact unchanged, 부모4개 whole preimage와
선언/export/helper visibility의 whole inverse exact 검사를 통과했다.
원래 P103 audit는 exact prior read-view에서 통과했다. inherited raw1544,
old executables194는 보존 확인이며 historical 모든 검사를 재실행했다는 뜻이 아니다.
현재911 source/evidence entries, delta15, archives17, predecessors2, owned executables39를
raw byte pins로 묶는다. 39에는 failed/unexecuted executable과 CLI도 포함되므로 모두 PASS가 아니다.

최소6개 잔여 묶음은 그대로다. 표 출력은 full comment/rich Flow/compiler 묶음의 부분 진척이다.
metadata/coordinates, durable integration, fields/Date/external/document semantics,
trusted protection/atomic execution/publication, actual P84 SQL cause/regression도 남는다.
Native34 NOT_RUN, P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
P09/A12/A13 OPEN, INPUT_CHANGED_RE_ADMISSION_REQUIRED, green0이며 P10 새 구현은 없다.

접근허용/한글/COM/UI/actual SQL/운영·trust DB/설치·설정/stage/commit/push/삭제·이동을
실행하지 않았다. HEAD/dirty user changes/private/native/failed evidence를 유지하고
root PLANS.md는 삭제된 상태를 유지한다. 목표는 P09~P20 범위 그대로 active다.
