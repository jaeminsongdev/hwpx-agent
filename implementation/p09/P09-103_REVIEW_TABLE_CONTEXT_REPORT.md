# P09-103 실제 메모 표 생성 위치·템플릿 결속 보고서

## 실제 진척

원래 최상위 빈 문단용 표 생성기를 메모 내부에서 사용하기 위한 source-bound 준비
경로를 추가했다. ImportedDocumentReviewBodies::prepare_table_creation은 실제
MEMO/hiddenComment 및 그 내부 기존 표 셀의 빈 문단과 실제 원본 native2×2 template를
연결한다. 호출자 치수/ID/XML/임의 Flow hash 대신 원래 package importer와 table
mapper/layout reader의 실제 source anchors, cell IDs와 native track 치수를 사용한다.

기존 공개 create reader/builder/lowerer는 그대로다. 내부 reader는 원래 ruling,
pagination, blank/unmerged/uniform/native-wrapper/insertion-wrapper 검사와 해당
destination section의 native table-ID collision 검사를 재사용한다. 완전히 같은
원본 header만 지원하며 서식 호환성이나 보호/Flow를 임의로 채우지 않는다.
새 profile/domain으로 기존 top-level create context와도 구분한다.

context의 fresh 재검증은 source/template 전체 archive를 묶고 실제 선택과 원래
native guards/readback을 다시 비교한다. 서로 다른 메모 위치는 서로 다른 digest다.
cached observation은 stored access나 실행·발행 권한이 아니다.

**새 표 출력은 아직 구현하지 않았다.** 실제 lowering, header reconciliation,
전체 package ID closure, rich review Flow와 full comment/compiler 연결은 남아 있다.
이 선행 구현을 전체 삽입 기능이나 P09 Gate 완료로 승격하지 않는다.

## 실행한 검증

- Rust scoped regression **320 PASS**, failed/ignored0: package153 + product167.
- package153에는 원래 이전138 검사, 재사용 native table create8 검사, 새 context7
  검사가 포함된다. 반복 실행을 별도 기능이나 추가 unique 검사로 더하지 않는다.
- context7: 실제 메모·숨김 위치, 실제2×2 track/cell IDs, foreign/본문/다른 메모/
  non-paragraph 선택 거부, 두 whole archive opaque drift, nonempty/ID collision,
  원래 template blank/uniform/repeat/header guards, 원래 builder header의 비호환,
  기존 review cell의 전체 ancestor 보호와 finite limits.
- 기존 package 메모 body/cell/paragraph/style/delete/location, full review import,
  metadata/assembly/catalog 및 patch/ID/textflow/lib 검사를 다시 실행했다.
- product comment8 + stored form/import/policy143 + stored comment16 PASS.
  encrypted in-memory repository/ACL/AEAD/head fixtures이며 actual PostgreSQL acceptance가 아니다.
- Python8 PASS: 원래 P102 prior audit/전체 preimage 역비교, inventory/pin 변경,
  원래 guard 변경, duplicate/missing/foreign executable, 근거 없는 qualification 승격 거부.
- package/product scoped strict lint PASS, 신규 Rust2개 format/구문2개/전체 diff check PASS.
- 원래 current-source component conformance15 PASS/green0/OPEN. 이 원래 component
  validator 결과는 새 context의 full product/native acceptance가 아니다.
- 원래 default conformance **FAIL:matrix_drift**를 유지했다.

정확한 실행 command/session/terminal chunk, tested source와 executable pins는
evidence/p09-103-review-table-context.source-regression.v1.json에 기록한다.

## 실패 보존과 수정

최초 빌드는 private module 경로, shadowed header helper, dependency 없는 hex 호출로
실패했다. crate-private packet export와 원래 create hex helper를 사용해 수정했다.
중간 수정이 private source hex helper를 참조한 실패도 별도 preimage로 보존했다.
최초 fixture는 private attribute API를 호출하여 E0624로 실패했다. 최종 fixture는
원래 공개 bounded ZIP와 실제 source span을 사용하며 parser/API를 넓히지 않았다.

최초 scoped context 실행의 14 PASS/1 FAIL은 UNKNOWN native boolean이 기존
review importer에서 거부된 결과를 준비 API 오류로 기대한 테스트 오류였다.
현재는 정확한 기존 table_layout_hwpx_invalid_boolean 거부를 검증한다.
그 실패 executable은 초기 target에 남기고 수정 검사는 별도 fixed target에서 실행했다.
최초13 PASS 단계의 같은 초기 executable은 뒤의 14/1 실패 빌드로 대체되었으므로
이전13 검사 executable까지 별도 보존했다고 주장하지 않는다.

strict lint의 excessive bools/pass-by-value/large packet을 enum/immutable Copy input/
borrowed internal packet으로 수정했다. lint allow/skip이나 기존 guard 삭제는 없다.
명령의 잘못된 package/test target 이름과 validator의 잘못된 --help 호출은 실행 전
거부됐으며 성공/실패 Gate나 원인 분석 완료로 계산하지 않는다.
원래 실제 SQL/native 실패도 최신 component 성공으로 덮지 않는다.

## 보존과 남은 전체 목표

이전890 source entries 중886개는 그대로이며 부모4개는 변경 전 전체 bytes를
보관하고 선언/export/신규 block/helper visibility 변경의 전체 역비교를 통과했다.
원래 이전 audit는 exact prior read-view에서 통과한다. 이전 raw1479와 old executables158
개를 보존했다. 현재source900, source/evidence delta14, archives13, predecessors2,
현재 executable36개는 각각 raw pins를 기록한다. executable inventory에는 초기 실패/
미실행 파일과 미실행 CLI도 있으므로36개 전부 검사 실행/PASS라고 주장하지 않는다.

최소6개 큰 잔여 묶음은 유지한다: metadata/coordinates, full comment/rich Flow/compiler,
durable integration, 남은 fields/Date/external/document semantics, trusted execution/
protection/atomic publication, P84 SQL failure cause/regression. 여기서 하나 전체가
닫힌 것은 아니다. Native34 NOT_RUN/green0, INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, P09/A12/A13 OPEN이다.
P10 새 구현과 full product 완료는 없다. 목표는 active이며 P09~P20 전체 범위를 유지한다.

한글/COM/UI/접근허용, actual SQL/운영·trust DB, 설치·설정, stage/commit/push,
삭제·이동을 수행하지 않았다. HEAD와 사용자 dirty changes/원본/native/private evidence를
유지하고 root PLANS.md는 재생성하지 않았다. 실행한 source/component 회귀와
actual Hangul 저장·재열기/render/differential/Gate는 분리한다.
