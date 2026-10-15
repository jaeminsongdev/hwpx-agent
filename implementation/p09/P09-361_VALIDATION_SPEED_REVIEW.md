# P09 검증 속도 분석과 재시도 개선

## 현재 재개 위치와 작업 방식 개선

2026-10-16 목표는 현재 채팅에서 ACTIVE다. 공식 수용은158/249·잔여91·next165이며 P09·A12·A13 OPEN, P10 미시작이다. case165/run007의 본문1 PASS는 최종 입력 재확인 실패 때문에 제품 수용으로 재사용하지 않는다. Native008은 실제 진입 후 엄격한 제품 캡처 시간 제한으로 실패했으며, 실제 제품 자식의 실행 여부는 미확인이다.

### 부모 연결 검증과 남은 전체 비용

`worker_readiness_connection_v1.py`는 기존10초 component가 만든 실제 Input 바깥에 준비 Gate를 연결하며, 원 Capture와 같은 프로세스를 사용한다. 생성 전 실패는 이벤트를 정리하고, 생성 후 설정 오류는 기존 실행기가 프로세스를 받아 Job에 배정한 뒤 GO 경계에서 드러내도록 유예한다. 이로써 설정 예외 때문에 Job 배정 전 자식을 잃는 경로를 막았다. 원 stream 정리 경로는 부모 이벤트도 닫는다. 이 연결·설정 실패·자원 중단·기존10초 만료와 보수적 비용 덧셈의12계약이2.002초·CPU최고27.73%·가용RAM최저22.18%·cleanupTrue로 통과했다.

`worker_readiness_bootstrap_v1.py`는 상속된 이벤트만 받아 protocol을 정확한 source pin의 private namespace로 읽고, 변경하지 않은 공개 worker의 원 main을 실행한다. 실제 부모 연결 진단에서 준비 대기는7.653406초, 실제 GO부터 원 캡처 완료까지는0.191429초로 분리됐다. 원10초·GO1회·Capture1회가 유지됐으며 원15초 default component는 변경하지 않았다. 제품 생성 audit hook이 첫 Popen을 생성 직전에 거부해 자식 exit1로 끝났으므로 캡처 완료를 제품 성공으로 판정하지 않는다. 전체9.408초·CPU최고41.60%·가용RAM최저22.42%·Job CPU3.312초·최종프로세스0/cleanupTrue였다. protocol의 default module import와 과거 runtime JSON 읽기도 없었다.

실제 Native008의 비용 모델은579.196405초다. 당시 source 목록3,109개에 없는 현재 알려진12개 입력4,046,681bytes와 별도 준비15초만 보수적으로 더하면598.912764/600초이며 명목 잔여는1.087236초다. 여기에는 새 Native 구성·추가 자격 증거·새 최종 목록 확인 비용이 아직 포함되지 않았으므로 완전한 Native009 비용 검증이 아니다. 기존3초 배정 비용·여유60초에서 준비 시간을 빼거나 IO/잠금 제한을 높이지 않았다. 다음은 Native008 원본을 보존하는 검증된 무손실 별도 저장 표현으로 실제 읽기량을 줄이고, 완전한 successor scope와 비용을 다시 산출하는 작업이다.

Native008 재실행·Native009 시작·제품 생성·수용 증가는0이다. 실제 Native 구성의 helper 상한과 전체 source/IO/부모·worker 연결 자격은 아직 닫히지 않았다. 상세 source pin과 실제 결과는 `worker-readiness-connection001`에 보존했다.

### 준비 완료 신호의 비제품 연결 검증

`worker_readiness_v1.py`는 실제 worker의 원래 `stdin.readline()` 바로 앞에서 별도의 이름 없는 Windows 이벤트를 알리는 미적용 후보다. 부모는 원 Job에 배정한 동일한 살아 있는 프로세스인지 준비 확인 전후에 검사하고, 최대15초의 준비 대기 동안 기존 자원 체크포인트를 계속 실행한다. 준비 실패·프로세스 종료·자원 중단이면 GO를 쓰지 않으며 재시도하지 않는다. 부모의 Gate는 기존 strict-window Input 바깥에 두어 실제 원 GO 쓰기에서만 기존10초가 시작되도록 설계했다. 입력 바이트·원래 GO 비교·캡처 제한·Job 정리 책임은 대체하지 않는다.

17개 계약은 준비 기한·정확한 기한 경계·시계 역행·소유권·자식 종료·자원 중단·중복 및 부분 GO·EOF 보존·정리 위임과 원10초 만료를 확인했다. 2.005초, CPU최고39.38%, 가용RAM최저21.40%, guard 정리True로 통과했다.

실제 Windows 이벤트를 사용하는 별도 소유 Job의 원 worker 진단3개와 공개 통합 worker 진단2개도 마쳤다. 원 worker는 EOF를 거부했고, 준비 신호가 없는0.25초 제한 진단은 GO 없이 중단했다. 공개 통합 진입점의 준비 신호는 한 측정에서2.813418초에 도착했다. GO 진단에는 사전에 모든 `subprocess.Popen`을 OS 생성 전 거부하는 audit hook을 설치했으며 실제 제품은 생성하지 않았다. 두 공개 worker 진단의 과거 runtime JSON 읽기는0, 다섯 Job 모두 최종 잔여0이다. 공개 worker 진단 전체8.924초의 CPU최고는54.01%, 가용RAM최저21.49%였다.

이 진단은 원 Native를 재실행하거나 통합 Native 연결을 자격 검증한 것이 아니다. 인라인 진단 harness는 Native 증거 생산자로 등록하지 않았다.15초 준비 비용을 전체600초 모델에 반영하고 현재 전체 source/IO/Job 및 부모·worker 연결을 검증해야 하며, AST 복사 후보도 아직 미적용이다. 원 Native008 실패·정리 순서 미확인·공식158/249는 그대로 보존한다. 근거는 `worker-readiness-diagnostic001`이다.

### Native008 실제 실패와 worker 준비 최적화

Native008은 실제 진입했지만 `STOP_STRICT_PRODUCT_WINDOW`로 미수용 종료했다. 제품 캡처10초 제한은 유지했으며 약10.015282초의 마지막 확인에서 중단됐다. stdout/stderr 수신은 모두0, 제품 본문 관측False·실제 제품 자식 실행 여부null·통과한 시험 목록은 비어 있어 제품이 실행되지 않았다고 단정할 수도 없다. Native007·008의 원본과 Native008 실행 의도를 보존하고 같은 Native008을 재실행하지 않는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작은 그대로다.

| Native008 실제 결과 | 값 |
| --- | --- |
| 전체 소요 | 451.85초 |
| 시스템/검증기 CPU 최고 | 73.63% / 2.841417% |
| 가용RAM 최저 | 24.18079% |
| Job CPU 누적/전용 메모리 최고 | 1.141 CPU초 / 47.23MiB |
| Native 입력 | 3,109개·208181487bytes |
| 잠금 핸들 | 3,481개 열기·닫기, 잔여0 |
| Frame과 Job | CLOSED·등록False, 최종 owned tree empty/cleanup True |
| 실제 바이트 경계 | 첫 경계1개만 완료, 마지막 재확인 미완료 |
| 디코더 | 68회·1.357740초/원합산5초 |

`original_owned_cleanup_confirmed_before_release=False`도 실패 원본 그대로 유지한다. 최종 Job과 핸들이 정리됐다는 사실을 이 정리 순서의 자격으로 대체하지 않는다. Native source frame·현재 제품 후보·Gate PASS는 모두 미성립이다. 현재 실패는 CPU 보호 중단이나 전체600초 초과가 아니라 GO 이후의 엄격한10초 제품 캡처 종료다.

실제 진입 전의 최종 Native 연결은12계약/fresh208-final208로 닫았고, 참조·완결성·helper64·유한 비용에 대한 별도 합성6계약도 통과했다. 새 실행 소스가 포함된 사전검사015는 입력계획3,097개/Rust787·fresh598-final598·112.548093초·CPU최고56.45%·cleanupTrue로 통과했다. dispatch008은 원6계약·scope3,121개·실제 Native helper64·fresh609-final609·118.084751초·CPU최고61.55%·cleanupTrue이며 모델은579.003741/600초였다. 이 준비 PASS를 실제 Native 성공으로 승격하지 않는다. 원본 코드는 `bc82297`에 먼저 커밋한 뒤 Native를 호출했다.

사전검사015의 별도 관측기는27표본 뒤250ms 프로세스 조회 비용 제한에 도달해 자기만 종료했고 검증기는 재시작하지 않았다. dispatch008의 관측기는147표본을 보존하고 대상 종료·자체 정리를 확인했다. 관측기를 이유로 원 CPU/RAM 보호나 입출력 검사를 바꾸지 않았다.

#### 제품 생성 없는 실패 분석

EOF/GO 진단은 실제 Native008이나 제품 시험을 반복하지 않았다. GO 경로 진단에는 Python audit hook을 시작 전에 설치해 모든 `subprocess.Popen`을 실제 생성 전에 거부했고, 별도 소유 Job의 종료와 잔여0을 확인했다. 진단의 첫 생성 요청 시간은13.224253초, 후속 측정은2.749779초와2.589974초로 달랐다. 이 편차는 준비·스케줄링 구간이10초 예산을 잠식할 수 있음을 보여주지만 Native008의 특정 단일 원인을 확정하지 않는다. 현재 cargo 경로 조회는 한 측정에서5.46ms였으므로 이 값으로 과거 지연을 단정하지 않는다.

한 진단 logger는 Windows Popen의 executable=None/문자열 commandline을 제대로 처리하지 못해 TypeError로 끝났다. 그 실행도 실제 자식 생성 전 거부됐지만 유효한 생성 지연 표본으로 쓰지 않는다. 다른 logger의 단일 문자 basename 역시 실행 파일 식별 근거로 사용하지 않는다. 원시 명령줄·로그·비밀정보는 보고하지 않았다.

프로파일을 켠 EOF 진단은8.290823초·범용 deepcopy 약353만 호출을 관측했고, 실제 원 GO 거부와 과거 제품/수용 파일 열기0을 확인했다. 프로파일 자체의 비용이 있어 이를 평상시 시작 시간으로 보지 않는다. 프로파일 없는 원 소유 Job의 EOF 실행은2.470204초였으며 GO를 보내지 않았다. 독립된0.15 CPU초 한도 진단도 원1코어·Job CPU cap·메모리·정리 제한 아래에서만 실행했다. 중첩 Job quota의 이론은 [Microsoft CPU rate 문서](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information)로 확인했지만 실제 원인으로 증명하지 않았으며 CPU 상한을 변경하지 않았다.

#### 미적용 AST 복사 후보

`ast_clone_namespace_v1.py`는 원 namespace loader의 전체 code object를 유지하고 copy 의존성만 전용 독립 AST 복사기로 연결한다. 새 source 읽기·bytes/hash·import·전체 non-import AST 검사를 그대로 실행하며 byte/hash/JSON/AST cache를 만들지 않는다. 원본·복사본의 코드 동일성, 위치/추가 속성·공유 그래프·순환 구조·fallback·변조 pin 거부·default module 불변을8계약으로 확인했다.

복사만10회 비교한 값은 범용0.129533초, 후보0.047190초로 약2.7449배였다. 실제 EOF worker 연결의 한 번 비교는 전체2.312491→2.012385초, 연결 본문1.411115→1.265564초였으며 양쪽 모두 원 GO 거부·제품 미실행·Job 잔여0이었다. 이는 작은 비제품 측정이며 현재 Native worker에 적용하거나 제품10초 문제를 해결한 결과가 아니다.

다음은 실제 GO 이전의 명시적 worker 준비 완료 신호와 시작 비용을 제한적으로 분리하고, 실제 GO→완전 캡처10초·Native 잠금600초·원IO1/2MiB·acquisition14·decoder5·1코어·RAM/commit95%를 유지하는 연결 검증이다. Native009에서 동일 시험을1회 추가 실행하는 승인은 별도로 요청했다. 승인 전에는 원본과 재실행 금지를 유지하며 비제품 코드·진단만 진행한다. 근거는 `native008-window-analysis001`에 모았다.

### 이전 사전검사와 dispatch 자격

v18의 실제 전체 사전검사014와 dispatch007이 모두 통과했다. 이전의 실제 Native helper66개 초과 문제는 공개 준비·worker 진입점 통합으로64개가 되어 기존 상한 안에서 닫혔다. 현재 CODE006·통합 진입점 CODE002·실제 EOF003은 다시 실행하지 않았다.

| 현재 원 본문 실행 | 결과 |
| --- | --- |
| 사전검사014 | 입력계획3,094개·Rust 목록787개·기본 import60개, fresh595/final595, 109.235256초, CPU 최고77.61%, 가용RAM 최저25.55772%, cleanup=True |
| dispatch007 | 원6계약, source scope3,118개·기본 import60개·실제 Native helper64개, fresh606/final606, 119.551021초, CPU 최고70.13%, 가용RAM 최저26.08234%, cleanup=True |
| dispatch의 원 비용 모델 | 실제 모델 입력3,105개·디렉터리372개, 578.724361초/600초. 여유60초·합산 decoder5초·원1/2MiB와 acquisition14 유지. 실제 완료 보장은 아님 |

dispatch007은 실제 CODE006과 사전검사014의 원 pin을 직접 읽었다. 원 controller 전체 소스 역변환 증명과 private namespace 소스 증명을 유지했다. 이것은 제품을 실행하지 않는 dispatch 구성 자격이며 실제 Native source frame·GO·제품 본문·제품 수용의 PASS가 아니다. Native metadata callback의 전체 admission도 그대로 남는다.

`preparation_live_cpu_observer_v1.py`는 별도 한 CPU·BelowNormal 프로세스에서 조회만 한다. 명시적 PID와64비트 생성 시각을 함께 확인하고 QUERY_LIMITED·SYNCHRONIZE 권한만 열며, 대상 프로세스를 시작하거나 종료하지 않는다. 프로세스 명령줄·경로는 읽지 않고 기존 닫힌 이름 그룹과 고정 PDH7개만 사용한다. 조회는1초 간격·최대240표본/240초·총 관측 작업5초이며 기존 PDH의1회50ms/합산2초 제한도 유지한다. 관측 실패나 비용 초과는 유효값0으로 바꾸지 않는다. 새11개 및 기존19개 계약이30/30으로 통과했다.

| 같은 실행의 관측 | 사전검사014 | dispatch007 |
| --- | --- | --- |
| 보존 표본과 종료 확인 | 106개·대상 종료 확인·정리 완료 | 151개·대상 종료 확인·정리 완료 |
| 별도 관측 작업 시간 | 1.876688초 | 4.107165초 |
| 검증기 CPU 최고 | 4.64684% | 6.318681% |
| 관측기 CPU 최고 | 0.193424% | 0.192678% |
| Defender 유효 표본 | 106개·최고3.907438% | 13개·최고2.208634% |

dispatch의 PDH는14번째 수집에서68.44ms로50ms 비용 제한을 넘어 비활성화됐다. 이후 Defender·System·DPC 값은 미확인으로 남기고 프로세스 그룹 관측만 계속했다. 따라서13개 값으로 dispatch 전체의 Defender 부하를 단정하지 않는다. Probe 내부 요약의 추가 thread/process 없음은 Probe 자체가 자식을 만들지 않는다는 뜻이며, 이번 관측기 전체는 별도 프로세스다. 프로세스 시간 차이·PDH·원 Guard의 측정 창도 서로 같거나 원자적이지 않다.

사전검사014의 첫 관측 연결은 도구 간 JSON 전달에서64비트 생성 시각이 반올림돼 identity mismatch로 거부됐다. 핸들은 정리됐고 검증기는 다시 시작하지 않았다. 원문 JSON 문자열을 숫자로 재해석하지 않고 전달해 두 번째 관측기에서 정확한 대상에 연결했다. 첫 실패 기록도 보존한다.

두 실행에서 이전 시스템97% 급등은 재현되지 않았다. 현재 계측은 이전 프리즈의 원인을 확정하거나 Defender를 배제하는 근거가 아니다. 검증기·관측기의 같은 실행 부하와 확인 불가 범위를 분리했으며, OS·Defender·외부 작업 설정은 변경하지 않았다. 원본 근거와 pin은 `preparation-readiness-review001`에 모았다.

남은 Native 진입 래퍼는 아직 과거 CODE001 참조를 고정하고 있다. 현재 CODE006·사전검사014·dispatch007을 원 Native 보호기와 연결하는 자격을 먼저 닫아야 한다. 준비용 CPU 정책을 Native에 적용하거나 기존 과거 참조로 실행하지 않는다. 새 실행 helper를 추가하면 그 소스·시험·자격 기록을 실제 준비 scope에 넣고 새 epoch를 확인한 뒤에만 Native008을 시작한다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작은 유지한다.

### 통합 진입점 자격과 이전 사전검사 중단

`xz_unified_runtime_v1.py`가 준비 연결과 실제 worker의 공개 진입점을 하나로 묶는다. 게시용 `xz_corpus_delivery_v1.py`를 로드하지 않고 필요한 codec pin과 기존 자원 관측 함수만 포함한다. 복구 함수6개와 관측 함수2개의 AST는 원본과 같고, 기존 v17 함수군은 전체 code object를 유지한 별도 명시적 namespace에서 연결한다. worker 경로와 v18 packet 정규식만 metadata로 변환하며 역변환을 확인한다. `sys.modules` 삭제·helper 상한 확대·실제 witness 누락은 없다.

| v18 실제 완료 항목 | 결과 |
| --- | --- |
| 통합 진입점 CODE002 | 18계약, fresh199/final199, 24.983042초, CPU 최고60.23%, cleanup=True |
| `successor-connections008.v18` | 물리68개 재구성, fresh256/final256, 50.628714초, CPU 최고70.31%, cleanup=True |
| `successor-code-run008-attempt006` 원 CODE | 전체74계약, 기본 import60개, 테스트 포함93개(분리), fresh221/final221, 37.268942초, CPU 최고71.68%, cleanup=True |
| `successor-xz-factory003` 원 EOF 검사 | 11계약, fresh228/final228, 48.193381초, CPU 최고55.46%, cleanup=True. GO 없이 실제 worker 권한 거부, 과거 제품·수용 파일 열기0, parent/worker dispatch0 |
| 현재 CODE006 metadata 바인더 CODE001 | 8계약, fresh205/final205, 27.407354초, CPU 최고46.78%, cleanup=True |

통합 진입점의 첫 CODE001은 자기 자격 기록을 생성하기 전에 읽는 순환 참조로 실패했다. v17 기반 증명과 새 후보 증명을 구분한 뒤 CODE002에서 닫았다. EOF002는 기존75% 단일 표본 보호기에서 시스템85.23%로 중단됐고 원본을 보존했다. 보호기를 바꾸지 않고 코드 검토 후 새 독립 실행003에서 통과했다. 이 시간 차이를 통제된 성능 개선율이나 프리즈 해결로 해석하지 않는다.

`xz_unified_preparation_binding_v1.py`는 고정된 통합 진입점 소스를 바꾸지 않고 실제 CODE006·v18 graph·EOF003의 pin과 모든 현재 프로그램 소스를 확인한다. 원 함수군을 그대로 유지하고 현재 CODE 식별자5→6 및 참조 metadata만 결속한다. 바인더 소스·테스트·8개 계약의 자격도 실제 stage reader에 추가한다. 과거 CODE005와 v17 사전검사012는 과거 profile의 근거로 남으며 현재 v18 준비의 PASS로 대체하지 않는다.

현재 전체 사전검사013은 실제 본문67.646610초에 시스템 CPU97.39%로 `STOP_PREPARATION_SYSTEM_PRESSURE90` 중단됐다. 마지막 표본의 자기 CPU는0%, 전용 메모리67.949MiB, 가용RAM17.63057%, commit51.94413%였다. 실제583읽기·43962835bytes, fresh547/final0이며 64KiB 작업 공간의583 lease가 모두 반환됐고 cleanup=True다. 원 CPU90 중단과 RAM/commit95%는 유지한다. 이를 입력 검증 PASS나 새 dispatch 자격으로 처리하지 않는다.

