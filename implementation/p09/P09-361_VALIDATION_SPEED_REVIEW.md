# P09 검증 속도 분석과 재시도 개선

제품 실행보다 입력 고정과 증거 재검사가 현재 지연의 대부분을 차지한다. 재시도마다 소스를 변경하는 흐름을 제거하고, 검증된 소스와 별도 실행 기록을 유지하는 방식으로 목표 작업을 재개한다. CPU 및 RAM 보호, 실제 전후 바이트 검사, 독립 승인 조건은 유지한다.

## 확인된 지연

case160 Native run004의 전체 실행은 568.98초이며 GO부터 제품 출력 수집 완료까지는 2.2358초였다. 제품 구간은 전체의 약 0.393%다. 나머지 566.74초는 입력 준비, 고정, 전후 확인, 자원 측정 및 정리 구간이다. 각 준비 단계의 실제 소요 시간은 이 기록에서 개별 측정되지 않았다.

같은 실행은 입력 2,845개와 디렉터리 372개를 고정했다. 전후 각각 242,518,001바이트를 실제 읽었으며 두 경계 합계는 약 462.57MiB다. 기존 비용 모델의 입력 고정 시간은 229.79초, 두 바이트 읽기는 258.40초다. 이는 고정된 초당 14개 acquisition, binary 1MiB/s 및 other 2MiB/s의 직렬 비용 추정이지 단계별 실측은 아니다. JSON decoder의 두 경계 누적 작업은 0.845초여서 이 실행의 주요 지연으로 볼 수 없다.

P09 도구 아래 Python 파일 1,517개와 runtime 버전 파일 65개가 존재한다. 전체가 실행마다 import된다는 뜻은 아니다. 이번 코드 검증의 실제 helper 수는 62개다. 다만 작은 실패마다 새 구현과 추가 검증 경로를 만들었던 작업 방식은 소스 재검증과 증거 관리 부담을 키웠다.

## 적용하고 검증한 변경

run007 controller는 소스를 다시 수정하지 않고 qualification 1..8과 preflight 2..8의 닫힌 범위에서 별도 산출물 위치를 선택한다. 자동 재시도나 기존 기록 덮어쓰기는 하지 않는다. 함수 본문 역투영과 실제 globals/API identity 검사를 유지한다.

검증 시작 시 계약 수 27을 31로 바꾸는 투영이 별도의 입력 읽기 수 31과 충돌한 오류를 발견했다. test_namespace에서 계약 수 투영만 제외해 원래 읽기 수를 보존하고, 기존 계약에 전체 코드 역투영 회귀 검사를 추가했다. 오류 시 제품 및 Native는 시작되지 않았으며 기존 기록을 변경하지 않았다.

수정 후 계약 31개는 오류 0, 실패 0, skip 0으로 통과했다. 코드 검증은 12.162초, fresh106/final106, CPU 최고63.64%, 가용 RAM 최저37.35%, cleanup=True다. 전체 사전 검증도 71.400초, 입력2,888개, 선언 바이트333,762,506, imports64, CPU 최고53.41%, 가용 RAM 최저34.83%, cleanup=True로 통과했다. 사전 검증의 바이트 값은 Native의 실제 물리 읽기 실측과 구분한다.

## 이후 실행 원칙

- 소스 및 연결이 동일하면 통과한 CODE를 재사용한다. 실행 기록 위치만 바꾸기 위해 소스를 수정하지 않는다.
- 통과한 제품 결과는 같은 입력과 독립 검사 조건까지 충족한 경우에만 승인에 재사용한다. run004는 독립 검사 실패가 남아 있으므로 현재 승인에 재사용하지 않는다.
- 보호 중단 뒤에는 원인과 입력 변경 여부를 확인한다. 동일한 진단을 자동 반복하거나 작은 문제마다 새 runtime 변형을 추가하지 않는다.
- 개별 변경에는 관련 계약부터 실행하고 전체 Native는 승인 경계에 실행한다. 필요한 전후 실제 읽기나 원체커를 생략하지 않는다.
- 더 큰 속도 개선은 실제 단계별 시간에 근거해 직렬 중복 작업을 줄여야 한다. 이번 변경으로 569초의 전체 Native 비용이 줄었다는 실측 주장은 하지 않는다.

