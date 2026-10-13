# P09-135 — 최종 저장소 제품 EXE의 제한 자원 개별 회귀

## 범위와 현재 상태

P134의 최종 `form_stored_provider-p134-final.exe`에 포함된 234개 사례를
정확한 이름별로 실행한다. 현재 진행 상태와 채택 건수는
`python tools/p09/verify_final_stored_regression.py --progress`로 확인한다.
최종 감사에서234개 distinct union과 signed corpus marker6개를 모두 채택했다.
상태는 `PASS_CURRENT_FINAL234_DISTINCT_UNION_NOT_NATIVE_SQL_OR_GATE`다.
최신 코드의 미완료 전체 회귀를 완료했지만 P09 제품/Gate 완료와 구분한다.
Rust 제품 소스·SQL migration을 변경하거나 EXE를 다시 빌드하지 않는다.
예전 고부하 P120 EXE 및 중단된 P134 단일-process 전체 실행은 재시작하지 않는다.

범위는 `actual_import` 206개, `full_document` 20개, root 8개다.
테스트 개수는 남은 제품 구현 작업 수 또는 P09 완료율이 아니다.
모든 개별 실행은 `--exact --show-output --test-threads=1` 및 하나의 완전한 이름으로
`1 passed / 233 filtered / failed=ignored=measured=0`의 terminal summary를 요구한다.
234개 정확한 이름의 중복 없는 합집합을 모두 확인할 때만 current union을 채택한다.
별개 process들의 합집합이므로 단일-process 전체 회귀 통과로 주장하지 않는다.

## 원본·입력·실행 파일 결속

- P134 checkpoint는 18,919 bytes 및 SHA256
  `f2d54f2a66c23cd3f2c8cc6049935bd33b735bdf608e99a6f0dd375b63ba89dd`로 고정한다.
- 현재 EXE는 10,753,536 bytes 및 SHA256
  `d406f4693798f6f8ae13982e8f5fcb464721176295a68c53514645df7650252a`다.
- 실행마다 declared input 806개와 기존/현재 EXE 21개의 bytes/SHA256를 확인한다.
  선언 입력은 기존 P134 compiled source 781개, SQL migration 21개, P134 checkpoint,
  새 runner 2개, 기존 safe-result helper 1개다. 전수 compiler dependency 주장과 구분한다.
- 이전 source graph 1,174개 및 raw pin entries 3,043개를 기존 검증기로 보존한다.
  이 단계의 source/tools/report delta는 5개다. generated checkpoint와 target receipts는
  source 파일 개수와 분리한다.
- 원본 36개, 수식 원본 16개, 변경/현재 파생 32개 등의 현재 signed corpus marker를
  과거에 결속된 정확한 payload와 대조한다. bool marker는 literal `true`만 채택한다.
  이름이나 exit0만 확인해서 수식/보호 corpus 검사를 통과시키지 않는다.

## CPU·RAM과 중단 보존

한 코어 affinity/BelowNormal/test worker1, 샘플 2초, 사례당 최대 600초를 적용한다.
새 배치 시작은 최대 30개/180초로 제한하되 이미 실행 중인 사례는 자기 시간 한도까지
같은 process handle로 관측한다. 시작 budget 만료를 사례 종료로 간주하지 않는다.
시작 전 CPU85% 이상 또는 가용 RAM4096MiB 미만이면 테스트를 시작하지 않는다.
실행 중 시스템 CPU85% 이상 3회 연속, 가용 RAM4096MiB 미만,
root working set2048MiB 초과 또는 시간 한도에서 해당 runner 소유 child tree만 중단한다.
다른 앱·다른 작업 process는 종료하지 않는다. 임계치를 완화하지 않았다.

27번째 사례의 attempt1은 시작 전 CPU88%로 deferred였고 실행하지 않았다.
실제 terminal/no-start 확인 후 독립 read-only 자원 대조 3쌍을 수집했다.
native CPU61.29/62.21/73.91%, CIM61/56/68%, 보수적 가용 RAM 최저9531.37MiB였다.
측정창은 인접하지만 동일하지 않다. 전체 PC 자원 압박의 원인은 `NOT_DETERMINED`다.
이후 attempt2로 해당 사례를 통과했다. attempt1과 측정 receipt는 그대로 보존한다.
77번째 사례의 attempt1은 시스템 CPU86/86/95%에서 35.11초 후 소유 테스트만 중단됐다.
terminal summary가 없어 미채택이다. input806/EXE21 보존 검사는 통과했다.
이후 독립 read-only 대조3쌍에서 보수적 CPU4.88/6.03/17%, 가용 RAM 최저13161.89MiB를
확인한 뒤 attempt2로 재개했다. 중단 기록으로 원인 귀속이나 PASS를 추정하지 않는다.
96번째 사례의 attempt1도 시스템 CPU96/93/92%에서29.68초 후 소유 테스트만 중단됐다.
terminal summary가 없어 미채택이며 input806/EXE21 보존 검사는 통과했다.
첫 독립 대조3쌍의 보수적 CPU는75.68/52.31/80%, 가용 RAM 최저11104.09MiB였다.
아직 CPU 여유가 작아 테스트 없는 상태에서 추가 대조를 수행했다.
추가 대조3쌍의 보수적 CPU8/22/9%, 가용 RAM 최저12560MiB를 확인한 뒤
96번째를 새 attempt2로 재개했다. 대조 창은 각각약5.5초다.
77/96번째 attempt2도 최종 통과했다. 전체234개 채택과 별개로 deferred1/owned CPU-stop2의
미채택 attempt3개와 독립 자원 대조12쌍을 모두 원장에 결속한다.
중단/실패 시 새 attempt 번호를 사용하며 이전 receipt를 덮어쓰지 않는다.
P134의 실패·중단 receipt도 그대로 남는다.

