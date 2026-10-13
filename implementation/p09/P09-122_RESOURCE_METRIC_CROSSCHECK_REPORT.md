# P09-122 — CPU/RAM 독립 대조 및 P121 회귀 자원 중단 보존

## 현재 상태와 범위

사용자 재개에 따른 목표 조회는 active였다. P09 Gate/제품 완료/P10 새 구현은 그대로 OPEN/false/false다.
이전 P121 partial checkpoint와 최종 partial audit, declared source1109 및 모든
원본·실패 증거·실행 파일을 변경하지 않는다. P121 소스/도구/검사/문서/원장에는 새 수정을 하지 않는다.
새 읽기 전용 metric 대조 도구와 byte/negative 검증만 별도 파일에 추가했다.
원본 HWPX/운영·trust DB/SQL/한글/Hwp/COM/UI/접근허용/설정·설치/stage·commit·push/삭제·이동 없음.

## 전체228 재검증 관측

P121 동일 source freeze14 및 executable04fefdf7…로 CPU2/BelowNormal/worker1/2초 감시를 유지했다.
full d:26.47초, CPU85% 이상3연속(100/100/98)으로 STOP_SUSTAINED_SYSTEM_CPU/exit-1.
full e:4회 연속 별도 CPU/RAM 대조가 낮아진 것을 확인한 뒤 재시작했으나82.35초에 같은 CPU 중단.
e는 테스트 RAM max26.12MiB/가용 RAM min15834MiB/시스템 CPU max100%였다.
d에서는25개/e에서는44개의 개별 ok marker가 관측됐지만 둘 다 terminal summary가 없으므로
전체228 PASS로 채택하지 않는다. 두 실행의 source freeze14 exact 및 잔여 test0을 확인했다.
기존 targeted3 PASS/strict lint/Changed16/current16/protected32/counterexample16의 범위는 유지한다.
현재 턴에서는 추가 full retry를 하지 않는다. 시스템 압박의 구체적인 원인은 특정하지 않는다.

## 독립 읽기 전용 지표 구현

GetSystemTimes의 kernel+user 차분에서 idle 차분을 빼 CPU를 계산한다.
kernel time에는 idle이 포함되며, 현재16 logical processor의 합계 범위를 사용한다(64 초과 거부).
GlobalMemoryStatusEx의64-byte MEMORYSTATUSEX에서 즉시 사용 가능한 physical RAM을 얻는다.
기존 CIM PerfOS CPU/RAM 값과 인접 시점에 대조하되 CPU 측정 window가 완전히 같다고 주장하지 않는다.
공식 근거: [GetSystemTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes),
[GlobalMemoryStatusEx](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex),
[MEMORYSTATUSEX](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/ns-sysinfoapi-memorystatusex).

대조에는 CPU=max(native,CIM), RAM 여유=min(native,CIM)만 사용한다. 관측 실패/불가능한 수치/
비단조 시간/0 delta/지원되지 않는 processor group/잘못된 memory layout을 거부한다.
기존 runner·85%3연속·RAM4GiB·test2GiB 등의 조건을 변경하거나 대체하지 않는다.
새 측정 프로세스 자체만 affinity1/BelowNormal이며 다른 앱·설정은 수정하지 않는다.

## 실패 보존과 실제 결과

initial arithmetic/conservative unit15 PASS 뒤 실제 측정은 Marshal.SizeOf overload에서 exit1로 실패했다.
System.RuntimeType가 아니라 boxed MemoryStatus instance로64-byte size를 확인하도록 수정했다.
첫 native metric call 전 실패였고 초기 receipt는 생성되지 않았다. initial script3 전체를 보존한다.
수정 b는 실제 native/CIM pairs4 측정에 성공했다. native CPU100%/99.85%를 테스트0 상태에서 확인했다.
이는 해당 window의 실제 시스템 압박을 뒷받침하지만 모든 이전 압박의 원인이나 특정 앱 책임을 증명하지 않는다.
b의 resource_decision은 HotSamples=3 가정값이었으며 실제 연속 횟수 검사 결과로 채택하지 않는다.
b의 실행 source3 전체를 보존한 뒤 c에서 실제 연속 hot count를 기록하도록 수정했다.
c native CPU13.61/11.79/12.85/11.51%, RAM 여유16482.78MiB 이상으로 pairs4가 완료됐다.
두 관측 총8 pairs를 보존한다. 이후 e의 CPU 압박을 앞선 낮은 관측만으로 무시하지 않는다.

current unit16 PASS는 실제 interop layout compile/64-byte check 및 numerical/conservative guards다.
unit에서는 native metric API를 호출하지 않으며 실제 API 호출 증거는 b/c의 측정 receipts다.
actual c receipt 기반 Python negative12 PASS: bool/NaN/infinity/완화된 CPU·RAM/가짜 hot count/
가짜 decision/실행 범위/Gate/누락 sample/동일 window 오인 조건을 모두 거부했다.
initial3 + measured-b3의 whole source archives6을 유지한다.

## 원장과 다음 경계

source delta8, whole archives6, predecessor receipts2, runtime receipts4를 전수 byte 대조한다.
previous declared source1109/current1117, inherited raw pin entries2340을 유지한다.
이는 전체 저장소 파일 개수나 모든 실행 파일 재실행 수가 아니다. 이전 executable506은 보존 범위다.
상세 원장은 `implementation/p09/evidence/p09-122-resource-crosscheck.source-progress.v1.json`에 있다.
원문 XML/숫자/키/전체 로그 대신 안전한 지표·digest·counts·closed outcome만 기록한다.
최소6 coarse groups/closed0 및 최소30 비완전 세부 조건을 그대로 유지한다.
native34 NOT_RUN/재수용 필요, P26 failed_semantic_non_green, P62/P84 SQL UNRESOLVED를 유지한다.
다음은 자원 상태가 안정된 후 동일 stored228 actual terminal 검증이다.
production trust/actual SQL/atomic execution/idempotency/publication/transport/whole-source 의미/native/Gate는
이번 read-only metrics 및 source-component 검증으로 완료되지 않는다.
