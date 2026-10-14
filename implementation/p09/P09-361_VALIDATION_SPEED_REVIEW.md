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

## Case161 공통 준비 경로

case별 준비 script를 복제하지 않도록 prepare_current_queue_step과 produce_current_queue_envelopes를161..249의 공통 인자로 구현했다. 기존160 이하의 승인 코드와 원본은 수정하지 않았다. STEP은 승인된 case160과 compiled249의 정렬된 명단에서 정확한161번 이름 및 before154를 확인하고 불변 config001로 준비했다. fresh9/final9, CPU최고41.78%, 가용RAM최저46.99%, cleanup=True다.

기존 qualified codec·exclusive publisher·2MiB/s 쓰기를 재사용해 과거134/run001,154/run002,127/run002 및 승인된160/run011의 별도 무손실 표현을 준비했다. 원본11,533,535바이트에서 encoded3,747,348바이트, 절감7,786,187바이트다. 각 원본을 두 번 정확한 바이트로 복원해8회 확인했으며 fresh31/final31, CPU최고39.97%, 가용RAM최저48.15%, cleanup=True다. 이는 자료 표현 준비이며 새 runtime·Native·제품 승인이나 기존 원본 교체가 아니다.

신규 선택·생성기7계약과 기존 codec·물리IO 관련 계약을 함께 실행해 총36개가 통과했다. 원본 경로·현재 사례·소스 파일은 envelope 대상으로 허용하지 않고, 사전 승인·정리·두 실제 경계·명단 전체를 요구한다.

승인된160의 전체 semantic 범위와 승인 fresh 입력을 기존 명시적 alias로 합친 예비 계산은 기존34개와 새4개를 합한38pair, physical2,861입력·371dirs·239,297,766바이트·명목596.085초다. 신규 controller/config/CODE/preflight는 포함하지 않았으므로600초 내 전체 실행을 증명하지 않는다. 실행 전에 전체 scope와 provenance 연결 및 원 비용 모델을 검증해야 한다. 제한·실제 두 바이트 읽기·원 검사 범위를 줄이지 않는다.

공식154/249·잔여95·next161·generation49와 P09/A12/A13 OPEN을 유지한다. case161 제품 실행은 NOT_RUN이며 다음은 공통 successor 연결과 전체 비용·사전 검증이다. 목표는 ACTIVE다.

근거: evidence의 case160-current-runtime-run004/run007/run008/run009/run010/run011, case160-current-epoch-accept001 및 optimized-acceptance-attempt001, case161-step-config001/successor-selection001/lossless-receipts001/prospective-inherited-cost001, 앞선 r391/r392 기록과 관련 소스.

## 반복 계산과 잘못된 최종 검사 제거

새 공통 successor Binding의 두 번째 준비 실행은 자원 보호가 아니라 audit_final_hash_inventory 오류로 실패했다. 원 AuditEvidenceReader.finish는 전체 입력을 다시 읽고 누적 final_fresh_hashes가 입력 수와 같은지 검사하는 일회성 종료 연산이다. 같은 reader에서 finish를 두 번 호출해 불필요한 전체 재읽기 후에도 개수 검사에서 실패했다. 실패 기록과 이미 발행된 manifest002는 보존하고 채택하지 않았다.

최종 검사를 manifest의 실제 발행·읽기와 범위 투영 뒤에 한 번만 호출하도록 수정했다. 모든 입력은 최초 실제 읽기와 마지막 실제 재읽기를 유지한다. 신규 manifest는 종료 검사가 실패하면 성공 결과로 채택되지 않는다. 코드 회귀 검사는 manifest pin과 투영 뒤에 finish가 정확히 한 번 있는지 확인한다.

기존 준비 코드의 입력 병합도 개선했다. 승인 fresh 입력 1,134개를 하나씩 추가할 때마다 전체 목록을 다시 검증하던 1,135회 extend를 두 번의 일괄 extend로 바꿨다. 명시적 물리 alias의 정확한 pin, 일반 입력 충돌, 전체 pin 형식, 원 guard 오류 및 변경 전후 입력 불변성을 검사한다. 실제 predecessor와 준비 메타데이터를 사용한 단일 코어·낮은 우선순위 비교에서 동일한 병합 결과 2,909개를 얻었다. 기존 23.4856초 대 수정 0.0610초였으며, 이 값은 물리 투영 이전의 범위 병합만 측정한다. 메타데이터 fresh6/final6, CPU최고29.14%, 가용RAM최저50.66%, cleanup=True였다. 전체 Native 시간 단축률로 환산하지 않는다.

수정한 Binding과 기존 범위·전체 oracle 연결 테스트 28개는 실패·오류 없이 통과했다. 실제 case161 준비003은 38pair를 그대로 연결하고 물리·의미 입력 각각2,871개, 물리 바이트239,778,095, 실제 준비 읽기208회·275,719,257바이트, fresh103/final103으로 통과했다. 원 constructor 역투영과 나머지 scope·resource·byte·handle oracle method identity를 유지하며, 과거 실패 lineage를 현재 승인으로 다시 표시하지 않는다.

준비003 전체136.7016초 중 admission1.0007초, predecessor·의존 입력9.6578초, 원본·envelope 읽기59.1105초, manifest 발행·범위 투영0.2275초, 한 번의 완전한 최종 재읽기66.7050초였다. CPU최고32.59%, 가용RAM최저50.42%, cleanup=True다. 이는 준비 경로 통과이며 새 parent·worker·CODE·전체 preflight 또는 제품 실행은 아니다. 준비 소스와 보고서 pin은 새 Native의 사전 검증에서 확인해야 한다.

