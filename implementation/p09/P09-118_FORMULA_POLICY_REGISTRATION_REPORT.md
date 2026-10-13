# P09-118 — 실제 원본 결합 수식 정책 생성·등록 제품 경로

## 구현 범위

P116 policy payload/media/strict decoder/whole actual target binder와 P117 SQL21은 변경하지 않았다.
실제 인증 provider와 원본 importer에서 source binding 및 전체 TableFormula 목록을 산출하고,
typed 서버 명시적 결정만 받아 실제 begin/end anchor, AST digest, whole meaning graph를 결합한다.
외부 JSON approval/issuer/anchor/AST/hash 입력, 기본 허용, 대상 누락/중복/외부 대상은 지원하지 않는다.

prepare와 register의 DocumentWrite/generation/fresh source 검사를 분리했다. register는 generated
payload 전체를 재검증한 후 기존 ArtifactService의 Evidence 암호화 ingest → descriptor/ACL/AEAD
download/whole bytes 검증 → 원본/전체 target 재검증 → trusted server metadata registration 한 번을
실행한다. SQL21 adapter는 original scoped named CAS API와 모든 반환 row 필드 대조를 사용한다.
commit acknowledgement/반환 불일치는 OutcomeUnknown이며 자동 재시도하거나 Evidence를 지우지 않는다.
등록 receipt는 원문 policy decisions, creator, document, anchors를 출력하지 않는다.

## 검증 및 보존된 실패

생산 library cargo check PASS(b5d58d). 첫 test compile8d3d6f/session46560 →3d0060/exit1은
새 quarantine test match arm의 반환 타입 불일치 E0308과 unused import였다. 새 test 파일만 수정하고
whole failed source를 보존했다(0c32e1). original guards/fixtures/SQL/dependencies는 변경하지 않았다.

첫 targeted runtime553ce2/session83374 →b7879a/exit1은 10 PASS/1 FAIL/197 filtered(141.90초)다.
실패한 새 테스트는 원본36개가 모두 수식 정책 등록 가능하다고 잘못 가정했다. 독립 원본 ZIP/XML
census(e71845)는16 formula inputs/20 no-formula inputs/16 native FORMULA fields를 확인했다.
기존 original typed importer로 각 원본을 별도 대조하고,16개 complete generated policy 등록·소비와
20개 no-formula policy 무저장 거부를 모두 검증하도록 테스트를 바로잡았다. no-formula 거부 guard와
36개 frozen corpus/size/SHA/original source는 변경하지 않았다. 실패는 PASS로 덮어쓰지 않았다.

첫 strict lint37bdbe/session91757 →4b87be/exit1은 새 test의 semicolon 스타일3건이다.
whole failed test와 failed runtime executable을 함께 보존했다(9c913d).
새 test 스타일만 수정했으며 suppression은 추가하지 않았다. 최종 strict lint fa9d2b/exit0 PASS.
new Rust4 only format and parent diff check502c2b/exit0 PASS.

생산·test·module parents6 전체 bytes/SHA를469262에서 고정했다. 이후 source는 수정하지 않는다.
최종 scoped regression d82440/session45941 →a3f81a/exit0은 artifact lib25 + CLI lib6 + product10 +
stored208 + form operation18 + revision lib20 =287 PASS/failed0/ignored0/filtered0다.
새 registration tests11개는 stored208에 포함하며 추가로 더하지 않는다. stored423.41초,
product12.95초, form11.68초이며 성능 승인 수치가 아니다. hwpx-package136/전체 workspace 또는
actual SQL/native qualification을 재실행했다는 주장은 하지 않는다. accepted run 중 source freeze6은
f59949/exit0에서 whole bytes/SHA exact로 다시 확인했다. HEAD unchanged/PLANS absent/Hwp0.
6 final binaries --list9cb8f6에서287 distinct binary+fully-qualified test pairs를 확인했다.
목록은 실행 증거가 아니다. initial failed regression executable은 final PASS 수에 포함하지 않는다.

current-source conformance6ad8b5/session25861 →ace9a2/exit0은15 upstream PASS/green0이며
original historical default matrix_drift는 유지한다. conformance는 native/SQL/제품 Gate 증거가 아니다.
unmodified P117 audit on exact parent preimage view47ea68/exit0 PASS: original1062 중1060 unchanged,
whole parent preimages2/inverse exact, inherited raw2206 및 prior executable473 보존.
최종 새 source/receipt/executable pin 검사와 negative evidence tests 결과는 동일 이름의
source-progress 및 final-audit 원장에 기록한다. 테스트 목록이나 이 문서만으로 Gate를 승격하지 않는다.

## 남은 경계

이번 경로는 서버 source-bound policy DATA generation/metadata registration 구현이다. typed server
decisions는 trusted issuer/signature/trust configuration 증거가 아니다. 실제 SQL21 migration/security/
role/RLS/ACL/CAS/revocation/concurrency/rollback/registration/readback은 NOT_RUN이다.
SQL21 adapter를 컴파일한 것으로 DB 실행을 주장하지 않는다. 단위 서버 저장소는 synthetic in-memory다.

whole import/metadata/coordinates/comments/rich compiler/field-Date-external-document 의미,
atomic execution/idempotency/publication/CLI·HTTP transport/native acceptance와 P84 SQL unresolved가 남는다.
최소6 coarse groups/closed0 유지, 최소30 세분 완료 조건에서 이번 부분 구현만으로 차감하지 않는다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, no P10/product false/full goal active.

한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않았다.
HEAD1f8cd23/P00~P08/user-owned dirty/private/original native/failed evidence/PLANS 삭제 상태를 보존한다.
