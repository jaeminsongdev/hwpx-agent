# P09-105 저장 원본·템플릿 표 출력 보고서

## 실제 진척

원래 authenticated stored service로 읽은 actual document/template 두 입력을
P09-104 실제 HWPX 표 출력에 연결했다. MEMO와 hidden 설명의 2×3 native output이
direct package output과 같은 전체 bytes/receipt인지 확인했다.
양쪽 독립 source의 권한 회수/AEAD 손상/헤드 변경/범위 대체를 callback 전에 거부한다.
동일 actor/document/generation이라도 다른 service result로 바꾸거나 swap하면 거부한다.
regrant 후 original fresh checks를 다시 통과할 수 있고 stale cache를 승인으로 쓰지 않는다.

현재는 source-authenticated candidate read/output이지 full comment/compiler execution,
durable SQL acceptance 또는 atomic publication이 아니다. route는 fresh failures를 먼저
드러낸 뒤에도 항상 RouteUnqualified다. 이 제한을 없애려고 original guard를 바꾸지 않았다.

## 실제 검증과 중복 구분

- 최종 Rust 실행342 PASS, failed/ignored0: package159 + product183.
- product183 = comment8 + stored form/import159 + stored comment16.
  form159 = 기존143 + 재사용 native fixture8 + 신규 dual-source service8.
- package159에도 같은 원래 native fixture8가 있어 재사용 중복8을 별도로 구분한다.
  중복8을 제외한 최종 unique count는334 = 이전326 + 신규8이다.
  반복 실행을 새 작업이나 새 검사로 세지 않는다.
- 신규8: memo/hidden/direct output 일치와 head/ingest 보존 및 receipt privacy, 양쪽 ACL/AEAD/regrant/
  callback 및 route 우선 거부, 각 head advance, 양쪽 provider scope5/principal 차이,
  같은 actor/document/generation service swap 거부, template kind/scanner admission,
  foreign actual template anchor와 finite writer reject, 준비 후 양쪽 입력의 격리 시 cached
  callback/product route 거부.
- package source가 변경되지 않았으므로 raw-pin 보존 확인된 원래 P104 executable16개를
  직접 다시 실행해159 PASS를 확인했다. 새 package build/qualification로 속이지 않는다.
- Python8 PASS: whole P104 prior read-view/부모 역비교와 inventory/raw/claim tamper checks.
- scoped product strict lint PASS, 신규 Rust3 scoped format와 전체 diff check PASS.
- 원래 current-source component validator15 PASS/green0/OPEN,
  원래 default FAIL:matrix_drift 유지. 이 결과는 새 stored table의 full acceptance가 아니다.
- 정확한 source/executable pins와 commands/session/terminal chunks는
  evidence/p09-105-stored-review-table.source-regression.v1.json에 기록한다.

## 실패와 보존

최초 테스트는 closed error enum의 clone 미구현으로 E0599 compile failure였다.
large limits(392 bytes)의 불필요한 by-value 전달 lint도 발생했다.
closed enum만 Clone을 추가하고 내부 helper limits를 빌려 쓰도록 수정했다.
원래 service/source/builder/parser/guards는 그대로다.

다음 strict lint는 원래 assembly fixture의 중복 module loading을 거부했다.
원래 fixture를 수정하거나 lint allow하지 않고, 이미 공유된 assembly fixture와 원래
native builder만 사용하는 test-only derivative helper로 바꿨다.
이 변경 전22 PASS(원래 native8+P103context7+신규7) executable과 test source를 보존했다.
그22를 최종342에 추가하지 않는다. 현재 helper는 native8만 재사용한다.
격리 검사를 추가하기 전 product182/form158 PASS 실행 파일과 test source도 별도로
보존했다. 이 중간 성공도 최종 검사 수에 추가하지 않는다.

이전911 source/evidence entries 중909 exact unchanged이고 부모2개 whole preimage와
module 선언의 whole inverse exact를 확인했다. 원래 P104 audit는 exact prior read-view에서
통과했다. inherited raw1617/old executables233을 보존한다. old 전체 executable을
재실행한 것은 아니며 그 중 package16개만 재실행했다.
현재922 source/evidence entries/delta13/archives6/predecessors2/current executables6다.
현재6에는 이전22 및 form158 PASS executable, 미실행 CLI가 있어 모두 현재 scope PASS는 아니다.

## 남은 전체 목표와 실행 경계

metadata/coordinates, full comment/rich Flow/compiler, durable integration,
fields/Date/external/document semantics, trusted protection/atomic publication,
actual P84 SQL cause/regression의 최소6개 묶음은 그대로다.
이번 연결은 전체 durable integration이나 full comment 완료가 아니다.

Native34 NOT_RUN, P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
P09/A12/A13 OPEN, INPUT_CHANGED_RE_ADMISSION_REQUIRED, green0/no P10을 유지한다.
전체 P09~P20 목표 active. 접근허용/한글/COM/UI/실제 SQL/운영·trust DB/설정·설치/
stage·commit·push/삭제·이동을 실행하지 않았다. dirty user changes/private/native/실패
증거와 HEAD를 보존하고 root PLANS.md는 삭제된 상태다.
