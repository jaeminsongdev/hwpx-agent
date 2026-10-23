# P09-136 — Formula issuer registry SQL21 → SQL22 source profile

SQL22는 서명 승인과 서버 신뢰 루트의 immutable version/revocation 메타데이터다.
기존 SQL21 policy register/read/revoke와 원래 exact SQL17/19/20/21 Rust connectors는 변경하지 않았다.
이 profile의 typed Rust repository/admission/ArtifactService adapter는 아직 구현 전이므로
현재 connector를 SQL22에 적용하거나 운영 schema를 올리면 안 된다. actual 적용은 NOT_RUN이다.

## 신뢰 경계

- 신뢰 루트 값과 승인 서명은 bounded AEAD Evidence artifact에 둔다. SQL에는
  artifact UUID/SHA256, issuer/version/generation/lifetime, subject/time 메타데이터만 둔다.
- trust media: `application/vnd.hwpx-agent.source-formula-issuer-trust+json`, 1..32768 bytes.
- approval media: 기존 `application/vnd.hwpx-agent.source-formula-approval+json`, 1..16384 bytes.
- trust register/revoke는 project owner와 별도 명시적 named-function 실행 권한을 모두 요구한다.
  ordinary 제품 DB 역할에는 trust 관리 함수와 private helper 권한을 부여하지 않아야 한다.
- SQL22 writer는 fixed tenant/subject를 기존 role helper로 확인하고 project lock → current
  owner/editor ACL 및 active tenant shared row lock → 필요한 branch lock 순서를 사용한다.
  최신 root/policy/approval counter를 CAS로 확인한다. 실제 race/deadlock 검증은 NOT_RUN이다.
- approval register/revoke는 editor/owner다. 조회는 current membership 및 artifact read ACL을
  매번 확인한다. 등록 artifact는 manage ACL도 필요하며 서로 다른 artifact domain의 alias를 거부한다.
- PUBLIC에는 새 table/function 권한을 모두 철회한다. direct table 권한/owner/bypass-RLS 역할,
  fallback root/default key/unsigned approval/캐시된 이전 latest는 제품 경로에서 금지한다.

SQL에서 Evidence의 `validation_state=verified`를 확인하는 것은 서명 검증이 아니다.
실제 소비자는 원래 Ed25519 domain/audience/operation/whole policy binding/clock/live trust
검사를 그대로 해야 한다. root payload는 메타데이터의 tenant/project/version/generation/issuer/
lifetime와 정확히 일치해야 하며 strict decoder·whole SHA/AEAD·키 수/길이·중복 검사를 추가해야 한다.
owner 관리도 production key custody/독립 issuer authority 설정 완료를 뜻하지 않는다.

## Current/read/revoke

read root는 latest generation을 먼저 고르고 current server time 범위/철회/ACL을 검사한다.
실패하면 이전 root로 fallback하지 않는다. read approval은 기존 SQL21 current policy/head 및
latest root와 exact metadata binding을 대조하고 최신 approval의 철회/ACL/alias를 검사한다.
root 교체·철회는 과거 approval 사용을 막는다. 승인 자체의 expires/not-before/signature 검사는
암호학적 소비자가 한다. 신규 root에서 재발급한 새 approval의 명시적 등록이 필요하다.

관리 철회는 latest version+generation CAS를 사용하되 이동한 원본 head/이미 철회된 root를
다시 유효화해야만 철회할 수 있는 순환 의존을 만들지 않는다. 같은 이력의 중복 철회는 충돌이며
commit acknowledgement 유실 뒤 자동 재시도하면 안 된다. typed adapter는 이 경계를 보존해야 한다.

## 적용 및 rollback 경계

새 adapter가 원래1..22 migration fingerprint, role/RLS/immutable trigger/guarded-write/function ACL 및
bounded search_path를 모두 admission한 후에만 별도 explicit SQL22 constructor를 열어야 한다.
원래 exact SQL21 constructor의 요구 조건을 완화하지 않는다. ordinary 앱 역할은 root관리/private
helper EXECUTE를 금지하고 필요한 named read/approval register/revoke만 명시적으로 부여해야 한다.
이 문서는 관리자 적용 조건일 뿐 GRANT/설정/DB 설치·마이그레이션을 수행하지 않았다.

down source는 explicit destructive gate/latest22/새4 history tables empty를 모두 요구한다.
FORCE RLS 아래의 ordinary owner가 다른 tenant의 이력을 못 보는 상태에서 내려가지 않도록
관리자의 superuser/BYPASSRLS 전역 조회 능력도 먼저 요구한다. 앱 역할에 이 권한을 주는 것이 아니다.
empty 검사 전에 새4 history table에 ACCESS EXCLUSIVE를 걸고 transaction 종료까지 유지해
검사 뒤 concurrent insert를 막는다. RLS 자체를 해제하지 않는다.
다른 source policy 이력은 유지하며 CASCADE/TRUNCATE/강제 데이터 손실을 하지 않는다.
실제 rollback, migration syntax/DDL/functions/RLS/ACL/CAS/race/rollback 검증은 모두 NOT_RUN이다.
소스 텍스트 계약 검사는 PostgreSQL parser 또는 SQL 실행 검증의 대체물이 아니다.

행 잠금 범위와 PL/pgSQL `FOUND` 의미는
[PostgreSQL SELECT](https://www.postgresql.org/docs/current/sql-select.html) 및
[PL/pgSQL statements](https://www.postgresql.org/docs/current/plpgsql-statements.html)의 공식 문서와 대조했다.
rollback 전역 조회 경계는 [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)와 대조했다.
