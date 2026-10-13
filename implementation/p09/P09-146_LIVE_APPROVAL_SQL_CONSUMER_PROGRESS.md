# P09-146 — 현재 consumer의 실제 SQL 승인 철회 경계

## 최신 현재성 — 2026-10-07

current_r4/source0/original/Unchanged의 run09는 실제 SQL22/원래27 checks PASS다.
source901/protected56 closing exact/컨테이너 제거/watcher·소유 Job74 정리를 확인했다.
P09/A12/A13 OPEN/product=false이며 native/전체36/운영 key·durable·atomic은 미완료다.
run10 current_r4/numeric_derivative/Changed는 fixed image 부재로 소비자 전 단계에서
FAIL_CLOSED였다. run07 미생성/coverage 실패와 run08 image missing도 보존한다.
이전 Changed PASS는 아래 당시 build/Source의 역사적 결과이며 current_r4 Changed가 아니다.
현재 자원 정책/계측은 P09-149 최적화 보고서의 최신 항목을 따른다.
원래 authority evidence-negative20은 실제 formatter2회를 포함해 latest actual run01에서
통과했지만 이 결과가 current Changed나 full authority/제품/Gate 감사를 대신하지 않는다.

2026-10-07 03:14: 원래driver의사전hash포함main-call시간/부분IO를수집하는별도collector를
추가했다. driver소스hash는기존run09 pin과동일하다. collector light10/10과실제컨테이너전
missing-build 실패2개만검증했으며새SQL성공/full wrapper cleanupqualification은아니다.
read-only environment run06에서fixedimage가없음을다시확인했다. fullSQL에서cooperative
취소/컨테이너정리를보장한뒤계측을통합해야하며P09-149보고서의미완료경계를따른다.

아래 구현·실행·NOT_RUN 문장은 당시 기록으로 보존한다. 최신 현재성은 위 항목과
P09-149 최적화 보고서/새 exclusive receipt로 판정한다.

## 구현과 범위

기존 example Source에 opt-in `P146_LIVE_CASE=approval` 검증을 추가했다. 기본 실행 경로는
기존 consumer 검사18을 유지하고, 승인 철회 사례에서만 아래9개 actual SQL 검사를 추가한다.
운영 library/provider/SQL migration/보안 역할/원본 파일은 수정하지 않았다.

1. 실제 생성·서명한 현재 승인 version/generation 바인딩 확인.
2. 유효하지만 잘못된 expected generation=2의 철회 거부와 전체 readback 불변.
3. 거부된 CAS 뒤에도 원래 prepared consumer candidate가 독립 evaluator와 동일함.
4. 독립 관리 연결2개와 barrier3를 이용한 동일 승인 철회 경쟁: commit1/denial1.
5. 철회된 승인 named read 거부.
6. prepared candidate의 fresh 검증 실패 및 사용자 callback 호출0.
7. fresh prepare 거부.
8. RouteUnqualified에 불과한 거부가 아니라 정확한 Repository-denial 경로로 제품 route 거부.
9. revision head 불변.

관리 API의 generic RepositoryFailure는 SQLSTATE를 보존하지 않는다. 경쟁 loser를 특정
SQLSTATE/예외 원인으로 단정하지 않는다. 이는 동일 승인 revocation 경쟁이며 issuer
provisioning generation 경쟁, trust/policy 철회 및 consumer 검증 중간의 모든 TOCTOU race를
완료했다는 뜻이 아니다. artifact ingest-count 검사는 기존18에서 시행했고, 새로운 live
철회 뒤 별도 전체 side-effect 검증을 대신했다고 주장하지 않는다.

## 실제 결과와 보존한 실패

- build-r9/r10: 실제 example dev build PASS, 현재 r10 source842/diagnostics0,
  CPU1/BelowNormal/jobs1. build PASS는 DB/native/Gate PASS가 아니다.
- P146 run01: Changed numeric derivative, Rust command60초 timeout → FAIL_CLOSED.
  actual consumer completion/live approval acceptance는 false이고 자기 UUID DB를 회수했다.
  source와 driver 전체 preimage 및 실패 receipt를 보존했다.
