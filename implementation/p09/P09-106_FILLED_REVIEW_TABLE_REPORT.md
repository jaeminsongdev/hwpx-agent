# P09-106 새 댓글 표의 셀 내용 출력 보고서

## 실제 진척

원래 source-bound blank table creation과 실제 셀의 typed paragraph output을 조합했다.
MEMO/hidden 설명에서 새 표의 선택한 셀에 여러 문단·서식 참조·한글·XML escape·탭·
줄바꿈·여러 run을 넣고, 매번 실제 output 전체를 original importer로 다시 읽는다.
각 셀마다 실제 새 anchor를 도출하므로 이전 output의 anchor를 재사용하지 않는다.
직접 row/cell/address 순회로 nested outer table의 셀을 선택하지 않는다.

canonical 좌표 순서로 같은 요청의 반대 입력 순서도 최종 bytes/receipt/chain이 같다.
각 original lowerer가 나머지 내용의 정확한 보존과 실제 typed readback을 검사한다.
독립 fixture oracle도 blank package의 지정 cell subList 내용만 치환한 전체 expanded
parts와 final package를 대조했다. 기존 4개 빈 셀·geometry·header·private opaque part와
중첩 outer table은 그대로다. blank_creation hash/state는 중간 결과로 명시하고
final package/bytes/chain은 별도로 기록한다. 원본/템플릿 및 stored 서비스는 수정하지 않았다.

## 현재 검증

- 최종 current Rust365 PASS, failed/ignored0: current package182 + current product183.
- package182 = 기존159 + filled table23. filled23 = 원래 native8/context7 재사용 + 신규8.
- product183 = comment8 + stored form/import159 + stored comment16. native8 fixture가
  package의 두 suite와 product suite에 재사용되어15 unique functions에서 총23 중복
  실행이 발생한다. whole current executable --list inventory에서 이를 확인했다.
- 재사용23을 제외한 unique count342 = 이전334 + 신규8. 초기23 PASS, 컴파일/검사
  반복과 전체 historical 실행 파일 수는 여기에 더하지 않는다.
- 신규8: MEMO/hidden 다중 문단의 나머지 전체 parts 정확성과 privacy/중간·최종 receipt
  구분, canonical 순서/모든 셀/1×1, 빈 입력·중복 좌표·128/512/8MiB 초과,
  실제 geometry 밖/u32MAX 좌표, 양쪽 전체 source drift, opaque/DATE payload·dangling
  style·writer 한도, 기존/cross-cell/같은 cell paragraph ID 충돌, nested actual 새 표
  내용 보존과 outer protection 거부다.
- 현재 package/lib/new test 및 current product/lib/기존3 suites strict lint PASS.
- Python whole inheritance/inventory/claim guard8 PASS. 새 Rust2 isolated fmt 및 diff check PASS.
- 원래 current-source component validator15 PASS/green0/OPEN. 원래 default
  FAIL:matrix_drift 그대로이며 이 검사는 새 filled table full acceptance가 아니다.
- exact commands, start/session/terminal chunks, actual executable/test inventory 및 pins는
  evidence/p09-106-filled-review-table.source-regression.v1.json에 기록한다.

## 실패 기록과 보존

초기 lib import는 sibling module 위치를 잘못 사용해 E0432였다. 원래 부모의 named
helper import를 재사용하도록 수정했다. 초기 test는 실제 public span 타입 이름과
crate-private attribute semantic getter를 잘못 사용해 E0425/E0624였다. 원래 public
API를 확대하지 않고 test-only raw span numeric fixture reader로 수정했다.
strict lint의 test-only useless_vec은 배열로 수정했으며 lint를 허용/약화하지 않았다.

수정 전 whole parent1, 초기 lib/test/lint sources3과 초기23 PASS executable1을
별도 경로에 보존했다. 원래 reader/writer/context/cell/style/ID/protection/service/SQL
guards, native builder와 테스트는 바꾸지 않았다. 부모 변경은 module 선언1개이며
이 선언을 제거한 whole inverse가 preimage 전체 bytes와 같다.

이전922 source/evidence entries 중921 exact unchanged, 부모1 whole preimage와
whole inverse를 확인했다. 원래 P105 audit는 exact prior read-view에서 통과했다.
inherited raw1644/old executables239은 보존됐지만 과거 전체 qualification/executable을
재실행하지 않았다. 현재932 source entries/delta11/archives4/predecessors2/current
executables22다. 현재22에는 초기23 PASS 실행 파일 및 미실행 CLI가 있어22개 전부
현재 regression을 실행했다는 뜻이 아니다. 현재20개 test executable만 최종 검사했다.

## 남은 전체 목표와 다음 실제 경로

현재 stored table route는 P105의 빈 표만 연결한다. 다음은 이 filled output을 양쪽
fresh authenticated stored document/template 경로에 연결하고, 권한 회수·격리·head
변경·source 대체/실행 거부 및 bytes/receipt replay를 original guards로 검증하는 것이다.
이 연결도 durable SQL/atomic publication/full comment compiler나 native acceptance가 아니다.

metadata/coordinates, full comment/rich Flow/compiler, durable integration,
fields/Date/external/document semantics, trusted protection/atomic publication,
actual P84 SQL cause/regression의 최소6개 큰 잔여 묶음을 차감하지 않는다.
날짜 parameter/locale/timezone은 미검증이라 추측해 출력하지 않았다.
Native34 NOT_RUN, P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
P09/A12/A13 OPEN, INPUT_CHANGED_RE_ADMISSION_REQUIRED, green0/no P10/full product false다.
전체 P09~P20 목표 active. 한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/
stage·commit·push/삭제·이동 없음. 사용자 dirty/private/native/실패 증거와 HEAD를
보존하며 root PLANS.md는 삭제된 상태를 유지한다.
