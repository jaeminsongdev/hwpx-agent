# P09-148 — 실제 trust/policy 철회 소비자 검증 진행

## 현재 판정

`CURRENT_R4_ORIGINAL_TRUST_POLICY_SQL33_COMPONENT_PASS_CHANGED_NOT_RUN`.
2026-10-07 current_r4/source0/original/Unchanged의 run11 trust/run12 policy는 각각
actual SQL33 PASS/source906·protected58 closing exact/container·watcher·소유Job 정리true다.
원래 evidence-negative20은 실제 formatter2회 포함 bounded owned runner actual run01에서
PASS했으며 legacy 증거 거부 검사와 current SQL qualification을 구분한다.
current_r4 Changed 두 사례/full current authority audit/전체36/native/운영보안·storage·atomic은
여전히 미완료이며 전체 trust_revocation_consumer_qualified=false를 유지한다.
고정 이미지의 반복 부재와 엔진시각 표본/이벤트조회 timeout은 P09-149 보고서를 따른다.
P09/A12/A13 OPEN/product=false/목표active/P10미진행이다.

### 2026-10-07 현재 receipt 계약 연결 (03:03)

current_authority_sql_receipts는authority validator의original/security/history/scope조건을
보존하고current_r4에만immutable build·842source/29helper/보호EXEcoverage·percentage
policy·모든Job readback/정리·watcher정리를요구한다. legacy default조건은whole-AST exact
검사로보존했다. 과거r14를현재r4로수용하거나원본을Changed로재명명하지않는다.
actual receipt audit run01에서승인원본27/trust원본33/policy원본33과964개입력union,
총997bound inputs closing hash를확인했다. Changed3개가없어PARTIAL이며fullauthority
audit/독립absence/strictlint/native/full36/Gate성공이아니다.
전체CPUmax92.58%/가용RAMmin47.5490%/commitmax34.0059%표본을보존한다.
후속최종실패exit보정은light run03 21/21 PASS이며실제감사run01은보정전epoch다.
보정후full-byte actual 재감사는NOT_RUN이다. 자세한실패/원문/IO는P09-149 보고서를따른다.

## 2026-10-06 보존 판정 및 당시 실행 기록

`HISTORICAL_FOUR_TRUST_POLICY_SQL33_CASES_PASS_P149_SOURCE_CHANGED_CURRENT_REPLAY_NOT_RUN`.
P09/A12/A13 OPEN, product=false, 목표 active, P10 새 구현 없음.
전체 제품 목표를 아래 구성요소 결과로 축소하지 않는다.

2026-10-06 업데이트: 사용자 요청에 따라 P149 전반 최적화를 먼저 진행한다.
이 보고서 아래 SQL33/build/lint PASS는 **변경 전 P148 Source에 대한 보존된 실제 결과**다.
P149의 graph digest/immutable borrow 변경 후 최신 제품 PASS로 재사용하지 않는다.
새 Source의 컴파일·제품·SQL 회귀는 NOT_RUN이며
[P09-149 최적화 진행 보고서](P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md)를 따른다.
직전 full current audit는 시작 안정 구간에서 7.75초 만에
`STOP_SUSTAINED_SYSTEM_CPU`로 끝났고 무거운 감사는 시작하지 않았다.
`p09-148-current-authority.progress.v1.json`은 생성되지 않았으므로 감사 PASS가 아니다.

## 구현한 경계

signed SQL consumer에 명시적 `P148_LIVE_CASE=trust|policy` 분기를 추가했다.
기존 P146 승인 철회와 동시에 지정하면 거부한다. 기존 consumer18 검사,
원래 SQL21/22 named API와 fresh policy/approval/trust 검증을 유지한다.

- stale generation 철회를 정확한 repository 실패로 거부하고 전체 원래 row와 candidate 보존을 검사한다.
- trust는 기존 Trust management capability, policy는 기존 PostgresFormulaPolicyRevoker와
  source-bound domain revoke API를 사용한다. 임의 SQL/direct table write나 새 권한은 없다.
- commit acknowledgement의 version/generation/actor/action 또는 policy digest를 대조한다.
- 중복 철회와 named read를 정확히 거부한다. prepared verify/fresh prepare/제품 route는
  정확한 Policy Repository 오류이며 단순 RouteUnqualified를 성공으로 인정하지 않는다.
- callback 0회, 원본 전체 bytes, revision head, artifact.ingested 수와 무관한 authority 보존을 검사한다.
- trust 철회 시 policy-only cached DATA는 보존, policy 철회 시 cached policy는 정확히 거부한다.

