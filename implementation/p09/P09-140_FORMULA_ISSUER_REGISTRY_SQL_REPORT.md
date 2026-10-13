# P09-140 — 실제 PostgreSQL22 metadata·권한·경합 CAS 검증

## 결과와 경계

고정 digest의 로컬 PostgreSQL 18.4 이미지로 새 disposable DB를 만들고 현재 migration 1~22를 실제 엔진에 적용했다. 기존 authorized full-IR SQL fixture의 25 assertions와 새 SQL22 metadata 검사 37개가 commit까지 통과했다. 두 세션의 실제 프로젝트 잠금 경합에서 하나만 generation 2로 커밋하고 다른 하나는 `40001 / FORMULA_ISSUER_GENERATION_CHANGED`로 거부된 것을 확인했다. 생성한 컨테이너는 소유권과 isolation을 확인한 뒤 제거했고 fresh inspect의 missing-object 응답으로 부재를 확인했다.

이 결과는 **실제 SQL 엔진의 metadata/permission/CAS 검증**이다. Rust DB adapter/connection admission, 실제 AEAD artifact나 Ed25519, 운영 private-key custody, 원자적 제품 publication, native 한글 저장·재열기 검증은 아니다. 특히 fixture는 synthetic artifact descriptor/digest/ACL metadata이고 실제 암호화 파일을 저장하지 않는다. 기존 P139 component crypto/consumer 실행과 이번 SQL 실행을 한 번의 실제 통합 제품 실행으로 합쳐 주장하지 않는다.

목표 active, P09/A12/A13 OPEN, 제품 완료 false, P10 새 구현 없음. native34는 `NOT_RUN / INPUT_CHANGED_RE_ADMISSION_REQUIRED`다. 큰 그룹 최소 6개를 이번 단계로 닫았다고 주장하지 않는다. SQL22 실제 엔진 검증의 공백 일부를 해소했지만 전체 DB/제품 그룹 완료는 아직 아니다.

## 실제 확인 항목

37개 고유 named checks는 4개 forced RLS table, 9개 bounded SECURITY DEFINER, 원래 named source formula 등록, owner root 등록·replacement CAS, editor approval 등록·replacement CAS, live 정확한 metadata readback, stale root/approval/policy/trust CAS, wrong digest/alias, root/approval/read profile 간 EXECUTE 분리, 직접 table read/write와 internal helper 실행 거부, reader 쓰기 및 editor root 설치 거부, nonmember·foreign tenant named read 거부, 직접 RLS own/foreign tenant visibility, immutable update/delete 거부, fresh artifact ACL read 폐기, root 폐기와 교체 후 old approval 거부, root 폐기 후에도 approval 관리 폐기 가능, 실패 subtransaction의 row 잔여 부재를 포함한다.

실제 권한 검사는 NOSUPERUSER/NOBYPASSRLS/NOINHERIT fixture 역할 아래에서 수행한다. 관리자는 새 임시 DB의 migration/fixture seed와 관측에만 사용한다. app 역할에는 named function만 허용하고 직접 table 권한을 주지 않는다. 별도 `p140_rls_probe`는 RLS 정책 자체를 시험하기 위해 root table SELECT와 정책식 `current_tenant_id()` EXECUTE만 받는다. 이 역할은 production admission profile이 아니며 다른 internal helper 또는 writer 권한은 없다.

별도 project scope의 contention 시험은 A가 root write 후 fixture-only 3초 잠금 보유를 하도록 한 다음 실제 `pg_stat_activity`의 PgSleep을 관측한다. B의 Lock wait도 관측해야 통과한다. A exit 0/returned generation 2, B exit 3/정확한 SQLSTATE 및 에러 코드, generation history 2행/latest 2/loser 0행, named live read의 승자 version·digest를 대조한다. 임의 순차 실행을 concurrency PASS로 부르지 않는다. PostgreSQL 스킬의 일관된 잠금 순서·짧고 제한된 transaction 지침을 사용했고, 기다림은 전용 fixture에서만 3초이며 운영 코드의 transaction/retry를 변경하지 않았다.

## 환경과 자원