중단 뒤 코드 검토에서 새 통합 진입점의 while loop0개, 원 관측 AST 동일, 추가 sampler·스레드 없음과 작업 공간 반환을 확인했다. 같은 시점의 자기 CPU/RAM 폭주는 이 표본으로 지지되지 않지만, 검증 I/O와 외부 도구의 상호작용은 배제되지 않는다. Defender 읽기 전용 조회는 평균 검사 목표10%, 낮은 우선순위True, idle CPU throttle 해제False, 실시간 보호True였다. 구성 경로의 literal·상위 경로·wildcard 비교에서는 `D:\개발`, `D:\dev`, `D:\devdata`에 대한 일치를 찾지 못했지만 실제 파일별 제외 여부를 증명한 것은 아니다. 중단 당시 Defender CPU를 측정하지 않았고, 중단 후 표본에도 유효한 Defender CPU 값이 없어 원인으로 확정하지 않는다. 설정 변경은0이다.

이후 같은 실행의 CPU 관측과 현재 전체 사전검사014·실제 dispatch007의 helper64·600초 비용 검증은 앞 절에서 완료했다. 이 절의013 중단은 실패 원본으로 보존하며 새 PASS로 덮어쓰지 않는다. Native008·제품 실행·GO·수용 증가는0이다. 당시 진단 근거는 `xz-unified-resource-review001`이다.

### 이전 v17 사전검사와 dispatch 구성 실패

현재 XZ v17과 실제 CODE005를 승인된 run007 사후 복구 경로에 연결했다. `xz_recovery_preparation_v1.py`는 이전 CODE를 복사하거나 재명명하지 않고 실제 `successor-code-run008-attempt005`의 pin을 직접 읽는다. 기존 준비 closure4..6과 실패한 Native007 원본, 10초 제품 window는 보존한다. setup 경로를 바꾸는 래퍼가 원 main의 실제 globals에도 게시되도록 수정했고, 원 closure의 전체 AST 및 code 역변환과 함께 12개 계약으로 검증했다.

| 현재 실행 | 결과 |
| --- | --- |
| recovery adapter CODE004 | 12계약, fresh199/final199, 27.180366초, CPU 최고73.15%, 가용RAM 최저16.62572%, cleanup=True |
| `successor-recovery-preflight-run008-attempt012` | PASS, 전체 입력3,085개와 Rust787개, 기본 import61개, fresh586/final586, 115.896960초, CPU 최고71.97%, 가용RAM 최저16.34190%, cleanup=True |
| 같은 사전검사의 원 비용 모델 | 575.697909초/600초. 원 acquisition14·1/2MiB·여유60초·decoder5 및 제품10초 포함. 실제 완료 보장은 아님 |
| dispatch qualification005 | `DISPATCH_ACTUAL_NATIVE_IMPORTED_HELPER_BOUND` 거부. 기본61개와 추가 실제 Native witness5개의 합집합66개가 기존 상한64개를 초과. 50.646517초, CPU 최고60.61%, cleanup=True |

사전검사011은 CODE 경로 결속 오류로 실패했고 원본을 보존했다. dispatch004와 진단006은 각각 시스템 CPU92.43%와100%에서 준비 보호기로 중단됐으며 setup 이후 자격 본문에는 들어가지 않았다. 004의 마지막 세 표본에서 자기 CPU는 모두0%였지만, 이것만으로 검증 I/O가 다른 프로세스 부하를 유발했을 가능성을 배제하지 않는다. 중단 후 별도 시점의 Python/Git CPU 관측으로 같은 실행의 원인을 확정하지 않는다. 관리자 작업이나 Defender·OS 설정 변경은 하지 않았다.

같은 검증을 다시 실행하지 않고 사전검사012의 저장된 전체 import 목록을 읽었다. 별도 시작 및 adapter build만 수행한 제한된 진단은 기본60개를 그대로 유지했고, 실제 준비 단계에는 `bounded_successor_capsule_wire_v2.py`가 더해져61개였다. 준비 어댑터는 게시용 `xz_corpus_delivery_v1.py`를 상수와 자원 관측에 사용한다. 이 의존성을 실제로 제거해도 한 개만 줄어들므로, 둘 이상이 필요한 현재 제한 문제를 해결했다고 볼 수 없다. 진단은 `xz-helper-import-review001`에 기록했다.

다음 작업은 게시·테스트 준비와 제품 실행 프로필의 의존성을 분리하는 설계다. helper64를 늘리거나 `sys.modules`에서 지우거나 실제 Native witness를 누락하지 않는다. 소스를 바꾸면 현재 CODE004·사전검사012는 그 이전 source epoch의 PASS로 남고, 새 소스의 전체 scope와 dispatch 비용을 다시 확인해야 한다. 현재 dispatch는 미자격이며 Native008·GO·제품 실행·수용 증가는 모두0이다. RAM95%/commit95%·Native CPU·1코어/BelowNormal과 기존 입력 검증도 변경하지 않았다.

### 실제 EOF 시작 검사와 현재 전체 CODE

현재 v17 worker source와 세 packet을 유지한 채 `xz_startup_adapter_v1.py`가 동결된 원 factory 시작 검사 본문을 호출했다. 인자는 case165/run008의 `--bootstrap`으로 고정하며, 새 Native/GO 인터페이스는 없다. 원 engine 구성·11개 계약·원 wire/bootstrap 바이트 비교·15초 자식 timeout·출력4096/16384bytes 상한·EOF·과거 파일 열기 audit·마지막 hash·정리를 모두 원 본문에서 실행했다.

| 실제 완료한 검사 | 결과 |
| --- | --- |
| startup adapter CODE001 | 8계약, fresh172/final172, 22.883095초, CPU 최고49.14%, cleanup=True |
| `successor-xz-factory001` 원 본문 | 11계약, fresh182/final182, 38.337971초, CPU 최고59.7%, 가용RAM 최저18.63110%, cleanup=True |
| `xz-startup-probe001` 추가 확인 | fresh205/final205, 94.860690초, CPU 최고53.49%, 가용RAM 최저18.49980%, cleanup=True |
| whole CODE adapter CODE001 | 6계약, fresh184/final184, 24.071826초, CPU 최고57.81%, cleanup=True |
| `successor-code-run008-attempt005` 원 본문 | 74계약, 기본helper62, 테스트 포함95, fresh187/final187, 43.254297초, CPU 최고86.79%, 가용RAM 최저16.62925%, cleanup=True |
| `xz-whole-code-qualification005` 추가 확인 | fresh217/final217, 107.858459초, CPU 최고75.86%, 가용RAM 최저17.78432%, cleanup=True |

자식은 실제 exit1과 원 `WORKER_NOT_AUTHORIZED` 거부를 보였고 과거 제품/수용 기록 열기는0회였다. GO를 보내지 않았고 parent/worker dispatch도 각각0이다. 원 factory state는 `PASS_WORKER_CLI_NO_GO_STARTUP_NOT_PARENT_ADMISSION_NATIVE_OR_PRODUCT`다. 바깥 어댑터의 추가 확인은 별도 Guard에서 수행하며 원 Guard·뮤텍스가 정리된 후에만 새 소유자를 만든다. 표의 원 실행과 추가 확인 CPU/RAM은 서로 다른 측정 창이며, 낮은 바깥 수치로 원 실행의86.79%를 대체하지 않는다.

`xz_whole_code_adapter_v1.py`는 기존 controller의 `run_code`와 전체74계약을 재사용했다. XZ 연결 CODE21·실제 EOF 증거·현재 source/packet을 별도로 확인하며, 과거 fixture PASS만으로 새 CODE를 만들지 않았다. 원 helper 상한64를 유지해 기본 import62개를 검사했고, 계약 실행 뒤 테스트 전용 import까지95개가 되는 것은 별도로 기록했다. 테스트가 로드된 process를 Native/preflight로 재사용하지 않는다. XZ61 및 특수7개의 앞선 물리 검증은 다시 실행하지 않았다.

현재 실제 CODE는 `implementation/p09/evidence/p09-361-case165-successor-code-run008-attempt005.v1.json`이다. 기존 `successor-recovery-code-run008-attempt001`은 과거 profile 증거이며 현재 CODE005로 승격할 수 없다. 현재 사전검사012는 CODE005의 실제 pin을 직접 참조한다. 이 차이를 숨기려고 이전 PASS를 새 경로의 실행 결과처럼 복사하거나 이름만 바꾸지 않는다.

남은 준비는 현재 v17 graph·CODE005·EOF 증거를 승인된 case165/run007 post-body 실패 복구, 기존 준비 closure4..6, 새10초 window와 연결하는 것이다. 그 위에서 현행 전체입력·Rust787·독립 판정기·미래 dispatch 필수 metadata를 포함한600초 비용 및 preflight/dispatch를 검증해야 한다. 원 사전검사010의 PASS와600.530초 하한은 여전히 v10의 증거다. 현재 단계는 CODE/시작 검사이며 Native008·제품·GO·P09 Gate는 미완료다.

### 현재 XZ 부모와 worker 재구성 연결

현재 재개 지점은 `successor-connections008.v17.json`이다. `xz_closed_preparation_v1.py`는 동결된 `level6_closed_preparation_v1.py`의 전체 본문을 재사용한다. 새 파일명·버전·고정 XZ Binding CODE 참조 등 명시한 metadata만 바꾸며, 바꾸기 전 함수 code와 되돌린 AST/code가 원본 전체와 같은지 확인한다. 같은 소스의 AST는 한 번 파싱해 두 함수에 재사용하지만 검사 대상·원본 hash·전체 code inverse는 줄이지 않는다.

실제 준비 경로에서 발견한 문제는 두 가지다. 먼저 원 graph main이 안쪽 profile이 아니라 최상위 loader에서 Guard를 만들고 있었다. graph root와 metadata 준비에만 선행 자격을 갖춘 준비 정책을 연결하고, worker root의 원 보호기는 그대로 두었다. 전체 profile의 안쪽에 둔 준비 라우터는 늦은 import가 profile 바깥을 거치지 못하게 했으므로 라우터를 전체 profile·현재 CODE 검증의 바깥으로 옮겼다. 원75% 한 표본 즉시중단을 준비 정책으로 바꾼 것이지90% 도달이나75% 지속 포화를 허용한 것은 아니다.

두 번째는 private namespace 설치 순서다. 제한된 함수 계측에서 최초 설치 직후에는 부모 공개 함수와 actual worker가 같은 재구성 함수를 봤지만, Binding API 구성 후 같은 runtime의 함수들이 다시 바뀌는 것을 확인했다. worker metadata 변환은 원 코드·기본값·클로저를 유지하면서 원 private 의존성 family를 공유하도록 했다. 원 namespace install/retarget을 끝까지 실행한 뒤 연결을 확인하고, 원 Binding API connect의 반환 직후 최종 공개 재구성·입력 scope 함수를 actual worker 환경에 연결한다. 원 Binding API 반환값과 증명은 그대로 반환하며, 원 graph의 `SAME_PUBLIC_AND_ACTUAL_WORKER_RECONSTRUCTION` 검사는 삭제하거나 약화하지 않았다.

| 현재 자격 | 실행 결과 |
| --- | --- |
| `xz-profile-connection-code009` | 21계약 PASS, fresh99/final99, 16.781097초, CPU 최고35.35%, 가용RAM 최저20.80315%, cleanup=True |
| `xz-entry-v17-graph-run008-attempt001` | 부모/actual worker 함수 동일성 및 전체68행 복원, fresh222/final222, 44.324748초, CPU 최고61.72%, 가용RAM 최저19.52410%, cleanup=True |
| 실제 v17 packet | manifest47454bytes, capsule9647bytes, bootstrap7076bytes, 원 wire/bootstrap16KiB 한도 이내 |

현재 graph와 세 packet은 새 배타적 경로에 게시됐다. graph state는 `PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO`이며, `all_worker_rows_restored=True`다. 이것은 실제 부모/worker metadata 재구성의 자격이지 실행된 worker의 EOF/NO-GO·전체 Native 입력 lock·제품 본문·독립 제품 판정 또는 Gate PASS가 아니다.

v11~v16의 graph 실패8개, CODE001~008, `xz-actual-worker-linkage-diagnostic001/002`는 보존한다. 과거 CODE의 PASS는 그 당시 소스에만 해당하며 현재 소스로 재사용하지 않는다. CODE004의 한 실패는 원 pressure module에도 `summary`가 있는데 없다고 가정한 테스트 오류였고, 현재는 worker 원 함수 code가 동일한지 비교한다. CODE006은 계약 실행 전 CPU95.17%에서 `STOP_PREPARATION_SYSTEM_PRESSURE90`으로 정리됐으며 원인은 미귀속이다. 후속 CODE는 기존 Guard의 새 표본에서 자기 CPU와 RAM을 집계하고, 별도 sampler·스레드·Windows 호출은 추가하지 않는다. 현재 CODE009의 자기 CPU 최고는 기계 전체 기준4.875971%로 기록됐지만 다른 실행의95.17% 원인으로 소급하지 않는다.

준비 CODE 기록의 유한 범위만1..16으로 명시했다. graph attempt와 Native physical run 상한은8, 현재 Native run은8이며 자동 재시도와 기존 기록 덮어쓰기는 없다. 이 구분을 현재 CODE 증거와 admission에 결속하고, CODE9/16 허용·17/boolean 거부·graph attempt9 거부를 테스트했다. 실제 제품·GO·queue advance는0이다.

실제 EOF/NO-GO와 원74계약은 앞 절에서 완료했다. 남은 준비는 기존 helper64와 새 연결 전체를 포함한 현행 scope·독립 판정기·미래 dispatch 필수 입력의600초 비용·preflight/dispatch다. 선행 v10 사전검사010과600.530초 하한은 그 profile의 증거로 보존하며, 새 v17 runtime 자격으로 승격하지 않는다. Native 보호·RAM95%·commit95%·1코어·BelowNormal·1/2MiB·acquisition14·여유60초·합산 decoder5는 유지한다.

### 새 파일 게시와 전체 물리 경계 검증

일반61개 XZ 파일을 세대 번호가 있는 별도 경로 `p361-lossless-runtime-inputs/caseNNN-runtime-runNNN.xz8m-g001.envelope.v1.json`에 게시했다. 각 파일의 bytes/SHA256은 선행 전체 실측과 동일하다. 원본·기존 zlib 파일·실패 증거는 보존한다. 파일이 이미 있으면 실제 bytes/hash를 확인하고 원본 바이트로 복원한 뒤 재사용하며, 다른 내용이나 부분 파일을 덮어쓰지 않는다.

첫 `xz-corpus-publication-g001-attempt001`은8개를 생성·복원한 뒤31.540336초·시스템 CPU92.51%에서 `STOP_PREPARATION_SYSTEM_PRESSURE90`으로 종료됐다. 마지막 hash는0이며 실패 원본과 생성 파일을 보존했다. cleanup=True다. 이 실행은 동시 자기 CPU를 기록하지 않아 원인이 미귀속이다.

중단 뒤 게시 코드를 재검토해 원본145671067bytes를 다시 읽고 압축하던 중복 작업을 제거했다. 새로 만들 파일은 기존 압축본의 실제 pin/bytes를 읽고 원 decoder로 복원한 뒤, 의미 원본의 크기와 SHA256 일치를 확인해 인코딩한다. 이미 생성된 정확한 새 파일은 인코딩하지 않고 실제 bytes를 다시 읽어 복원한다. 이것은 게시 입력의 무손실 표현 재사용이며 제품 경계·의미 입력·원본 hash 검사를 생략한 것이 아니다. 기존 원 보호기의 새 표본만 단계별로 집계해 자기 CPU·RAM을 추가 기록하며 별도 sampler·스레드·Windows 측정 호출은 만들지 않았다.

`xz-corpus-publication-g001-attempt002`는53개 생성·8개 재사용으로61개를 완료했다. 실제 seed 읽기는34477145bytes였고 원본 runtime 파일 재읽기는0개다. 원 DecoderBudget5 안에서 기존 seed와 새 물리본114회 복원·2.729851초, 관련17계약 및 선행 baseline3계약, fresh204/final204, 105.756370초·시스템 CPU 최고84.19%·자기 CPU 최고4.294955%·가용RAM 최저17.60823%·cleanup=True로 통과했다. 두 CPU 최대값은 서로 다른 표본일 수 있으며 프리즈 원인이 해결됐다는 판정은 아니다. 원본과 기존 표현은 수정하지 않았다.

별도 `xz-corpus-verification-g001-attempt001`은 고정 실측과 원68개 manifest로 기대 descriptor를 독립 재구성해 게시 manifest와 대조했다. 특수7개는 기존 pin과 decoder를 유지했다. 실제 물리68개를 첫 읽기와 마지막 hash 재확인에서 각각 복원했으며, 원본 크기·SHA256 대조136/136회가 원합산5초 중2.245594초에 완료됐다. fresh159/final159·관련17계약·55.918337초·CPU 최고75.71%·가용RAM 최저17.78297%·cleanup=True다. 새61개와 특수7개를 합친 물리 크기는21611691bytes다. 이것은 전체 물리 경계 검증 PASS이며 아직 Native의 live lock·제품 본문·전체 독립 판정 PASS는 아니다.

`xz_ordinary_binding_v1.py`는 private namespace의 원 Binding constructor와 descriptor에 고정61개 표를 연결한다. 전체68개·고정61개 digest를 모두 확인하고, 완전한 Binding에서 허용된 실제 압축 bytes의 hash에만 XZ decoder를 선택한다. 미완성 표·새 포맷의 미등록 bytes·현재 제품·실패 기록 재압축·다른 세대·임의 경로를 거부한다. 특수7개와 기존 포맷은 원 decoder로 처리하며, Binding의 모든 nonconstructor와 Projection의 모든 원 메서드는 동일한 함수 객체로 유지한다. 원본 private codec도 바꾸지 않고 해당 source namespace에만 명시적 선택기를 둔다.

`xz-binding-code001`은 원 클래스에 대한 실제13계약(전체 매핑·원 메서드 유지·부분/변조 거부·private 범위·단일 seed 복구·실제 두 XZ 복원·기존 zlib·guard 전파 포함), fresh95/final95·15.660118초·CPU 최고53.98%·가용RAM 최저19.43384%·cleanup=True로 통과했다. 시간 열을 포함한 과거 진단 표 fingerprint는 사용하지 않는다. 실제 ordinary61 digest는 `38bbf083c60b66c125611e0abd136520557f2ffe952dae49c4ca356cc5ec24b5`, full68 digest는 `c858a48e5c4d615e8aac8709b5e214b09a35d5533860370a035204b63fdc8026`이다.

이 고정 표와 decoder의 부모·worker metadata 재구성 연결은 앞 절의 v17에서 완료했다. 기존 profile은 유지한다. 아직 독립 제품 판정·기존 helper64와 새 연결 전체를 포함한 현행 source scope·필수 metadata·600초 비용·CODE/preflight/dispatch는 다시 닫아야 한다. Native008·제품 실행·GO는 아직 없으며 CPU/RAM/commit·1코어·BelowNormal·1/2MiB·acquisition14·여유60·decoder5는 변경하지 않았다.

### 일반 기록 전체의 무손실 표현 비교