## 목표 재개 결과

소스를 고정한 Native run007은 실제 제품 호출을 한 번 실행했다. GO부터 완전 출력 수집까지 2.940초, exit0, 제품 terminal summary 1 passed/0 failed/248 filtered out이었다. 그러나 544.93초 시점 final_source_freeze에서 시스템 CPU97.16%로 STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING이 발생했다. before 경계는 입력2,855개/242,575,809바이트를 읽었지만 after 경계가 완료되지 않아 전체 Native는 STOPPED_NOT_ACCEPTED다. 제품 출력만으로 공식 승인하지 않는다.

중단 시 소유 Job active_processes0, owned_job_cpu_machine_percent0, parent CPU0%, 가용 RAM31.58%, owned_tree_empty=True 및 cleanup=True였다. 마지막 CPU 상승의 프로세스별 원인은 확정되지 않았다. 마지막 가용 attribution 표본은 보호 프로세스 등의 접근 불가로 coverage_complete=False이므로 Defender 또는 다른 프로세스가 원인이라고 단정하지 않는다. OS 설정 및 외부 프로세스는 변경하지 않았다.

이 결과도 지연의 대부분이 제품 자체가 아니라 준비·전후 검증에 있음을 뒷받침한다. 다음 최적화는 이 직렬 준비 경로의 중복 비용에 집중하며, 통과한 CODE31은 같은 소스를 쓰는 동안 유지한다. Native 실패를 제품 승인으로 대체하거나 같은 실패를 즉시 자동 반복하지 않는다.

공식153/249, 잔여96, next160, generation48 및 P09/A12/A13 OPEN을 유지한다. 목표는 ACTIVE이며 PC 프리즈 또는 전체 속도 문제가 해결됐다고 주장하지 않는다.

## 동일 소스의 Native 실행 번호 선택

입력 읽기 경로는 이미 잠근 핸들을 재사용해 두 경계의 중복 Native open을 제거했다. 남은 두 실제 읽기를 과거 결과로 대체하지 않는다. 따라서 이번 추가 개선은 보호 중단 후 새 runtime 파일을 복제하던 흐름을 없애는 데 적용했다.

기존 controller 한 개에서 --native-attempt 7..14를 실행 전 한 번 선택한다. worker는 정확한 case160 task에서 같은 번호를 선택한다. 각 번호의 graph config, manifest, capsule, CODE/DATA, preflight 및 Native root는 별도 위치이며 기존 파일 덮어쓰기와 자동 재시도는 허용하지 않는다. 새 runtime 소스 파일은 추가하지 않았다. 변경된 연결과 소스는 새 CODE로 검증하고, 이후 같은 소스의 실행 선택에는 복제·편집을 하지 않는다.

Native008의 최초 CODE 시도는 시스템CPU82.54% 경고로 current_source_bytes에서 중단돼 실패 기록을 보존했다. 짧은 읽기 전용 자원 표본에서 CPU28.32/41.41/27.15%, 가용RAM32.3~32.5%를 확인한 뒤 별도 슬롯으로 진행했다. 두 번째 CODE는 32계약 오류0·실패0·skip0, 12.209초, fresh106/final106, helper62, CPU최고46.2%, 가용RAM최저30.25%, cleanup=True로 통과했다.

Native008 whole preflight는 71.452초, 입력2,888개, 선언 바이트333,764,489, imports64, CPU최고63.48%, 가용RAM최저31.03%, cleanup=True로 통과했다. CODE32 및 preflight는 Native·제품·승인이 아니다. 보호 조건·초당 acquisition14 및 binary1MiB/s/other2MiB/s는 유지했다.

Native008은 실제 입력 고정 중 시스템CPU92.38%로 STOP_NATIVE_OPEN_AFTER_HOST_SATURATION이 발생해 70.13초에 DEFERRED_NOT_STARTED로 종료됐다. worker_created=False, actual_product_child_executed=False, owned_tree_empty=True, cleanup=True였다. 부모 CPU최고2.536%, 마지막0%, 가용RAM최저25.37%이며 입력고정90% 경고 기준을 유지했다. 같은 실패의 자동 재시도나 승인 승격은 하지 않았다.

## 선택형 프로세스 성능 계수

