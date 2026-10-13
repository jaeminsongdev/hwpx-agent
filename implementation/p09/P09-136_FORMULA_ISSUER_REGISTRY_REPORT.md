# P09-136 — 서명 승인·신뢰 루트의 영속 SQL22 메타데이터

## 구현 범위

기존 제품의 `FormulaApprovalRepository`/`FormulaIssuerTrustRepository` 뒤에 필요한
영속 이력의 SQL22 up/down source를 구현했다. 새 이력4개, named API6개 및 private helper3개다.
버전/철회 이력은 immutable+forced RLS이고 metadata 외의 키·서명 payload는 저장하지 않는다.
owner-only trust 관리, fixed writer context/active membership row locks, root/policy/approval CAS,
최신값 실패 시 fallback 금지, artifact media/whole digest/ACL/quarantine/크기 및 alias 검사,
head가 이동한 뒤 관리 철회와 데이터가 있으면 거부하는 rollback 경계를 포함한다.

이는 full production issuer 또는 영속 제품 통합 완료가 아니다. typed Rust SQL22 repository와
ArtifactService admission/strict trust payload decoder/원래 서명 소비자 bridge는 다음 구현 경계다.
기존 Rust source/SQL1..21/EXE/원본/native/private/실패 증거는 변경하지 않았다.
SQL22를 기존 exact SQL21 connector에 억지로 연결하거나 조건을 완화하지 않았다.
실제 migration/DB/키·trust 설정/GRANT/설치/한글/UI/접근허용/stage·commit·push/삭제·이동은 없다.

## 검증과 실패 보존

현재 static source 계약12개가 통과한다. schema gate/digest/암묵적 grant 없음, table4개 RLS/immutable/
foreign-key8개, function9개 signature/PUBLIC revoke/search_path, owner-only/fixed subject/잠금 순서,
artifact domains/bounds/ACL, CAS/overflow/인덱스 prefix, latest root의 expiry/revocation,
정책/head/root/approval exact binding 및 head 이동 뒤 관리 철회, empty-history-only rollback을 검사한다.
이 검사는 SQL parser 또는 실제 PostgreSQL 실행 테스트가 아니다. 로컬 Python에는 pglast가 없어
parser를 실행하지 않았고 설치하지 않았다. 실제 SQL 문법·RLS·ACL·CAS·동시성·rollback은 NOT_RUN이다.

초기 source guard는 전체 SQL의 `json` 단어를 검사해 필수 media type `+json`을 평문 열로 오인했다.
테이블 정의의 column type 범위로 수정한 중간 guard에서는 FK 수를9개로 잘못 기대한 것을 확인했다.
실제 설계는 root2 + root-revocation1 + approval4 + approval-revocation1 =8개이며 참조 대상6종도 대조한다.
SQL source를 통과시키기 위해 변경하지 않았고, 초기/중간 두 테스트 파일 전체와 failure receipts를 보존했다.
원래 실패 guard를 다시 실행해 각각12개 중11 PASS/1 FAIL임을 확인한다.
해당 두 오탐에 관련된 up SQL bytes는 그대로이며, down source의 별도 안전 조건만 아래처럼 보강했다.
초기 combined shell은 마지막 diff check 때문에 exit0이었으므로 child exit code는 확인 불가로 남겼다.
중간/진단 반복은 실제 child exit1을 확인했다. 현재12개는 errors/skipped/unexpected successes0이다.
전체 source·전체 assertion 로그는 결과에 첨부하지 않는다.

추가 source review에서 down의 FORCE RLS에 의해 다른 tenant의 이력이 숨겨질 위험과
empty 검사 뒤 concurrent insert 창을 발견했다. 초기 down whole bytes를 보존하고,
explicit rollback gate에 전역 조회 가능한 관리자 역할 및 새4 history table의 transaction-wide
ACCESS EXCLUSIVE를 추가했다. 앱 역할에 superuser/BYPASSRLS를 부여하거나 RLS를 해제하지 않는다.
현재 guard12개를 pre-fix down view에서 실행하면 rollback 계약1개가 실패하고 현재 down에서는 통과한다.
이는 실제 SQL에서 데이터 손실을 재현했다는 주장이 아니라 source counterexample다.

## 이전 증거와 현재 migration inventory

P135 checkpoint51,117 bytes/SHA256
`30c9a61c6bbe9271e75ce2b733ae762e036ed9e82e90be1fbae57f0f88bdf55a`를 고정한다.
원래 검증기의 SQL21 historical view에서 새 SQL22 파일만 과거 migration 열거에서 제외하고
나머지 hash/source/guard/resource/test 이름 검증은 그대로 실행한다. 실제 파일/DB를 되돌리지 않는다.
P135의234개 distinct current-Rust/SQL21-profile 실행 및 marker6개는 historical 증거로 유지한다.
이번에234개를 다시 실행했거나 SQL22 제품 runtime을 통과했다는 주장은 하지 않는다.
현재 실제 up migration inventory는22개 전부를 별도 지문으로 결속한다. 이전1179 source graph에
delta9개를 추가하며 raw inherited pins3291, 초기/중간 whole test archives2개와 pre-fix down archive1개를 보존한다.

## 명령과 다음 경계

- `python tools/p09/verify_formula_issuer_registry.py --source`: current source 계약과 이전 증거 감사.
- checkpoint 게시 후 `python tools/p09/verify_formula_issuer_registry.py`: exact source/archive/migration pins 감사.
- `git diff --check`.
- 정책: `protocol/migrations/p09-formula-issuer-registry-sql21-to-sql22.md`.
- 원장: `implementation/p09/evidence/p09-136-formula-issuer-registry.source-progress.v1.json`.

다음은 SQL22 explicit constructor/typed read/register/revoke/commit-unknown 처리, owner-provisioned
root strict AEAD reader와 원래 Ed25519 live consumer에 대한 제품 adapter다. actual SQL 권한·race·rollback,
production key custody/issuer authority, atomic 실행·publication·transport/native 의미는 미완료다.
최소6 coarse groups/closed0 및 최소30 비완전 조건 유지. native34 NOT_RUN/INPUT_CHANGED,
P09/A12/A13 OPEN, product false, P10 새 구현 없음, 목표 active. PLANS.md 삭제 상태를 보존한다.

PostgreSQL 스킬의 최소 권한·forced RLS·WHERE/JOIN/index 지침을 적용해 PUBLIC/direct grants를
추가하지 않고 tenant/project/정책 generation prefix의 unique indexes를 사용했다.
행 잠금과 FOUND 해석은 공식
[SELECT 문서](https://www.postgresql.org/docs/current/sql-select.html) 및
[PL/pgSQL 문서](https://www.postgresql.org/docs/current/plpgsql-statements.html)와 대조했다.
문서 대조를 실제 SQL 검증으로 승격하지 않는다.