작업 속도 개선은 불필요한 검증 변형과 재검사를 줄이는 데 우선 적용한다. 동일 입력·소스에서 통과한 결과는 정확한 pin 및 승인 조건이 유지되는 범위에서 재사용하고, 변경에는 관련 계약부터 실행한다. 원인 확인 없는 자동 재시도, 사례별 controller 복제, 개별 진단마다 보조 script 추가, 상태 확인만을 위한 전체 Git 조회를 반복하지 않는다. 이 실행에는 OS 설정 변경·Defender 제외 변경·외부 프로세스 종료·한글 접근 허용 요청이 없었다.

P09 목표는 case161 공통 successor 연결 작업으로 재개했다. 다음 완료 경계는 실제 parent·worker·독립 oracle 연결과 전체 입력 비용 검증이다. 앞선596.085초 계산과 준비003은 아직 신규 전체 runtime 연결을 포함하지 않으므로 GO를 허용하지 않는다. 공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN을 유지한다.

근거: tools/p09/current_queue_successor_binding.py 및 해당 테스트, evidence/p09-361-case161-successor-binding001/002/003.v1.json과 successor-manifest002/003.v1.json. 병합 비교는 이 세션의 bounded terminal 실행 결과다.

## 공통 부모 작업 프로세스와 전체 검사 연결

current_queue_successor_connections는161..249의 공통 private graph를 구성한다. 원 parent·Frame·worker·whole oracle 소스10개를 고정된 hash와 원 non-import AST로 읽고 동일한 Binding namespace를 공유한다. 원 worker connector 본문·defaults·closure를 유지하며 encoder·decoder와 compact pack의 사례·개수·필드명 상수만 변경한다. 역변환은 원 code 전체와 같아야 한다. 사례별 원본 연결 소스나 approved case160을 변경하지 않는다.

공통 연결8계약과 기존 Binding·worker·compact wire·whole oracle 계약을 함께 실행해53개가 통과했다. fixture parent에서 원 두 읽기·decoder·Frame 정리와 정책 복원을 확인했고, whole checker의 원 terminal 실패가 계속 실패하는지 확인했다. 타 사례의 transport, hash 변조, 닫힌 실행 번호 위반 및 자동 재호출은 거부한다. 최초 whole oracle fixture는 필수 mechanics_projection 의존 항목이 빠져 실패했으며 fixture를 원 인터페이스에 맞춘 뒤 통과했다. 원 oracle 조건은 바꾸지 않았다.

실제 case161 연결 준비001은 승인160·compiled249 명단·STEP·manifest003의 맥락과 pin을 새로 확인했다. 38pair 전체를 compact wire13,340바이트로 전달·복원해 descriptor 및 manifest pin이 모두 일치했다. 기존16KiB 제한을 유지했고 actual artifact를 읽은 뒤 입력29개 모두 최종 재확인했다. 전체9.1513초, CPU최고17.70%, 가용RAM최저45.43%, cleanup=True다. 현재 연결 소스·테스트·capsule의 실제 hash도 준비 기록과 일치한다.

기존 strict window의 원 전체 비용 함수를 연결 준비 범위에 적용한 계산은 physical2,877입력·239,853,617바이트, shared decoder5초 포함597.8299초다. 한도600초까지 명목 여유는2.1701초이며 새 actual runtime controller·CODE·whole preflight를 아직 포함하지 않았다. 이 계산은 실행 허용이 아니다. 추가 증거 표현 최적화와 실제 실행의 전체 imported closure를 검증해야 한다. 범위·속도·시간 제한을 완화하지 않는다.

공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN을 유지한다. 새 전체 engine·worker dispatch·독립 oracle의 실제 제품 실행은 NOT_RUN이며 목표는 ACTIVE다. 다음은 실제 공통 실행 컨트롤러 연결과 전체 비용 여유 확보다.

근거: tools/p09/current_queue_successor_connections.py와 해당 테스트, evidence/p09-361-case161-successor-connections001.v1.json 및 successor-worker-capsule001.compact.v1.json. 비용 계산은 이 세션에서 원 비용 함수를 실행한 bounded terminal 결과다.

## 추가 무손실 표현과 실제 엔진 구성

연결 준비002는 승인 predecessor 범위에서 아직 표현을 바꾸지 않은 과거 runtime 영수증6개를 크기순으로 선택했다. source·EXE·현재 사례·이미 mapped된 항목은 제외한다. 기존 qualified codec과2MiB/s exclusive publisher로 원본13,595,897바이트를 encoded3,678,102바이트로 준비해9,917,795바이트를 절감했다. 원본마다 두 번 정확히 복원해12회를 확인하고 원본을 변경하지 않았다. 새 selector 계약도 통과했다.

기존38pair를 보존한 expanded manifest002와44pair 전체를 복원하는 worker capsule002를 발행했다. wire15,335바이트는 원16KiB 한도 안에 있다. 실제 준비는 fresh52/final52,29.0961초, CPU최고45.83%, 가용RAM최저44.80%, cleanup=True다. 준비001은 보존하고 현재 준비에는002의 실제 source·artifact pin을 사용한다.

원 strict window 비용 함수를 같은 방식으로 실행한 현재 연결 범위 추정은 physical2,878입력·229,988,091바이트, shared decoder5초 포함588.4928초다. 앞선597.8299초보다 낮고600초까지 명목 여유11.5072초지만, 새 전체 controller·CODE·whole preflight 비용까지 검증한 결과는 아니다.

current_queue_successor_runtime은 사례161..249·물리 실행2..8에서 기존 qualified template chain과 단일 argument adapter를 그대로 사용한다. 원 두 source pin과 전체 metadata code 역변환을 검사해 root·task·logical run이 일치하는 factory를 구성한다. 실제 case161/run002의 기존 whole engine과 worker callable을 구성했고 새 parent 입력 binding·worker 진입점은 아직 연결하지 않았다.

