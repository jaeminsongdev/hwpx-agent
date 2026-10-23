# P09 수식 정책 원본 결합 생성·등록 v1

기존 P116 소비 payload/schema/media와 P117 SQL21은 변경하지 않는다. 새 경로는
`StoredImportedDocumentForms::prepare_formula_policy_registration` →
`PreparedFormulaPolicyRegistration::register` → `FormulaPolicyRegistrationRepository`다.

## 입력과 원본 결합

인증된 서버 구성요소가 typed `FormulaPolicyDecision`으로 실제 대상별 명시적 bool을 전달한다.
이 타입/등록 record/prepared object에는 Deserialize 또는 public JSON 승인 endpoint가 없다.
문서의 모든 실제 TableFormula 대상을 대상으로 하며, 누락/중복/외부 대상/비수식 대상/빈 목록과
4096 초과를 거부한다. 기본 허용 또는 caller AST/anchor/hash는 받지 않는다.

원본 artifact/result revision/head/tenant/project/branch/document/subject는 기존 provider에서,
provenance 및 observed form graph는 원래 importer에서, field meaning graph/AST/begin/end anchor는
원래 field importer에서 산출한다. 대상은 실제 reference ID로 정렬한다. 기존 strict P116 wire 및
전체 target binding으로 생성 payload를 다시 검증한다. Data 허용은 native 보호를 대체하지 않는다.

## 저장과 등록

DocumentWrite scope와 expected generation의 SQL i64 범위를 먼저 검사한다.
등록 때 원본과 전체 대상 payload를 재검증한 후 기존 ArtifactService로 formula 전용 Evidence를
암호화 ingest한다. descriptor의 media/kind/verified/available/quarantine/digest/size와 ACL/AEAD
다운로드 및 whole bytes를 확인하고 원본/targets를 다시 검증한다. 서버 등록은 한 번 호출한다.

SQL21 adapter는 기존 scoped named registration/CAS를 사용한다. 모든 반환 row identity/source
digest/head/creator/version/generation/artifact/policy digest를 대조한다. 반환 불일치 또는 commit
acknowledgement 손실은 `OutcomeUnknown`이며 재시도하지 않는다. 실패 또는 모호한 등록에 남은
Evidence는 삭제하지 않는다. 이 메타데이터 등록과 문서 결과 publication은 서로 다른 경계다.

## 미완료 경계

서버 API는 아직 신뢰된 issuer/signature/trust configuration으로 승인된 policy 발급 경로가 아니다.
typed server 결정 자체는 issuer 증거가 아니다. 외부 CLI/HTTP 등록 endpoint를 추가하지 않는다.
실제 SQL21 migration/권한/RLS/ACL/CAS/동시성/철회/rollback은 NOT_RUN이다.
실행 lease, 전체 문서 import, idempotency/publication/native/접근 허용/P09 Gate는 미완료다.