- P146 run02: current build-r10, index0 RAM numeric derivative → Changed, 원래18+live9=27 PASS.
  original SQL22 checks37/full IR25/metadata42/Ed25519 서명/원래 mandatory consumer를 유지했다.
  source860/EXE50 before-after exact, final approval revocations3(기존2+새1), root revocations2.
  driver83.78초, system CPU 최대60.68%, free RAM 최소11761.32MiB, resource stop 없음.
  UUID/label 자기 DB 회수 및 ID/이름 부재를 독립 확인했다.
- current unit-build-r4 + P144 unit-run3 + P145 bootstrap-run04: 실제 route6/index5 Rust11 PASS.
  unit6.22초, source847/EXE before-after exact. 새로운 live-denial 전용 typed unit은 별도 미실행이다.
- source/protocol guard6: 초기 테스트가 원래 전용 DB의 PASSWORD 초기화 `ALTER ROLE`까지
  금지해1건 실패했다. 원래 driver와 해당 statement 전체가 정확히 같아야 한다는 검사로
  정정했고 guard6 실패0/오류0을 확인했다. 실제 SQL 실패나 Gate를 통과시키기 위한 보안
  조건 완화가 아니며 초기 실패 기록도 보존했다.
- strict lint-r1: source/EXE hash 뒤 CPU/RAM 안정 조건을 충족하지 못해
  DEFERRED_RESOURCE_PRESSURE_NOT_STARTED. cargo/clippy 실행이나 strict lint PASS로 계산하지 않는다.
- 이어진 idle-preflight-r10 역시20.06초/안정 sample0으로 defer했다.
  system CPU 최대80.71%, free RAM 최소7961.68MiB였으며 새 heavy work는 시작하지 않았다.

## 자원·진단과 역사

P146 driver는 첫 manifest/source/EXE hash 전에 CPU1/BelowNormal을 적용하고 pre-hash
안정 구간을 요구한다. 기존 post-hash admission/continuous CPU85% 3회/free RAM4096MiB
stop, DB CPU1/RAM512MiB/pids64/loopback/no host mount/read-only rootfs/tmpfs를 유지했다.
실행 중 별도 관측에서도 Python/Rust 모두 affinity1/BelowNormal이었다.
Supabase Postgres Best Practices의 최소권한/RLS 지침을 기존 권한 검사 보존에 적용했다.
다른 저장소 Rust 프로세스가 있을 때 빌더가 시작을 거부했으며 해당 프로세스를 중단하지 않았다.

run02 진단은 단계 표식과 pg_stat_activity의 app/state/wait metadata만 제한적으로 수집했다.
관측한 SQL 대기에서 blocked_count는0이었다. 첫 timeout의 정확한 원인이나 SQL deadlock,
Codex freeze 원인/해결을 입증하지 않는다. Windows CRLF 때문에 run02 단계 표식은 빈 배열로
기록됐고, 이후 driver에서 줄바꿈을 정규화했다. DB statement/query text, password, key,
원본 내용이나 전체 로그를 저장/출력하지 않았다.

현재 driver는 unit-build-r4 EXE 추가 보존과 진단 CRLF 정규화를 포함한다. 이 두 변경 이전의
run02 driver 전체를 archive로 보존했다. 변경 후 driver의 새 actual SQL 실행은 아직 NOT_RUN이다.
run02의 Rust source/EXE와 현재 Rust source는 같지만 현재 driver 전체를 실행한 PASS로
재포장하지 않는다. 원본 Unchanged live 승인 철회 사례도 아직 NOT_RUN이다.

archive: p09-146-pre-live-sql-consumer, p09-146-pre-timeout-diagnostics,
p09-146-pre-unit4-and-marker-normalization. P145 이전 current ledger는 당시 snapshot으로
보존하며 새 Source의 current acceptance로 그대로 재사용하지 않는다. PLANS.md는 복구하지 않았다.

## 남은 경계와 다음 단계

P09/A12/A13 OPEN, product=false, goal active, coarse 최소6/닫힌 그룹0을 유지한다.
현재 Changed approval revocation의 좁은 actual component 증거와 전체 P09 완료를 구분한다.
현재 driver 재실행, Unchanged live 사례, strict workspace lint 및 전체 current history audit가
우선 남아 있다. 이후 trust/policy 철회, provisioning CAS/race, 검증 중간 TOCTOU, 남은 corpus,
native 저장·재열기·시각 검증, durable storage/custody/atomic publication/scanner/IR fidelity를
완료해야 한다. 접근 허용/native 실행, push/commit, 원본 삭제/이동은 없었다.