첫 factory 준비는 script 실행의 저장소 모듈 검색 경로 누락으로 계약 로딩에 실패했다. 실패001은 보존하고 명시적 저장소 sys.path를 추가했다. factory002의3계약·실제 구성·fresh16/final16은7.0705초, CPU최고7.86%, 가용RAM최저44.13%, cleanup=True로 통과했다. 연결·factory와 기존 관련 계약 전체57개도1.316초에 통과했다. 현재 연결 및 factory 소스·테스트·expanded manifest·capsule의 실제 hash는 준비 기록과 일치한다.

목표는 ACTIVE, 공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN을 유지한다. actual Native·제품 실행은 NOT_RUN이다. 다음은 실제 부모 입력 binding·worker 진입점과 독립 whole oracle을 연결하고 전체 CODE·closure·cost·preflight를 검증하는 것이다. OS·보호 기준·원본·approved case160은 변경하지 않았다.

근거: current_queue_successor_connections와 current_queue_successor_runtime 및 해당 테스트, evidence의 case161-successor-connections002, expanded-manifest002, worker-capsule002 및 factory001/002. 비용 추정은 원 비용 함수를 실행한 이 세션의 bounded terminal 결과다.

## 실제 부모 입력 준비와 작업 프로세스 정책 연결

공통 runtime에 실제 부모 binding callback과 once-only worker policy 연결을 추가했다. 새 binding은 현재 STEP·연결 준비·manifest·capsule·승인 predecessor·compiled249를 실제 읽고 확인한다. 이전 초기 bootstrap 입력을 모두 읽은 뒤 전체 inherited scope와 승인 fresh 입력을 명시적 alias만 사용해 병합하며 Rust787 및 고정 EXE를 유지한다. 원 parent·worker 함수는 대체하지 않고 동일 private environment와 Binding/Frame 연결을 유지한다.

부모의 두 번 읽기·정리·정책 복원, 타 worker task 및 재호출 거부, 타 사례의 부모 준비를 receipt IO 전에 거부하는3개 회귀 계약을 추가했다. 전체 관련60개가1.811초에 통과했다.

factory003은 실제 구성 검증의 bindings import 누락으로 종료돼 성공한 준비 기록이 없었다. 관측 실패를 별도 보존하고 serialized cleanup receipt는 unavailable로 구분했다. 올바른 함수에 import를 추가하고 NameError도 안전한 실패 보고 경계에 포함했다. factory004는6계약과 실제 부모 입력 준비·worker callable 연결을 fresh375/final375,87.0413초, CPU최고14.99%, 가용RAM최저43.03%, cleanup=True로 통과했다. 부모·worker dispatch count와 생성된 실제 Frame 수는0이다.

준비 의미 입력2,877개·Rust787의 원 비용 모델은 decoder5초 포함588.4297초다. 전체 imported closure·실제 worker CLI·독립 whole oracle·CODE·whole preflight는 미완료이므로 실행 허용이 아니다. factory004의 실제 runtime 소스와 테스트 hash는 현재 파일과 일치한다.

공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN, 목표ACTIVE를 유지한다. 다음은 제한된 worker bootstrap으로 실제 CLI 진입점을 연결하고 독립 whole oracle과 전체 사전 검증을 완성하는 것이다. Native·제품 실행 및 공식 승인 delta는0이다.

근거: current_queue_successor_runtime와 해당 테스트, evidence/p09-361-case161-successor-factory003/004.v1.json. fixture 및 입력 준비 결과는 실제 제품 또는 Native 승인과 구분한다.

## 실제 작업 프로세스 CLI의 승인 전 거부 검증

9,327바이트의 worker bootstrap을 발행했다. 원본 영수증 본문 대신 현재 STEP·capsule/manifest pin·과거 provenance와 특수 경로 alias5개만 전달한다. worker는 원본 runtime·authority·manifest를 읽지 않고 동일 private Binding과 capsule44pair를 복원한다. first descriptor·manifest pin·transport hash·현재 사례·작업 번호를 확인하며 기존16KiB 입력 한도를 유지한다.

actual owned-worker CLI는 case160 전용 argv parser를 불러오지 않고 원 qualified 공통 window template을 직접 사용한다. sys.argv를 숨기거나 case161을160으로 바꾸지 않는다. 원 worker의 GO 문자열·Job 소속 검사·실행 본문 및 once-only 정책은 유지한다. 관련5계약을 추가해 전체65개가3.363초에 통과했다.

factory005는 부모 입력 준비 중 기존 시스템CPU 경고로 중단됐다. 늦은 subprocess import가 예외 처리도 방해해 성공 영수증은 없었으며 원 중단 사유와 serialized resource evidence unavailable을 별도 보존했다. import를 앞당겨 보호 중단을 그대로 기록하도록 수정했다. 이 중단으로 CPU 폭증 주체가 확인되지는 않았다.

이번 변경에 대한 실제 CLI 준비는 startup-only로 검사했다. 동일한 전체 부모 입력 읽기를 다시 수행하지 않지만, parent admission을 통과했다고 표시하지 않으며 현재 소스의 전체 CODE·imported closure·parent admission·whole preflight는 실제 GO 전에 여전히 필수다. factory006/007의 준비 실패도 보존했다. audit wrapper의 script argv/import root를 바로잡고 case160 전용 parser 의존성을 제거했다.

factory008은 실제 CLI에 EOF를 전달하고 GO를 보내지 않아 원 WORKER_NOT_AUTHORIZED로 거부되는 것을 확인했다. Python audit의 과거 current-runtime/current-epoch-accept 파일 open event는0이고 제품 실행은 없었다. Source·bootstrap의 fresh17/final17,10.3759초, CPU최고32.21%, 가용RAM최저42.52%, cleanup=True다. 현재 소스·테스트·bootstrap의 실제 hash도 일치한다. 이 결과는 승인 전 startup이며 Job 승인 후 실행이나 Native·제품 통과가 아니다.

