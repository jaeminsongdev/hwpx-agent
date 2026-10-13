# P09-141 — 실제 계정 기반 Rust SQL22 adapter 검증

## 결과와 경계

고정 digest의 로컬 PostgreSQL 18.4 disposable container에서 원래 migration 1~22와 기존 full-IR 25 assertions, 기존 P140 SQL22 37 checks를 실제 실행했다. 새 `revision-service` example은 reader/root/approval의 별도 LOGIN credential로 원래 Rust adapter에 접속하고 metadata 검사 42개를 통과했다. 잘못된 migration22 fingerprint 연결 거부 1개와 정상 fingerprint 연결 대조 1개도 동일 실행 안에서 통과했다. 최종 run06은 current r5 EXE에 정확히 묶이며 44개 결과, 원래 SQL 검사, 최종 row history, source/EXE 보존, owned container 제거를 함께 확인한다.

이는 **credential-bound 실제 Rust DB metadata 검증**이다. fixture의 artifact descriptor/digest는 synthetic이고 실제 AEAD blob이나 Ed25519 원본 consumer를 이번 DB와 연결하지 않았다. P139 component crypto와 이번 SQL/Rust 결과를 같은 통합 제품 실행으로 합치지 않는다. 운영 key custody, issuer 원천 admission, atomic product publication, 실제 한글 저장/재열기·렌더 Gate는 여전히 검증되지 않았다. P09/A12/A13 OPEN, product false, P10 새 구현 없음, 목표 active, native34 `NOT_RUN / INPUT_CHANGED_RE_ADMISSION_REQUIRED`다. 큰 그룹 최소 6개를 닫았다고 주장하지 않는다.

## 실제 검증 범위

42 checks는 원래 adapter의 schema1..22/fingerprint, forced RLS/table/function/profile admission을 통과한 세 계정의 접속, profile 상호 거부, 직접 table SELECT 또는 internal helper EXECUTE가 추가된 deliberately bad 계정 거부, 정확한 typed root/approval readback, 고정 tenant/subject context 거부, nonmember named read 거부, owner/editor preflight와 capability 거부를 포함한다.

실제 root generation3 등록/commit ack/모든 필드의 fresh named readback, 잘못된 artifact digest와 같은 CAS 재시도 거부, root rotation 뒤 old approval 거부, editor approval generation3 등록/readback, stale root 및 같은 CAS 거부, root 폐기 후 live read 거부, root 없이도 가능한 approval administrative 폐기, duplicate 폐기 거부를 실행한다. SQLSTATE40001/23505의 기존 adapter mapping `RepositoryFailure`를 유지하며 새 typed conflict라고 주장하지 않는다. 최종 history는 root3/approval3, max generation3/3, revocations2/2다. commit receipt echo와 별도 readback을 구분한다. advisory role preflight를 lease/원자성 증거로 바꾸지 않는다.

fingerprint 대조는 원래 불변 schema row를 UPDATE하거나 trigger/constraint를 비활성화하지 않는다. schema21을 원래 migration으로 새 DB에 설치한 뒤 이를 clone한 정상 control과 원본 negative control 각각에 **동일한 원래 SQL22 source**를 적용한다. migration session setting만 exact SHA256 대 deliberately wrong zero digest로 다르다. 계정과 grant statements는 동일하며 정상 control이 전체 admission을 통과해야 negative만 성공한 것으로 포장하지 않는다. empty control DB들은 admission만 확인하며 제품 data readback을 주장하지 않는다.

## 최소 권한과 자원

PostgreSQL 스킬의 최소 권한·forced RLS 지침을 적용했다. 세 정상 계정과 두 deliberate bad 계정 모두 NOSUPERUSER/NOBYPASSRLS/NOINHERIT/NO CREATEDB/NO CREATEROLE다. 원래 adapter가 요구하는 legacy guarded APIs와 SQL20/21 named APIs만 공통 허용하고, SQL22 read2/root writer2/approval writer2는 분리한다. direct SQL22/20/21 table read/write, owner membership, internal helper, schema CREATE는 정상 계정에 허용하지 않는다. 검사를 통과시키기 위해 production admission을 완화하지 않았다.

Rust host connection을 위해 container는 bridge network와 `127.0.0.1`에만 bound한 새 ephemeral port를 사용한다. P140의 network-none/포트 없음 조건과 같다고 주장하지 않는다. 기존 DB/container/설정은 변경하지 않는다. host mount/volume 없음, read-only rootfs, bounded tmpfs, CPU1/RAM512MiB/swap total512MiB/pids64다. 운영 password/trust/private key를 사용하지 않고, 새 무작위 password는 stdin/env로만 전달하여 명령 인수/receipt/log에 기록하지 않는다.

