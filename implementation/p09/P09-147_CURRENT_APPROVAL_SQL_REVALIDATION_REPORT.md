# P09-147 — 최신 코드의 승인 철회 SQL·엄격 lint 재검증

## 현재 실행 결과

P146 lint-r2에서 발견한 네 가지 Clippy 오류를 수정한 현재 Source를 새 실행 파일로
빌드하고 실제 단위 테스트·SQL consumer·workspace lint를 재실행했다. 수정 전 P146
run03/04 또는 r10 결과를 최신 코드의 실행으로 승격하지 않는다.

| 검사 | 실제 결과와 범위 |
|---|---|
| main build-r11 | 실행용 dev profile, source842, 경고/오류0. DB/native/Gate 실행 아님 |
| unit build-r5 + unit-run4 | test profile, route6/index5 실제 Rust11 PASS |
| P145 bootstrap-run05 | unit-run4 첫 hash 전 CPU1/BelowNormal과 안정 구간 확인. 대상의 연속 자원 guard 유지 |
| P146 run05 | index0 원본 Unchanged, 기존 consumer18 + 승인 철회9 = actual SQL27 PASS |
| P146 run06 | index0 숫자 leaf 한 개 RAM 파생 Changed, 같은 SQL27 PASS. 새 원본으로 세지 않음 |
| P146 lint-r3 | workspace32 packages/361 distinct targets, 원래 compiler artifact identity coverage exact, diagnostics0, -D warnings PASS |
| source/protocol guards | 현재 source 검사6 PASS. actual SQL 검사 수에 더하지 않음 |
| 새 evidence negatives | 7 PASS. 검사 누락·가짜 scope 승격·입력 대체·미실행 live 경계·잘못된 이력/exit/resource/cleanup 및 원래 consumer 조건 변조 거부 |

SQL 각 실행은 기존 full-IR fixture25, SQL22 checks37, credential metadata42, fingerprint
controls2를 유지했다. 소비자 전체 candidate는 독립 evaluator와 같고, 승인 철회 뒤
prepared/fresh/route의 정확한 거부와 callback0을 확인한다. final approval revocations3은
기존2+새1이다. 서로 다른 두 management 연결의 동일 승인 철회 경쟁은 commit1/denial1이다.
generic RepositoryFailure에서 SQLSTATE나 loser의 상세 원인을 추정하지 않는다.

## 자원과 보호

main build13.05초, system CPU 최대40%, available RAM 최소10813MiB.
unit build2.84초, CPU 최대31%, RAM 최소12722MiB. SQL run05는50.21초/CPU 최대32.62%/
RAM 최소13194.58MiB, run06은84.90초/CPU 최대70.07%/RAM 최소12487.49MiB였다.
실행 중 resource stop은 없었다. 순간 수치는 측정 범위의 관측이며 전체 PC 정상이나
Codex freeze 원인 해결의 증거가 아니다. unit 실제 시간과 lint 자원 수치는 각 원본
receipt를 사용한다. 실행마다 CPU1/BelowNormal/jobs1 또는 test-threads1을 유지했다.

SQL driver의 unit EXE 보호를 r1~r5 전체로 확장했고, lint도 이전 r4 EXE를 별도 보존한다.
현재 SQL source862/보호 EXE53, lint source858/EXE53 전후 bytes/SHA exact다. 숫자는
선언된 검증 inventory이며 전체 dependency closure나 남은 제품 작업 수가 아니다.

DB는 이미 있는 pinned image와 새 UUID/전용 label, loopback port, CPU1/RAM512MiB/
pids64, read-only rootfs/tmpfs/no host mount로 격리했다. 기존 최소권한/강제 RLS와 원래
role PASSWORD 초기화를 유지했다. Postgres 스킬의 최소권한/RLS 지침을 권한 보존에
적용했으며 스킬 자체를 실제 DB 증거로 사용하지 않는다. 자기 DB 제거를 각 receipt에서
확인했고 새 감사는 ID/이름 부재를 다시 검사한다. 운영 DB·키·trust 설정은 변경하지 않았다.

## 현재 증거 감사

`tools/p09/verify_formula_issuer_live_current.py`는 CPU1/BelowNormal 관측 및 안정 구간 뒤
현재 build/unit/SQL/lint/source/EXE와 P145 기존 direct pins988, P146 실패·수정 전 실행,
네 개 whole source archives를 전후 독립 hash로 대조한다. 동일 경로의 이전 bytes는
검증된 전체 archive bytes/길이/SHA로만 인정하며 source drift를 없던 일로 하지 않는다.
현재 Source의 선언된 opt-in 승인 철회 추가를 메모리에서 제거해 원래 consumer 전체와
대조한다. rustfmt stdin 결과의 줄바꿈 정규화 비교이며 원본 raw archive는 별도 인증한다.
소스 파일을 되돌리거나 원래 validator/receipt를 수정하는 과정은 없다.

새 감사 승인 원장: `evidence/p09-147-current-approval.progress.v1.json`.
해당 파일이 없거나 감사 실패이면 전체 current audit는 미완료다. 이 문서의 실행 결과
요약은 전체 감사 성공 문구를 대신하지 않는다. 감사는 기존 declared snapshot과 현재
증거의 재결합이며, 모든 이전 qualification 명령·최초 source graph 전체·native campaign의
새 실행이라고 주장하지 않는다. 역사적 receipt 보존과 최신 source 재실행을 구분한다.

관찰 명령 한 번의 `Select-Object -Skip sixty`는 잘못된 정수 인자로 실패했다. 파일 읽기
관찰 오류이며 SQL/build 실행의 실패나 성공으로 세지 않는다. 기존 P146 최초 timeout,
lint-r1 defer, lint-r2 실패4개 및 원래 source-guard 실패를 모두 보존한다.

## 남은 실제 제품 경계

P09/A12/A13 OPEN, product=false, 목표 active, P10 새 구현 없음을 유지한다.
현재 범위는 원본 index0 + RAM 파생 index0의 승인 철회·동일 철회 경쟁 component다.
현재 consumer의 trust/policy 철회, provisioning generation CAS/race, 검증 중간 TOCTOU,
live 철회 뒤 추가 전체 side-effect 불변, 원본36 전체와 보호/수식 없음의 분기는 남아 있다.
durable storage/키 보관·발급 원천/scanner·IR fidelity/ExecutionManifest/원자적 publication/
CLI transport 및 P62/P84 SQL 원인도 완료하지 않았다. full import/comment/field 의미와
실제 native 재-admission·저장·재열기·render·differential/Gate는 별도 미완료다.

한글/COM/UI/접근 허용 창, stage/commit/push, 원본 삭제·이동은 없었다. 사용자 dirty 상태,
private/native/실패 증거 및 PLANS.md 삭제 상태를 보존했다. 이 구성요소의 통과를 P09
완료율 또는 전체 목표 완료로 환산하지 않는다.