기존18 + 추가15 = 각 실행33개 named checks다. 사례별 반복을 고유132개 검사나
남은 제품 작업의 차감 수로 계산하지 않는다.

## 실행 결과와 현재성

| 증거 | 실제 결과와 범위 |
|---|---|
| main build-r12 | E0599 두 건. 잘못 사용한 policy 메서드명. 실패 receipt와 전체 Source 보존 |
| main build-r13 + unit build-r6 + unit-run5 | 당시 코드 빌드와 Rust11 PASS |
| authority run01 / run02 | 당시 trust 원본 Unchanged / RAM 파생 Changed, 각각 actual SQL33 PASS |
| authority run03 / run04 | 당시 policy 원본 Unchanged / RAM 파생 Changed, 각각 actual SQL33 PASS |
| workspace lint-r1 | Clippy too_many_lines 1건, exit101. 검사 완화 없음, 실패 보존 |
| main build-r14 + unit build-r7 + unit-run6 | 보존 확인 helper 분리 후 최신 코드 빌드와 Rust11 PASS |
| P145 bootstrap-run07 | unit-run6 첫 hash 전 CPU1/BelowNormal 및 안정 구간 확인, target exit0 |
| authority run05 | helper 분리 후 최신 trust 원본 Unchanged actual SQL33 PASS |
| authority run06 | 같은 r14 최신 trust RAM 파생 Changed actual SQL33 PASS |
| authority run07 | 같은 r14 최신 policy 원본 Unchanged actual SQL33 PASS |
| workspace lint-r3 | 최신 workspace32 packages/361 distinct targets, diagnostics0, -D warnings PASS |
| authority run08 | policy RAM 파생 Changed 소비자 단계에서 owned_command_timeout. FAIL_CLOSED, 성공으로 수용하지 않음 |
| authority run09 | 같은 r14 재실행 중 STOP_SUSTAINED_SYSTEM_CPU. FAIL_CLOSED, 성공으로 수용하지 않음 |
| authority run10 | r14와 새 bounded streaming driver의 policy RAM 파생 Changed actual SQL33 PASS |
| workspace lint-r2 | CPU 안정 구간 미확보로 DEFERRED, lint_started=false. 최신 strict lint PASS 아님 |
| idle preflight-r21 / r22 | CPU 안정 구간 미확보, 추가 heavy work 미시작 |
| idle preflight-r23 | 가용 RAM 1385.74MiB로 중단 기준4096MiB 미달, heavy work 미시작 |

run01~04는 helper 분리 전 역사적 실행이다. 최신 policy/Changed 실행으로 승격하지 않는다.
최신 trust 두 사례(run05/06)와 policy 원본(run07)/Changed(run10)는 각각33 검사가 통과했다.
실패 run08/09는 그대로 보존한다. full current authority audit는 아직 NOT_RUN이다.
run01~05는 원래 full IR fixture25, SQL22 checks37, credential metadata42,
동일 migration/grants의 schema fingerprint negative/control2를 유지했다.
real AEAD/Ed25519/원래 소비자/실제 DB를 한 실행에 결합하지만 blob/key는 RAM,
scanner/baseline은 synthetic이다. 운영 durability/custody/native 증거가 아니다.

최신 CPU1/BelowNormal Python 실행에서 source guards8, 기존 evidence guards7,
owned absence guards5, 실패 보존 guards7, admission diagnostics guards5, bounded pipe guards8 = 40 PASS다.
네 최신 성공 실행 전체를 요구하는 여덟 번째 evidence suite 사례는 full auditor에서 실행한다.
부분 검사40 또는 네 SQL 사례의 통과가 전체 감사의 성공을 대신하지 않는다.
기존 승인 source guards6은 최신 full auditor에서 재검증하도록 구성했다.

## CPU·RAM과 권한 보존

소유 빌드/테스트/SQL worker는 CPU1/BelowNormal/jobs1 또는 test-threads1이다.
driver 첫 hash 전에 제한과 안정 구간을 확인한다. CPU<=50%, RAM>=8192MiB 연속3회,
2초 간격/최대20초의 admission과 CPU>=85% 연속3회 또는 RAM<4096MiB 중단을 유지한다.
전용 DB는 CPU1/RAM512MiB/pids64/read-only rootfs/tmpfs/no host mount다.
Postgres 스킬의 최소권한·RLS 지침에 따라 원래 roles/grants/FORCE RLS를 변경하지 않았다.