공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN, 목표ACTIVE를 유지한다. 다음은 독립 whole oracle 및 전체 CODE·closure·cost·preflight를 연결한 뒤 실제 Native 검증이다. 준비 실패를 제품 승인으로 바꾸거나 보호 기준을 완화하지 않았다.

근거: current_queue_successor_runtime와 해당 테스트, case161-successor-worker-bootstrap002 및 factory005/006/007/008 기록.

## 현재 사례의 독립 전체 검사 연결

current_queue_successor_oracle은 qualified case160의 validator family 전체를 private namespace로 복제한다. 현재 사례·이전 승인 개수·strict window 사례 번호만 원 code 전체 역변환이 성립하는 범위에서 변경한다. 원 generator·checker·defaults·closure, source·cost·resource·strict window 조건과 관측 record는 유지하며 기본 namespace를 수정하지 않는다.

기대 입력은 승인된 predecessor 및 현재 명시적 선언에서 가져온다. 원 scoped_validator가 추가하는 inherited 범위를 private generator에만 연결하고, 그 뒤 원 full physical/semantic oracle projector를 사용한다. 후보 source_freeze를 비우거나 입력을 누락해도 독립적으로 선언된 입력이 기대 범위에 계속 남는5개 회귀 계약이 통과했다.

실제 case161/run002 연결001은 기대 의미 입력2,871개를 선언에서 구성했다. 현재 candidate record를 읽거나 기대 입력의 근거로 사용하지 않았다. 연결·초기 guard와5계약 확인은 fresh28/final28,9.1565초, CPU최고34.77%, 가용RAM최저42.12%, cleanup=True로 통과했다. 현재 oracle 소스·테스트 hash는 준비 기록과 일치한다. 관련 전체70계약은3.470초에 통과했다.

이 연결은 실제 후보 checker 실행이나 공식 queue 승인에 해당하지 않는다. 전체 current imported closure·CODE·cost·parent admission·whole preflight를 검증한 뒤 Native 후보와 독립 전체 검사를 수행해야 한다. 공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN, 목표ACTIVE를 유지한다.

근거: tools/p09/current_queue_successor_oracle.py와 해당 테스트 및 evidence/p09-361-case161-successor-oracle-connection001.v1.json.

## 공통 코드 검증과 전체 메타데이터 사전 검증

current_queue_successor_controller에 CODE와 preflight의 닫힌 실행 선택을 추가했다. CODE의 원 실행 helper64개 한도는 유지하며 테스트 전용 import는 별도 증거로만 기록한다. 동일 보호 모듈을 새 default module로 중복 읽지 않고 승인된 controller의 명시적 private guard를 재사용했다. 초기 CODE helper 초과 실패와 수정 전 통과 기록은 모두 보존했다.

현재 CODE008은74계약 오류0·실패0·skip0, 기본 실행 helper63, 코드·테스트 import91, fresh91/final91,12.9625초, CPU최고31.51%, 가용RAM최저42.19%, cleanup=True로 통과했다. source 또는 연결이 바뀐 뒤에는 이전 CODE를 현재 것으로 사용하지 않았다.

전체 preflight는 원10계약을 자식 생성 금지 상태에서 실행하고, 실패 원본·Native definition pin·현재 부모 입력·Rust787 전체 목록·전체 source 범위와 비용·독립 검사기 연결을 확인한다. 원 시험이 전역 CONFIG에 가상 STEP을 남기는 문제는 시험 동안만 격리해 실제 STEP의 일회성 설정을 보존했다. 현재 STEP 파일을 실제 읽은 뒤 선언에 포함하도록 수정했다. 해당 실패와 진단 기록은 별도 보존했다.

실제 helper 목록 대조로 default import가 추가되는3개 경로를 확인했다. STEP derive 함수는 고정된 원 소스의 함수 본문을 그대로 컴파일하고 loader는 승인된 명시적 객체를 재사용했다. 원10시험 소스도 승인된 pin을 먼저 확인하고 non-import AST 전체를 유지하는 private namespace에서 실행한다. sys.modules의 기존 항목을 숨기거나 helper 한도를 늘리지 않았다. 원 source 및 두 실제 Native 읽기 의무는 유지한다.

현재 preflight007은 source 입력2,885개·Rust787·기본 helper64, fresh381/final381, 실제 준비 읽기768회·110,036,851바이트를 확인했다. 전체96.1678초, CPU최고63.13%, 가용RAM최저41.98%, cleanup=True다. 원 메타데이터 checkpoint가 복원됐고 실제 Native Frame·제품 자식은 실행하지 않았다. controller·테스트·runtime의 현재 hash는 사전 검증 기록과 일치한다.

현재 의미·물리 입력은 각각2,885개이고 물리 바이트230,075,691이다. decoder5초를 포함한 원 비용 모델은589.0763초로600초 안이다. preflight 자체의 발행 이후 기록과 실제 실행 진입점이 Native 입력으로 추가될 때 전체 비용과 핀을 다시 확인해야 한다. 사전 검증을 Native 두 실제 경계 읽기 또는 제품 승인으로 대신하지 않는다.

공식154/249·잔여95·next161·generation49 및 P09/A12/A13 OPEN, 목표ACTIVE를 유지한다. 다음은 CODE·preflight pin을 요구하는 실제 Native 실행 진입점을 연결하고 현재 후보와 독립 검사를 수행하는 것이다.

