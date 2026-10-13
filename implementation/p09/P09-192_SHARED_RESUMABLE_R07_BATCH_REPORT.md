# P09-192 — 준비를 공유하는 순차 exact-one 검증

## 실제 결과

기존 완료case1을 재실행하지 않고 신규case2/3을 순차로 실행했다.
두 개 모두 정상 exit0/정확한1PASS/0failed/0ignored/0measured/248filtered이며
각 owned Job의 정리를 확인했다. 별도 공유 전체 입력 closing도 통과했다.

현재 테스트 큐는 3/249 완료, 246 pending = 일반 240 + corpus 묶음 6이다.
후속 read-only plan이 완료3개를 모두 skip하고 index4/attempt1을 선택했다.
이 수치는 P09 전체 제품 작업 개수나 완료율이 아니다.
full249/signed16/single-process/SQL/native/product/Gate는 미수용이다.
목표 active, P09/A12/A13 OPEN, P10 새 구현 없음.

## 공유 준비 방식

`tools/p09/run_shared_resumable_r07_batch.py`는 P191의 봉인된 whole closing을
historical before anchor로 재사용한다. 이를 새로운 whole before fresh audit라고
표현하지 않는다. 원baseline1470 입력과binding을 유지하여 통과한case1을 재사용한다.
새 scheduler/helper source2개는 별도 byte핀으로 before/after 검증한다.

각case는 현재EXE와 원모든non-EXE1403 + scheduler2 = 1405개 입력의 모든byte를
전후fresh 확인한다. 당시 actual executable는 그입력과현재Rust785 범위에 묶인다.
역사적EXE67개는 공유 end closing에서 전체68EXE와 함께fresh 재검사한다.
원본/corpus/Rust/fixture 제거, stat-only freshness, hash cache 도입은 없다.

원 P191의 worker, GO, actual Job membership, kernel limit readback, one-affinity,
BelowNormal, CPUhard6.25%/RAMhard8·soft7%/.5초 guard/CPU98%4회/여유RAM8·commit95,
원1200초/stream32768/assertion·overflow를 유지한다.
새Cargo compile/SQL/한글/COM/UI/외부PID query/병렬 실행은 없다.

동시에 한 case만 실행하고 결과를 따로 보존한다. 묶음은최대5개, 새시작budget최대300초,
이번 실제 범위는2개다. 중단 시 다음case나자동closing을 시작하지 않는다.
이미완료된 정상후보는 별도closing으로 수용 가능하게 보존하며 자동retry하지 않는다.

## 실행 기록

| 단계 | 결과 | 범위와 시간 |
| --- | --- | --- |
| Shared preparation | PASS, stop=null/cleanup=true | historical sealed baseline 확인 + scheduler 현재핀, 5.8067초; 새whole before 검사 아님 |
| Case002 | exit0/1PASS/248filtered | head advance가 동일한 result bytes인 경우에도 이전 import를 무효화; wrapper142.25초 |
| Case003 | exit0/1PASS/248filtered | 실제fixture 저장결과10개를 caller map 없이 import하고 whole graph 보존; wrapper155.83초 |
| Shared end closing | PASS, 신규2개 수용 | whole68EXE/Rust785/source249/59module + scheduler/event/receipt,354.9399초 |
| Plan004 | 완료3을 skip, next4 선택 | 실제 새test body를 실행하지 않은 read-only 계획 |

두case 전후 각각1405readpasses/117837770bytes다.
closing은bound1480/finalfresh1480/read3037/972982664bytes로 전체 종결했다.
원 P190 acceptor 및 supplemental source validator로 source/EXE/binding/terminal/
외부 receipt pin/cleanup을 확인하며 partial 또는 synthetic 결과를 runtime으로 승격하지 않는다.

## 자원 관측

- Case002:275samples,hostCPUmax52.02%,availableRAMmin45.153147%,
  ownedJobCPU0.422초/peak private32.54MiB.
- Case003:296samples,hostCPUmax42.14%,availableRAMmin46.533953%,
  ownedJobCPU4.656초/peak private38.21MiB.
- 전체end closing 마지막8표본:hostCPU14.69~17.95%,availableRAMmin46.991324%.
  이tail을closing 전체최고/최저 부하라고 주장하지 않는다.

이번두case는 자원중단 없이 종료했다. wrapper시간은 admission/전후hash/정리를 포함하여
test body만의 실행시간이 아니다. PCfreeze 근본원인 해결이나Defender/외부프로세스 원인
귀속을 증명하지 않는다. 동일workload A/B성능배수 또는CPU감소율도 측정하지 않았다.

## 계약 검사와 보존

원142 + scheduler12 =154 synthetic/no-child 계약 PASS.
실제 runtime와mock 계약을 분리한다. 첫light02의 mocked main stop검사에서 출력된
STARTING_ONE_OWNED_CASE는 실제case 실행이 아니며 subprocess/새thread를 차단했다.
이전helper/test 전체를 source-archive에 보존하고 이후unit출력을capture했다.
latest light03은154 PASS다. 기존closing경로 재사용도 actual 준비 전에 거부한다.
원P189 CPU중단/partial48, P191 case1, 실패원본/사용자변경/기존EXE를 수정하지 않았다.

## 다음 경계

Next actual은 NOT_RUN인 index4:
`actual_import::debug_and_receipts_do_not_expose_raw_package_graph_or_policy_values`.
같은 shared baseline에서 작은 순차case를 이어서 실행하고 무거운6개는 원본별로
분할하되 기존 모든assert/입력수/최종집계를 유지한다. 무거운6개는ignored가 아니다.
접근허용/SQL/image pull/Git/Review/삭제·이동/설치/전역 설정 변경 없이 진행했다.

주 증거:

- implementation/p09/evidence/p09-192-shared-r07-batch02.preparation.v1.json
- implementation/p09/evidence/resumable-r07/p190-case-002-attempt-001.json
- implementation/p09/evidence/resumable-r07/p190-case-003-attempt-001.json
- implementation/p09/evidence/p09-191-r07-resumable-run02.closing.v1.json
- implementation/p09/evidence/p09-192-shared-r07-batch04.plan.v1.json