run01~04 system CPU 최대21.94/30.18/34.67/79.22%, available RAM 최소
13328.67/13306.58/13380.28/13158.79MiB. 최신 run05는54.14초,
CPU 최대49.86%, available RAM 최소12412.95MiB였다.
lint-r2 admission은 CPU78~93%로 보류됐다. 이후 별도 cargo/rustc의 Normal 우선순위와
전체16 logical CPU affinity를 관측했다. 소유 프로젝트는 확인 불가이며 중단하지 않았다.
r23 시점에는 P09 빌드/SQL이 없고 CPU21.19%, available RAM1385.74MiB였다.
run06은84.91초/CPU 최대51.09%/RAM 최소10530.36MiB, run07은63.21초/
CPU 최대68.94%/RAM 최소11734.18MiB, lint-r3은2.27초/CPU 최대17%/RAM 최소12529MiB였다.
run08은77.36초/CPU 최대87.6%/RAM 최소11371.14MiB이며 resource stop은 없었다.
run09 재개 첫 시도는 pre-hash admission CPU 최대87.6%/RAM 최소12173.88MiB로
DB/Rust 미시작이며 receipt 파일도 생성하지 않았다. 이후 독립 GetSystemTimes 관측3회
25.33/22.75/17.49%와 Windows 성능 counter의 낮은 CPU를 확인한 뒤 같은 fresh 경로로 시작했다.
실제 run09는66.21초/CPU 최대93.39%/RAM 최소12214.14MiB였고 마지막3회
85.22/93.39/87.88%로 원래 안전 guard가 중단했다. 무거운 작업을 추가 재시도하지 않았다.
다음 별도 turn에서 bounded pipe 개선/가벼운40 검사 후 fresh run10을 실행했다.
run10은82.46초/CPU 최대82.46%/RAM 최소17763.7MiB, resource_stop_reason=null이었다.
그 실행에서 자신의 Rust PID209384는 BelowNormal/affinity1/RAM18.7~20MiB,
실제8.022초 관측 동안 CPU3.172초 증가였다. 이는 전체 PC/Codex freeze 원인의 증거가 아니다.
이 관측만으로 Codex 멈춤의 원인을 확정하지 않는다.

## 보존과 감사

최신 SQL run05는 source867/protected EXE57의 전후 bytes/SHA exact를 확인했다.
새 streaming run10은 helper 추가를 포함한 source868/protected EXE57의 전후 exact를 확인했다.
기존 strict lint-r3의 Rust 입력/EXE는 그대로지만 해당 receipt의 driver pin은 변경 전 epoch다.
새 auditor는 정확한 whole driver archive와 닫힌 선언 delta로만 이를 수용하며 현재 bytes로 덮어쓰지 않는다.
소유 SQL run01~09는 자신의 UUID/label DB 제거를 확인했다. 기존 DB는 손대지 않았다.
full auditor의 각 현재 DB ID/name 독립 부재 검사는 아직 미실행이다.

전체 bytes/길이/SHA archive를 보존했다: pre-live-authority(P147 Source),
initial-method-binding(E0599 Source), pre-strict-lint-correction(Source/SQL driver/lint).
새 opt-in/helper/import만 제거한 전체 정규화 결과가 P147 Source 전체와 같음을 확인했다.
원본을 되돌리거나 과거 receipt를 수정하지 않는다.

verify_formula_issuer_authority_current.py는 P147 direct pins1023, 전체 archives,
실패/수정 전 실행, 네 최신 실행, Rust11, strict workspace32/target361, guards와
resource/scope negatives를 전후 fresh hash로 묶도록 작성했다. 아직 실행 완료가 아니다.
최초 source graph와 모든 이전 qualification 재실행이라고 주장하지 않는다.

## 다음 단계와 전체 미완료 경계

### 자원 보류 중 독립 정리 증거 보완

idle preflight-r25는 CPU47.17%, available RAM3462.39MiB로
STOP_LOW_AVAILABLE_RAM/미시작을 기록했다. r26도 자원 보류이며, 별도 Normal
cargo/rustc를 관측했지만 소유 프로젝트는 확인하지 못해 중단하지 않았다.

빌드/SQL/native를 새로 시작하지 않고 원래 owned run01~05의 container ID/name
총10개를 각각 docker inspect로 확인했다. 모두 no-such object/container였다.
receipt5개를 전후 fresh hash로 대조하고 owned-absence-run01.v1.json에 기록했다.
이는 원래 cleanup 주장과 별개의 독립 관측이다. 운영/다른 프로젝트 DB는 손대지 않았다.

