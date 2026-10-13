# P09-145 — 사전 hash 자원 제한 및 두 번째 원본 SQL22 검증

## 변경 범위와 사용 경로

`tools/p09/run_resource_bounded_python.py`를 추가했다. 기존 P143/P144 main/Source,
빌더, unit/SQL driver, current auditor와 역사적 receipt는 수정하지 않았다.
PLANS.md를 복구하지 않았고 기존 원본, private evidence, 사용자 변경을 보존했다.

이 opt-in 진입점은 같은 Python 프로세스에서 기존 대상 스크립트를 실행한다.
대상 import/manifest/source/EXE hash 전에 CPU affinity=1 및 BelowNormal을 적용하고
Win32 API로 관측한다. CPU≤50%, free RAM≥8192MiB 3회 연속/2초 간격/최대20초의
pre-hash 안정 구간이 필요하다. 대상이 유지하는 post-hash admission과 CPU85% 3회/
free RAM4096MiB continuous stop을 대체하거나 완화하지 않는다.

허용 대상은 current-audit, unit, sql 3개뿐이며 각 원래 receipt 경로 범위를 검증한다.
임의 실행 파일/코드/입력 경로는 받지 않는다. stdout/stderr는 각각32KiB로 제한해
폐기하고 최종 상태만 표시한다. 대상 실패 exit 또는 정확한 성공 receipt 부재는
bootstrap PASS로 바뀌지 않는다. 새 receipt는 exclusive-create로만 기록한다.

중요한 한계: bootstrap 자체에는 pre-hash 단계의 continuous stop이 구현되지 않았다.
pre-hash CPU/priority 제한과 시작 admission을 추가한 것이며, 이후 continuous stop은
기존 대상의 담당이다. 이 진입점을 거치지 않는 직접 호출의 사전 검사 구간은 그대로다.
따라서 모든 검증의 자원 문제가 해결됐거나 Codex 멈춤 원인이 제거됐다고 주장하지 않는다.

## 실제 검증 결과

| 사례 | 권위 receipt | 실제 결과 |
|---|---|---|
| 실행 경계 테스트 | `tools/p09/tests/test_resource_bounded_python.py` | 실제 unittest11, 실패0/오류0. 임의 경로/옵션, 안정 구간 reset/stop/timeout, UTF-8 출력 한도, 비정상 exit, argv 복원, 자원 제한 순서 |
| current audit | `implementation/p09/evidence/p09-145-resource-bootstrap-run01.v1.json` 및 `p09-144-corpus-consumer.progress.v1.json` | 977 unique files freshly double-hashed, 역사959 pin 연결, protected EXE48, current Rust11/source guards6, packages32/targets361, 기존 DB ID/이름 부재4 |
| 실제 Rust 재실행 | `implementation/p09/evidence/p09-145-resource-bootstrap-run02.v1.json` 및 `target/p09-121-resource-optimized/p144-corpus-unit-run2.json` | 실제 route6/index5 =11 PASS, zero/filtered 실행 아님 |
| 두 번째 원본 actual SQL | `implementation/p09/evidence/p09-145-resource-bootstrap-run03.v1.json` 및 `p09-144-corpus-consumer-run03.v1.json` | manifest index1 original/Unchanged, original digest exact, consumer18/metadata42/full IR25/SQL22 checks37, source859/EXE48 before-after exact |

각 실제 bootstrap run은 target/hash 이전과 target 종료 후 affinity1/priority class16384를
Win32 API로 확인했다. SQL 실행 중에도 별도 관측에서 Python affinity1/BelowNormal/
working set24.5MiB를 확인했다. 이후 source/EXE 전체 hash 불변 검사와 기존 least privilege,
FORCE RLS, schema/fingerprint negative controls를 유지했다.

current audit: bootstrap13.52초, 감사 구간 system CPU 최대32.96%, free RAM 최소12899.54MiB.
unit 재실행: bootstrap16.45초, unit 구간 system CPU 최대33.55%, free RAM 최소14572.34MiB.
index1 SQL: bootstrap55.71초/driver47.45초, driver 구간 system CPU 최대67.68%,
free RAM 최소14410.59MiB, resource stop 없음. system CPU는 전체 PC 수치이며
검증의 CPU 점유율이나 Codex UI freeze 원인으로 대체 해석하지 않는다.

SQL run03은 고정 cached Postgres image를 사용한 자기 UUID/label 격리 DB만 생성·회수했다.
driver가 자기 identity/isolation과 회수를 검증했고 이후 정확한 ID와 이름의 부재도 별도 확인했다.
운영 DB, 사용자 DB, 설정, private key, native application은 변경/실행하지 않았다.
Supabase Postgres Best Practices의 최소권한/RLS 지침은 기존 검사 보존에 적용했다.

## 역사와 현재 상태

P144 기존 보고서는 initial CPU stop/full audit 보류 당시의 기록으로 그대로 보존한다.
이번 current audit 성공은 새로운 `p09-144-corpus-consumer.progress.v1.json`에 있다.
이 성공 감사의 corpus 범위는 original index0 + RAM derivative index0이며,
후속 run03의 original index1은 별도 actual SQL receipt로 증명한다.

현재 실제 original consumer 범위는 original indices[0,1], RAM derivative indices[0]이다.
RAM derivative를 새 원본이나 원본36 완료로 계산하지 않는다. 이전 실패/defer/부분 결과,
preimage archive와 EXE는 보존했다. 삭제, 이동, push, commit, native/access-allow 실행은 없다.

P09/A12/A13 OPEN, product=false, goal active. current consumer live SQL revocation/CAS/race,
나머지 원본/무수식/protected corpus, native 저장·재열기·시각 검증, durable storage,
production key custody, atomic publication, scanner/native IR fidelity는 미승인이다.
coarse 최소6/이번에 닫힌 그룹0을 유지하며 세부 최소30을 완료율로 계산하지 않는다.
다음 제품 검증은 현재 prepared consumer의 actual SQL revocation/CAS/race 거부 경계다.