근거: current_queue_successor_controller와 해당 테스트, case161-successor-code-run002-attempt001..008 및 successor-preflight-run002-attempt001..007 기록.

## 실제 실행 진입점과 중복 준비 읽기 개선

current_queue_successor_dispatch는 고정된 CODE와 전체 preflight를 요구하고 원 외부 실행 chain, Native 진단 연결, 단일 작업 프로세스의 GO/Job, 전체 입력의 두 실제 읽기와 자원 정리를 유지한다. 기존 제품 실행 본문을 새로운 간소화 실행기로 대체하지 않는다. 새 실행 번호는 이전 번호의 제품 미실행·정리 완료·Frame 부재가 모두 확인된 경우에만 허용하며, 통과 또는 미해결 제품을 다시 실행하지 않는다.

실제 Native002는 메타데이터 시작1.65초에 기존 CPU 경고 보호로 중단됐다. 시스템CPU는97.54%, 해당 부모CPU 표본은0%, 부모 메모리는 약46MiB였다. 작업 프로세스와 제품은 생성되지 않았으며 source Frame도 없었다. cleanup과 빈 프로세스 트리가 확인됐다. 높은 CPU 표본에서 추가 프로세스 진단은 기존 정책에 따라 unavailable로 기록됐으므로 CPU 상승 주체는 확인되지 않았다.

준비 단계가 약110MB를 읽고 최종 확인한 뒤 실제 실행의 메타데이터 단계가 같은 선언을 다시 읽는 중복을 제거했다. 시작 단계에서는 고정된 작은 선언과 코드만 확인하고, 전체 CODE·preflight·모든 source pin 및 predecessor 검사에는 실제 metadata callback을 사용한다. 이 callback은 Frame 획득과 GO 전에 반드시 실행된다. 미래 Native 두 바이트 경계 검사를 준비 기록으로 대신하지 않는다.

번호003의 CODE001은74계약·fresh91/final91·12.959초, 전체 preflight001은 원10계약·입력2,885개·Rust787·fresh381/final381·96.257초로 통과했다. 연결003은44pair·wire15,335바이트, worker bootstrap003은9,327바이트로 기존16KiB 한도 안이다. 이들 준비 결과는 제품 승인과 구분한다.

Native003은49.02초에 실제 실행의 imported-helper 한도 검사로 중단됐다. CPU최고64.96%, 가용RAM최저31.57%였고 제품 및 작업 프로세스는 실행되지 않았다. cleanup과 빈 트리가 확인됐다. 사전 검증의 default import 수 외에 실제 엔진이 명시적으로 요구하는 helper가 추가되는 차이를 확인했다. 약3.09초의 구성 점검은 private 연결 이후에도 default60개와 실제 witness를 합친65개가 남는 것을 확인했다.

고정된 원 소스 전체와 기존 controller를 명시적 private namespace에서 재사용하도록 수정했다. 원 loader의 모든 non-import AST 확인을 유지하고, 내부 import는 같은 고정 그래프로 연결한다. 함수의 builtins가 생성 시 고정되는 점을 반영해 동일 code·defaults·closure로 함수를 다시 연결했다. 기본 sys.modules와 공유 builtins를 수정하지 않았으며, 기존 모듈을 숨기거나 원 입력을 삭제하지 않았다. 실패한 namespace 연결과 이전 qualification 기록도 보존했다.

현재 dispatch qualification run003-006은6계약 오류0·실패0·skip0, fresh385/final385, 기본 helper59개 및 실제 Native 명시 witness 포함64개를 확인했다. Rust 전체 목록의 실제 조회는167회이며 원 비용 모델은590.6479초다. 전체108.787초, CPU최고62.85%, 가용RAM최저31.975%, cleanup=True다. 현재 dispatch와 테스트의 hash·바이트 수는 해당 기록과 일치한다. qualification 자체의 발행 및 새 실행 번호 선언을 실제 Native 입력으로 추가할 때 비용과 핀은 다시 확인해야 한다.

공식154/249·잔여95·next161·generation49, P09/A12/A13 OPEN 및 목표ACTIVE를 유지한다. 수정본의 실제 Native·제품은 아직 NOT_RUN이다. 다음은 중단된002/003을 덮어쓰지 않는 번호004의 선언·CODE·전체 preflight·entry 검증과 실제 Native 및 독립 전체 검사다.

근거: tools/p09/current_queue_successor_dispatch.py와 해당 테스트, case161-current-runtime-run002/003, successor-code-run003-attempt001, successor-preflight-run003-attempt001, successor-dispatch-qualification-run002-attempt001/002 및 run003-attempt001..006 기록. OS 설정과 자원·시간 한도는 변경하지 않았다.

## 사례161의 실제 실행과 공식 승인

번호004의 연결44pair·wire15,335바이트와 bootstrap9,327바이트를 준비하고, CODE74계약 및 원10계약의 전체 preflight를 통과했다. entry qualification001은 시작1.512초에 시스템CPU91.21%로 기존 보호에 중단됐고 제품은 실행되지 않았다. 중단 시 부모 CPU·메모리·실제 읽기량을 작은 숫자 기록으로 남기도록 보완했다. 짧은 시스템 표본11.29%·23.99% 이후 qualification002는 실제 Native helper64개·fresh386/final386·101.028초·CPU최고43.58%·가용RAM최저32.223%·cleanup=True로 통과했다.

Native004는 전체 입력2,891개에 대한 실제 두 바이트 경계와 제품1PASS를 완료했다. GO부터 완전한 출력 수집까지1.3049초로 원15초 이내였고, 전체576.33초·CPU최고82.01%·가용RAM최저29.924%였다. Frame은 COMMITTED이며 cleanup과 빈 소유 프로세스 트리가 확인됐다. 자원·속도·입력·시간 한도는 유지했으며 PC 프리즈의 원인 해결을 주장하지 않는다.

