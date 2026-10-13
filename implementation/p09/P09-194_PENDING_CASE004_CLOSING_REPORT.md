# P09-194 — 정확한 1개 실행과 중단된 최종 확인의 후보 보존

2026-10-08. 목표 active/P09·A12·A13 OPEN/product=false/P10 새 구현 없음.
P09 전체 완료율이 아니라 현재 r07 executable의 249-case 큐 상태다.

## 현재 상태와 다음 경계

- 수용 완료3/249, 미수용246 = 일반240 + corpus6.
- 미수용 중 case004는 정상 통과했으나 별도 source closing이 중단된 후보1.
- 따라서 아직 실행하지 않은 항목은245 = 일반239 + corpus6.
- 다음 미실행index5/attempt1이지만 기존후보 closing 전에는 시작하지 않는다.
- case004를 자동 재실행하지 않고 원 통과 receipt를 재사용해 별도 closing을 완성해야 한다.
- compiled249=true/full249=false/signed16=false. 개별/fixture PASS를 실제 Hancom/native/SQL Gate로 승격하지 않는다.

## 실제 제품 테스트 — 4번만 실행

`python -B tools/p09/run_shared_resumable_r07_batch.py --mode actual --run 5 --max-cases 1 --start-budget-seconds 300`

원 P190/P191/P192 source를 수정하지 않았다. 원3개 완료를 skip하고 단 한 개만 실행했다.
새컴파일/Cargo/SQL/Hangul/접근허용/전수249실행/외부프로세스 종료/OS설정변경은 없다.

공개 case: actual_import::debug_and_receipts_do_not_expose_raw_package_graph_or_policy_values.
stored fixture를 product import/bind 경로로 처리하고 debug/receipt에 raw package/graph/policy가 노출되지 않는지 검사한다.
fixture를 사용한 product 경로 검사이며 실제 고객자료/SQL/한글 의미 수용으로 확대하지 않는다.

- preparation PASS, 원154 계약검사, max-cases1, wall6.8746s, stop=null/cleanup=true.
- case004 PASS_EXACT_R07_SINGLE_CASE_NOT_FULL_OR_GATE, exit0,1PASS/0failed/0ignored/0measured/248filtered.
- 원 CPU hard6.25% machine/RAM hard8·soft7%/one-affinity/BelowNormal/1200초/stream32768cap 유지.
- 실제 owned Job membership과 종료/cleanup/owned_tree_empty/active_processes0 확인.
- 전후 각각1405 fresh readpasses/117837770bytes, source/EXE/scheduler 입력 그대로 유지.
- wrapper elapsed131.34s(전후 입력확인 포함),257samples, hostCPUmax23.31%, availableRAMmin56.03818843986835%.
- aggregate JobCPU0.391s, peak Jobprivate33.08MiB(총RAM0.10383263684507678%).
- event01 PASS는 후보 보존 metadata이며 최종 closing 수용이 아니다.

## 최종 source closing — CPU 보호 중단/미수용

같은 실행 핸들은 exit1로 종결됐으며 살아 있는 Job/프로세스처럼 취급하지 않는다.
closing wall309.6208s, FAILED_NOT_ACCEPTED/error=resource_stop_reason=STOP_SUSTAINED_SYSTEM_CPU,
watcher cleanup=true. bound1478/read2859/859546566bytes/final fresh1303/finished=false.
최종 whole1470 입력/기타metadata가 완성됐다고 주장하지 않는다.
원 실패파일을 덮어쓰지 않고 복구 closing은 별도 새 출력으로 만들어야 한다.

중단된 공개 보호 EXE는
`target/p09-151-durable-negative/build/debug/examples/formula_issuer_product_postgres_probe-p151-r01.exe`다.
이 EXE를 실행한 것이 아니라 historical artifact의 최종 fresh hash를 읽던 중이다.
원 whole scope의67개 과거EXE도 최종 확인에 포함돼 body1개 실행보다 closing IO가 크다.

마지막8표본에서 hostCPU26.53→23.55→37.12→94.12→100→100→100→100%.
4연속 포화 구간의 parentCPU(machine)는0.178571→0→0→0%, 가용RAM51.29~51.76%다.
내 reader가 직접 CPU를 전부 사용했다는 수치는 아니며, 파일 읽기에 의한 간접부하나
Defender/다른 프로세스 또는 PC프리즈 원인은 이 자료만으로 확정하지 않는다.
원95% read-yield가2회/5pause windows/2.5초 동작했지만 원98%4회 STOP은 억제하지 않았다.

## 후보 재확인

신규 review_pending_r07_closing.py 및 test_pending_r07_closing_review.py는
원 case004/CPU STOP 전체byte pin과 동일한 baseline identity/별도수용3을 확인한다.
원 v.validate_case/v.plan과 supplemental before/after 증거를 유지한다.
후보1을 완료4로 세거나 자동 재실행하거나 5번을 먼저 시작하는 것을 거부한다.
원154＋신규4 synthetic contracts PASS, bound24/final fresh24/read58/21972698bytes/finished=true,
stop=null/cleanup=true, 추가productchild=false. 새whole source audit/closing이 아니라 metadata 검증이다.
원 실패와 후보 receipt는 변경하지 않았다.

## 증거핀

아래 경로는 implementation/p09/evidence/ 기준이다.

| 경로 | bytes | SHA256 |
|---|---:|---|
| p09-192-shared-r07-batch05.preparation.v1.json | 305951 | 70a6ed3467421125b53ebaa9461e0202d860fcebc1db27c8cc63e3fb4164b318 |
| resumable-r07/p190-case-004-attempt-001.json | 617816 | 53159ac973e75e5562439c8a173afa948c9b7c23719826cb51a205d305b9634a |
| p09-192-shared-r07-batch05.event-01.v1.json | 7418 | 90b9785a028c28ca4b4c94a7dbeb7c93ff2a44b5c32df49627f0e0785de1235e |
| p09-191-r07-resumable-run05.closing.v1.json | 304809 | 715d9f22098622741f5f844ed832a5917078b417cfb4122dee081b1bb90cb3bd |
| p09-194-pending-case004-closing-review-run01.v1.json | 16265 | a0789196efcba9e241ec77f2deff0227b427a17a3d601a462a732dfc8dcf5dd9 |

CURRENT_STATE.md와P09-149의 이전r63전체를 source-archive/p09-194-pre-pending-progress/에
복사 보존한 후 같은 r64 prefix로 현재 후보/STOP 경계를 갱신했다.
위 후보 review receipt는 뒤에 작성된 이 보고서/r64 문서 자체의 입력 증거라고 주장하지 않는다.

다음 구현은 failed closing의 출력 재사용 제한을 지키는 독립 복구와 해당 alias의 검증/재개 연결이다.
최종 확인의 IO 부담을 줄일 경우 원 freshness/receipt/source 범위나 보호 기준을 약화하지 않아야 한다.
같은 heavy closing의 자동retry 및 성공 body 재실행을 하지 않았다. 목표완료/프리즈해결로 처리하지 않는다.
