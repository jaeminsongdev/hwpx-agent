# P09-109 인증된 저장 댓글 본문과 기존 최종 compiler 연결 보고서

## 실제 구현

기존 StoredFormProvider의 sealed revision-selected source/IR readers 및 stored state/context를
P108 실제 rich Flow body/final compiler preparation에 연결했다. 기존 body 전체는 실제
다운로드한 IR root property에서 읽으며 caller existing body override를 받지 않는다.
새 삽입 body만 기존 strict request/논리 anchor 아래 명시적으로 제공한다.

canonical outer graph와 inner body JSON 문자열을 별도로 확인한다. private typed DTO와
exact canonical equality로 missing/unknown/duplicate/lexical aliases를 거부한다.
원래 state/body order/ID/digest/style/resource/table/nested caller protection/partial/whole
document guards 및 P108 final target hash/compiler를 유지한다. main Flow를 body로 덮지 않는다.
fresh source와 IR의 독립 ACL/AEAD/scanner/head/scope 재검증 후 전체 body/compiler를 replay한다.
getter는 memory candidate이며 반복 읽기는 atomic lease/CAS나 publication 권한이 아니다.

원래 P94 서비스 API/AES-GCM을 실제 호출했지만 repository/scanner/actor와 완전한 caller IR은
in-memory/synthetic fixture다. source fixture bytes는 native HWPX가 아니다.
이 검증을 실제 SQL durability, native author/time/state/source import 또는 Gate로 승격하지 않는다.
검토한 P95 보고서의 locked actual capture는 native metadata positive가 없으며, 보관된 공식
fieldBegin.h/cpp의 generic parameters/metaTag 지원은 author/time/state 의미를 확정하지 않는다.
원본 native 미확정 값은 그대로 유지하며 synthetic fixture 값을 native default로 쓰지 않았다.

## 검증

- 최종 Rust389 실행 PASS, failed/ignored0: unchanged package182 + current product207.
- product207 = original comment16 + stored form/import167 + stored comment24.
  stored comment24 = 기존16 + 신규8. unique366 = 이전358 + 신규8.
- 원래 재사용 native8/context7는15 functions의 중복23 executions다.
  actual20 current test executable --list inventory에서 확인했다. 재사용 native 경로만
  정규화하며 다른 모듈의 동명이인 함수를 합치지 않는다.
- 신규8:5 operations direct P108 whole graph/body/final compiler/preservation/privacy,
  inner JSON exact canonical/duplicate/unknown/missing/oversized, complete inventory/order/
  digest/original body structure/protection, independent result/IR ACL/AEAD/quarantine/regrant,
  head 변경 및 download callback, actor/tenant/project/branch/document5 scope 대체,
  insertion/request/partial/document protection, 원래 missing IR/kind/media/scanner/digests다.
- package source는 unchanged다. 원래 P10617 test executables의 exact byte/SHA pin 확인 후
  직접 재실행해182 PASS다. 새 package build/native qualification을 주장하지 않는다.
- 현재 CLI3 suites 재빌드·전체 실행207 PASS, product lib/3 test suites strict lint PASS.
  신규 Rust2 isolated format 및 diff check PASS.
- Python8 whole parent inverse/prior raw/current inventory/claim guard PASS.
- 원래 current-source upstream component15 PASS, green0/OPEN.
  원래 default FAIL:matrix_drift를 확인했고 유지했다.

## 실패와 보존

첫 신규 test compile은 set_permissions 반환형/unit 및 서로 다른 ProjectId/미지정 BranchId
3 errors로 실패했다. 두 번째 test compile 및 진행 중이던 첫 lint는 quarantine 반환형/unit
불일치로 실패했다. 각 exact owned test source를 보존하고 새 테스트만 바로잡았다.
production library check에는 실패가 없었다.

첫 runtime24 실행은23 PASS/1 FAIL이었다. oversized negative의 typed graph 생성이
원래 string ceiling에서 먼저 LimitExceeded를 반환했는데 성공을 기대한 테스트 구성 문제였다.
원래 graph ceiling을 넓히지 않았다. oversized negative를 유지하며 실제 graph 생성 거부 및
실제 stored raw graph 재읽기 거부를 명시적으로 검증했다. 실패 source/executable은 보존했다.
수정된 focused24 PASS는 최종389 count/unique count에 반복 합산하지 않는다.
새 lint allow 또는 원래 guard/test assertion 삭제는 없다.

기존952 source entries 중950 unchanged, 부모2 whole preimages/whole inverses exact다.
부모2에는 각각 새 module declaration만 있다. 원래 함수/test bodies/helper visibility와
P108 body/compiled preparation, P94 source/IR/state/ACL/AEAD/scanner/head/limits는 그대로다.
prior unchanged audit를 exact read-view에서 확인했다. inherited raw1739/old executables278
보존이며 모두를 재실행한 주장은 없다. 그 중 unchanged package17만 재실행했다.
현재962 sources/delta12/archives5/predecessors2/current executables5이다.
현재5는 final test3 + 미실행 CLI1 + failed runtime1이며 실패 executable을 PASS로 세지 않는다.

## 미완료와 다음 경계

실제 원본 author/time/state/native coordinates/source-to-full-comment mapping, HWPX lowering,
durable SQL 제품 통합, trusted issuer/보호/atomic execution/publication, field/Date/external/
document 의미 및 actual P84 SQL cause/regression은 미완료다. route는 fresh 검증 뒤
계속 RouteUnqualified다. native_metadata_verified/hwpx_lowered/execution_authority_verified=false.

최소6 큰 잔여 묶음을 이번 일부 연결만으로 차감하지 않는다. P09/A12/A13 OPEN,
native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED, P26 failed_semantic_non_green,
P62/P84_SQL UNRESOLVED, green0/no P10/product false다. 전체 P09~P20 목표 active.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없이
진행했다. HEAD/사용자 dirty/private/native/실패 증거와 PLANS 삭제 상태를 보존했다.
commands/session/terminal chunks/test inventory/raw pins는 evidence/p09-109-stored-rich-comment.*.v1.json에 기록한다.