이미지 `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`는 기존 로컬 cache만 사용하며 pull/install하지 않는다. server_version_num은 180004다. 컨테이너는 network none, 공개 포트 없음, host mount/volume 없음, read-only rootfs이며 PostgreSQL·socket·tmp 전용 bounded tmpfs만 사용한다. 실제 검사 전에 container ID/name/label/run UUID/image ID와 isolation을 확인한다. 기존 DB, 컨테이너, 앱 또는 설정을 건드리지 않는다.

컨테이너 CPU 1개, RAM 및 swap total 512MiB, pids 64. Python dispatcher도 한 코어 affinity·BelowNormal이다. 전체 실행 제한 240초, 각 명령/SQL 및 race에는 별도 timeout이 있다. CPU/RAM은 Windows 실제 system times/available physical RAM으로 2초 간격 측정한다. CPU 85% 3회 연속 또는 free RAM 4096MiB 미만이면 다음 관측에서 owned command handle을 중단하고 owned DB를 정리한다. 다른 프로세스를 kill하지 않는다. resource preflight에는 CPU 85% 이상도 거부한다.

최종 run04는 12.37초, 시스템 CPU 관측 최대 12.01%, available RAM 관측 최저 15130.7MiB(약 14.8GiB)다. resource stop은 없다. SQL-only run03은 8.61초, CPU 최대 34.4%, available RAM 최저 14537.04MiB이며 concurrency 실행 전의 historical 결과다. 이 수치로 Codex 앱 멈춤의 원인이 해결되었다고 말하지 않는다.

## 실패 보존

run01은 migration 22개와 기존 full-IR 25 assertions를 통과한 뒤 새 fixture에서 24개의 provisional marker까지 출력하고 SQLSTATE 42501로 실패했다. 해당 transaction은 rollback되므로 24개를 committed PASS로 기록하지 않는다. dedicated direct RLS probe에 정책식 helper의 실행 권한이 빠진 fixture 오류였다. 해당 역할에만 최소 권한을 추가했고 migration/Rust 또는 product profile을 수정하지 않았다.

run01의 컨테이너는 제거됐지만 Docker29의 소문자 `no such object` 메시지를 case-sensitive 제거 확인이 놓쳐 receipt에는 unverified가 남았다. 그 실패 receipt를 수정하지 않고 fresh inspect exit 1/missing-object 관측과 resolution finding을 추가했다. unknown creation outcome도 새 name/run UUID label/image identity 확인 후 자기 컨테이너만 정리한다. Docker 실패 exit만으로 missing-object를 추정하지 않는다.

run02는 초기화 ready 단계에서 SQL 연결이 실패해 migration 0개였다. redacted diagnostic만으로 직접 원인은 확정하지 않았다. image의 초기화 socket server를 최종 server로 오인하지 않도록 owned container 내부 `pg_isready -h 127.0.0.1`로 final TCP-listening readiness를 요구했다. host 포트를 공개하거나 운영 settings/adapter retry를 바꾸지 않았다. run02 컨테이너 제거는 확인됐다.

run01 whole driver/SQL preimage, run03 pre-concurrency driver, run01/run02 실패 receipt와 resolution, run03 성공, run04 최종 성공을 모두 보존한다. 원본 migration/fixture/과거 실패는 수정하지 않았다. 전체 로그나 password 값을 기록하지 않는다.

Harness source contracts는 최종 8 PASS다. 초기 7 PASS/1 FAIL은 금지된 BYPASSRLS token 검사식이 NOBYPASSRLS까지 잘못 일치한 것이었다. whole 실패 guard와 finding을 보존하고 token boundary만 수정했다. SQL/harness/runtime 결과는 이 guard 수정으로 바꾸지 않았으며, 감사에서 원래 1개 실패와 정확한 수정 전이를 재현한다.

## 다음 경계

다음은 별도 제한된 application role/profile로 실제 Rust read/write adapter admission 및 P139 AEAD/signing workflow까지 같은 DB에서 연결하는 검증이다. SQL-only SET ROLE 시험을 credential-bound adapter 연결로 승격하지 않는다. 운영 key custody/issuer 원천 admission, 제품 atomic publication과 실제 native Gate 작업도 여전히 필요하다. 사용자 소유 dirty 변경과 PLANS.md 삭제는 보존하고 stage/commit/push하지 않았다.