review_current_queue_successor는 선언 및 승인 predecessor에서 기대 범위를 먼저 구성하고, 그 뒤 원 frozen prepare와 전체 validator를 그대로 호출한다. 후보 관측을 기대 범위로 복사하지 않는다. 새 리뷰 코드는 별도 source reader로 실제 앞뒤 해시를 확인하며 Native 입력이었다고 소급하지 않는다. 연결2계약과 실제 독립 전체 검사001은 fresh390/final390·108.876초·CPU최고51.69%·가용RAM최저31.011%·cleanup=True로 통과했다. 리뷰 과정에서는 제품·Native 및 원장 쓰기를 실행하지 않았다.

accept_current_queue_successor는 qualified optimized acceptance v1-v3와 원 수용 bytecode를 재사용한다. 다시 수행하는 전체 후보 검사가 성공한 뒤에만 독립 리뷰 및 새 facade의 source witness를 읽는다. 리뷰의 일회성 CONFIG는 원 configure 코드와 defaults·closure를 유지한 private module에 연결하며 기본 실행 CONFIG를 초기화하지 않는다. 3개 회귀 계약이 통과했다.

처음 승인 연결은 진단 파일명 규칙에서 거부됐다. 승인 검증은 시작되지 않았고 canonical 및 기존 진단 파일이 생성되지 않은 것을 확인했다. 해당 실패를 별도 보존하고 원 optimized-acceptance 경로 형식으로 수정했다. 기존 validator의 경로 규칙을 완화하지 않았다.

공식 canonical case161-current-epoch-accept001은 before154·delta1·after155, 잔여94·next162·generation50으로 발행됐다. 수용 경계의 fresh input1,196개와 최종 해시1,196개, 실제 읽기2,410회·186,423,657바이트 및 resource cleanup을 확인했다. 승인CPU최고55.08%·가용RAM최저30.212%이며 제품·Native 재실행은0이다. Native 후보 해시와 독립 리뷰·승인 source의 현재 해시도 일치한다.

155/249는 해당 제품 검증 큐의 공식 승인 수다. P09/A12/A13은 OPEN이며 full249·signed16·전체 runtime reconciliation을 완료했다고 표시하지 않는다. 목표는 ACTIVE이고 다음 작업은 현재155 원장을 기준으로 사례162를 준비·실행·독립 검사·승인하는 것이다.

근거: case161-current-runtime-run004, successor-whole-review-run004-attempt001, current-epoch-accept001, optimized-acceptance-attempt001 및 successor-acceptance-facade-setup001 기록. 구현은 review_current_queue_successor와 accept_current_queue_successor 및 해당 테스트다. 모든 이전 중단·준비 기록과 사용자 소유 변경은 보존했다.

## 사례162 준비와 작업 프로세스 전송 크기

현재155 원장과 승인161 후보에서 사례162의 STEP을 준비했다. 새로 선택한 원본4개는11,056,581바이트에서 무손실 표현3,469,660바이트로 바뀌며7,586,921바이트가 절감됐다. 원본은 수정하지 않았고 모든 복원과 최종 해시 확인이 통과했다.

Binding001은 기존44개와 새4개 연결을 합친48pair를 확인했다. fresh123/final123, 물리 입력2,902개·229,104,023바이트, CPU최고51.89%·가용RAM최저30.778%·cleanup=True다. 이어진 기존 compact wire 연결002는 원16KiB 한도를 초과해5.234초에 거부됐다. 실패 기록은 보존됐고 제품·Native는 실행하지 않았다.

bounded_successor_capsule_wire_v2는 동일한 전체 compact 자료에만 무손실 압축 표현을 적용한다. 원 worker encoder/decoder의 code·defaults·closure와 기존 pack/unpack, 현재 context·transport hash·Binding 검사는 유지한다. 전송 한도는16KiB 그대로이며 복원 자료에는131,072바이트 상한을 둔다. 끝나지 않은 복원·남은 압축 데이터·잘못된 해시·중복 또는 추가 키·비정상 형식을 거부하고 canonical 재인코딩으로 정확한 역변환을 확인한다. 입력 객체나 기본 namespace를 변경하지 않는다.

5개 회귀 계약과 실제 사례162의48pair 검증001이 통과했다. 전송은7,003바이트이며 원 decoder가48개 연결과 manifest를 정확히 복원했다. 실제 준비는 fresh23/final23·8.173초·CPU최고34.05%·가용RAM최저31.924%·cleanup=True다. 새 소스와 테스트의 현재 hash도 기록과 일치한다. 249개 임의 해시를 항상16KiB에 넣을 수 있다는 보장은 하지 않으며, 임의 자료가 한도를 넘으면 연결을 버리지 않고 거부한다.

이 결과는 전송 단위의 검증이다. 원 parent와 실제 worker 진입점 모두에 v2를 연결하고, 새 source 선언·전체 CODE·preflight·비용·실제 Native 및 독립 검사를 수행해야 한다. 승인된161과 기존 v1 소스는 그대로 보존했다. 공식155/249·잔여94·next162·generation50, P09/A12/A13 OPEN 및 목표ACTIVE를 유지한다.

근거: case162-successor-selection001, lossless-receipts001, successor-binding001, successor-connections002 및 bounded-wire-qualification001.v2.json. 새 전송 자료는 case162-bounded-worker-capsule003.v2.json이며 구현과 회귀 검사는 bounded_successor_capsule_wire_v2에 있다.

## 사례162의 v2 실행 연결과 CPU 보호 중단