`receipt_xz_envelope_v1.py`는 원본을 JSON으로 정규화하지 않고 그대로 보존하는 별도 XZ 후보 포맷이다. 기존 zlib 포맷과 명시적으로 구분한다. XZ dictionary8MiB·decoder memory limit32MiB·입출력 chunk64KiB로 제한하고, 닫힌 필드 집합·선언 크기·원본 SHA256·끝난 stream을 확인한다. 중복 키, 잘린 stream, 뒤에 붙은 데이터와 연결된 stream, 선언 초과 출력, 잘못된 포맷 및 guard 중단을 거부한다. 원본·기존 압축본을 수정하거나 제품 decoder에 연결하지 않았다. 표준 API 근거는 [Python 3.13 lzma 문서](https://docs.python.org/3.13/library/lzma.html)다.

첫 `codec-candidate-sample001`은4.037612초·CPU 최고82.03%에서 `STOP_PREPARATION_CPU_ATTRIBUTION_MISSING`으로 종료했고 cleanup=True다. 첫 표본에 자기 CPU 귀속값이 없던 것이며 이를0으로 대체하지 않았다. 진단 전용 `owned_cpu_baseline_v1`은 아직 표본이 없는 Guard에 실제 monotonic/process CPU 쌍을 기록한다. clock skew50ms 초과·역행·비유한 값·이미 활성화된 owner는 거부하며 원 check/close/deadline/표본/중단 정책을 교체하지 않는다. 작은3계약을 먼저 통과한 뒤 진단 Guard에만 사용했다. 현행 준비 진입점과 Native 보호기는 그대로다.

후속 `codec-candidate-sample002`는 실제 크기 상위3개의 원본·기존 물리본을 다시 읽고 baseline/zlib9/XZ 후보 각각을 두 번 복원했다. 후보9계약 및 baseline3계약, fresh93/final93, 44.741715초·CPU 최고88.51%·가용RAM 최저13.48340%·cleanup=True다. zlib9의 절감은79808bytes, XZ는4074423bytes였다. 이3개 표본의 약83% 절감을 전체61개로 외삽하지 않았다.

`xz-corpus-diagnostic001`은 원68개 manifest와 일반61개의 고정 mapping SHA256을 확인한 뒤 일반61개 모두를 순차 비교했다. 각 원본과 기존 압축본을 실제로 읽고, 새 XZ 후보를 메모리에서 만들어 원본 바이트와 두 번 대조했다. 기존 zlib본도 원본과 대조했으며 모든 입력은 마지막에 다시 hash를 확인했다.

| 실제 일반61개 비교 | 결과 |
| --- | --- |
| 의미 원본 크기 | 145671067bytes, 원본 변경 없음 |
| 기존 물리본 합계 | 38801131bytes |
| XZ 후보 합계 | 13032050bytes |
| 절감 | 25769081bytes, 66.413221% |
| 후보 decoder | 122/122회, 원합산5초 중1.766134초 |
| 소스 경계 | fresh211/final211 |
| 계약 | baseline3 및 codec/corpus12 모두 PASS |
| 실제 진단 시간과 자원 | 227.185808초, CPU 최고77.15%, 가용RAM 최저15.11864%, cleanup=True |

그 비교 실행은 새 파일 게시 없이 후보 크기·해시만 기록한 일반61개 표현 비교 PASS다. 특수7개는 descriptor를 그대로 보존했지만 그 비교에서 두 번 복원한 대상은 아니다. `proposed_mapping_sha256`은 시간 측정 열도 포함한 진단 후보 표 전체의 fingerprint이며, worker의 고정 descriptor mapping digest로 사용할 수 없다. 후속 새 파일·특수7개 포함 실제 두 경계 및 고정 Binding CODE 자격은 앞 절에 구분했다. 두 비교 기록은 `implementation/p09/evidence/p09-361-case165-codec-candidate-sample002.v1.json`과 `implementation/p09/evidence/p09-361-case165-xz-corpus-diagnostic001.v1.json`이다.

원 비용식에서 다른 입력·항·경로 수가 같다면 비실행파일의 두 읽기 항만24.575311초 줄어든다. 새 helper·manifest·자격 산출물 비용을 아직 합치지 않았으므로 이를 새 dispatch 총시간이나600초 통과로 쓰지 않는다. 원1/2MiB 속도·acquisition14·여유60초·합산 decoder5·RAM95%·commit95%·Native CPU 보호·1코어/BelowNormal은 유지한다.

원본과 과거 표현·실패 증거를 보존한 새 파일 게시와136회 실제 복원은 후속 검증에서 완료했다. 남은 경계는 앞 절의 실제 부모/worker/독립판정 연결과 현행 전체scope·600초 비용·CODE/preflight/dispatch 재자격이다. 이 조건이 충족되기 전 Native008을 시작하지 않는다.

### Bootstrap 분리와 현재 통과한 사전검사

`preparation_attributed_entry_v1.closed_bootstrap`은 짧은 고정 정책 증명을 원75% Guard에서 먼저 닫은 뒤 그 Guard를 정리하고, 준비 Guard를 새로 만들어 전체 연결 소스를 다시 확인한다. 앞 단계의 소스 확인·마지막 hash·정리 중 하나라도 실패하면 뒤 Guard를 만들지 않는다. 두 소유 sampler/뮤텍스는 직렬이며 Native의 보호기는 바꾸지 않았다. Bootstrap 실패는 `preparation-attributed-bootstrap-{stage}-run008-attemptNNN`으로 별도 기록하고, planner는 이를 실제 사전검사 실행과 구분하며 해당 슬롯을 소비한 것으로 처리한다.

분리 후009는 원 Guard의 정책24/24와 준비 Guard의 연결78/78을 통과했지만, 실제 준비는 `EXPANDED_CLOSED_PREPARATION_EXACT_PARENT_CODE_CONTEXT`로 실패했다. 5.783864초·CPU 최고35.48%·cleanup=True였으며 원인은 번호 확장 래퍼의 globals가 기존 경로 변환과 달랐던 것이다. `closed-io2-` 접두사로 나온 setup·diagnostic과 실패 결과·audit는 보존했다. 래퍼가 동일한 원 함수 환경을 공유하도록 수정하고, 전체 동결 진입점에서 실제 setup/결과 경로가 복구 접두사를 사용하는지 Guard 생성 전에 중단하는 회귀를 추가했다. 이 경로 테스트의 출력 존재 여부는 격리 fixture이며 실제 Guard acquire와 제품/자식은 차단한다. 실제 실행의 덮어쓰기 금지는 그대로다.

현재 `preparation-attributed-connection-code010`은30계약·fresh77/final77·CPU 최고39.58%·가용 RAM 최저21.25828%·cleanup=True로 통과했다. 선행 CODE009와 모든 실패 원본은 보존하며 현재 소스 자격에 섞지 않는다.

실제 `successor-recovery-preflight-run008-attempt010`은 입력3066·Rust787·helper59·fresh563/final563, 119.613973초·CPU 최고89.74%·가용 RAM 최저20.43520%·cleanup=True로 통과했다. Bootstrap 정책24/24·연결78/78·정리된 Guard2개가 audit에 기록됐다. 준비 실행의75% 경고는 총4개였지만 지속 중단 조건에는 도달하지 않았으며90% 이상을 허용한 결과는 아니다. 이 통과 결과는 현재 소스로 보존한다. 비용 모델은598.436290초이며 실제 실행 시간이나 Native 완료 보장은 아니다.

이어 dispatch003 진입은8.652809초의 bootstrap에서 시스템 CPU98.41%·가용 RAM22.72324%로 `STOP_PREPARATION_SYSTEM_PRESSURE90`이 발생했다. Guard2개 모두 정리됐고 실제 dispatch stage와 제품/Native는 시작하지 않았다. 원본은 `preparation-attributed-bootstrap-qualify-run008-attempt003.v1.json`이며, 이를 dispatch 자격 실패 본문이나 성공으로 바꾸지 않는다.

종료 후 별도2.058초의 일부 프로세스 관측에서는 Git2개가 기계 전체 기준6.075%, pwsh8개가3.037%였고 관측 대상 Python6개는0%였다. 전체 프로세스 coverage가 아니며 baseline 없는 새 프로세스도1개여서 앞선98.41%의 원인 귀속 자료는 아니다. 다른 프로세스나 설정은 변경하지 않았다. 이후 직접 실행하는 셸은 invocation 단위 `login=False`로 `-NoProfile`을 확인했다. 기존 프로필 파일은0개여서 이 변경이 이번 CPU 문제를 해결했다는 주장은 하지 않는다.

### Dispatch 필수 비용 하한과 다음 최적화

CPU가 회복되더라도 같은 dispatch를 즉시 반복하지 않는다. `recovery_workflow_plan_v1.py --preflight-attempt 10 --dispatch-budget-lower-bound`는 실제 통과한010 scope의 원 비용 공식을 대조하고, 원 `prepared_run_closure_v1` admission이 반드시 읽는 closure4..6·packet·생산자/worker source와 preflight/audit를 현재68개 manifest의 의미/물리 대응으로 합친다. 각 exact pin·원 closure 판정·Native4..6 부재를 확인하며 큰 EXE를 다시 읽거나 제품을 실행하지 않는다.

기존3066입력의598.436290초에 필수11개 입력을 추가한 정책상 비용 하한은3077입력·600.530425초다. 미래 qualification setup 등은 포함하지 않았는데도 원600초를 초과한다. 이것은 실제 runtime 시간의 실측 하한이 아니라 기존 직렬 acquisition·두 실제 읽기·여유60초·제품10초·decoder5 등의 원 비용 모델에 필요한 예약의 하한이다. 원 guard나 여유를 줄여 통과시키지 않는다.

관련21개 회귀가 통과했고, 필수 packet pin 변조도 거부했다. `dispatch-cost-lower-bound-pref010.v1.json`은 약0.126초·1,616,140바이트 읽기로 계산한 metadata pin20개와 별도 분석 코드 pin을 보존한다. GO=False이며 제품/전체 자격 증거가 아니다. Planner 자체와 테스트는 현재010 물리 입력 scope에 포함되지 않으므로 이번 읽기 전용 진단 변경은 현재 사전검사 소스를 바꾸지 않는다.

큰 불변 증거의 물리적 표현 비교는 앞 절의 일반61개 실측까지 진행됐다. 원본 파일·전체 의미 입력·부모/worker의 동일한 매핑·두 실제 바이트 경계·독립 판정기를 모두 보존해야 한다. 표현이 바뀌면 그 변경에 의존하는 source/worker/전체 자격은 다시 닫아야 하며, 현재 Native008은 아직 시작할 수 없다.

### 유한한 후속 준비 기록과 선행 자격 이력

준비 슬롯1..8의 원본을 보존한 채 사전검사 기록과 연결 CODE 기록의 선택 범위를1..16으로 명시적으로 확장했다. Dispatch 자격 번호·Native 실행 번호는1..8, 현재 Native physical run은8, 제품 CODE 참조는1로 유지한다. `metadata_identifier_policy`를 새 연결 증거와 admission에 명시했으며 자동 재시도와 기존 파일 덮어쓰기는 허용하지 않는다.

동결 IO·level6·dispatch 함수는 metadata 참조를 비교하는 정확한 내부 generator의 상한만 투영하고, 전체 재귀 code inverse가 원본을 복구하는지 확인한다. 컨트롤러 destination은 preflight ID9..16만 추가 허용하며 CODE ID9와 Native run9는 계속 거부한다. 이 변경은 CPU/RAM·600초·입력 읽기·정리 조건을 바꾸지 않는다. 원본 준비 함수는9번을 거부하고, 연결된 실제 준비 함수는9번을 받아들인 뒤 Guard 생성 직전에 테스트가 중단되는 회귀로 확인했다. 테스트에서 실제 Guard·sampler·제품·자식·준비 산출물은 생성하지 않았다.

당시 `preparation-attributed-connection-code008`은27계약·fresh77/final77·CPU 최고45.51%·가용 RAM 최저19.48759%·cleanup=True로 통과했다. 읽기 전용 planner도1..16을 조회하고 당시19개 회귀를 통과했다. 당시 조회는194개 입력·13,089,672바이트·0.091728초이며 기존9개 단계를 재실행 불필요 후보로 유지하고 다음 준비 번호9를 반환했다.

첫 preflight009 진입 명령은8.016초에 `STOP_TERMINAL_METADATA_WARNING_BEFORE_MORE_WORK`로 종료됐다. 위치는 당시 `preparation_attributed_entry_v1.main`의 연결 소스 bootstrap 재확인이며 실제 사전검사나 새 준비 정책의90% 중단이 아니다. 정확한 CPU 표본과 별도 cleanup receipt는 이 CLI 출력에 없으므로 수치를 추정하거나 전체 검증 PASS를 만들지 않는다. 당시009의 setup·사전검사 결과와 Native008 파일이 모두 없음을 확인했다. 후속 bootstrap 분리 뒤 실제009와010 실행 결과는 첫 절을 따른다.

이 시점에는 기존75% bootstrap을 무조건 제거하지 않고 짧은 정책 증명과 전체 연결 재확인을 분리하는 설계가 다음 작업이었다. 그 구현과 현재 비용 판정은 첫 절을 따른다. 원 정책·연결 증거의 실제 전후 재확인과 Native 보호기는 유지하며 Native helper64 전체 자격은 아직 없다.

### 재로딩 연결 수정과 선행 자격 이력

`recovery_dispatch_window_v1.py`는 dispatch `main`의 정확한 컨트롤러 loader 호출 한 개만 연결한다. 원 함수 전체와 자격을 갖춘 graph4 메타데이터 변형을 먼저 대조하고, 연결 변경을 역변환했을 때 나머지 AST가 전부 일치하도록 검사한다. 바깥 alias뿐 아니라 실제 재로딩 결과의 캡처 창·비용 모델·template가10초를 사용하는 회귀가 통과했다. 기본 컨트롤러·과거15초 창과 동결 `prepared_run_closure_v1.py`·공유 `conservative_maintenance.py`는 변경하지 않았다. 별도 Native 진입점은 준비용 CPU Guard를 설치하지 않으며, 전체 Native 자격은 아직 없다.

준비 전용 연결에서 발견한 두 누락도 수정했다. 첫째, 원 사전검사의 실제 `MetadataCheckpoint`가 별도75% 즉시중단을 유지하고 있었다. 실제 입력 binding의 namespace attribute만 준비용 facade로 연결하고, 원10개 계약의 함수 globals와 기본 Native class는 그대로 유지했다. 둘째, dispatch가 새로 로딩한 컨트롤러의 Guard가 준비용 정책을 받지 못했다. 준비 모드에서만 명시적 controller 변환을 전달하고, Native의 기본 변환은 비워 둔다. 실제 재로딩 회귀는 준비 역할의 Guard와 정리를 함께 확인한다.

당시 소스의 `preparation-attributed-connection-code007`은23계약·fresh76/final76·CPU 최고72.25%·가용 RAM 최저21.79473%·cleanup=True로 통과했다. CODE004의 실패, 선행 CODE005·006과 모든 실행 원본은 그대로 보존한다. 후속 변경 뒤 현재 자격은 첫 절을 기준으로 하며 소스가 달라진 과거 PASS를 재사용하지 않는다.

| 실행 접미사 | 실제 결과와 경계 |
| --- | --- |
| `successor-recovery-preflight-run008-attempt006` | 66.785초·CPU85.26%에서 원 `metadata_pressure_failfast.py`의75% 단일 표본 중단. 새 Guard는 경고1개·미중단 상태였으며 cleanup=True. 이후 실제 binding 연결 수정 |
| `successor-recovery-preflight-run008-attempt007` | 입력3066·Rust787·helper59·fresh563/final563, 121.032초·CPU80.27%·가용 RAM 최저22.24283%·cleanup=True PASS. 실제 준비 Guard의75% 경고1개, checkpoint51388회·복구 완료. 비용 추정598.415565초. 이후 dispatch Guard 소스 수정 전의 결과이므로 현재 자격에 재사용하지 않음 |
| `successor-recovery-dispatch-qualification-run008-attempt002` | 46.916초·CPU79.81%에서 내부 재로딩 Guard의 원75% 단일 표본 중단, 계약/전체 비용 미확인·cleanup=True. 이후 준비 모드의 명시적 Guard 변환 추가 |
| `successor-recovery-preflight-run008-attempt008` | 당시 소스. 50.664초·CPU90.46%에서 `STOP_PREPARATION_SYSTEM_PRESSURE90`, 가용 RAM20.25158%·commit53.22706%·부모 CPU0%·private68.25MiB. 메타데이터 checkpoint가 latch 후 복구됐고 cleanup=True. 전체 사전검사 미통과, Native·제품 실행 없음 |

실제80.27% 일시 경고를 처리한 선행 사전검사와, 현재90.46%에서 중단한 실행은 준비 정책의 서로 다른 경계를 보여 준다. 직접 부모 점유가 낮다는 관측만으로 간접 영향이나 외부 프로세스, 프리즈 원인을 확정하지 않는다.

이 시점에는 기존 준비 슬롯1..8을 모두 소비해 명시적 유한 준비 번호 범위 설계가 다음 작업이었다. 이후 범위 확장과 현재 실행 위치는 첫 절을 따른다. Native008은 아직 시작할 수 없으며600초 전체 비용과 실제 Native helper64도 미확인이다. 목표는 ACTIVE다.

아래 준비 정책의005/003 기록은 선행 소스의 검증 이력이며, 현재 실행 위치와 소스 자격은 이 절을 우선한다.

### 승인된 준비 단계 CPU 정책과 실제 확인

사용자의 “준비 단계 정책 재설계 허용”에 따라 `preparation_attributed_cpu_v1.py`와 준비 전용 진입점 `preparation_attributed_entry_v1.py`를 추가했다. 이 진입점은 case165/run008의 사전검사·dispatch 구성만 허용하고 Native·worker·제품·수용 명령을 거부한다. 공유 기본 모듈과 실제 Native 보호기는 바꾸지 않았다.

- 시스템 CPU75% 이상은 경고이며, 새 표본4개 연속·최소1.5초 지속 시 중단한다. 90% 이상은 즉시 중단한다.
- 자체 검증 부모의 기계 전체 기준 CPU가 1코어 비중의1.25배를 새 표본2개 연속 넘으면 중단한다. 귀속 값 누락·표본 변조·순서 오류는 fail-closed다. 같은 표본의 반복 checkpoint는 지속 표본 수에 넣지 않는다.
- 원래 hard guard가 먼저 실행되며 RAM95%·commit95%·원 deadline/IO/정리를 유지한다. 실제 affinity1코어·BelowNormal을 읽어서 확인한다. 추가 sampler·자식·자동 냉각 재개는 없다.

설계 `preparation-attributed-CPU-design-code001`은20계약·fresh21/final21, 실제 무제품 `preparation-attributed-CPU-probe001`은fresh23/final23으로 통과했다. Probe의 CPU 최고는74.8%여서 실제75% 이상 구간의 개선 실측은 아니며, 경계 조건은 합성 테스트와 과거 중단 표본 재생으로 확인했다. 연결 CODE001은 후속 소스 수정으로 현재 사용하지 않고, CODE002는 CPU93.96%로 마지막 확인이 중단됐다. 당시 소스에 대한 CODE003은13계약·fresh72/final72·CPU 최고67.1%·cleanup=True로 통과했다. 증거 선택은 명시적 `--connection-attempt`를 사용해 보호 중단 때마다 소스를 수정하지 않는다.

실제 `successor-recovery-preflight-run008-attempt005`는 입력3064·Rust787·helper59·fresh561/final561, 122.350753초·CPU 최고69.34%·가용 RAM 최저25.18289%·cleanup=True로 통과했다. 전체 비용 추정은598.250136초다. 별도 `preparation-attributed-preflight-run008-attempt005`는 준비 전용 정책을 사용한2개 직렬 Guard와 연결 소스의 재확인을 기록한다. 두 Guard의75% 경고 표본은0개이므로, 이번 실행이 기존 정책보다 중단을 줄였다는 실측 주장은 하지 않는다.

이어 `successor-recovery-dispatch-qualification-run008-attempt001`은6계약을 통과했지만 `DIRECT_VIEW_ORACLE_FINAL_SAMPLE_INSIDE_ORIGINAL600`으로 실패했다. 72.342057초·CPU 최고68.75%·가용 RAM 최저27.47376%·cleanup=True이며 Native·제품 실행은 없다. 준비 정책 자체가 아니라 비용 자격 단계의 실패다. 제품 생성을 차단한 실제 동결 진입점 구성 확인에서 바깥 컨트롤러 alias는10초지만 dispatch `main`이 새로 로딩한 컨트롤러는15초임을 확인했다. 따라서 기존의 “실제 창·비용·독립 판정기 연결 완료” 주장은 전체 dispatch 경로에는 적용할 수 없다. 다음은 이 재로딩 연결을 수정하고 같은 창·전체 입력·600초 예산·helper64를 다시 확인하는 작업이다. Native008은 그 전까지 시작하지 않는다.

### 확인한 반복 비용과 개선

최근 복구 준비의 선택된23개 기록은 합계252.07초였다. 현재 채택한8개 준비 기록은91.03초이며, 별도 전체 CODE74는36.26초다. 이 차이는 같은 조건의 성능 벤치마크가 아니라, 연결 수정 뒤 증거를 반복 발급한 실제 작업 비용이다. 개별 함수 검사를 먼저 통과했어도 함수 내부 import와 기존 경로 정규식의 연결 문제를 뒤늦게 발견해 반복 범위를 키웠다.

이제 수정과 제품 없는 전체 진입점 구성 검사를 먼저 끝내고 소스를 고정한 뒤 증거를 발급한다. 구성 회귀는 실제 진입점을 사용하되 제품·자식 프로세스 생성을 차단하고, 복구용 경로와 실제10초 창의 연결을 확인한다. 경로만 바꿀 때에도 전체 코드 역변환 동등성을 검사하며 과거 파일을 덮어쓰지 않는다.

`tools/p09/recovery_workflow_plan_v1.py`는 통과 증거의 입력 해시와 단계 의존성을 읽기 전용으로 대조한다. 동일 조회의 중복 입력은 한 번만 해시하고 영속 캐시는 만들지 않는다. 기존194개 입력·약0.10~0.11초의9개 단계 조회는 유지한다. 준비 setup만 실패해도 슬롯을 소비한 것으로 구분하며, 현재 명시적 상한16 중1..8을 소비했고 다음 슬롯은9다. 실제 사전검사·제품 진입의 원래 독립 입력 재확인은 그대로 수행한다. 이 조회는 제품 자격이나 GO 승인이 아니다. 관련19개 회귀는 통과했다.

새 PASS 사전검사561개 입력까지 포함하는 계획 조회는64MiB 진단 한도에 도달한다. 이 경우 이미 확인한9개 단계는 유지하고 사전검사 재조회만 `BOUNDED_CHECK_INCOMPLETE_NOT_REUSABLE`로 반환한다. 원 사전검사의 실제 PASS를 실패로 바꾸거나, 덜 읽은 조회를 재사용 자격으로 승격하지 않는다. 최신 조회는0.083초였으며 한도를 늘려 전체 재검증을 겹쳐 실행하지 않았다. `--budget-lower-bound`는 필수 부분집합의594.249872초만 계산하는 읽기 전용 계획이며, 원 run007 전체 비용599.843613초와 원 공식을 대조했다. 미래 qualification 입력까지 포함한 전체 비용 통과가 아니다.

```powershell
python -B tools/p09/recovery_workflow_plan_v1.py --preflight-attempt 9
```

현재는 window CODE·실제 pipe·실패 판정 CODE와 review·복구 CODE·준비 closure3개·전체 CODE와 선행 사전검사005·007 원본을 보존한다. 후속 재로딩·Guard·번호 범위 변경으로 과거 사전검사는 현재 소스 자격에 재사용하지 않는다. 선행008은90% 보호 중단, 현재009는 bootstrap 중단으로 실제 사전검사 NOT_RUN이다. 변경 소스에 의존하는 자격만 확인하며, 문서·전체 diff·무관한 단계 검사를 반복 조회하거나 전체249개를 다시 돌리지 않는다.

### 현재 채택한 복구 준비

| 증거 이름 접미사 | 확인된 결과 |
| --- | --- |
| `prepared-recovery-code002` | 27계약·fresh75/final75·정리 완료 |
| `post-product-recovery-window-code006` | 12계약·fresh25/final25 |
| `post-product-recovery-window-pipe005` | 실제 정상 출력 수집·10초 중단·fresh26/final26·소유 자식0 |
| `post-product-recovery-code003` / `review003` | 8계약·fresh19/final19 / 실제 원본 판정fresh21/final21 |
| `prepared-only-closure-run004..006-attempt007` | 각fresh80/final80·실제 EOF/NO-GO 거부·제품 실행 없음 |
| `successor-recovery-code-run008-attempt001` | 74계약·helper59·fresh185/final185·36.256초·CPU 최고59.02%·가용 RAM 최저36.35% |

이름은 모두 `evidence/p09-361-case165-` 접두사와 `.v1.json` 확장자를 사용한다. 복구 admission은 정확한 실패 원본·명시적 승인에 따른 판정·완전한 정리·다음 Native 부재를 요구하며 case165/run008에만 적용한다. 실패 원본은 새 전체 입력에 RAW로 포함한다. 개별10초 창·비용·독립 판정기 연결은 통과했으나 위 dispatch 내부 재로딩 불일치는 남아 있다. 기존15초 창과 과거 기본 모듈, 원래 source/CPU/RAM/IO·600초·60초 여유 조건은 유지한다. 새 전체 입력의600초 예산과 실제 Native helper64는 아직 전체 자격 검사가 끝나지 않았다.

### 사전검사 보호 중단과 다음 작업

`successor-recovery-preflight-run008-attempt001`은41.379초에 시스템 CPU89.54%로 중단됐다. 종료 표본의 검증 부모는 CPU0.161%·private61.62MiB, 가용 RAM32.38%였다. attempt002는4.051초에 CPU79.49%로 같은 보호 중단됐다. 둘 다 cleanup=True이며 제품 실행은 없다. 직접 부모 점유가 낮다는 관측만으로 간접 영향이나 외부 원인까지 배제하지 않는다.

이후 attempt003은 setup의 CPU76.65%에서 중단돼 실제 사전검사 기록이 없고, attempt004는 CPU76.36%·부모0%/private47.81MiB에서 중단됐다. 모두 정리 완료이며 원본을 보존한다. 승인된 준비 정책의 attempt005는 당시 소스로 통과했으나 이후 재로딩 연결 수정이 있어 현재 자격에 재사용하지 않는다. 현재007·008 및 다음 작업은 첫 절을 따른다. CODE·pipe·기존 준비 closure는 소스 또는 선행 증거가 바뀌지 않으면 다시 발급하지 않는다. OS·Defender 설정과 다른 작업은 변경하지 않았다.

## 이전 run007 검증과 실행 설정

2026-10-15 현재 대화에서 목표를 ACTIVE로 유지한다. RAM 95%는 현재 검증 진입점의 `configure_host_policy` 실행 설정이다. 정확히 95%는 허용하고 초과 시 중단하며, CPU·commit 95%·소유 Job 7% 중단/8% hard limit은 유지한다. 공유 `conservative_maintenance.py`와 관련 테스트 6개는 이전 고정 소스와 동일한 바이트로 복원했다. 공유 파일의 기본값을 재작성하지 않고 정책 dict의 동일 객체에 profile·RAM 시작/중단 값만 적용하므로 기존 Guard와 SQL의 바인딩도 함께 갱신된다. Native007 기록의 실제 policy도 가용 RAM 5%다.

이 분리로 이전 준비 그래프와 직전 수용 증거의 소스 해시 충돌을 해소했다. V6의 구성요소 자격 파일명 투영은 제거했고 원래 runtime-code002·worker-code004 검사를 유지한다. `prepared_run_closure_v1.py`는 16,889바이트, SHA-256 `8c914a79faf481f86c18126e8a3fddc9ff5ae370ba53b93b510ad30d74775151`이다. closure-code006의 9개 회귀와 run004..007 closure-attempt005가 PASS했다. 이전 소스의 CODE·실패 증거는 삭제하지 않았다.

| 현재 준비 증거 | 계약 또는 범위 | 실제 전후 해시 | 시간 | CPU 최고 |
| --- | --- | --- | ---: | ---: |
| `evidence/p09-361-case165-successor-code-run007-attempt005.v1.json` | 74계약·helper59 PASS | 170/170 | 31.157초 | 53.82% |
| `evidence/p09-361-case165-successor-preflight-run007-attempt008.v1.json` | 입력3044·Rust787·helper59 PASS | 538/538 | 109.818초 | 61.17% |
| `evidence/p09-361-case165-successor-dispatch-qualification-run007-attempt001.v1.json` | 6계약·입력3068·Native helper64 PASS | 549/549 | 113.502초 | 56.92% |

모두 cleanup=True이며 준비 자격이지 제품 수용 결과가 아니다. preflight007-007은 CPU78.99%에서 보호 중단됐지만 당시 검증 부모 CPU는 약0.19%, private memory48.05MiB였다. 검증 종료 후 새 10표본의 CPU 최고26.76%를 확인하고 CODE 재실행 없이 preflight008을 실행해 통과했다. 이 관측은 직접 CPU 점유를 구분할 뿐 간접 영향이나 외부 원인을 확정하지 않는다.

### 실제 제품 실행 후 최종 입력 재확인 중단

Native007은 case165 한 개만 실행했다. 본문 출력은 1 PASS·0 failed·248 filtered, exit0이며 GO부터 완전한 출력 수집까지 2.442초다. 그러나 전체 실행은 574.41초의 `final_source_freeze`에서 `STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING`으로 중단됐다. 전 경계의 실제 바이트 검사는 입력3056개·228,558,382바이트로 완료됐지만 후 경계는 완료되지 않았다. 따라서 `Native_source_frame_qualified=False`, 현재 후보 자격=False, 수용 증가0을 유지한다.

잠금3428개는 모두 닫혔고 활성 reader/byte stream·잔여 잠금0, cleanup=True, owned tree empty=True다. 마지막 표본은 시스템 CPU94.87%, 검증 부모0.164%·private65.95MiB, 소유 자식0개였다. 원 source 경고 기준90%의 fail-fast로 중단됐으며 관련 원 회귀16개 PASS다. CPU 원인 프로세스 귀속과 프리즈 해결은 미확정이다.

원본은 `evidence/p09-361-case165-current-runtime-run007.v1.json`(4,199,057바이트, SHA-256 `3271eb9b07cd0eb1462630bb0f61e7ca7894545ec67f0c516ea8d898391a0f6c`)이다. 기존 prebody 재시도 판정기는 실제로 `V2_PREVIOUS_PREBODY_ONLY`로 거부했다. 이전 준비-only closure로 이 원본을 대체하거나 완료되지 않은 후 경계를 새로 만든 것으로 표시하지 않는다.

### 사용자 승인에 따른 복구 판정

사용자는 현재 채팅에서 “복구 경로 설계·검증 진행”을 승인했다. `post_product_stop_recovery_v1.py`는 이 원본의 exact byte/SHA와 case/run·제품 출력·15초 창·닫힌 Frame·전체 잠금 정리·완료된 전 경계만 읽기 전용으로 검증한다. 다른 후보, 수용 PASS, 알 수 없는 중단, 잔여 핸들, 가짜 경계, 변경된 제품 출력은 거부한다.

`post-product-recovery-code001`의 8회귀/fresh19-final19, 실제 `post-product-recovery-review001`의 fresh21-final21은 PASS다. 실제 판정은 10.405초·CPU 최고67.76%·cleanup=True다. 이는 **정리된 제품 실행 후 자원 실패이며 새 전체 재시도 경로를 설계할 수 있다는 판정**이다. `runtime_retry_admission_implemented=False`, `next_Native_start_authorized=False`, GO=False이며 원본의 PASS 승격이나 제품 출력만의 재사용은 허용하지 않는다.

이 시점에는 run8 admission 연결이 미완료였다. run7 자격의 비용 추정은599.662초로 여유가 작아 새 입력 비용을 반드시 포함해야 한다. 이후 연결과 준비 검증 결과는 첫 절을 따른다. 기존 Rust 본문/원본 비교 실패도 보존한다.

아래 내용은 이전 검증과 최적화 이력이다. 현재 실행 위치와 정책 판정은 첫 절을 우선한다.

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

## 준비 reader의 반복 할당 개선과 사례163 실제 통과

successor_preparation_workspace_v1은 기존 reusable_audit_chunk_v1의64KiB readinto workspace를 준비용 AcceptanceReader에 연결한다. 원 reader의 MRO wrapper·파일 열기·속도 제한·checkpoint·parse budget·hash·최종 전체 재읽기를 유지한다. 기존 v2와 승인 소스는 변경하지 않고 정확히 고정된 소스를 private namespace로 구성한다. 새 helper·시험·기존 leaf·guard source 및 코드 검증 기록은 각 실제 reader에서 입력·최종 해시로 확인한다. Native worker·GO·승인 진입점은 제공하지 않는다.

초기 guard namespace 설정 오류는 stage와 guard 생성 전 거부됐으며 별도 기록을 보존했다. 같은 원 controller의 고정 guard namespace로 수정한 뒤 기존15개 scratch 계약과 새2개 연결 계약이 통과했다. code001은 계수 기록 추가 전 소스의 검증이고 현재 source qualification은 code002다. code002는17계약·fresh7/final7·2.019초·CPU45.68%·cleanup=True다. 최종 소스의 CODE002-003은 원74계약·fresh100/final100·14.388초·CPU44.76%·cleanup=True다. 실제 reader1개, workspace65,536바이트1개, leases200/returns200, readinto400회·1,810,596바이트·최종 해시100개를 확인했다.

whole preflight003은12.779초·CPU79.69% 경고로 중단됐으며 parentCPU0.389%·private48.039MiB·cleanup=True다. 짧은 검증 종료 후 표본에서 다른 Python2개와 Git1개가 상위였지만 중단순간 attribution은 아니며 Python2개는 이 준비 명령이나 hwpx 저장소 명령이 아니었다. 특정 외부 프로세스를 원인으로 확정하거나 종료하지 않았다. CODE를 유지하고 preflight004만 진행했다. preflight004는118.998초·입력2,927/Rust787·helper62·fresh415/final415·CPU73.60%·가용RAM44.030%·cleanup=True로 통과했다. 실제 workspace1개·readinto3,685회·836읽기·141,080,631바이트·leases836/returns836·active=False를 확인했다. 이전118.694초와 비슷하므로 시간 감소 또는 프리즈 해결은 입증되지 않았다.

준비 entry로 진행한 qualification003은55.091초·CPU98.26% 보호중단·parentCPU0%·private50.223MiB·cleanup=True다. qualification004는CPU56.70%에서 실제 Native helper 한도에 거부됐다. 준비 entry의 helper를 숨기거나64개 한도를 늘리지 않았다. 이 entry는 CODE/preflight에 사용하고 실제 Native 연결 qualification은 기존 v2 entry로 수행한다. qualification005는6계약·실제Native helper64개·fresh416/final416·116.098초·CPU60.74%·가용RAM45.937%·cleanup=True다. 예상 비용594.166초/600초, Native 발행 직전과 종료 후 해당 source416개 해시 일치를 확인했다.

실제 Native002는567.86초에 제품1개 통과, GO부터 완전 출력 수집1.824초, 물리 입력2,929개·232,279,766바이트에 대한 실제 전후 경계2회 및 Frame COMMITTED·빈 소유 tree·cleanup=True를 확인했다. 시스템CPU최고65.72%·가용RAM최저42.399%·parent private최고55.387MiB다. 후보는4,525,503바이트·SHA256 f2151271e6d74e6019773d198fba861d00a60dcccebcb41969f4bd77ec05736e다. Native 소스와 경로는 변경하지 않았으므로 이전 사례보다 짧은 시간을 준비 버퍼 개선의 효과로 단정하지 않는다.

독립 리뷰001은2계약 통과 뒤60.088초·CPU75.20% 경고로 중단됐다. 원 파일 열기 pacing과 guard 코드를 확인하고 부하 회복 뒤 리뷰002만 진행했다. 리뷰002는117.212초·2계약·fresh420/final420·CPU55.47%·가용RAM41.018%·cleanup=True로 통과했다. 제품을 재실행하지 않았다.

공식 승인001/002는 각각CPU80.23%와75.77% metadata 보호로 중단됐고 delta0·cleanup=True다. 중단순간 부모CPU는 모두0%, private55.129/56.230MiB다. 승인002의 실제 reader도 이미 workspace65,536바이트1개·readinto2,855회·91,642,147바이트·leases831/returns831·active=False를 사용했다. 같은 scratch 개선을 중복 적용할 근거는 없다. canonical은 생성되지 않았고 세 번째 동일 승인 재시도는 시작하지 않았다.

공식156/249·잔여93·next163·generation51, P09/A12/A13 OPEN 및 목표ACTIVE를 유지한다. 사례163 제품·Native·독립 전체 리뷰는 통과했고 공식 승인만 미완료다. 다음은 승인 단계의 반복 읽기·검증 비용을 점검하되 현재성 검사와 원 승인 조건을 보존하는 것이다. CODE·preflight·실제제품·독립검사 통과 및 모든 실패 기록을 보존한다.

근거: preparation-workspace-setup001 및 code001/002, workspace CODE/pref/qualify 계수, successor-code002/003, preflight003/004, dispatch-qualification003..005, current-runtime-run002, whole-review001/002, optimized-acceptance001/002. 사용자 소유 변경과 원본·승인162는 보존했고 OS 설정 변경·외부 프로세스 종료·검증 범위 축소는0이다.

## 사례163 공식 승인과 사례164 준비

승인 경로는 이미 실제64KiB workspace1개·요청별 fresh stat1회를 사용하며 현재 source 확인과 최종 전체 재해시를 유지한다. 이번 검토에서 해당 검사를 삭제하지 않고 안전하게 제거할 수 있는 중복을 찾지 못했다. 현재 자원 표본CPU23.87/24.56% 및 qualification source416개 해시 일치를 확인한 뒤 제품·Native·독립 리뷰를 재실행하지 않고 승인003만 진행했다.

승인003은238.429초에 공식 canonical을 한 번 발행했다. before156·delta1·after157·잔여92·next164·generation52, fresh1,226/final1,226·2,468읽기·217,192,418바이트·resource cleanup=True다. CPU최고56.53%·가용RAM최저46.818%이며 제품·Native 재실행은0이다. canonical은445,427바이트·SHA256 9471987562d9c5cc25d734487b9c356b57f0e81855b7f9d59c85267f686ac8f2다. 기존 승인001/002 중단과 모든 실패는 보존했다. P09/A12/A13은 OPEN이며 full249·signed16·전체 runtime reconciliation은 미완료다.

사례164의 STEP001은 원장163에서 준비됐으며 fresh9/final9·CPU18.63%·cleanup=True다. 새 원본4개는10,906,643바이트에서3,468,032바이트의 무손실 표현으로 변환했고7,438,611바이트가 절감됐다. 원본을 보존했고 fresh31/final31·CPU42.34%·cleanup=True다. Binding001은 기존52개와 새4개를 합친56pair·fresh139/final139·물리입력2,936개·229,948,922바이트·196.324초·CPU53.61%·가용RAM47.208%·cleanup=True로 통과했다. 원본/envelope 읽기88.993초·최종 재해시96.250초가 대부분의 비용이다.

graph002 v2는5.761초에CPU98.64% metadata 경고로 중단됐으며 cleanup=True·product/Native=False다. 실패 report만 생성됐고 capsule002·bootstrap002·Native002는 생성되지 않았다. 원 exclusive report를 덮어쓰거나 없는 Native 기록을 만들어 넣지 않는다. 현재 원 graph attempt와 실제 run 번호가 묶여 있으므로 단순 run003 재시도는 이전 Native002를 요구한다. 다음은 이 준비 전용 종료 상태를 원 증거로 확인하고, 실제 제품 재실행 방지와 미해결 Frame 거부를 유지하는 재시도 연결을 마련하는 것이다.

공식157/249·잔여92·next164·generation52 및 목표ACTIVE를 유지한다. 사례164는 STEP·무손실 준비·Binding 통과, 전송 준비 실패, CODE/preflight/Native/독립 리뷰/승인 NOT_RUN이다. source·OS 설정 변경 및 검증 범위 축소는0이며 PC프리즈 근본 해결·전체 시간 단축은 입증되지 않았다.

근거: case163-current-epoch-accept001, optimized-acceptance-attempt003 및 case164-step-config001, successor-selection001, lossless-receipts001, successor-binding001, successor-connections002.v2.json.

## 준비 전용 실패의 검증된 재시도 연결

current_queue_successor_retry_runtime_v3는 고정된 v2 bridge와 시험 소스를 private namespace로 읽고 기존 본문·defaults·closure 및 graph/worker/전체 검사 경로를 유지한다. 바뀌는 entry/test 경로와 새 재시도 코드는 실제 reader의 입력과 최종 해시에 포함한다. 기존 v2와 승인 파일 및 공유 모듈을 수정하지 않는다. 현재 Native 결과가 있으면 v2의 전체 closed-prebody 판정을 사용한다. Native가 없다면 기존 graph 실패의 정확한 key/형식·index·제품 미실행·GO 미승인·delta0·정리 및 CPU metadata 오류를 확인한다. 이전 capsule/bootstrap이 없고 Native 부재를 다시 확인해야 한다. 실패 graph를 가짜 Native 기록으로 바꾸지 않는다.

재시도 code001은6계약 중 mock 연결 오류3개로 실패했다. 시험 namespace의 alias 대신 실제 함수 globals에 fixture를 연결하고 종료 시 원 값으로 복원했다. 해당 실패를 보존했고 code002는6계약·fresh5/final5·1.501초·CPU25.10%·cleanup=True로 통과했다. 제품/GO/정리 불일치, 잘못된 수치, 남은 worker 자료, 부재 재확인 실패를 거부하며 기존 Native 기록은 원 v2 판정을 유지하는 계약이다. 새 entry 경로 metadata 변경에서도 기존 function code identity를 유지한다.

사례164 graph003은56pair 전체 복원·wire8,071바이트·fresh41/final41·10.639초·CPU36.70%·cleanup=True로 통과했다. factory001은GO 없는 원11계약·fresh26/final26·11.748초·CPU46.48%·cleanup=True다. CODE003-001은74계약·fresh99/final99·14.095초·CPU31.25%·cleanup=True로 통과했다. 전체 preflight003-001은 입력2,942개·Rust787·helper62·fresh429/final429·120.637초·CPU57.39%·가용RAM44.698%·cleanup=True다.

entry003-001은 원6계약·실제Native helper64개·fresh431/final431·123.275초·CPU52.46%·가용RAM45.521%·cleanup=True로 통과했다. 이전 실패 graph002가 실제 입력 pin에 포함됐고 Native002의 부재를 확인했다. 실제 실행 직전431개 source pin이 모두 일치했다. 예상 비용594.547초/600초는 완료 보장이 아니며 원16KiB/64helper/GO/Job/전후 읽기/자원 보호 조건은 유지한다.

Native003은57.73초에 STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME로 종료됐다. 마지막 시스템CPU83.81%·parentCPU0%·private50.371MiB·가용RAM43.370%·commit40.804%다. worker와 제품 미실행·Frame=None·passed_test_names=[]·delta0·Native/current qualification=False·cleanup=True·빈 소유 tree를 확인했다. 코드의 같은 pin 재사용과 전체 입장 검사의 Native metadata callback 배치를 점검했으며 직접 계산 폭주를 입증하지 못했다. 검증·원본을 삭제하거나 자원 보호를 완화하지 않았다.

실제 v3 독립 리뷰·승인 adapter는 구현됐으나 Native 후보가 없어 실행하지 않았다. 다음은 원003 종료 기록의 완전한 prebody 조건을 유지한 새 번호 준비다. 공식157/249·잔여92·next164·generation52, P09/A12/A13 OPEN 및 목표ACTIVE를 유지한다. 제품·독립 리뷰·승인은 NOT_RUN이며 전체 시간 개선·PC프리즈 해결은 입증되지 않았다.

근거: case164-retry-code001/002, successor-connections003.v2, successor-factory001, successor-code-run003-attempt001, successor-preflight-run003-attempt001, successor-dispatch-qualification-run003-attempt001 및 current-runtime-run003. 구현은 current_queue_successor_retry_runtime_v3와 해당 시험 파일이다.

## 반복 원본 읽기의 무손실 대체 후보

소스를 변경하지 않은 사례164의004 graph는56pair·wire8,071바이트·fresh41/final41·10.668초, factory002는 원11계약·fresh26/final26·11.876초로 통과했다. CODE004-001은74계약·fresh99/final99·14.159초·CPU46.48%·cleanup=True다. whole preflight004-001은 scope2,942/Rust787/helper62·fresh429/final429·120.715초·CPU47.35%·가용RAM44.881%·cleanup=True로 통과했다. entry004-001은6계약·actualhelper64·fresh432/final432·123.720초·CPU48.85%·cleanup=True이며 source432개 현재 해시가 일치했다. 원 예상 비용594.779초/600초다.

Native004는15.96초 metadata CPU 경고로 중단됐다. 마지막CPU85.69%·parentCPU0.154%·private47.082MiB·가용RAM45.386%·commit39.388%이며 제품/worker 미실행·Frame=None·정리 완료다. Native003/004의 원 timestamp 정밀도를 유지해 계산한 표본 간격은 각각500.881..564.068ms와501.230..624.113ms로,100ms 미만 간격은0개다. 짧은 강제 CPU 표본이 해당 두 중단을 만들었다는 가설은 지지되지 않았다. 경고표본의 기존 kernel busy26.415%·user busy59.277% 및 optional attribution unavailable만 확인했으며 상승 프로세스는 확정되지 않았다.

004 metadata는 중단까지139회·18,038,896바이트를 읽었다. 실제 input pin에는 이미 무손실 표현이 있는 원본162/163이 포함되며 두 원본의 합계9,001,891바이트 대비 물리 표현은3,537,734바이트다. 현재 초기 메타데이터 reader가 원본을 다시 읽는 비용을 줄이는 후보로 fresh_lossless_metadata_reader_v1을 구현했다. 명시적 Projection/descriptor에 있는 과거 runtime JSON만 매 요청 실제 물리 읽기·완전 복원·원본 크기/해시 확인으로 제공한다. 다른 파일은 원 reader를 사용하며 JSON/byte/hash cache는 없다. 물리 bytes_read에는 decoded bytes를 더하지 않고 별도 계수로 기록한다. 현재 Native·Frame·승인 경로는 바꾸지 않았다.

후보8계약은 원본 해시/물리 해시 변조·잘못된 projection·parse budget·decoder 실패를 거부하고 fresh 요청·unmapped 원 reader·물리/의미 byte 구분을 확인했다. actual probe001/002는 각각 current descriptor를 historical로 전달한 오류와 manifest 누락으로 실패했고 기존 Binding 조건을 완화하지 않았다. 이전 manifest의 과거 descriptor를 사용하고 현재 manifest를 전체 projection scope에 포함한 probe003은14.701초·CPU36.52%·가용RAM43.448%·cleanup=True로 통과했다.

probe003은 전체56개 descriptor를 구성한 뒤 큰 원본2개인159-run001과163-run002의 실제 읽기 및 최종 재읽기를 비교했다. 기존 물리 읽기18,212,358바이트 대비 후보6,998,420바이트로11,213,938바이트·61.57%가 절감됐다. 각각의 JSON과 semantic pin이 일치했고 candidate 최종 fresh hash2개·물리읽기4회·mapped decode4/4를 확인했다. 별도 source12개도fresh12/final12 및 현재 해시가 일치한다. 이는2개 원본의 bounded reader 결과이며 전체56개 fresh IO, 실제 Native 메타데이터 연결, 공유 decoder 작업 한도, 전체 비용/후속 원체커/승인 및 PC프리즈 해결은 아직 검증하지 않았다.

다음은 이 후보를 초기 metadata reader에 연결하되 원 workspace·source/ancestor stat·guard·속도 제한과 실제 물리 byte 계수를 유지하고, explicit semantic/physical 기록과 decoder budget을 전체 Native·독립 체커에서 확인하는 것이다. 공식157/249·잔여92·next164·generation52 및 P09/A12/A13 OPEN·목표ACTIVE를 유지한다. 사례164 제품·독립 리뷰·승인은 NOT_RUN이며003/004 및 기존 실패와 원본은 보존한다.

근거: successor-connections004.v2, successor-factory002, successor-code/preflight/dispatch-qualification-run004-attempt001, current-runtime-run004 및 fresh-lossless-metadata-probe001..003. 구현은 fresh_lossless_metadata_reader_v1과 해당 시험 파일이다.

## 실제 초기 reader 연결과 공유 decoder 한도

lossless_metadata_connection_v1은 고정된 v3 실행 구성에서 실제 private 엔진을 구성하고 BuildReader에 명시적 fresh 무손실 reader를 연결한다. 엔진 run/worker 함수, 원 생성자 MRO, open pacing·64KiB workspace·source/ancestor stat 및 metadata CPU 경고를 유지한다. 원 dispatcher의 construct 안에 있는 전체 callback AST를 그대로 구성해 CODE/preflight 입장, 이전 종료, 전체 current_input_scope를 실행한다. GO·subprocess·Frame 실행은 하지 않는다. 사전 검증에 선언된 모든 semantic pin이 반환 범위에 유지되는지 확인하고,56개 모든 원본 pin의 실제 복원과 최종 재읽기를 수행한다.

connection001은4계약 통과 후 현재 STEP을 선언하지 않은 KeyError로40.999초에 중단됐다. cleanup=True·제품/Frame 미실행이며 실패를 보존했다. 원 dispatcher와 같이 STEP을 읽고 report와 일치시킨 connection002는110.625초·4계약·current scope2,961/Rust787·metadata fresh476/final476·물리140,330,051바이트·CPU53.71%·가용RAM45.501%·cleanup=True로 통과했다. 실제 original engine function과 reader MRO wrapper를 유지했다. workspace1개·leases961/returns961·returned_bytes140,330,051·source 요청961/stat961·ancestor 방문4,599/stat4,599를 확인했다.

이 실행의 mapped 원본56개는113회 fresh decode·물리93,455,827바이트·복원된 semantic303,651,939바이트다. decoded bytes는 physical counter에 더하지 않았다. metadata decoder 작업은1.399초이며 예전 원 Budget의5초 제한을 사용했다. 이 비교는 계수 구분이며 원 방식의 전체 동일 실행 시간과 직접 비교한 결과는 아니다.

shared_metadata_frame_decoder_budget_v1은 metadata와 Frame의 original Budget object에 추가 합산 check를 연결한다. 원 budget 타입/run 본문/owner/resource 우선 검사 및 Frame-only 계수를 유지한다. active decoder 작업까지 합해5초를 넘으면 sticky error로 중단한다. 새 sampler·thread·IO·deadline은 없다. 원 Frame constructor 이후 해당 budget을 등록하고 summary에 합산 증거를 별도로 추가하는 factory hook을 구현했다. 아직 실제 Native Frame을 생성해 이 hook을 검증하지 않았다.

공유 code001은 bound method 객체의 Python 조회 identity를 잘못 비교한 시험1개가 실패했다. 실제 저장된 원 method와 동일한 function/owner 복원을 검사하도록 시험을 수정했고 기존 실패를 보존했다. code002의8계약과 Frame constructor/summary hook을 포함한 현재 code003의8계약이 통과했다. code003은fresh3/final3·1.501초·CPU16.73%·cleanup=True다. 각 decoder가5초 미만이더라도 합계가 초과하면 거부하고, active 작업·중복/비신선 budget·owner 변경을 거부하며 원 guard 실패가 먼저 발생하는 조건을 확인했다.

공유 계수와 실제 parent Frame factory 연결점을 포함한 connection003은110.817초·4계약·scope2,964/Rust787·metadata fresh479/final479·물리140,359,045바이트·CPU57.27%·가용RAM45.186%·cleanup=True로 통과했다. metadata56개·113decode·mappedphysical93,455,827/semantic303,651,939바이트이며 실제 공유 작업은1.395초/5초다. metadata budget만 등록되고 Frame budget은 미등록·Frame 생성0이다. 실제 private parent가 참조하는 동일 Frame factory에 hook을 연결한 것을 확인했지만 실제 Native 실행·Frame 전후 읽기·원체커·승인 검증은 아니다. source25개 현재 hash와 최종 확인이 일치한다.

다음은 이 연결을 실제 새 Native 진입점에 채택하고 모든 새 source/fixture/qualification을 실제 입력에 포함한 뒤, 원64 helper·16KiB wire·600초 및720초·공유decoder5초·GO/Job·원 전후 읽기 조건을 유지해 제품·독립 원체커·승인을 검증하는 것이다. 원 메타데이터 physical/semantic 계수와 새 공유 budget 증거를 후속 원체커에서 확인하기 전에는 승인하지 않는다. 공식157/249·잔여92·next164·generation52, P09/A12/A13 OPEN 및 목표ACTIVE다. 사례164 제품·Native·독립 리뷰·승인 및 프리즈 근본 해결은 미완료다.

근거: lossless-metadata-connection-run004-attempt001..003 및 shared-metadata-frame-decoder-code001..003. 기존 v3/v2, 승인163, 원본 및003/004 중단 증거는 변경하거나 삭제하지 않았다. 새 구현은 lossless_metadata_connection_v1, shared_metadata_frame_decoder_budget_v1과 해당 시험 파일이다.

## 무손실 metadata의 실제 실행 진입점 채택

current_queue_successor_lossless_runtime_v4는 고정된 v3/v2 및 연결·reader·공유 budget 소스를 명시적 private namespace로 읽어 원 함수 본문과 기존 전체 원체커를 유지한다. 실제 parent template의 초기 BuildReader에 무손실 연결을 적용하고 같은 parent Frame factory에 공유5초 budget hook을 연결한다. 원 metadata binding 뒤56개 전체 semantic pin을 확인한다. 원 전체 validate_candidate가 먼저 통과한 뒤 독립 manifest의56개 descriptor를 기준으로 추가 accounting을 검사한다. 새 source와 기존 component qualification은 실제 reader 입력과 최종 hash에 포함된다. 원본·기존 실행/승인 소스와 공유 builtin을 수정하거나 default module을 숨기지 않는다.

추가 원체커는 독립 descriptor와 actual semantic read counts에서 물리/복원 bytes를 다시 계산하고 cache=False, 모든 mapping, 성공 decode 횟수를 확인한다. metadata와 Frame의 원 work 계수가 shared evidence와 일치해야 하고 Frame은2×56회의 decode를 유지해야 한다. active/error/owner/resource 정책과 합산5초를 확인하며 metadata bytes를 Frame-only evidence로 바꾸지 않는다. 6개 계약은 잘못된 물리 계수·누락 mapping·계수 변조·Frame 미등록·시간 불일치·합산 초과를 거부하고 private import map과 원 function code를 보존하는 것을 확인했다.

초기 adoption001/002와 CODE005-001·preflight005-001은 통과했지만 entry005-001에서 private alias의 globals 이름을 원 helper와 같은 이름으로 덮은 TypeError가 발생했다. Frame·제품 실행 전 종료했고 cleanup=True이며 실패를 보존했다. 원 globals가 해당 function을 가리키는 경우에만 그 이름을 바꾸도록 수정하고3인자 alias/4인자 helper 회귀 검사를 같은6계약에 추가했다. 준비 기록은 이전005.v2를 덮어쓰지 않고005.v4 경로로 분리했다. 고정 v2 graph path projector의 suffix 상수1개만 metadata로 바꿨으며 전체 AST inverse를 확인했다. 전송 내용은 동일한8,071바이트의 기존 v2 wire다.

현재 adoption003은6계약·fresh29/final29·4.023초·CPU32.94%·cleanup=True로 통과했다. graph005.v4는56pair·fresh57/final57·12.159초·CPU33.64%로 통과했고 factory004는GO 없는 원11계약·fresh43/final43·13.741초·CPU32.17%·cleanup=True다. CODE005-002는74계약·fresh115/final115·15.572초·CPU34.74%·cleanup=True다. 전체 preflight005-002는 입력2,957/Rust787/helper60·fresh444/final444·122.133초·CPU57.95%·cleanup=True로 통과했다.

entry005-002는 원6계약·actualNative helper64·fresh448/final448·125.665초·CPU55.70%·가용RAM44.156%·cleanup=True로 통과했다. 원 예상 비용596.192초/600초이며 실제 Native 발행 전과 종료 후 source448개 현재 hash가 모두 일치했다. 원16KiB·64helper·CPU/RAM·GO/Job·600초/720초·전후2회 및 공유decoder5초 조건을 유지했다.

Native005는7.62초에 metadata CPU 경고로 중단됐다. actual 초기 reader의 explicit_fresh_lossless_metadata 기록이 확인됐으나 mapped read/decode 시도는0회였다. metadata 실제117읽기·2,501,662바이트, 마지막시스템CPU82.26%·parentCPU0%·private49.637MiB·가용RAM43.373%다. worker/제품/Frame 생성0·delta0·cleanup=True·빈 소유 tree를 확인했다. 압축 원본 및 decoder 작업을 시작하기 전의 경고이므로 이 실행으로 IO 절감·공유 Frame budget 또는 프리즈 해결을 입증하지 않는다. 원CPU 경고를 무시하거나 동일005를 반복 실행하지 않았다.

실제 독립 원체커/승인 연결은 구현됐지만 Native 후보가 없어 미실행이다. 다음은 이 초기 보호 중단의 깨끗한 prebody 조건을 유지한 새 실행 준비와, 실제 Frame 전후 읽기·기존 및 추가 원체커·승인 검증이다. CODE/preflight 및 component 검증은 같은 소스에서 유지한다. 공식157/249·잔여92·next164·generation52, P09/A12/A13 OPEN 및 목표ACTIVE이며 제품·Frame·독립 리뷰·승인은 미완료다.

근거: lossless-v4-adoption-code001..003, successor-connections005.v2/v4, factory003/004, successor-code/preflight-run005-attempt001/002, dispatch-qualification-run005-attempt001/002 및 current-runtime-run005. 구현은 current_queue_successor_lossless_runtime_v4와 해당 시험 파일이다.

## 속도 병목과 사례164 공식 승인

사례164가 공식 승인됐고 현재158/249·잔여91·next165·generation53이다. P09/A12/A13은 OPEN이고 목표는 ACTIVE다. 사례165 STEP은fresh9/final9·CPU54.04%·가용RAM45.564%·cleanup=True로 준비됐으며 아직 제품·Native·승인을 실행하지 않았다.

전체 Native006은558.86초지만 제품 GO부터 완전 수집은2.101초로 약0.376%다. 전체Frame의2,963입력 고정과 전후 실제읽기, 누적 증거·현재 source 검증이 지연의 대부분이다. Binding001의196.324초 중 원본/envelope 읽기88.993초·최종읽기96.250초가94.35%다. CPU 경고 중단도 재준비 비용을 추가한다. 보호 기준이나 원Fresh/Final 검사 삭제는 속도 개선 수단으로 사용하지 않는다.

실제 Native metadata는 봉인된 preflight와 entry에서 독립적으로 선언한 논리원본17개를 모두 읽었으며 요청18회 모두 fresh 물리읽기와 decode를 수행했다. mapped physical20,058,350바이트로semantic58,350,277바이트를 복원했으므로 해당 변환 대상의 물리읽기량은38,291,927바이트·65.62% 감소했다. 전체 metadata physical44,345,826바이트와 분리한 계수다. 전체Frame56개는 전후112decode로 유지됐고 metadata0.295초+Frame1.463초=공유1.758초/5초다. 제품1PASS·Frame COMMITTED·두 실제경계·cleanup 및 빈 소유tree를 확인했다. 이는 IO 절감의 실측이며 전체 검증시간 감소의 인과 증명은 아니다.

후속 review001은 metadata에도전체Frame56개를 요구해 ALL_DECLARED_METADATA_MAPPINGS로 거부됐다. 원 dispatch의 outer binding이 compose_parent의 추가56개 metadata pin wrapper를 대체하므로 이 wrapper는 실제 실행되지 않았다. 실제 요청17개는 모두 변환됐고 실행 전 봉인된 두 선언과 정확히 일치했다. lossless_metadata_scope_review_v1은 원Native/v4소스를 수정하지 않고 후속 독립검사에서 단 하나의 metadata 이름비교를 두 선언의 정확한 집합으로 구분한다. 원전체체커와 나머지 v4 계수·전체Frame56·전후112·hash·공유5초·owner/resource 조건을 그대로 유지하며 전체 AST inverse를 확인한다. 누락·추가 metadata, 선언 불일치, 잘못된 pin/바이트/계수,Frame 축소 및 budget 위반을 거부하는9계약과 원 workspace15계약이 통과했다. 새 소스는 post-Native 증거이며 실행입력에 소급 넣지 않는다.

review002는 전체체커 통과 후 최종읽기79.202초에CPU82.90% 경고로 중단됐다. 후속 reader의64KiB 반복할당을 기존 reusable workspace로 연결했다. 원MRO/open/stat/checkpoint/pacing/parse/hash/final읽기는 유지한다. review003은fresh453/final453·127.644초·CPU37.38%·가용RAM47.227%·cleanup=True로 통과했다. 실제 workspace1개·65,536바이트·leases474/returns474·readinto2,236회·90,215,317바이트를 전체체커 이후 계수 시점에 확인했고 최종읽기도 완료했다. 성공 표본만으로 버퍼가CPU경고를 해결했다고 단정하지 않는다.

승인001은84.53% 경고로 중단됐지만 parentCPU0%·private47.465MiB·가용RAM46.266%·commit38.758%·cleanup=True·delta0였다. 승인reader는 이미 reusable workspace와 요청당 single fresh stat을 사용하고 있었으므로 동일 최적화를 중복 적용하지 않았다. 원1/2MiB pacing·20open/s·no-burst·0.5초 표본 재사용과 정리를 점검했다. 낮아진 별도CPU15.26/18.52% 표본 후 승인002만 재시도했으며 제품·Native·독립 리뷰를 재실행하지 않았다. CPU 상승의 외부 프로세스 원인은 미확정이고 OS설정·외부 프로세스를 변경하지 않았다.

승인002는248.685초·fresh1,259/final1,259·2,540읽기·233,216,086바이트·CPU59.33%·가용RAM44.728%·resource cleanup=True로 canonical을 단 한 번 발행했다. before157·delta1·after158이며 제품/Native 재실행0이다. 실패 기록과 원본을 보존했다. 같은소스에서 통과한 준비·제품을 반복하지 않고 실패한 후속 단계만 진행하는 방식으로 운영한다. 일반화된 metadata 연결에도 sealed metadata와 fullFrame 집합을 처음부터 분리해야 하며, 사례164 전용 review 연결을 다른 epoch에 무검증 재사용하지 않는다.

근거: case164 successor-connections006.v4·factory005·code/preflight/dispatch-qualification-run006-attempt001·current-runtime-run006·whole-review-run006-attempt001..003·optimized-acceptance-attempt001/002·current-epoch-accept001 및 case165 step-config001/selection001. Native root SHA256은3d68ad7f4d6775354cde2f3989a29025d3408330308ca00ed08e4b72ad935959, canonical은461,984바이트·SHA256 3d3c118de9421d8601c9d9dc9e4177c64bdb63d12226a68a0e148452de463382다. PC 프리즈 해결과 전체 검증시간 대폭 단축은 아직 입증되지 않았다.

## 사례165의 봉인된 metadata 연결과 준비 reader 최적화

공식 원장은158/249·잔여91·next165·generation53이며 P09/A12/A13은 OPEN, 목표는 ACTIVE다. 사례165의 원본4개10,434,968바이트를3,343,196바이트로 무손실 표현해7,091,772바이트를 줄였고 원본은 보존했다. Binding001은60pair·fresh147/final147·215.566초·physical2,972입력/230,079,111바이트·CPU70.83%·cleanup=True로 통과했다.

current_queue_sealed_metadata_runtime_v5는 frozen v4와 metadata-scope 독립검사를 명시적 private namespace로 재사용한다. 진입점·시험·새19계약 자격은 실제 reader의 입력과 최종 해시에 포함하고 기존 v4/승인164를 수정하지 않는다. frozen component 자격은 현재 해시를 모두 다시 확인하며 새 V5 계약 자격을 대신하지 않는다. 준비 전용 실패 재시도는 graph/capsule/bootstrap의 suffix3개만 실제 v4 경로로 연결하고 전체 AST inverse와 기존 Native의 완전 closed-prebody 분기를 유지한다. source-code001은19계약·fresh34/final34·4.625초·CPU58.74%·cleanup=True다.

graph002는60pair·wire8,603바이트·fresh63/final63·13.213초, factory001은GO 없는 원11계약·fresh49/final49·14.696초로 통과했다. CODE002-001은74계약·helper60·fresh120/final120·16.186초·CPU21.51%로 통과했다. 첫 preflight는79.411초·CPU76.72% 경고로 중단됐다. 준비 workspace의 기존17계약을 다시 확인해 연결했지만 preflight002도69.146초·CPU88.13%로 중단됐다. 부모CPU0%·private46.961MiB였고 실제 workspace1개·64KiB·leases472/returns472·readinto2,191회·87,229,129바이트가 확인돼 버퍼가 미적용된 실패는 아니었다.

준비 reader의 원 source conjunction은 일반 파일에서 is_file/is_symlink/is_junction의 경로 조회3회를 사용했다. 기존 single_snapshot_source_guard_v1의10계약·fresh3/final3·cleanup=True를 확인한 뒤 workspace와 결합했다. 일반 Windows non-reparse 파일은 매 요청마다 fresh no-follow stat1회로 같은 조건을 판정하고 나머지 reparse·unknown·오류는 원 메서드로 돌아간다. 원 open pacing·읽기·hash·전체 final pass·자원검사 및 held Native path guard는 유지한다. preflight003은scope2,980·Rust787·helper61·fresh466/final466·130.382초·CPU48.18%·가용RAM42.205%·cleanup=True로 통과했다. workspace1개·leases939/returns939·readinto4,285회·168,584,382바이트·fresh stat939회/ordinary939/fallback0을 확인했다. 이는 실제 연결 확인이며 CPU 급등 해결의 인과 증명이 아니다.

진입 qualification001은 원6계약 통과 후 최종 읽기74.935초·CPU94.34%에서 중단됐다. 동일 reader 개선을 적용하되 준비 helper를 고정된9656바이트 소스의 private namespace로 명시적으로 구성해 기본 모듈을 삭제하거나 실제 helper 한도를 늘리지 않았다. qualification002는6계약·source2,992·기본helper60/actualNative64·fresh467/final467·133.028초·CPU51.04%·가용RAM43.116%·cleanup=True로 통과했다. 예상 비용597.362초/600초이며 알려지지 않은 지연까지 완료를 보장하지는 않는다.

실제 Native002는248.86초에 입력 고정 포화 보호로 중단됐다. 마지막 시스템CPU9.29→89.19→90.75%, 마지막 parentCPU0%·private50.910MiB·가용RAM40.092%·commit42.103%였다. directory372개와 regular2,341개 등2713핸들은 전부 닫혔고 remaining0·active reader/stream0·별도 pathname재열기0·Frame CLOSED·cleanup 및 빈 소유tree를 확인했다. worker/제품은 생성되지 않았고 실제 바이트 경계 및 Frame decode는0회다. 실제 metadata는 봉인된 pref/entry와 같은18개 논리원본을19회 fresh decode해physical21,882,861바이트로semantic62,957,746바이트를 복원했다. 이 결과는 제품·Native PASS가 아니다.

입력 고정 코드의 조상 중복 제거·같은 pacer·no-burst·14회/s acquisition과 원 identity/cleanup 경로를 재검토했다. open with pacing 총194.671초에는 요청 sleep190.899초가 포함됐으며 inspect metadata 총0.547초였다. busy loop·무제한 fan-out·재열기가 병목이라는 근거는 확인하지 못했다. 직렬 attribution은32query 총0.317초·최대0.0138초였고 포화 순간에는 기존75% 정책으로 optional 조회가 억제돼 unavailable이다. 마지막 가용 표본은 다른 시간 구간이고 coverage incomplete이므로 특정 외부 프로세스나 Defender 원인으로 확정하지 않는다. OS설정과 외부 프로세스를 바꾸지 않았다.

원closed-prebody 검사를 실제 root의 fresh1/final1에 적용해 통과했고 제품 재실행 없이 cleanup=True를 확인했다. 새 graph003은60pair·동일wire8,603바이트·fresh63/final63·13.155초·CPU30.08%·cleanup=True로 준비했다. 다음은 새 번호의 GO 없는 factory·CODE·전체 preflight·entry를 준비하고 기존 중단 기록을 그대로 검증하는 것이다. 원002는 덮어쓰거나 재실행하지 않으며 아직 사례165 후속 독립 리뷰와 승인은 NOT_RUN이다.

근거: case165 lossless-receipts001·successor-binding001/manifest001·sealed-metadata-code001·connections002/003.v4·factory001·CODE002-001·preflight002-001..003·workspace/single-snapshot qualification과 실제 reader 계수·dispatch-qualification002-001/002·current-runtime-run002. root는2,521,689바이트·SHA2562465c110c3c01fd40a90f6d7f0ff0ca40268ea9eab136e5d4071670bc864dc03이다. 프리즈 해결이나 전체 시간 단축은 아직 입증되지 않았다.

## 준비 읽기량 감소와 사례165의 두 번째 Native 중단

준비 preflight는 같은2,983입력·Rust787개 규모에서130.673초/168,632,774바이트에서92.903초/89,264,287바이트로 줄었다. 이번 관측의 시간 감소는28.90%, 물리읽기 감소는79,368,487바이트다. helper와 실행 시점이 다른 비교이므로 모든 검증이나 PC 프리즈가 해결됐다는 의미는 아니다. 최종471개 fresh 해시는 모두 완료했고 CPU48.18%·가용RAM38.922%·cleanup=True였다. 공식158/249·잔여91·next165·generation53과 P09/A12/A13 OPEN 및 목표ACTIVE를 유지한다.

새 preparation_rust_inventory_snapshot_v1은 기존 Rust 목록 snapshot을 준비용 private build에 연결한다. 원 template run 함수의 code/defaults/closure/worker는 유지하며 기본 build 모듈은 변경하지 않는다. 최초 연결은8.252초에 EXACT_ORIGINAL_METHOD_CODE로 거부됐고 실패를 보존했다. 차이는 full-module import symbol을 아는 컴파일과 AST-only 함수 선택의 LOAD_ATTR/PUSH_NULL 호출 준비였다. 실제 함수가 고정된 원본 전체 소스의 컴파일된 함수와 정확히 일치함을 먼저 확인한 다음 같은 원본 AST를 기존 엄격한 projection에 넘긴다. 임의로 유사한 opcode나 변경된 소스를 허용하지 않는다. 실제 Rust 판정1,118회가fresh stat1,118회·file787/directory331·fallback0으로 처리됐다.

run003 preflight001은70.103초·CPU81.44%,004는51.349초·CPU75.47%,005는5.680초·CPU94.06%에서 중단됐다.005는부모CPU0%·private46.496MiB였으며 mapped read/decode0회라 새 무손실 작업 시작 전의 포화다. 별도 설정 검증은fresh15/final15·cleanup=True로 그래프/manifest와 현재 코드 자격을 확인했다. 해당 실패와 초기15/17/22계약 버전 기록을 보존했다. 현재code004는 원 fresh reader8·Rust목록10·새 연결17 등35계약·fresh10/final10·2.021초·CPU18.77%·cleanup=True다.

준비 reader도 기존 fresh_lossless_metadata_reader_v1을 원 reader 계층 아래에 연결한다. 한 preparation reader만 원 DecoderBudget 한 개를 소유하며 매 요청의 실제 물리읽기와 decoder 호출·owner/resource 검사·5초 합산 한도·checkpoint 복원을 유지한다. 기존 snapshot/workspace/자격 witness는 그 위에 쌓고 unmapped 경로는 원 reader를 사용한다. 실제pref006은37회fresh 복원으로physical41,964,355바이트에서semantic121,349,006바이트를 복원했으며 decoder 작업0.518초/5초·error=False·active=False였다. 원본·decoded bytes·JSON·hash 캐시로 최종읽기를 대체하지 않았다. 이 계수는 준비 단계이며 Native Frame decode로 표시하지 않는다.

별도로 원 run_preflight 함수 전체 code/defaults/closure와 import map을 유지한 private json 의존성만 연결했다. ensure_ascii=True/allow_nan=False/indent2의 정확한 최종 profile에서 공백만 없애며 summary/다른 옵션/기본 json 모듈은 변경하지 않는다. 모든 필드·타입·순서·문자열 내부 공백과 오류 전파를 유지한다. 새pref006 파일은1,128,424바이트다. 기존pref003의 공백만 줄인 별도 in-memory 비교는1,392,926→1,152,020바이트·전체 파싱 값 동일이었으며 원본 파일은 수정하지 않았다.

진입003-001은6계약 뒤 ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5로 거부됐다. 한도/60초 margin/decoder5/검사 범위를 줄이지 않고 물리기록 비용을 낮춘 후 진입002는6계약·기본helper60/actualNative64·fresh473/final473·98.005초·CPU52.15%·가용RAM38.688%·cleanup=True로 통과했다. 준비 helper는 고정 source pin을 private namespace로 명시적으로 로드했고 기본 모듈을 숨기지 않았다. 원18개 metadata 선언은 pref/entry에서 일치했다. 비용599.821934초에 실제 qualification99,631바이트와 파일 예약을 추가한 추정599.988378초였고 실제 Native 비용도599.988378초로 확인됐다. 이 계산은 완료 보장이 아니며 원600초 한도를 유지한다.

실제 Native003은입력 고정93.60초에 CPU95.12%로 중단됐다. 직전79.17%·parent0%에서 마지막parent0.191%·private51.719MiB·가용RAM37.338%·commit43.147%였다. directory372개와 regular154개 등526개 핸들은 모두 닫혔고 remaining0·Frame CLOSED·cleanup 및 빈 소유tree를 확인했다. worker/제품/실제byte boundaries는0·delta0이며 후속 독립 리뷰와 승인은 NOT_RUN이다. open with pacing37.727초 중 요청sleep37.132초, inspect0.0186초였고 기존 no-burst와14회/s 고정을 유지했다. CPU 급등을 코드 busy loop 또는 특정 프로세스 원인으로 확정하지 않는다.

원 closed-prebody 검사를 실제root fresh1/final1에 적용해 통과했고 별도 재실행 없이 cleanup=True를 확인했다. root는2,287,325바이트·SHA256c425e8f636f632f5e8faf9f95b4f4edec89f6902a77a01b156620b1c526b733e다. 다음은 누적된 실패 증거까지 포함하는600초 비용과 Native 입력 고정 경로를 점검하는 것이다. 같은 고비용 실행을 즉시 반복하거나 OS설정·외부 프로세스를 변경하지 않는다. 근거는run003 factory002·CODE001·preflight001..006·entry001/002·해당 workspace 계수·preparation-rust-inventory-code001..004 및 current-runtime-run003이다.

## 완전히 종료된 중단 기록의 무손실 표현

누적 중단 증거의 물리 크기가 다음 실행의 준비 및 전체 입력 비용을 늘린다. 별도 closed_prebody_source_alias_v1은 원 판정으로 완전 종료가 확인된 같은 사례의 이전 실행만 정확한 원본 pin에 연결한다. 현재 또는 미래 실행, 제품 통과 기록, body나 worker가 실행된 기록, 불완전 정리 기록은 거부한다. 기존 projection·budget·handle·정리 검사 메서드와 일반 descriptor 판정은 유지한다. 공유 기본 모듈 대신 검증된 private namespace만 연결한다.

현재 code002는14계약·fresh23/final23·3.672초·CPU55.13%·가용RAM40.080%·cleanup=True로 통과했다. producer002는 run002/003 원본4,809,014바이트를2,047,754바이트로 무손실 표현했다. 원본과 최종 복원 바이트를 검사했고 fresh28/final28·10.178초·CPU26.52%·가용RAM40.666%·cleanup=True였다. producer001의 필수 schema 누락은 projection001이 거부했다. 해당 실패를 보존하고 공통 producer_fields와 시험을 수정한 code002/producer002만 후속 검사에 사용했다.

projection002는 기존60pair에 검증된2pair를 연결했다. 봉인된 이전 preflight 선언과 중단 원본의 논리 pin 전체2,985개를 변경 없이 유지하며 물리표현 합계를235,012,330→232,251,070바이트로2,761,260바이트 줄였다. 실제 읽은33개 입력은 모두 최종 fresh 해시를 완료했고15.266초·CPU34.18%·가용RAM41.428%·cleanup=True였다. 이는 선언된 범위의 표현 연결 검사이며 현재 전체 소스 바이트 재검증은 아니다. parent·worker·독립 oracle의 실제 실행 연결과 Native/제품 검증은 NOT_RUN이다.

다음 작업은 이 구성요소를 실제 parent·worker·독립검사에 동일하게 연결하는 것이다. 연결 전 Native004를 반복하지 않는다. 기존 코드 자격과 통과한 결과는 해당 source pin이 유지되는 범위에서 재사용하고, 변경된 연결 및 이후 단계만 검증한다. 공식158/249·잔여91·next165·generation53과 P09/A12/A13 OPEN·목표ACTIVE를 유지한다. 근거는case165-closed-prebody-code001/002·sources001/002·projection001/002이며 원본과 실패 기록은 삭제하거나 덮어쓰지 않았다.

## 중단 기록의 부모 선언과 worker 전송 연결

closed_prebody_worker_connection_v1은 부모의 원 VerifiedPolicy에서만 전송 선언을 생성한다. worker는 그 선언의 사례·이전 실행 번호·정확한 pin·유일한 대응을 확인하되 원본 바이트 검증을 했다고 주장하지 않는다. 원 worker reconstruction 함수의 code/defaults/closure를 유지하며 private binding 의존성만 연결한다. 전송 복원 뒤 모든 선언 항목이 실제 wire에 존재하는지 다시 비교한다. 원본 전체 검사와 독립 리뷰는 실제 실행 승인에 계속 필요하다.

현재 code004는10계약·fresh32/final32·5.739초·CPU24.8%·가용RAM41.054%·cleanup=True로 통과했다. 원본 증거 IO를 금지한 복원, 부모/worker representation 일치, 원 oracle code 유지, 변경된 pin과 wire·중복·미선언 같은 사례·공유 namespace 거부를 확인했다. 초기 code001은 시험의 필수 manifest pin 누락으로 원 검사가 거부했으며 실패를 보존했다. 중간 code002/003도 보존한다.

실제62pair transport001은 구v1 wire16KiB 한도에 걸렸다. 현재 실행 경로가 사용하는 기존 bounded v2를 private source graph에 연결한 뒤 transport002가 통과했다. wire8,887바이트·bootstrap 선언6,064바이트이며16KiB 한도와 전체62개 항목을 유지했다. 실제64개 입력의 final fresh hash를 완료했고17.290초·CPU54.91%·가용RAM40.516%·cleanup=True였다. 부모와 worker의 descriptor 및 representation을 정확히 비교했다.

진단용 확장 manifest는 별도 불변 파일로 발행했지만 실행 capsule/bootstrap은 발행하지 않았다. 전체 현재 소스 바이트 재검증과 실제 parent/worker entry·독립 oracle 연결은 NOT_RUN이다. 이 결과를 Native 또는 제품 통과로 승격하지 않으며 공식158/249는 변하지 않는다. 다음은 실제 entry 연결과 변경 범위 자격·preflight·비용 검증이다. 근거는case165-closed-prebody-worker-code001..004·transport001/002·successor-closed-transport-manifest001/002다.

## 실행 준비 경로의 중단 기록 연결

closed_prebody_runtime_connection_v1은 실제 private runtime의 부모 입력 callback과 worker API 및 동적으로 생성되는 runtime에 같은 연결을 적용한다. 부모 callback은 독립적으로 선언된 producer pin으로 원본을 fresh 검증한 뒤 원 전체 입력 callback을 호출한다. worker 선언만으로 부모·독립 리뷰를 허용하지 않는다. 원 worker 복원 및 hint 함수의 code/defaults/closure는 유지하고 원 내부 validator 의존성을 고정했다. 초기 의존성 연결 실패 code001은 보존했고 현재 code002는8계약·fresh32/final32·6.938초·CPU23.84%·cleanup=True다.

current_queue_closed_metadata_runtime_v6은 frozen V5 실행 준비를 재사용하고 기존 V5 19계약·worker 10계약·runtime 8계약 및 그 소스 해시를 모든 부모 독자에서 확인한다. 실제 graph004.v4는62pair·fresh97/final97·25.314초·CPU25.44%·가용RAM37.412%·cleanup=True로 통과했다. 실제 확장 manifest와8,871바이트 capsule을 배타적으로 발행했다. 이 준비는 Native 실행이나 전체 비용 자격이 아니다.

factory003은 원11계약 통과 후 같은 사례의 source alias를 거부했다. 원 함수가 독자 생성 전에 binding import를 확정하므로 독자 생성 시의 연결 변경이 실행 중인 함수의 import를 바꾸지 못한 것이 원인이다. 준비 graph와 V6 source는 보존했다. closed_prebody_factory_admission_fix_v1은 import를 먼저 연결하되 실제 독자의 VerifiedPolicy가 생긴 후에만 Binding을 만들며 검사를 생략하지 않는다. factory004는11계약·fresh94/final94·28.829초·CPU38.96%·가용RAM39.290%·cleanup=True로 통과했다. 실제 별도 worker CLI는 GO를 받지 않았고 원 GO 거부를 확인했으며 과거 runtime/authority open은0이었다. 제품 실행도0이다.

CODE run004-attempt001은 원74계약·기본helper60/64·fresh145/final145·29.186초·CPU28.97%·가용RAM39.617%·cleanup=True로 통과했다. 이후145개 소스 pin도 현재 파일과 일치했다. 다음은 기존 준비 IO 최적화를 이 경로에 연결한 whole preflight·진입 비용 자격이다. Native·독립전체리뷰·승인은 아직 NOT_RUN이며 V6은 native/review/accept CLI를 거부한다. 공식158/249·잔여91·next165·generation53 및 P09/A12/A13 OPEN·목표ACTIVE를 유지한다. 근거는closed-prebody-runtime-code001/002·successor-connections004.v4·closed-manifest004·worker-capsule/bootstrap004·factory003/004·code-run004-attempt001이다.

## 준비 IO 연결 후 전체 preflight 결과

closed_prebody_preparation_io_v1은 현재 해시가 일치한 준비35·상태조회10·workspace17 계약 구성요소를 재사용한다. 설정 단계에도 workspace와 fresh no-follow stat을 적용하고, 실제 단계에는 요청마다 물리읽기·복원·5초 decoder·원 Rust 목록 조회와 최종 재해시를 유지한다. 최초 setup001의 빈 pin union 오류와 setup002의CPU79.1% 중단을 보존했다. pref003/005의 KeyError는 원 전체 callback185행에서 찾았다. graph004.v4의 source 목록에 원 STEP 도출 소스가 없었다. pref004의CPU84.96% 중단 당시 parentCPU0.194%·private53.660MiB였으며 원인 프로세스는 확정하지 않는다.

원 graph004.v4와 V6 source는 변경하지 않았다. 원 selection001에 봉인된 STEP 소스·시험을 fresh 검증하고 원 함수로 STEP을 재도출한 connections004.v6와 bootstrap004.v6를 별도 발행했다. 기존 source pin을 모두 유지하고119개 final hash와 cleanup=True를 확인했다. 실제 capsule은 기존 것을 사용한다. graph/bootstrap receipt suffix만 전체 code inverse가 확인되는 metadata projection으로 연결하며 원 callback·입력 판정·물리 바이트·한도 검사는 바꾸지 않는다.

현재 pref004-006은 원10계약·source3,003개·Rust787개·기본helper63·fresh493/final493·109.453초·CPU59.75%·가용RAM26.251%·cleanup=True로 통과했다. 실제1,009읽기/106,274,376바이트였고45회 fresh 무손실 복원은physical50,155,371바이트에서semantic140,585,062바이트를 복원했다. decoder 작업0.950초/5초·완료45/45·비활성·terminal error 없음이다. Rust predicate1,118회는fresh stat1,118회·file787/directory331·fallback0으로 처리됐다. 이전92.903초 표본보다 입력과 증거가 늘었으므로 전체 시간 단축으로 주장하지 않는다.

진입점 qualification001에서는 dynamic wrapper와 실제 dispatch 함수군의 globals가 달라 새 연결이 실행되지 않았다. closed_preparation_private_entry_v1은 실제 함수군에도 동일한 연결을 등록하며 원 main의 code/defaults/closure를 유지한다. 회귀3계약·fresh6/final6·CPU27.94%·가용RAM41.829%·cleanup=True로 검증했다. qualification002..004는 원 실제 helper 한도가 거부했고004의 계측은default61/actual66이었다. 고정 source의 private 의존성, 기존 namespace loader 재사용, private 진입점 실행으로 소스 검증을 유지하며 기본모듈 중복을 줄였다. sys.modules 삭제나 실제 source 제외는 하지 않았다.

qualification005는 원6계약과 helper 한도 및 Rust 목록 검사를 통과한 뒤 전체 비용과 shared decoder5 한도로 거부됐다.65.166초·CPU61.89%·가용RAM40.265%·cleanup=True였고 실제529읽기/64,459,191바이트·fresh497/final0이다. 최종 자격 PASS가 아니다. preflight의 예측599.814초는 진입점 전체 비용을 대신하지 않는다. 다음은 원600초·margin60·decoder5·전체 scope를 유지하고 미매핑 과거 영수증을 추가로 무손실 표현하는 등 물리비용을 줄인 후 자격 단계만 재시도하는 것이다. Native/제품·후속 독립 전체 리뷰·승인은 실행하지 않았다. 공식158/249·잔여91·next165·generation53과 P09/A12/A13 OPEN·목표ACTIVE를 유지한다.

근거는closed-io-preflight setup001..006·실행003..006·graph setup001·connections/bootstrap004.v6·private-family-code001·closed-io-qualify setup/실행001..005 및 successor dispatch qualification004-attempt001..005다. 실패와 원본을 모두 보존했다.

## 추가 과거 영수증의 물리비용 감소

expand_closed_preparation_receipts_v1은 기존 qualified select_extra_receipts와 codec13 및 원 배타적 paced publisher를 재사용한다. 통과한 선언 범위에서 미매핑 과거 영수증6개를 선택했으며 현재 사례·소스·EXE·fixture는 변환하지 않는다. 원본2,756,811바이트를741,340바이트로 표현해2,015,471바이트를 줄였다. 전체 바이트 복원12회와fresh33/final33·9.144초·CPU51.98%·가용RAM27.259%·cleanup=True를 확인했다. 새 파생본6개만 생성했고 원본은 보존했다.

probe_extra_closed_receipts_v1은 생산자의 후보 목록을 기대값으로 신뢰하지 않고 승인된 이전 사례164의 원본 source scope에서6개를 독립 재선정했다. 생산자 현재 source 및 원 codec 자격, 실제 원본·encoded pin, 전체 복원 바이트를 다시 검사했다.68개 대응에 기존 논리 입력3,003개를 모두 유지했고 새 진단 manifest1개만 추가해3,004개가 됐다. 같은 원 complete cost 엔진과167개 inventory reservation을 사용한 선언 범위 예측은599.814→598.008초다. 실제fresh53/final53·25.034초·CPU47.06%·가용RAM39.547%·cleanup=True였고 이후53개 source pin도 현재 파일과 일치했다.

이 비교는 선언된 scope의 projection과 비용 검사이며 현재 전체 source 바이트 재검증이나 실제68pair parent·worker·독립 oracle 연결은 아니다. 실제 진입점 전체 비용·자격·Native/제품/후속 독립 전체 리뷰·승인은 NOT_RUN이다. 예측598.008초를 실제 완료 보장 또는 자격 PASS로 처리하지 않는다. 기존 preflight 통과와 qualification005 비용거부, 원600초·margin60·decoder5·전체 scope는 유지한다. 다음은68pair를 실제 경로에 연결한 뒤 변경 범위와 진입점 비용을 검증하는 것이다. 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·목표ACTIVE를 유지한다.

근거는extra-ordinary-receipts001·extra-ordinary-projection001·successor-extra-probe-manifest001 및 실제6개 p361-lossless-runtime-inputs 파생본이다.

## 실제 68개 연결과 전체 사전 검증

68개 무손실 대응을 실제 private parent·worker 준비 경로에 연결했다. 원 validator·callback·독립 oracle 및 고정 source는 변경하지 않았다. namespace-code003은6계약과fresh6/final6, serialization-code002는4계약과fresh3/final3으로 통과했다. 실제 bootstrap 발행 형식과 기대 직렬화 형식을 맞추되 해당 bootstrap 외 JSON은 바꾸지 않는다. 원 함수의 code/defaults/closure와 전체 역투영 검사를 유지했다. 공유 private 함수군의 실제 globals를 보존해 늦게 연결되는 reader도 같은 worker hint를 확인한다.

graph004.v9는68pair·fresh143/final143·36.184초·CPU50.93%·가용RAM42.265%·cleanup=True로 통과했다. 원 선행 graph의 source pin을 유지하고 추가6개는 승인된 이전 사례164의 scope에서 독립 재선정했다. 실제 manifest와 capsule/bootstrap을 발행했고 두 전송 한도16KiB를 유지했다. 실패시 canonical 성공 graph를 발행하지 않고 별도 진단만 남긴다. v7 manifest suffix 오류와 v8 CPU84.12% 중단 기록을 보존했다.

factory005의 expected bootstrap bytes 오류와006의 private globals 연결 오류도 보존했다. 수정 후 factory007은 원11계약·fresh104/final104·36.456초·CPU56.36%·가용RAM40.407%·cleanup=True다. 실제 별도 worker CLI가 원 GO 부재를 거부했으며 과거 runtime/authority open0, GO 전송0, 제품 실행 허가0이다. 이것은 worker 시작 검사이지 parent 진입 자격이나 Native/제품 통과가 아니다.

원 준비 orchestration이 이전 bootstrap.v4를 읽어 setup007/008이 실패한 원인을 확인했다. 고정 원본은 보존하고 정확히3개 metadata literal만 AST 역투영으로 연결했다. 새 closed-io2 설정 경로는 실패 증거를 덮어쓰지 않는다. 해당 회귀3계약도 원 본문과 전체 AST 역투영을 검사한다. 새 세대 pref007은CPU82.61% 보호 중단이었다. 당시parentCPU0.186%·private48.770MiB·가용RAM40.289%·cleanup=True였으며 원인 프로세스나 프리즈 해결을 주장하지 않는다.

현재 pref004-008은 원10계약·전체source3,016개·Rust787개·기본helper59·fresh516/final516·111.027초·CPU53.04%·가용RAM40.423%·cleanup=True로 통과했다. 실제1,056읽기/108,987,137바이트였고57회 fresh 무손실 복원으로physical51,638,051바이트에서semantic146,098,684바이트를 복원했다. decoder0.904초/5초, 완료57/57, 비활성, terminal error 없음이다. 입력 범위가 늘었으므로 이전 preflight보다 전체가 빨라졌다고 주장하지 않는다.

## 비용상 실패가 확실한 재검증 방지와 압축 표본

whole preflight 예측598.978초는 최종 진입점의 비용이 아니다. check_expanded_entry_cost_floor_v1은 원 complete cost 모델의 baseline을 정확히 재현한 뒤 실제 preflight 결과1,158,296바이트를 추가했다. 그 파일 하나만 더해도 하한600.153630초로 원600초 제한을 넘는다. 자격 영수증과 이후 입력은 아직 포함하지 않았으므로 현재 표현 그대로는 통과할 수 없다. 감사fresh330/final330·42.844초·CPU45.59%·가용RAM40.091%·cleanup=True다. 이는 현재 Python source 모델 재검사이며 전체3,016개 물리 입력의 재검증이 아니다. 결과는DEFERRED이고 실패가 예상되는 full qualification을 다시 실행하지 않았다.

probe_receipt_compression_level6_v1은 기존 encoder의 압축 level1→6 정수 literal 하나만 정확히 투영하고 전체 code 역투영을 확인한다. wire schema·decoder 원본·해시·크기·EOF·64KiB checkpoint·자원 보호는 유지한다. 현재68개 manifest에서 큰 과거 ordinary 영수증3개를 골라 원본과 기존 파생본을 fresh 읽고 전체 원본 바이트를 복원했다. 현재 level1 인코딩이 기존 파생본과 같은지도 확인했고 level6 결과는 각각 기존 decoder로 두 번 완전히 복원했다. 원본과 파생본을 덮어쓰거나 새 압축 파일을 발행하지 않았다.

표본 원본13,672,665바이트의 기존 압축본5,300,577바이트가level6에서4,858,917바이트로 줄었다. 절감441,660바이트(기존 압축본 대비8.33%)다. 세 표본의 encode CPU 합계는level1 0.125초/level6 0.234375초이고level6 두 번씩 복원한 CPU 합계0.140625초다. 전체 실험20.822초·CPU25.19%·가용RAM38.721%·fresh14/final14·cleanup=True로 통과했다. 전체68개 비용·공유 decoder5초 적합성이나 제품 경로 속도 향상은 아직 증명하지 않았다.

지연의 핵심은 여전히 제품 실행 자체보다 직렬 입력 고정·전후 실제 읽기·증거 연결 비용이다. 작은 연결 오류마다 wrapper와 검증 증거를 추가한 작업 방식도 재검증 범위와 준비 부담을 키웠다. 이를 시스템 CPU 폭증의 원인이라고 단정하지 않는다. 동일 소스의 통과 검사는 보존하고, 전체 실행 전에 비용 하한을 검사해 확정 실패 반복을 피하며, 새 증거가 다시 입력비용을 키우는 문제를 포함해 전체 표현을 검증해야 한다. 원600초·margin60·공유decoder5·scope·자원 보호 조건은 완화하지 않는다.

다음은 전체 대응 범위에서 압축효과·전체 바이트 복원·공유 decoder 비용을 검증하고 실제 진입점을 재자격하는 것이다. Native004는 생성되지 않았고 제품·독립 리뷰·승인은 실행하지 않았다. 공식158/249·잔여91·next165·generation53 및 P09/A12/A13 OPEN·목표ACTIVE를 유지한다. PC 프리즈 근본 해결이나 전체 속도 개선 완료는 미입증이다.

근거는expanded-namespace-code001..003·expanded-bootstrap-serialization-code001/002·successor-connections004.v7/v8/v9·successor-expanded68-manifest004.v1·successor-factory005..007·closed-io/closed-io2 setup007/008·closed-io2 실행007/008·successor-preflight004-007/008·expanded-entry-cost-floor001·level6-sample001이다. 실패·원본·기존 승인 source와 사용자 소유 변경을 모두 보존했다.

## 전체 68개 압축본의 순차 준비와 독립 복원

전체68개 원본167,564,011바이트의 새 압축본을 준비했다. 기존 압축본51,971,092바이트에서46,666,900바이트로5,304,192바이트(10.206%) 줄었다. 원본과 기존 압축본은 변경하지 않았고 별도의 `.level6.envelope.v1.json` 파일68개를 배타적으로 발행했다. 새 파일은 현재 실행기의 경로 규칙에 아직 채택되지 않았다.

recompress_preparation_corpus_v1은 최대8개씩9개 배치로 순차 처리한다. 각 배치는 원본과 기존 압축본을 실제 읽고 원본 전체 바이트를 복원한 뒤 level6 결과를 같은 기존 decoder로 두 번 복원한다. 발행된 파일의 실제 hash와 모든 배치 입력의 마지막 fresh hash도 확인한다. 배치마다7개 계약이 통과했고 전체 배치의fresh/final 개수는 같았다. 통과한 배치는 다시 실행하지 않았다. 배치 CPU최고59.82%·가용RAM최저38.708%였으며 자원 보호 중단은 없었다.

첫 시도의 기존 `.failed` 물리파일명 누락 오류는 수정하고 실패 영수증을 보존했다. 다음 배치의 선행 프로세스 종료 확인 전 진입1회는 기존 중복 실행 잠금이 실제 작업 시작 전에 거부했다. 이후에는 실행 핸들의 terminal 결과를 확인하고 다음 배치만 시작했다. 실패를 통과 배치로 계산하거나 기존 파일을 덮어쓰지 않았다.

verify_level6_corpus_v1은 생산자의 목록을 그대로 승인하지 않고 원 graph004.v9의68개 manifest와 각 배치의 순서·범위·원본 descriptor·불변 소스 pin을 비교한다. 누락·중복·미완료·실패 배치 및 바뀐 원본·ordinal·통계를 거부하는6개 계약이 통과했다. 전체 새 압축본을 전후 두 경계에서 실제 다시 읽고 각각 복원해 원 manifest의 원본 크기·SHA256과 일치시켰다. 하나의 기존 DecoderBudget에서136/136회 복원·1.324859초/5초·비활성·오류 없음이며fresh94/final94·52.413초·CPU24.53%·가용RAM40.719%·cleanup=True다. 전체 원본의 동시 current-source freeze나 실제 Native 경계 검증을 대신하지 않는다.

원 complete cost 엔진으로 기존3,016개 physical scope의68개 압축본만 일대일 대체했다. 실제 새 검사 소스·배치 영수증·진단 manifest·이전 preflight 결과까지 포함한3,032개 선언 입력의 모델은596.428080초다. 기존 선언 모델598.977564초를 정확히 재현했고600초 한도·60초 margin·공유decoder5초·Rust inventory 예약167개를 유지했다. 향후 채택 코드와 자격 영수증 및 실제 진입점 전체 범위는 아직 포함하지 않았으므로 이 계산은 실행 허가나 최종 비용 자격이 아니다.10.206%는 압축본 바이트 감소율이지 전체 실행 시간 개선율이 아니다.

다음은 새 물리 경로를 parent·worker·독립 oracle의 동일 private Binding에 연결하고 현재 진입점을 재자격하는 것이다. 기존 canonical 경로·실패 및 같은 사례 closed-prebody 판정은 보존한다. Native004는 없고 제품·후속 독립 리뷰·승인도 실행하지 않았다. 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·목표ACTIVE를 유지한다. OS 설정 변경과 GUI 접근 허용 요청은 없었다.

근거는level6-corpus-batch001-attempt001/002·009-attempt001·017-attempt001/002·025/033/041/049/057/065-attempt001·level6-corpus-manifest001·level6-corpus-verification001 및 새 level6 파생본68개다.

## 일반 과거 영수증의 실제 Binding 연결

level6_ordinary_binding_v1은68개 논리 입력을 모두 유지하면서 일반 과거 영수증61개에 새 압축본을 연결한다. 기존 실패 이력5개와 같은 사례의 closed-prebody2개는 기존 물리 pin 및 원 판정을 그대로 사용한다. 일반 과거 영수증61개의 절감량은4,590,320바이트다. 앞선 전체68개 대체 모델596.428초는 이 연결의 실제 진입점 비용으로 사용하지 않는다.

부모의 mapping admission은 원 코퍼스 자격 영수증과 실제 baseline·신규 manifest 및 검사 소스를 fresh 확인한다. 원 manifest에서61개 대응을 독립 재선정하고 코드에 고정한 전체 대응표 SHA256과 비교한다. private Binding은 원 생성자 전체 본문으로 각 항목과 기존 이력을 먼저 검사하고 새 압축본61개가 포함된 경우 전체68개 및 정확한 대응표 digest를 추가 검사한다. 새 descriptor는 원 판정에 위임하는 검사를 유지하며 명시적 새 경로와 전체 digest를 추가한다. Projection·바이트·자원·oracle 메서드는 바꾸지 않는다. 이 metadata admission은 실제 Native의 전후 물리 바이트 읽기를 대신하지 않는다.

첫 두 코드 검사는 시험 namespace 연결 오류로 실패했고 기록을 보존했다. 수정 후8계약이 통과했지만 실제 transport001/002에서 원 worker가 decoder 생성용으로 먼저1행 Binding을 만드는 구간을 확인했다. 전체 대응표 검사는 이 원 초기화 단계도 거부했다. 관측값은rows1/new_rows1이었으며 압축본 변조나 자원 보호 중단이 아니었다.

원 복원 함수의 정확한 첫 descriptor와 manifest로 만드는 초기화에만1회 scoped seed를 연결했다. 같은 구간의 두 번째 생성과 구간 종료 후에는 전체68개 및61개 digest 검사가 적용된다. 원 constructor를 포함한 초기화 본문은 유지하고 이탈 시 원 full 검사 생성자를 복구한다. 현재 code005의10계약은 원 Binding·Projection 동작, 전체 digest, 바뀐 원본·물리 hash, 부분표, current/failed 새 경로, private namespace, 단일 profile, 정확한 seed·잘못된 seed·미사용·복구를 검사했다. fresh8/final8·2.631초·CPU49.5%·가용RAM40.955%·cleanup=True로 통과했다.

transport003은 실제 private parent Binding으로 원 compact wire를 생성하고 원 worker 복원 함수에서68개 전체를 복원했다. 부모·worker의 모든 descriptor와 원 representation이 같았고 parent·Frame·worker·full oracle이 동일한 private Binding namespace를 사용했다. wire9,687바이트와 bootstrap 선언7,078바이트 모두 기존16KiB 한도 안이다. fresh102/final102·27.882초·CPU51.14%·가용RAM37.537%·cleanup=True로 통과했다. 이102개는 transport 준비 입력이며 전체 현재 runtime source freeze가 아니다. 독립 전체 oracle의 실제 실행도 아직 아니다.

발행한 것은 별도 진단 manifest이며 실행 capsule·bootstrap과 Native004/005는 생성하지 않았다. 다음은 동일 연결을 공통 parent·worker entry와 독립 검증 경로에 등록한 뒤 실제 CODE·whole preflight·진입점 비용·별도 worker 시작을 검증하는 것이다. 제품·GO·후속 전체 리뷰·승인은 실행하지 않았고 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·목표ACTIVE를 유지한다. 원본과 기존 파생본, 실패 기록, 사용자 소유 변경은 보존했다.

근거는level6-binding-code001..005·level6-binding-transport001..003·successor-level6-probe-manifest001..003이다.

## 실제 공통 진입점과 중복 물리 별칭 정규화

level6_closed_preparation_v1을 실제 parent 준비와 별도 worker CLI에 연결했다. 초기 별도 CLI는 공개 복원 함수가 아니라 원 함수군의 이전 복원 함수를 참조해1행 초기화 검사에서 거부됐다. 같은 private 함수군의 참조를 맞춘 뒤 통과했다. 원 준비 IO 설정이 public runtime 대신 transport를 직접 부르는 경우에도 scoped seed를 연결했다. 기존005..007 및008.v9 준비와 실패·과거 source 결과는 보존했다.

현재008.v10 graph는68개 대응·fresh161/final161·37.684초·CPU50.55%·cleanup=True로 통과했다. 원 namespace projector의 전체 코드 역투영을 유지하면서 receipt suffix만v10으로 연결했고 직렬화 기대값도 동일한 새 suffix에 한정했다. 실제 level6-factory005는 원11계약·fresh119/final119·31.402초·CPU32.39%·가용RAM29.925%·cleanup=True다. 별도 worker는 EOF에서 원 WORKER_NOT_AUTHORIZED로 종료했고 과거 runtime/authority open0, GO 전송0, 제품 실행 허가0이다.

실제 비용 거부를 원 predicate에서 관측하고 전체 scope 차이를 보존했다. 원 모델·Binding 거부 조건을 바꾸지 않았고, 기존 예외 관측에만 덧붙였으며 line/opcode tracing을 추가하지 않았다. 실제3,048개 physical pin을 기존 baseline과의 delta로 재구성한 SHA256이 일치했고 원 거부값603.215125초도 정확히 재현됐다. 진단 파일1개의 비용만 제외한 값은603.128736초이며 다른 관측용 import까지 모두 제거한 원 실행 비용이라는 뜻은 아니다.

같은 원본에 대응하는 이전 압축본15개·6,328,475바이트가 새 압축본과 함께 별도 입력으로 남았다. 그중9개·5,587,135바이트는 승인된 prior164의 descriptor이면서 prior bootstrap metadata에도 있었다. 원 inherited_scope는 승인 fresh 입력의 물리 별칭은 원본으로 환산하지만 준비 reader의 snapshot은 그대로 합친다. 표현을 새 압축본으로 바꾸면 current reverse table이 이전 물리 별칭을 인식하지 못해 이9개가 중복 입력이 된다. 현재 준비 산출물인 나머지6개는 승인된 prior 별칭이 아니므로 그대로 보존한다.

prior_preparation_alias_v1은 승인된 이전 descriptor의 정확한 물리 pin만 원본 논리 pin으로 정규화하고 원 semantic_union 본문을 그대로 호출한다. 원본·실제 읽기·해시 검사를 삭제하거나 물리 IO를 논리 IO로 바꾸지 않는다.6계약은 정확한 별칭·변조·논리 충돌·잘못된 source/context·신규 표현·중복·idempotence·private adapter와 나머지 메서드 보존을 검사했다. fresh8/final8·CPU24.02%·cleanup=True로 통과했다. 실제 scope 재생에서도 prior 논리 pin 전부와 기타 입력이 같았고9개만 환산한 모델은597.243960초였다.15개를 전부 제거하는596.108392초 가정은 적용하지 않았다.

사전 검증의 부모 그래프는 worker wire에서 복원되며 그 hint에는 비정형 이력5개만 전달된다. 이 선언만으로 부모 정규화를 허용하지 않는다. 현재 부모 current_input_scope는 승인 파일과 prior runtime을 매번 fresh 읽고 승인 수·next index·root pin·cleanup 및 representation을 확인한 뒤 전체56개 이력으로 해당 private Binding을 보강한다. 이후 snapshot이 다시 합쳐져도 같은 정규화를 거친다. 원 current_input_scope와 모든 기존 검증은 이어서 호출한다.

현재 CODE008-002는 원74계약·기본helper60/64·fresh167/final167·31.051초·CPU44.79%·가용RAM29.447%·cleanup=True로 통과했다. whole preflight008-002도 원10계약·source3,041개·Rust787개·helper60·fresh535/final535·109.446초·CPU39.36%·가용RAM28.270%·cleanup=True다. 실제1,094읽기/106,412,888바이트이며 decoder57/57회·0.763초/5초·비활성·오류 없음이다. 전체 비용 모델597.391502초가 원600초 한도와60초 margin을 유지하며 통과했다. 이전의 선언 범위 추정과 달리 실제 전체 preflight 결과다.

실제 진입점 qualification008-001은 원6계약 뒤 V3_EXACT_CLOSED_GRAPH_FAILURE로 거부됐다.52.292초·CPU44.79%·가용RAM28.706%·cleanup=True이며 최종 자격 통과가 아니다. 기존 previous_stops는 Native가 없을 때 CPU 경고로 실패한 graph와 미생성 worker 산출물만 허용한다.004..007에는 Native 없이 준비만 끝낸 회차가 있어 이 분류에 맞지 않는다. 다음은 없는 Native 기록을 만들지 않고 실제 파일 부재·준비 산출물 hash·NO-GO 종료 증거로 준비 전용 회차를 종결 검증하는 정책을 추가하는 것이다.

007 preflight001/003/004와008-001의 비용 거부 및007-002의CPU85.76% 보호 중단도 보존했다. 해당 CPU 표본에서 parentCPU0%·private56.574MiB·가용RAM34.320%였지만 부하 원인 프로세스는 확정하지 않는다. Native004..008과 제품 실행·GO·후속 독립 전체 리뷰·승인은 없고 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·목표ACTIVE를 유지한다. OS 설정 변경과 접근 허용 요청은 없었다.

근거는level6-entry graph005..008.v9 및008.v10·level6-factory001..005·CODE006-001/007-001/008-001/002·closed-io2 preflight setup/실행006..008·successor-preflight007-001..004/008-001/002·current-cost-diagnostic001..003·known-scope-cost001..006·observed-scope-replay001/002·prior-preparation-alias-code001·closed-io2-qualify008-001 및 successor-dispatch-qualification008-001이다. known-scope-cost002/006의597.007초는 실제 stage reader의 전체 추가 입력을 포함하지 않은 하한이며 실제603초 거부를 대신하지 않는다.

## 준비 회차 분류와 불필요한 선행 import 수정

느린 진행에는 직렬 입력 고정·전후 읽기 비용뿐 아니라 연결 오류마다 보조 실행기와 증거가 늘어 재검증 범위까지 커지는 작업 방식이 영향을 줬다. 준비만 끝낸 회차를 실패 graph로만 분류하는 경로도 정상 준비 산출물을 거부했다. 같은 실패를 전체 재실행으로 확인하는 방식은 줄여야 한다.

prepared_run_closure_v1은 사례165의 준비 전용004~007에만 별도 분류를 적용한다. 실제 Native 파일 부재를 전후 확인하고 준비 graph·capsule·bootstrap 및 생산자 소스의 현재 hash와 EOF에서 원 WORKER_NOT_AUTHORIZED 종료를 검사한다. 실제 Native가 있는 회차와 나머지 실패 graph는 원 previous_stops 본문에 위임한다. 없는 Native 기록을 생성하거나 이전 준비를 제품 PASS로 바꾸지 않는다. 현재 closure-code003의6계약과 회차004~007 attempt002가 통과했다. 각 회차fresh7/final7·과거 runtime/authority worker open0·GO0·제품 실행0·cleanup=True다. 첫 코드 검사 실패와 수정 전 attempt001도 보존했다.

수정 전 CODE008-003은 원74계약·helper62·fresh170/final170·32.436초로 통과했고 whole preflight008-003은 원10계약·source3,044/Rust787·fresh538/final538·111.040초·CPU55.98%·가용RAM27.720%·cleanup=True였다. 그러나 qualification008-002는 실제 Native helper67/64 상한에서 거부됐다. 생산 모드에서만 쓰는 pressure·distinct·publisher를 모든 모드에서 선행 import한 원인을 확인했다. 이3개 import를 생산 모드 안으로 옮기고 회귀 검사에 해당 경계를 추가했다. sys.modules 숨김·삭제나 helper 상한 완화는 없다. 최종 CODE008-004는 원74계약·helper59·fresh170/final170·33.557초·CPU40.19%·가용RAM27.642%·cleanup=True다. helper 감소는 확인했지만 전체 실행 시간 개선율은 아직 입증하지 않았다.

최종 소스 preflight008-004는62.135초·CPU91.79%, 이어 동일 CODE와 준비 산출물을 재사용한008-005는45.102초·CPU96.79%에서 원 보호 조건으로 중단됐다. 두 실행 모두cleanup=True이며 전후 해시 완료나 현재 사전검사 PASS로 계산하지 않는다. 해당 급등 표본의 부모 CPU는 각각전체0.183%/0%, private63.082/62.313MiB였다. 종료 후 PerfProc와 실행 파일·스크립트 이름만 제한적으로 확인했으며 books 검증과 MapleRust 검증의 병행 실행을 관찰했다. 이는 동시 부하 관측이지 급등 순간의 원인 프로세스나 검증이 유발한 외부 부하의 인과 증명은 아니다. 명령행 원문·비밀정보는 출력하지 않았고 외부 프로세스·Defender·OS 설정은 바꾸지 않았다.

그래프008.v10과 기존 worker NO-GO 증거는 소스가 동일하여 다시 만들지 않았고, 통과한 CODE74도 두 번째 CPU 중단 때 재실행하지 않았다. 같은 무거운 사전검사 재시도를 추가하지 않는다. 다음 경계는 현 소스의 사전검사 성공 → 실제 helper 상한과 준비 회차 분류를 포함한 실행 자격 → 미실행165번이며, 준비 분류의 전체 dispatcher 연결까지 통과했다고 주장하지 않는다. 수정 전 preflight PASS를 현재 소스로 승격하지 않는다. Native004~008·제품 실행·후속 독립 리뷰·승인은 미완료이고 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·목표ACTIVE를 유지한다.

근거는prepared-closure-code001..003·prepared-only-closure-run004..007-attempt001/002·successor-code008-003/004·successor-preflight008-003..005와 대응 closed-io2 설정/진단·successor-dispatch-qualification008-002다.

## 실제 이전 이력의 독립 검증과 CPU 관측

직전 턴은 불필요한 선행 import 수정과 CODE 통과를 포함한 진전이었다. 이번에는 생산 소스와 CODE74·그래프·worker 준비 자료를 그대로 재사용했다. 시작 전8초 관측은 CPU최고42.97%·가용RAM최저27.187%였지만 preflight008-006은94.628초/CPU88.53%, 별도 프로세스 관측을 함께한008-007도91.405초/CPU80.79%에서 원 보호 조건으로 중단됐다. 두 실행 모두정리 완료이며 부모의 해당 표본 CPU는0%, private62.008/61.605MiB였다. 006은종료 해시358/538까지만 완료했으므로 성공으로 처리하지 않는다.

검증을 시작하지 않은45.457초 대조 관측90표본의 CPU최고는34.77%였다. 검증 중 별도 관측의 마지막 PerfProc 표본은 MsMpEng13.31%·Explorer9.44%·Codex9.44%·System6.81%·Git5.19%를 기록했다. 관측 창과 조회 지연이 원 Guard와 다르므로 이 값을 중단 시점 CPU의 정확한 분해나 특정 프로세스의 인과 증명으로 사용하지 않는다. 관측 Python 자체의CPU0.172초는 sampling child 및 WMI service의 비용을 포함하지 않는다. 검증이 외부 부하를 유발했을 가능성도 배제하지 않는다. 다른 작업 종료·메시지 전송·OS/Defender 변경은 없었다.

이 저장소의 상태 탐색 비용도 별도로 비교했다. Git2.54.0.windows.1의 untracked-cache 파일시스템 검사는 통과했고,5회 상태 출력과 전후 인덱스 엔트리는 동일했다. baseline 중앙값0.190149초, warm cache0.175783초로 미리 정한20% 및50ms 개선 조건을 충족하지 않아 설정하지 않았다. fsmonitor daemon도 시작하지 않았다. 이 결과는 해당 저장소의 status 비교이며 다른 저장소나 diff 등 모든 Git 작업의 비용을 설명하지 않는다. 캐시 기능과 파일시스템 검사 조건은 [Git 공식 설명](https://git-scm.com/docs/git-update-index#_untracked_cache)을 따랐다.

전체 검사를 반복하는 대신 probe_prepared_run_admission_v1에서 새 분류 경로를 실제 자료로 검증했다. CODE008-004에 고정된 원 v3 retry·v5 suffix projection·v2 Native 판정 전체 본문과 현재 adapter를 같은 private namespace 구조로 실행했다. 원 Native 중단002/003과 준비 전용004~007이 모두 통과했고 Native004~008의 부재도 확인했다. 실제 사용한 direct/private helper와 입력의 fresh45/final45,10.198초·CPU54.3%·가용RAM26.168%·cleanup=True다. 이 검사는 supporting integration test이며 실제 dispatcher 구성·전체 사전검사·Frame·GO·제품·수용을 대체하지 않는다. 생산 진입점이나 새 필수 Gate를 추가하지 않았다.

현 소스의 전체 사전검사 성공 → 실제 dispatcher 재자격 → 미실행165번 경계는 남아 있다. 무거운 동일 재시도는 추가하지 않으며 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·목표ACTIVE를 유지한다. 근거는prepared-closure-live-admission001·resource-attribution-summary001·successor-preflight008-006/007 및 대응 closed-io2 설정/진단이다.

## 역할 메타데이터 충돌 수정과 자원 차단

외부 부하 감소를 새로 관측한 뒤 동일 CODE로 진행한 preflight008-008은source3,044/Rust787/helper59·fresh538/final538·114.539초·CPU62.91%·가용RAM21.595%·cleanup=True로 통과했다. 이어 qual008-003은 원6계약 통과 후 PRODUCER_SOURCE_WITNESSES로 거부됐다. 원 v4.load가 private retry에 설치된 모든 함수의 globals에 SELF/TEST 역할명을 다시 쓰는 구문이 생산자 경로까지 덮어쓴 원인이다. 이전 live001에는 이 원 구문이 포함되지 않았으므로 실제 dispatcher 연결을 증명하지 못했다.

생산자 경로를 CLOSURE_SOURCE/CLOSURE_TEST로 분리하고 일반 역할명만 존재하는 잘못된 inventory를 거부하는 회귀를 추가했다. 현 closure-code004의6계약, prepared-only004~007-attempt003, CODE007-002의74계약이 통과했다. CODE는helper59·fresh170/final170·31.064초·CPU68.64%·cleanup=True다. live002는 CODE007-002에 고정된 원 v4 소스에서 정확한 재바인딩 For 구문 하나를 추출해 실제 실행했고 역할명 변경 발생까지 확인한 뒤 원 Native 중단2건과 준비 전용4건을 검증했다. fresh46/final46·10.182초·CPU34.28%·가용RAM22.299%·cleanup=True다. 원 검사/해시/부재 조건은 완화하지 않았다. 이전 CODE·preflight·live 결과는 해당 이전 소스의 이력으로 보존한다.

8번 회차의 사전검사 번호를 모두 사용했으므로 Native007/008이 실제 없고 기존007.v9/008.v10이 준비만 끝난 상태임을 먼저 확인했다. 기존 자료를 덮어쓰지 않고 아직 없던007.v10 graph/manifest/capsule/bootstrap 경로를 사용했다. predecessor adapter로 graph를 만들려던 첫 시도는 SAME_PUBLIC_AND_ACTUAL_WORKER_RECONSTRUCTION에서 거부됐고 기록을 보존했다. graph/startup에는 predecessor hook이 필요하지 않으므로 원 level6_closed_preparation_v1 진입점을 직접 사용한다. 원 진입점의 graph007-v10-attempt002는68pair·fresh161/final161·37.680초·CPU60.93%·가용RAM18.308%·cleanup=True로 통과했다. adapter의 graph 호출을 통과했다고 주장하지 않는다.

이어 원 진입점의 level6-factory006은5.702초·CPU100%·가용RAM16.614%에서 보호 중단됐다. contracts/root_path는미완료이고cleanup=True이며 Native004~008은 없다. 같은 자원 중단이8ff251d·da1f94e 작업 및 이번 턴의3연속goal턴에서 반복됐다. 수정한 코드의 작은 회귀와 실제 자료 연결은 완료했지만 현 소스 전체 사전검사·실행 자격·제품 경로는 완료하지 못했다. 다른 프로젝트 검증을 중단하도록 요청할 권한도 받지 않았다. 무거운 동일 재시도나 보호 조건 변경 대신 update_goal 결과BLOCKED를 확인했다. 완료/일시정지가 아니며 전체P09~P20 목표 범위는 유지한다.

재개 시 원 level6 진입점으로run007 startup의 다음 미사용 factory 번호를 먼저 검증한다. 이후 현재 prepared_run_closure 소스15411바이트/SHA256 b5e307896acede9ac9f5a4be517a3f4b8986def0ac27d933fe04a3603d852025 및 CODE007-002로 미사용preflight007-005 → qualification007-001 → 아직 실행하지 않은Native007을 순차 진행한다. 어떤 실제 검증도 성공을 가정하지 않으며, 기존007/008 Native가 생겼다면 먼저 상태를 재평가해 재실행을 막는다. 수정 전 preflight008-008을 현 소스 PASS로 재사용하지 않는다. 공식158/249·잔여91·next165·generation53/P09-A12-A13 OPEN·P10미시작을 유지한다.

근거는preflight008-008·qual008-003 및 대응 closed-io2 설정/진단, closure-code004·prepared-only004~007-attempt003·CODE007-002·live-admission002·level6-entry-v10-graph007-attempt001/002·successor-connections007.v10·manifest/capsule/bootstrap007.v10·level6-factory006이다.
