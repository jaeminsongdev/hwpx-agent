# P09 수식 정책 서명 승인 구성요소 v1

P116 수식 DATA wire/원본 결합/보호 검사, P117 SQL21, P118 생성·등록은 변경하지 않는다.
P119는 명시적 서버 의존성을 요구하는 새 `prepare_formula_with_issuer` 경로다.
기존 unsigned 경로는 trusted 승인 경로가 아니며, 제품 route 거부를 그대로 유지한다.
외부 CLI/HTTP endpoint, 운영 issuer/key/trust 설정, DB migration을 실행하지 않는다.

## 서버 전용 입력과 서명

`PreparedFormulaApproval::from_registration_record`는 P118의 private validated registration record에서만
전체 원본/정책 binding을 산출한다. public JSON에서 승인 flag, key, issuer, clock, signature를 받지 않는다.
issuer identity/time는 서버 typed 입력이며, signing input 또는 envelope 생성 자체가 권한이 아니다.

전용 media는 `application/vnd.hwpx-agent.source-formula-approval+json`,
envelope schema는 `hwpx-agent.source-formula-approval/v1`, claims schema는
`hwpx-agent.source-formula-approval-claims/v1`이다. signature_hex는 lowercase 128 hex다.
Ed25519는 `hwpx-agent.source-formula-approval/ed25519-v1` 뒤의 NUL과 정확한 UTF-8 signed_claims
bytes를 서명한다. 소비 시 JSON을 재직렬화하여 signature input을 바꾸지 않는다.
audience는 `hwpx-agent.source-table-formula-policy`, operation은 `recalculate_table_formulas`다.

envelope/claims/binding은 object-only이며 unknown/duplicate/escaped duplicate/positional array,
trailing JSON과 타입 coercion을 거부한다. envelope 최대16384 bytes, claims 최대8192 bytes다.
서명은 tenant/project/branch/document/source revision/head/result/package/provenance/graph,
policy version/generation/creator/artifact/digest와 issuer/key/trust generation/time를 모두 결합한다.

## 현재 신뢰·원본·승인의 재확인

`FormulaIssuerDependencies`는 현재 정책/최신 승인/현재 trust/서버 clock을 모두 명시적으로 요구한다.
embedded key, request key, default approval, 과거 승인 fallback은 없다.
approval 전용 Evidence descriptor/media/검사상태/격리/전체 digest 및 실제 ACL/AEAD download를 확인한다.
서명 전에 현재 selector를 읽고, 실제 Ed25519 검사 후 정책·승인·전체 trust snapshot을 다시 읽는다.
server tenant/project/current membership와 root active keys를 매번 재확인해야 하는 repository contract다.

허용 시간은 issued_at <= not_before <= now < expires_at, root window 안이다.
전체 lifetime은 서버 제한 이하이면서 86400초 이하, 키1~8개/unique ID, generation1~i64::MAX다.
clock failure/backwards, key/root/proof 변경 또는 철회는 거부한다.
prepared 결과의 verify와 bytes callback도 supplied CURRENT provider/deps로 재검증한다.
generation뿐 아니라 전체 root snapshot/approval/policy digest가 같아야 한다.
이 fresh callback 검사는 lease/transaction/원자적 결과 발행을 증명하지 않는다.

## 제품과 미완료 경계

원래 source/full-target binding, strict request, native 보호, math/output/compiler 검사는 그대로다.
유효한 서명이라도 deny decision/보호/잘못된 후속 section/불완전 제품 route를 허용하지 않는다.
receipt에는 원문 claims/key/서명/actor/document/idempotency key를 포함하지 않는다.

이번 검증은 synthetic in-memory issuer/root/metadata repository와 실제 Ed25519/ArtifactService
AES-GCM/원본 importer/수식 compiler의 결합 증거다. production issuer/key custody,
실제 승인 registry/SQL21/신뢰 root 서명·등록/CLI·HTTP transport/lease/idempotency/publication,
전체 문서 의미·native/한글/P09 Gate는 미완료다. 운영 키를 생성·설치·신뢰시키지 않는다.