current_queue_successor_wire_runtime_v2는 승인161에서 고정된 v1 source5개를 명시적 private namespace로 읽고 원 함수 본문·defaults·closure를 유지한다. parent와 실제 worker가 같은 v2 전송을 사용하도록 연결했으며 새 코드·테스트·전송 코드를 각 실제 reader의 입력과 최종 해시 확인에 포함한다. v1 파일과 공유 builtins 및 sys.modules는 수정하지 않았다.

첫 worker 시작 검사는 사례160 전용 controller의 인자 파서 의존성으로 실패했다. 해당 기록을 보존하고 worker에서는 과거 controller를 구성하지 않도록 수정했다. 이후 원 worker의 GO 없는 WORKER_NOT_AUTHORIZED 거부를 확인했다. 준비004의 entry 검사는 실행하지 않은002/003의 Native 기록을 요구해 중단됐다. 없는 기록을 만들어 넣거나 기존 replay guard를 완화하지 않았다. graph 기록의 경로 metadata만 v2로 분리했고, source AST 전체의 정확한 역변환으로 그 외 본문이 유지되는 것을 확인했다.

현재002 graph v2는48pair·wire7,003바이트·fresh37/final37·10.180초로 통과했다. startup factory003은 원11계약·fresh23/final23·11.769초·CPU최고40.34%·cleanup=True로 통과했다. CODE002-001은74계약·fresh96/final96·13.942초, 전체 preflight002-001은 원10계약·입력2,909개·Rust787·fresh400/final400·114.609초·CPU최고62.75%·가용RAM최저28.018%로 통과했다.

entry002-001은 원6계약, 실제 Native helper64개 및 fresh401/final401을 확인했다. 전체118.039초·CPU최고44.47%·가용RAM최저29.373%·cleanup=True다. 준비된 물리 입력2,910개의 원 비용 모델은591.2856초이며 추가로 발행된 qualification도 실제 Native 입력에 포함된다. 이 계산은 실제 완료를 보증하지 않는다.

실제 Native002는233.13초에 원 acquisition CPU 포화 보호로 중단됐다. 마지막 시스템CPU94.65% 표본에서 해당 부모CPU는0%, 부모 메모리는49.449MiB였다. 직전 시스템 표본은29.8%·21.55%·31.81%였다. worker와 제품은 생성되지 않았고 실제 입력 바이트 경계도 시작되지 않았다. Frame은 CLOSED, 열린 잠금2,366개가 모두 닫혀 remaining0이며 cleanup과 빈 소유 프로세스 트리가 확인됐다.

잠금 코드의 원 호출 속도·no-burst 및 resource/identity 검사를 점검했다. 경고 구간의 추가 프로세스 진단은 기존 정책에 따라 unavailable이었다. 낮은 부하 구간의 일부 Python·앱 계수는 중단 순간의 CPU 상승 주체를 증명하지 않으므로 특정 외부 프로세스 원인으로 확정하지 않았다. 보호나 OS 설정을 바꾸지 않았으며 프리즈 해결도 주장하지 않는다.

v2 readonly review/acceptance adapter는 원 frozen source와 검사·승인 본문을 재사용하는 별도 연결을 구현했고2개 계약이 통과했다. 실제 Native 후보가 없으므로 실제 독립 검사·승인은 NOT_RUN이다. 다음은 중단된 partial Frame의 완전 정리 증거와 원 replay 조건을 보존한 새 번호 준비다. 동일002와 승인161을 덮어쓰거나 재실행하지 않는다.

공식155/249·잔여94·next162·generation50, P09/A12/A13 OPEN 및 목표ACTIVE를 유지한다. 근거는 case162-successor-connections002.v2, successor-factory001..003, successor-code/run002·004, successor-preflight/run002·004, successor-dispatch-qualification/run002·004 및 current-runtime-run002 기록이다. 구현은 current_queue_successor_wire_runtime_v2와 current_queue_successor_wire_review_v2 및 해당 테스트다.

## 사례162 재시도 연결 개선과 공식 승인

제품 실행 전 중단된 partial Frame은 CLOSED, 모든 잠금 닫힘, 실제 읽기 경계 없음, reader와 stream 없음, 원 open 함수 복원 및 빈 소유 프로세스 트리가 확인된 경우에만 새 번호 준비에 사용한다. 살아 있는 Frame이나 제품 실행이 관측된 기록은 거부한다. 원 기록을 수정하거나 제품 결과를 재실행하지 않는다. graph와 capsule 및 bootstrap의 경로 metadata를 함께 v2로 분리하고 원 AST의 정확한 역변환을 유지했다.

CODE003-001은74계약 통과 뒤 CPU80.84% 최종 경고로 거부됐으며 기록을 보존했다. CODE003-002는74계약·fresh96/final96·14.019초로 통과했다. 전체 preflight003-001은 입력2,909개·Rust787·fresh400/final400·105.596초, entry003-001은6계약·실제helper64·fresh402/final402·110.195초로 통과했다. 현재 qualification source402개 해시가 모두 일치한다.

Native003은578.76초, 제품 GO부터 완전 출력 수집3.193초로 통과했다. 물리 입력2,912개·233,019,142바이트에 대해 실제 전후 경계2회를 완료했고 Frame COMMITTED·cleanup 및 빈 소유 트리를 확인했다. 시스템CPU 최고65.07%·가용RAM 최저30.602%·parent private 최고56.961MiB다. 제품 구간은 전체의 약0.552%이며, 여전히 입력 고정과 증거 확인이 대부분의 시간을 차지한다. 전체 속도가 크게 개선됐다는 실측 주장은 하지 않는다.

