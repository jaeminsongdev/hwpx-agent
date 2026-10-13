# P09-116 — 실제 수식 필드에 결합된 저장 정책 데이터

## 적용 범위

기존 form-control 정책을 수식 필드 권한으로 재사용하지 않는다. 별도
FormulaPolicyRepository와 application/vnd.hwpx-agent.source-table-formula-policy+json
Evidence artifact를 사용한다. schema는 hwpx-agent.source-table-formula-policy/v1이다.
이는 서버 저장소가 선택한 정책 **데이터** 검증이며 외부 trusted issuer, 서명 검증,
운영 SQL 저장소, atomic lease 또는 실행 권한의 완료를 뜻하지 않는다.

## 실제 원본 결합

원래 인증된 sealed Result에서 source scope/head/package/provenance/form graph를 검사한다.
추가로 원래 field ranges/semantics의 전체 meaning graph와 모든 TableFormula target의
reference ID, begin/end source anchors, original typed AST SHA를 정확히 대조한다.
현재 값이 이미 계산된 target도 반드시 explicit allow_recalculation bool을 가진다.
빠진/추가/중복/다른 필드/다른 source anchor/AST/graph target은 거부한다.
rule 순서는 허용하되 원본 bytes SHA와 sorted target binding SHA를 구분한다.
모든 실제 수식 target이 허용된 경우만 공통 제품 요청을 준비한다. 허용 데이터는
원래 native mutation protection을 덮어쓰지 않으며, protected current/no-op도 거부한다.

## 저장·해석 경계

원래 artifact 서비스의 descriptor/ACL/AEAD/quarantine/validation/size/digest를 유지한다.
1 MiB 이하의 explicit object만 해석한다. root/binding/rule/anchors positional arrays,
unknown/duplicate/escaped duplicate keys, missing fields, boolean coercion, trailing bytes와
빈 target은 거부한다. caller request에 policy/issuer/approval/AST/results/artifact/path를 넣어
권한을 획득할 수 없다. 원래 v2 request parser는 읽기 전에 같은 strict envelope 검사를 한다.

## 원래 제품 API 연결

StoredProductRequest::prepare_formula_with_policy는 원래 v2 source-only request와 동일한
인증 source를 사용한다. source import → fresh field policy binding → all-target permission →
원래 formula factory/math/lowerer/OperationPlanCompiler → fresh policy 재검증 순서다.
후속 verify는 원래 source/math/candidate 검사의 전후로 정책을 재선택한다.
with_verified_bytes는 consumer callback 직전에도 latest/revocation/ACL/source/target 검사를 한다.
policy/version/bytes/whole receipt가 바뀌면 old cached preparation을 사용하지 않는다.
owned immutable private 객체이며 caller Deserialize grant와 self-reference/unsafe는 없다.

이 검사는 transaction 중의 권한 lease가 아니다. 소비 뒤 변경을 막는 SQL lock/CAS,
execution manifest/issuer/idempotency/publisher/transport는 미완료다. 원래 ungated v2 API는
unqualified read-only preparation으로 유지한다. 두 API의 actual product route는 계속 거부된다.
NoChange는 원래 exact lowerer/protection 검사만 인정하고 empty plan이나 실행 PASS를 만들지 않는다.

## 보존·검증 경계

기존 부모4개 whole preimages와 module3/accessor/shared factory의 exact inverse를 검사한다.
원래 P115 checker는 P116 preimage read-view에서 수정 없이 실행한다.
1034 old source 중1030 unchanged와4 whole parent preimages, inherited raw2114/old executable440을
보존한다. 과거 native/SQL qualification 전체를 재실행했다는 주장은 하지 않는다.
실제 input36 및 원래 fixture bodies/scanner/ACL/compiler/guard/failed evidence를 보존한다.
최종 source가 고정된 뒤 실행된 회귀만 최종 통과 수로 세며 focused/failed runs를 중복 합산하지 않는다.

한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않는다.
PLANS 삭제 상태, P00~P08 및 사용자 dirty/private 원본을 보존한다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, product false/no P10/full goal active다.
최소6 coarse groups 유지/closed0. 대화의 최소30 세분 점검 조건은 전수 확정 총수나 feature PASS 수가 아니다.