전체 auditor에 이 독립 증거의 정확한 run/reference/receipt inventory와 CPU1/BelowNormal,
미실행·미완료 scope를 결합했다. 추가 absence-negative 검사5 PASS는 누락/중복/다른
대상/실제 존재·exit0/boolean coercion/제품 승격/제한 변경을 거부한다.
이 문단의 독립 검사 대상은 당시 run01~05뿐이며 최신 run06~09의 독립 부재로 승격하지 않는다.
그 뒤 run06/07 및 strict lint-r3이 통과했지만 policy Changed와 full audit는 미완료다.
이5개 검사나 DB 부재로 SQL 소비자 전체 완료를 주장하지 않는다.
변경 전 auditor/tests/report 전체 bytes를 별도 archive에 보존하여 partial checkpoint26
지문을 현행 파일 또는 정확한 whole preimage로 검증할 수 있게 했다.

### run08/09 실패 진단과 보존

run08의 bounded pg_stat_activity 관측5회와 run09의4회 모두 blocked_count=0이며
Client/ClientRead의 idle 또는 idle in transaction이었다. DB lock 대기 증거는 없지만
이는 CPU starvation·암호화·importer 연산 등 구체적 원인을 확정하지 않는다.
live_progress_markers는 두 실패 모두 비어 있어 실제 마지막 Rust 단계는 확인 불가다.
설치된 Windows Python Popen._readerthread/_communicate 소스를 읽어 EOF 전 partial.stderr가
전달되지 않는 수집 경계를 확인했다. 원래 두 실패의 marker 부재는 미실행 증거가 아니다.

새 BoundedProcessCapture는 공개 pipe의 read1과 두 reader thread로 실행 중 출력을 읽는다.
stdout/stderr 각각32768 bytes 이내 메모리만 쓰며 raw 로그 파일은 생성하지 않는다.
고정 stage allowlist/완전한 줄만 metadata에 전달하고 unknown/malformed/incomplete/출력 초과를 거부한다.
프로세스 wait와 bounded join을 유지해 EOF만으로 살아 있는 child를 완료 처리하거나 busy-spin하지 않는다.
기존60초/전체240초/resource guard/SQL/API/검사33/원본 Rust Source는 변경하지 않았다.
새 실제 pipe8 검사 PASS는 실행 중 marker, 종료 output JSON/stderr 보존, stream별 초과,
chunk/CRLF 경계, unknown/incomplete marker 거부, EOF 전 child 생존, private non-marker 미노출을 검사한다.

run10의 실제 source_begin은 command0.427초, consumer_begin은2.223초에 관측됐다.
이 두 표시만으로 consumer 내부 세부 병목을 확정하거나 성능 개선을 주장하지 않는다.
변경 전 driver37629 bytes/SHA6b408bda…는 whole source archive에 보존하고,
새 import·source inventory·command 수집의 정확한 선언 delta 외 모든 bytes를 대조한다.

두 실패는 product_probe/final_history가 없고 source/executable post-check가 미도달(false)다.
last_command_exit_code=0은 앞선 metadata probe의 값이며 시간 초과/중단된 소비자 성공이 아니다.
새 실패 보존 validator와7개 actual receipt 기반 negative guards는 실패의 PASS 재표기,
post-check 성공 조작, exit0/제품 실행 승격, 다른 입력/EXE/cleanup, 제한 변경, SQLSTATE 추정,
원문 SQL 필드 추가/boolean coercion 및 CPU stop의 실제3회 관측 누락을 거부한다.
이 검사7 PASS가 실제 policy Changed 성공이나 원인 해결을 의미하지 않는다.
auditor는 실패08/09와 독립 소유 DB 부재를 필수로 확인하고 fresh run10을 성공 사례로 요구한다.
Rust Source/SQL roles/grants/trigger/resource thresholds/60초 소비자 timeout은 변경하지 않았다.
driver는 위 bounded 출력 수집만 변경했고 실제 제품 의미/검사/권한은 유지했다.

1. 네 최신 성공 실행·현재 Rust lint·실패·원본을 full current auditor로 결합하고 문서 갱신.
2. consumer 내부 세부 단계의 bounded 관측과 원인에 맞는 최적화를 진행하되 fresh 권한 검사를 줄이지 않음.
3. provisioning generation CAS/race, 검증 중간 TOCTOU, 전체 부수효과 불변,
   나머지 corpus/무수식/보호 분기를 실제 현재 소비자에서 검증.

durable blob/lineage/IR lifecycle/운영 issuer·key custody/scanner/full importer/field/comment 의미,
ExecutionManifest/원자적 execution·publication/CLI transport/P62·P84 원인 및 native
재-admission·저장·재열기·render·differential/Gate는 별도 미완료다.
native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED, P26 non-green을 유지한다.
한글/COM/UI/접근허용, stage/commit/push, 원본 삭제·이동, trust/config 변경은 없었다.
사용자 dirty/private/native/실패 증거와 PLANS.md 삭제 상태를 보존했다.