빌드/엄격 lint는 CPU affinity1, BelowNormal, cargo jobs1, 테스트 opt1/overflow/debug assertions 보존이다. probe main 빌드는 dev profile opt1이며 **test harness가 아님**을 compiler artifact profile로 확인한다. Python dispatcher도 CPU1/BelowNormal, Rust child affinity와 우선순위를 실제 확인한다. CPU85% 3회 연속/freeRAM4096MiB 미만 시 owned 실행을 중단한다. build/lint root working set 2048MiB 제한도 유지한다. dispatcher의 container memory 제한과 system RAM 관측을 Rust child working-set 샘플이라고 주장하지 않는다.

run06 17.53초, system CPU 최대12.55%, available RAM 최저15013.58MiB(약14.7GiB), resource stop 없음. 엄격 lint는 32 packages/359 targets 전체의 compiler artifact identity coverage를 대조하고 경고0으로 PASS다. 358에서 새 example 1개가 추가됐다. 이번 수치로 Codex freeze 원인 해결을 주장하지 않는다. 다른 Maple cargo 실행과 CPU91%를 발견했을 때 해당 프로세스는 건드리지 않고 source 작업만 했고, 부하 감소 후 빌드를 시작했다.

## 실패와 역사 보존

r1 compile E0308/E0382 4개와 최초 whole probe를 보존했다. run01/02는 새 fixture의 과거 verified_at 복사로 `23514 / artifacts_time_order` 실패했고 Rust DB는 NOT_RUN이다. 원래 SQL22 37개는 먼저 commit됐지만 새 fixture transaction은 rollback됐다. fixture 시간만 수정했다. run03은 test-profile example이 0-test harness인 설정 문제여서 Rust DB 검증이라고 기록하지 않았다. 그 EXE는 보존하고 bounded `--list`로 zero tests/zero benchmarks를 관측했다. dev main profile로 교정했다.

run04는 실제 metadata42 PASS 뒤 원래 schema immutable UPDATE가 `55000`으로 거부됐으며 전체 성공으로 바꾸지 않았다. 보호 해제 대신 두 admission control DB를 원래 migration으로 구성했다. run05 historical44 PASS를 보존했다. strict lint의 too_many_lines 1개는 suppression 없이 함수 분리로 고쳤으며 원래 42개 검사 순서/조건이 그대로인지 감사한다. final r5로 run06 전체 DB 검증을 다시 실행했다. failed lint/build/engine receipts와 8개 whole source archive를 유지한다. run05 driver archive는 sole count inverse transition 후 기존 receipt의 bytes/SHA256에 정확히 맞는지 확인해 만들었음을 명시한다.

최초 full-history source audit의 `current_workspace_metadata_drift` 실패도 whole auditor와 finding으로 보존한다. P133 이후 historical358 inventory에 새 auto-discovered example이 추가돼 현재359를 보고한 것이었다. 예전 verifier나 receipt를 수정하지 않는다. predecessor 평가에만 현재359/32 inventory를 먼저 확인한 후 exact revision-service example name/kind/source path 1개를 제외한 historical metadata를 제공한다. 그 밖의 target은 그대로라 다른 drift를 숨기지 않는다. 현재359 전체 lint coverage는 별도 검사한다. live 파일 또는 Cargo metadata를 재작성하지 않는 임시 in-memory history view이며 항상 복구한다.

P139 이전 32개 EXE와 P141 r2/r3/r4 3개를 보호했으며 final r5도 pin으로 묶었다. r2는 잘못된 harness로 DB probe 자격이 없음을 유지한다. owned 컨테이너 6개 모두 finalizer 제거와 fresh ID/name inspect로 부재를 확인한다. source guards8은 runtime evidence와 분리한다. 컴파일 실패를 재실행했다고 주장하지 않고 원래 diagnostics/whole inputs/receipts를 대조한다. 원래 migration, adapter, 기존 fixture, P00~P08 evidence, user dirty changes, PLANS.md 삭제를 변경하지 않았고 stage/commit/push하지 않았다.

## 다음 경계

다음은 원래 ArtifactService의 실제 AEAD 저장/회수·issuer Ed25519 생성/검증·원래 consumer·실제 registry DB read/write를 **한 실행에서** 연결하는 것이다. 이번 synthetic metadata 결과만으로 그 통합이나 운영 key custody/atomic publication/native Gate를 닫지 않는다.
