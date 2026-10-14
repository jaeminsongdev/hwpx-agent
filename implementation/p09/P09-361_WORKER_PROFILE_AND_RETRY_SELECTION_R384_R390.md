# P09 사례 160 worker 계측과 검증 시도 선택

공식 상태는 153/249, 잔여 96, next160, generation48이며 P09/A12/A13은 OPEN이다. 기존 run006과 실패 기록을 보존하고 별도 run007을 준비했다. 현재 실행기는 검증 시도 선택 기능을 추가한 뒤 전체 계약 검증을 기다리고 있으며, run007 제품 및 Native 실행은 시작하지 않았다.

## 초기화 스택과 CPU 측정

r384는 증거 폴더 입력을 잠근 조건에서 15초 제한 중단을 재현했다. 5초 시점의 스택은 과거 검증기의 candidate_connection 재귀 복제 위치였고, 소유 Job CPU 시간은 최종 약 1.19초였다. 이 위치만으로 해당 함수가 병목이라고 확정할 수 없다.

실제 worker의 후속 계측 r387에서 candidate_connection은 6회 호출, 최대 깊이 6, 약 0.144ms로 끝났다. 후속 스택은 run_case112_current_stored의 제품 subprocess 호출 대기 위치에 도달했고 GO부터 완전 출력 수집까지 5.509초였다. 진단 watchdog의 stderr가 있어 원 terminal 조건을 충족하지 못했고 결과는 실패로 보존했다. 제품 종료 코드와 통과 요약을 독립 증거로 저장하지 않았으므로 제품 PASS로 승격하지 않는다.

원 Job 한도를 바꾸지 않은 CPU 전용 진단은 다음과 같다. 제품·SQL·Native를 실행하지 않았고 두 실행 모두 정리와 빈 Job을 확인했다.

| 진단 | 요청 CPU 작업 | 측정 CPU 시간 | 작업 벽시계 시간 | Job CPU rate | 단일 코어 mask |
| --- | --- | --- | --- | --- | --- |
| r385 | 0.1초 | 0.109375초 | 0.110150초 | 625 | 1 |
| r386 | 0.8초 | 0.812500초 | 0.820547초 | 625 | 1 |

Windows Job CPU rate는 스케줄링 주기에 사용할 수 있는 사이클 비율이며, 중첩 Job에서는 부모 할당량의 영향을 받는다. [Microsoft CPU rate 문서](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information). 이번 부모 연결 Job 조회의 rate flags는 0이었고 위 실제 작업은 약 한 코어의 처리율을 보였다. 초기화가 항상 10배 이상 제한된다는 가설은 이 측정에서 재현되지 않았다.

r385의 최초 구현에는 출력 수집 전 결과 분기를 잘못 배치한 UnboundLocalError가 있었다. GO 이전 실패와 사후 잔여 없음 관측을 별도 기록하고 분기 위치를 수정했다. 최초 실패에는 정상 cleanup receipt가 없으므로 후속 정상 측정으로 대체하지 않는다.

## 별도 run007과 반복 비용 수정

run007은 보존된 run006의 함수 본문·기본값·closure를 유지하고 실행 identity와 출력 위치만 명시적으로 투영했다. 이전 초기 qualified 입력 읽기와 독립 체커도 유지한다. 보존된 소스의 초기화에서 읽은 run006 config·manifest·capsule도 새 Native 선언에서 숨기지 않도록 포함했다.

r388의 초기 연결 검증은 기존 27개 계약, fresh106/final106, helper62, cleanup=True로 통과했다. 이 소스 버전의 전체 사전 검증 preflight045는 CPU 75.95% 경고로 중단됐다. 이후 시도 선택 기능을 추가했으므로 r388은 현재 소스의 승인이 아니다.

현재 기능은 다음 제한 안에서 출력 위치를 선택한다. 기존 검증 함수 본문과 시간·자원·입력 범위는 그대로이며 자동 재시도는 하지 않는다.

- `--qualification-attempt`: 정수 1부터 8까지. CODE와 DATA 출력 쌍을 함께 선택한다. 기본은 r390과 data047이다.
- `--preflight-attempt`: 정수 2부터 8까지. preflight046부터 preflight052까지 선택한다.
- 출력은 기존 exclusive writer를 사용한다. 실패 파일을 덮어쓰지 않으며 이미 있는 출력에 같은 시도를 반복하지 않는다.
- 같은 소스 버전에서 연결 검증이 통과한 뒤 사전 검증만 중단됐다면 CODE를 다시 실행하지 않고 새 사전 검증 번호를 선택할 수 있다. 소스 또는 관련 입력이 바뀌었으면 새 검증이 필요하다.

기존 27개 계약에 선택 범위·함수 본문 역투영·실제 globals와 API identity를 확인하는 4개 계약을 추가해 총 31개로 구성했다. 두 파일의 문법 검사와 4개 추가 테스트 본문 존재 확인은 통과했지만, 31개 계약 실행은 아직 NOT_RUN이다.

## 자원 경계와 다음 실행

시도 선택 기능을 처음 추가한 r389 검증은 resource_admission에서 가용 RAM 3.877%로 중단됐다. 계약 실행과 제품·Native 시작 이전이며 cleanup=True다. 현재 코드가 요구하는 r390/data047은 아직 생성되지 않았고 제품 실행 조건을 충족하지 않는다.

사후 읽기 전용 표본은 가용 RAM 약 1.24GiB, committed26.21GiB, cache13.34GiB, nonpaged pool2.30GiB, paged pool1.46GiB였다. 마지막 표본은 가용 RAM 1.51GiB/4.86%였다. 캐시와 풀의 사용 주체 또는 이 작업의 누수는 확정하지 않았으며, 해당 P09 검증의 잔여 Python 프로세스는 없었다. OS 설정이나 외부 프로세스는 변경하지 않았다.

다음은 기존 자원 시작 조건을 충족할 때 현재 31개 연결 계약을 한 번 실행하고, 통과한 CODE/DATA를 유지한 채 전체 사전 검증을 수행하는 것이다. 그 뒤에만 새 run007의 실제 두 Native 바이트 경계·제품 경로·독립 결과 검사와 공식 승인 연결을 진행한다. 기존 15/600/720초, Job CPU/RAM 보호, 전체 검사 범위를 유지한다.

근거는 evidence의 r384 worker stack, r385/r386 CPU budget, r387 worker profile, r388 CODE 및 preflight045, r389 resource stop과 case160_run007_controller 및 해당 테스트 소스다. 목표는 ACTIVE이고 PC 프리즈 해결이나 P09 Gate 완료는 주장하지 않는다.