기존 읽기 전용 measure_resource_crosscheck.ps1에 IncludeProcessCounters 선택을 추가했다. 기본값은 꺼져 있고 원 runner·중단 기준·Native Frame에는 연결하지 않는다. 해당 세 PowerShell 파일은 Native008 입력 범위에 없으며, 변경 후에도 controller CODE32의 실제 소스 hash가 같음을 확인했다.

표준 Win32_PerfFormattedData_PerfProc_Process 조회로 관리자 승인 없이 Defender 등 지정 역할의 성능 계수를 수집했다. 임의 프로세스명·경로·command line은 저장하지 않고 역할과 PID 및 숫자만 보존한다. 최대64개, 조회실패는 unavailable, PID 생성 identity와 인과관계는 미확정으로 기록한다. Process 계수의 모든 thread 시간 합계를 논리 프로세서 수로 나눈 값과 시스템 전체 계수를 구분한다. [Microsoft WMI 성능 모니터링 문서](https://learn.microsoft.com/en-us/windows/win32/wmisdk/wmi-tasks--performance-monitoring)와 [Process 계수 정의](https://learn.microsoft.com/en-us/previous-versions/aa394323(v=vs.85))를 따른다.

mock 기반 수치·범위·누락·역할 필터·64개 상한 검사가 통과했다. 실제 선택형2표본은 native CPU26.23/48.88%, CIM CPU24/46%, Defender의 전체 용량 기준 시간 계수5.9375/6.875%, 조회0.4082/0.4343초였다. 이는 Native008 중단 이후의 다른 구간이며 CPU92.38% 중단 주체를 증명하지 않는다. 기본값1표본에서는 선택형 필드가 생성되지 않았고 제품 실행 없이 완료됐다. 기존 자원 증거 검증12개도 통과했다.

두 측정 기록은 target의 원본을 유지한 채 evidence에 바이트 그대로 복사하고 hash 일치를 확인했다. 다음은 같은 소스를 유지하면서 입력 고정 구간과 프로세스 성능 계수의 시간 관계를 확인하는 것이다. 현재까지 CPU 폭증의 원인은 미확정이며 공식153/249, 잔여96, next160 및 P09/A12/A13 OPEN을 유지한다.

## 동시 측정과 전체 초기 입력 복원

Native009는 CODE32 및 whole preflight 통과 뒤 실행 시작3.23초에 시스템CPU83.15% 경고로 중단됐다. worker·제품 실행은 없고 cleanup=True였다. 후속8표본은 Native CPU19.98~32.58%와 CIM18~32%가 대체로 비슷했으며 중단 순간을 측정한 것은 아니다.

Native010은 보조8표본을 시작한 뒤 실행했다. 시작 구간의 Native CPU11.14~27.71%, CIM7~35%, Defender 전체 용량 기준 시간 계수0~0.3125%를 확인했다. 입력 고정 구간의 별도8표본은 Native CPU24.48~36.36%, CIM22~35%, Defender0.3125~3%였다. 보조 측정은 원 guard와 별도이며 서로 동일한 측정 구간을 보장하지 않는다. 이 실행에서는 이전 급등이 재현되지 않아 CPU 폭증 원인을 확정하지 않는다. 세 측정은 target 원본을 유지한 채 evidence로 복사하고 동일 hash를 확인했다.

Defender 평균 검사 CPU목표10, 낮은우선순위True 및 idle scan throttle 비활성화False를 현재 읽기 전용으로 확인했다. HideExclusionsFromLocalUsers=True이고 제외 목록에는 실제 경로 대신 비경로 표시값만 반환돼 개발 폴더 제외 유지 여부는 현재 권한에서 UNVERIFIED다. 목록이 안 보인다고 제외가 없다고 판단하지 않는다. [Microsoft의 제외 목록 표시 정책](https://learn.microsoft.com/en-us/windows/client-management/mdm/defender-csp#configurationhideexclusionsfromlocalusers)에 따라 표시와 실제 적용은 구분한다. 설정은 변경하지 않았다.

Native010 당시 후보 검사는 실제 전후2경계·2,855입력, 제품1PASS, GO→완전수집2.010초, 전체585.14초, CPU최고72.29%, 가용RAM최저44.71%, 빈tree 및cleanup=True로 통과했다. 그러나 독립 전체 검사는 BOOTSTRAP_CONTROLLER로 실패했다. 첫 누락에서 검사를 끝내는 원 조건을 바꾸지 않고, 실패 frame의 원 CODE_PINS/SOURCES 요구 집합을 확인해 누락된 초기 tool50개를 모두 찾았다. Native010 기록은 보존하며 승인에 사용하지 않는다.

50개의 핀 값은 현재 후보의 source_freeze가 아니라 승인된 case159의 고정 원본에서 가져왔다. 50개 모두 승인된 원본에 있었고 합계477,533바이트였다. 선언 준비는 실제 fresh53/final53, cleanup=True로 완료됐다. 최초 선언 준비의 authority 정리 필드명 오류도 별도 실패 기록으로 보존하고 실제 resource_cleanup_confirmed 필드를 확인해 수정했다.

기존 controller에 이 선언·생성자 pin·50개 입력을 bootstrap 반환 및 DATA 읽기 전에 연결했다. 검사 조건·파일·기존 실패 기록을 삭제하지 않았다. 수정된 Native011 CODE32는 오류0·실패0·skip0, fresh158/final158, helper62, 17.419초, CPU최고55.3%, 가용RAM최저47.90%, cleanup=True로 통과했다. 기존 독립 검사기에는 실행 번호·보고서 슬롯 선택을 추가했으며 경로 선택3계약은 통과했다. 이3계약은 전체 oracle 검증을 대신하지 않는다.

수정된 연결의 Native011 whole preflight는 76.565초, 입력2,890개, imports64, CPU최고61.86%, 가용RAM최저38.04%, cleanup=True로 통과했다.

## Case160 공식 승인 완료

2026-10-15 Native011은 전후 실제2경계·2,857입력, bootstrap340입력, 제품1PASS, GO→완전수집1.957초, 전체555.37초, CPU최고49.61%, 가용RAM최저44.17%, 빈tree 및cleanup=True로 통과했다. 원 검증이 요구하는 전체 초기 입력을 복원한 뒤 기존 독립 검사도 fresh279/final279, 76.290초, CPU최고62.69%, 가용RAM최저43.81%, cleanup=True로 통과했다.

기존 qualified optimized acceptance v1/v2/v3 엔진과 원 acceptor bytecode를 유지한 case160 facade를 연결했다. Native scope를 먼저 검증한 뒤 독립 oracle 및 새 facade·테스트를 추가 승인 증거로 읽었다. 새 파일을 과거 Native 입력으로 소급하지 않았고 제품을 재실행하지 않았다. facade 경로·epoch·원 범위 검증 실패 시 증거를 읽지 않는 순서3계약은 별도로 통과했다.

공식 case160-current-epoch-accept001 기록은 accepted_count_before153, delta1, after154, remaining95, next161, generation49, resource_cleanup_confirmed=True다. 원 runtime 전체2,857입력·242,618,708바이트·372디렉터리·두 실제 읽기와 소유 Native 정리를 검증했다. 승인 단계 fresh1134/final1134, 2281 read passes, 154,648,309바이트이며 runtime·controller·oracle·facade·테스트 핀 일치를 다시 확인했다. 승인 단계 CPU최고66.99%, 가용RAM최저47.44%, cleanup=True다.

공식154/249, 잔여95, next161, generation49로 이동했다. P09/A12/A13은 OPEN이고 full249 및 signed16 전체 승인이나 whole-runtime reconciliation 완료로 승격하지 않는다. 다음 compiled249의161번 대상은 actual_import::source_review_cell_output::cached_cell_callback_rejects_all_provider_scope_substitutions다. 목표는 ACTIVE이며 PC 프리즈 해결 또는 P09~P20 전체 완료는 주장하지 않는다.

근거: evidence의 case160-current-runtime-run004/run007/run008/run009/run010/run011, native009/010/011-controller-r391, native010-independent-oracle-r392-attempt001..004 및 native011-independent-oracle-r392-attempt001, native010-bootstrap-requirements-r392 및 attempt002, case160-current-epoch-accept001, case160-optimized-acceptance-attempt001, 세 r392 crosscheck 기록과 관련 소스.