독립 리뷰001은117.629초에 통과했다. 승인 조립용 Sources의 checkpoint 누락은 승인 시작 전에 발견됐고 canonical과 진단이 없음을 확인한 뒤 실패를 별도 보존했다. 이미 봉인된 Native 소스를 바꾸지 않고 post-Native adapter에서 정확한 준비 객체만 연결했다. 실제 guard callback이 있는 reader는 그대로 유지한다. 어댑터2계약과 새 리뷰002가 통과했다. 리뷰002는 fresh406/final406·113.476초·CPU62.43%·가용RAM32.542%·cleanup=True다.

승인001은 시스템CPU96.38%의75% metadata 경고로 중단됐다. 당시 parentCPU0.135%·private56.863MiB·가용RAM32.662%였고 cleanup=True·delta0·canonical 없음이다. guard는0.5초 원 표본을 재사용하며 각 callback이 추가 OS sampler를 실행하지 않는다. CPU 상승 주체는 확정되지 않았다. 짧은 후속 표본26.37%·17.58%에서 부담이 내려간 것을 확인한 뒤 제품 및 독립 리뷰를 재실행하지 않고 승인002만 실행했다.

승인002는234.209초에 canonical을 한 번 발행했다. before155·delta1·after156·잔여93·next163·generation51, fresh1,212/final1,212·2,441읽기·206,537,101바이트·cleanup=True다. 승인CPU최고53.55%·가용RAM최저33.614%이며 제품 및 Native 재실행은0이다. P09/A12/A13은 OPEN이고 full249·signed16·전체 runtime reconciliation은 미완료다. 목표는 ACTIVE이며 다음은 사례163이다. 프리즈 근본 해결과 전체 검증 시간 감소는 아직 입증되지 않았다.

근거: case162 current-runtime-run003, successor-whole-review-run003-attempt001/002, successor-acceptance-facade-setup001, optimized-acceptance-attempt001/002 및 current-epoch-accept001. canonical은437,552바이트·SHA256 dc5b07a24c330e7f72c4f9e1def6ac8017015ca0f72cd1b01f0b93cba7f23718이다. 운영 출력은 개수·요약 값만 남기고 pin 및 전체 로그 배열을 반복 출력하지 않는다.

## 사례163 준비와 최종 읽기 비용

사례163은 actual_import::source_review_delete::cached_delete_callback_rechecks_actual_aead_acl_regrant_and_advanced_head다. 사례162 canonical에서 STEP을 준비했고 fresh9/final9·cleanup=True다. 새 원본4개는11,209,169바이트에서3,904,408바이트 무손실 표현으로 변환했으며7,304,761바이트가 절감됐다. 원본은 보존했고 fresh31/final31·CPU52.06%·cleanup=True다.

전체Binding001은 기존48개와 새4개를 합친52pair, fresh131/final131, 물리 입력2,921개·230,766,078바이트로 통과했다. 총183.949초 중 admission1.001초, predecessor와 dependency 읽기9.577초, 원본 및 envelope 읽기82.773초, manifest와 scope projection0.173초, 최종 전체 재해시90.426초다. 실제 소요의 약94.2%가 원본·envelope와 최종 읽기 두 구간이다.

graph002 v2는52pair를 모두 복원했으며 wire7,535바이트·fresh37/final37·10.191초로 통과했다. factory001은GO 없는 원11계약·fresh23/final23·11.709초로 통과했다. CODE002-001은74계약·fresh96/final96·14.329초·CPU57.39%·cleanup=True다. 전체 preflight001은71.421초·CPU95.55% 보호중단이고 parentCPU0%·private47.625MiB였다. 읽기 경로의64KiB 블록·원속도·no-burst·0.5초 표본 재사용을 점검했으며 직접 계산 폭주를 확인하지 못했다. CODE는 재실행하지 않고 preflight002만 진행했다. preflight002는118.694초·scope2,924·Rust787·fresh412/final412·CPU63.42%·가용RAM31.770%·cleanup=True로 통과했다.

진입 qualification001은54.881초에CPU76.39% 경고로 중단됐다. fresh413·414읽기·69,017,258바이트, parentCPU0.691%·private47.113MiB다. 중단 위치는 이미 읽은 pin의 checkpoint이며 pin은 같은 reader의 snapshots에 있으면 추가 파일 읽기를 하지 않는다. 원반복 fresh 검사는 유지한다. 현재 자원 표본43.20%·37.81% 후 qualification002만 진행했지만 최종 해시 단계67.595초에CPU99.35% 경고로 중단됐다. 6계약은통과했으나 final 미완료이므로 qualification PASS가 아니다. fresh413·452읽기·79,118,885바이트·parentCPU0%·private49.855MiB·가용RAM33.637%·commit44.134%·cleanup=True다.

같은 검증의 세 번째 재시도와 제품 실행은 시작하지 않았다. 최종 읽기는 모든 입력을 다시 읽는 원신선성 경계이며 이전 pin으로 대체하지 않는다. allocation 개선용 기존 reusable_audit_chunk_v1과 원 reader의 완전재해시를 검토했으나56MiB 미만의 부모 메모리와 중단순간0% CPU 자료만으로 이를 포화 해결책으로 주장하지 않는다. 다음 개선은 실제 입력 고정·동일 reader 재사용 및 최종 읽기의 비용을 줄이되 source·현재성·CPU/RAM·최종검사 범위를 보존해야 한다. 공식156/249·잔여93·next163·generation51, P09/A12/A13 OPEN 및 목표ACTIVE다. 사례163 제품·Native·독립검사·승인은 NOT_RUN이다.

근거: case163 successor-selection001, lossless-receipts001, successor-binding001, successor-connections002.v2, successor-factory001, successor-code-run002-attempt001, successor-preflight-run002-attempt001/002, successor-dispatch-qualification-run002-attempt001/002. 소스 변경이나 OS 설정 변경 없이 준비 및 실패 증거를 보존했다.
