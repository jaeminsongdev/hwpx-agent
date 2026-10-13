# P09-117 — 수식 정책 전용 SQL21 소스와 제품 저장소 연결

## 범위

기존 source-form-policy SQL20 테이블/함수/원문과 exact17/19/20 연결 동작은 유지한다.
SQL21은 별도 source_formula_policy_versions/revocations와 dedicated formula Evidence media를 사용한다.
원래 SQL20 source/form graph binding 정의를 바꾸지 않는다. whole field meaning graph/target/AST/anchors는
정책 artifact SHA와 P116의 strict actual-source consumer가 추가로 결합한다.
SQL metadata에는 plaintext policy values/allow flags를 저장하지 않는다.
이 단계의 source/compile 검증은 actual SQL migration/admission/권한/CAS 실행 증거가 아니다.

## 등록·조회·철회

SQL20 전체 role/project/tenant active membership/source-head/artifact type/ACL/state/size 검사 구조를
수식 전용 namespace에 유지한다. 원래 branch FOR UPDATE + latest generation CAS와 immutable history,
revocation/latest-only read 및 양쪽 artifact 접근을 유지한다. source-form media는 formula policy로 받지 않는다.
각 함수는 원래 SECURITY DEFINER/고정 search_path/PUBLIC·helper EXECUTE 금지 구조를 유지한다.
새 up/down은 작성만 했으며 어떤 DB에도 적용하지 않는다. rollback source는 explicit owner gate,
latest schema21 및 empty formula history/revocations가 아니면 거부한다. 실제 rollback은 실행하지 않는다.

## 연결 방식

새 artifact/revision profile은 migration1~21 compile-time 원문 SHA와 DB registry를 LIMIT22로 대조한다.
원래 연결의 exact/prefix 동작을 넓히거나 기본값을 교체하지 않는다.
revision connector는 원래 revision role/RLS/guarded-write checks와 원래 form policy security를
수정 없이 유지하고, 추가로 formula history/RLS/privileges/functions security를 확인한다.
loopback127.0.0.1/NoTls/connect3초/statement5초/lock1초/transaction10초 한도와 redacted errors를 유지한다.
fixed tenant/subject context와 원래 scoped transaction/revision repository/lease/CAS implementation을 사용한다.
새 decoder는 exact request project/branch/document/head 및 typed identities/digests/alias/version을 검사한다.
SQL register의 whole row readback을 같은 transaction에서 확인하고 commit ambiguity는 원래
CommitOutcomeUnknown으로 유지한다. 자동 retry/credential 출력/permission escalation은 없다.

PostgresFormulaPolicyProvider는 private P116 PolicyReadScope만으로 새 repo 요청을 만들고,
원래 P116 target/strict payload/artifact ACL/AEAD/head/revocation 재검사에 연결한다.
새 library adapter가 trusted issuer/서명된 실행 권한/atomic lease를 제공하지 않는다.
실제 원본에서 정책을 생성하는 product registration 서비스와 trusted issuer 검증은 다음 경계다.

## 검증·보존

SQL/Rust source tests는 원래 전체 migration20 guard의 domain-separated derivative,
원래 form security 및 새 formula security 함수의 whole token equivalence를 확인한다.
형식적인 SQL string 검사는 실제 DB 동작 검증을 대신하지 않는다.
기존 부모3개에는 module 선언만 추가하고1047 old source 중1044 unchanged/3 whole preimages와
원래 P116 audit의 preimage-view 실행을 확인한다. inherited raw2162/old executable459를 보존한다.
실패 원문/사용자 dirty/private/기존 migration1~20/native evidence와 PLANS 삭제 상태를 유지한다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, no P10/product false/full goal active다.
최소6 coarse groups 유지/closed0. 최소30 세분 점검 조건은 전수 확정 총수나 feature PASS 개수가 아니다.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않는다.