양의 process RAM 관측이 없는 짧은 사례는 `null`이며 RAM peak0으로 주장하지 않는다.
root working set은 children 합계나 전체 peak memory 측정이 아니다.
CPU·RAM 관측은 자원 제한 준수 증거이며 PC 전체 건전성이나 성능 비교 증거가 아니다.

채택된234개 실행의 샘플532개에서 시스템 CPU 관측 최댓값100%, 가용 RAM 최저9649MiB,
양의 root working set 관측 최댓값26.05MiB였다. accepted 사례에는 연속3회 과부하,
RAM 부족 또는 root working set 제한 위반이 없다. 시스템 CPU의 짧은100% 관측을
테스트 한 process가 전체 CPU를 사용했다는 주장 또는 문제가 없다는 주장으로 바꾸지 않는다.
195개 짧은 사례는 양의 process RAM 샘플이 없으며 실제 peak0이 아니다.
채택 사례의 runner elapsed 합계990.64초는 빌드/배치 preflight/중단/대기 시간을 포함한
전체 wall time 또는 이전 EXE 대비 성능 개선율이 아니다.
마지막 배치 terminal 확인 후 실행 중 stored test0개를 확인했다.

## 검증과 산출물

- `python tools/p09/tests/test_final_stored_batch.py`: guard unit 16개.
  잘못된 EXE/사례, exact filter 누락, 병렬 worker, 입력 drift/중복,
  보존 실패, Gate/SQL/native 승격, summary 누락·불일치, 자원 제한 완화,
  새 시작 budget/실패 후 시작, attempt 덮어쓰기, signed marker 변조,
  read-only 측정의 scope 및 보수적 CPU·RAM 판단 완화를 거부한다.
- `python tools/p09/verify_final_stored_regression.py --progress`: 실제 현재 진행 감사.
- `python tools/p09/verify_final_stored_regression.py --complete`: 전체234 및 signed marker6
  모두 충족해 exit0으로 채택했다. 미완료 상태를 complete로 보충하지 않는다.
- checkpoint 게시 후 기본 명령은 checkpoint의 exact pins와 실제 현재 진행을 다시 대조한다.
- `git diff --check`.
- 개별 receipt: `target/p09-121-resource-optimized/p135-case-NNN-attempt-NNN.json`.
- 자원 대조: `target/p09-122-resource-crosscheck/p135-case27-notstarted-a.json`,
  `target/p09-122-resource-crosscheck/p135-case77-ownedstop-a.json`,
  `target/p09-122-resource-crosscheck/p135-case96-ownedstop-a.json`,
  `target/p09-122-resource-crosscheck/p135-case96-recheck-b.json`.
- checkpoint: `implementation/p09/evidence/p09-135-final-stored-regression.source-progress.v1.json`.

## 남은 제품 경계

이 작업은 현재 저장소 제품 source/component 회귀다. actual SQL/production issuer/key custody/
approval·trust registry/원자적 실행·publication·transport, whole import/native metadata/
coordinates/comment/rich compiler/field-Date-external 의미, P84 SQL 원인,
실제 한글 저장·재열기·렌더링을 대체하지 않는다.
최소6 coarse groups/closed0 및 최소30 비완전 완료 조건을 테스트 수로 차감하지 않는다.
native34는 `NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED`다.
P09/A12/A13 `OPEN`, product_complete=false, goal_status=active, P10 새 구현 없음.
전체 workspace runtime 통과도 주장하지 않는다. 한글/COM/UI/접근허용/actual SQL/
운영·trust DB/설정·설치/stage·commit·push/삭제·이동 없이 진행한다.
사용자 dirty/private/원본·실패 증거를 보존하고 `PLANS.md` 삭제 상태를 유지한다.
