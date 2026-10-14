# P09 사례 160 입력 잠금과 실제 worker 진단

공식 상태는 153/249, 잔여 96, next160, generation48이다. P09/A12/A13은 OPEN이며 P10 구현은 시작하지 않았다. 아래 실행은 실제 worker 시작 경로의 비교 진단으로, 공식 Native 후보나 승인 결과를 생성하지 않는다.

## 제품 호출과 잠금 조건 비교

| 증거 | 조건 | 결과 | 전체 시간 | GO 이후 완료 시간 | 시스템 CPU 최대 | 가용 RAM 최소 |
| --- | --- | --- | --- | --- | --- | --- |
| r379 | 실제 controller worker 함수, 마지막 제품 호출 가로채기 | 진단 통과 | 3.07초 | 1.50초 | 16.11% | 30.94% |
| r380 | 실제 CLI, Python 소스와 설정 및 실행 파일 218개 잠금, 실제 사례 160 | 1 passed, 0 failed, 248 filtered out | 63.83초 | 2.50초 | 25.98% | 30.28% |
| r381 run002 | 실제 CLI, 기존 run006 선언의 전체 2,850개 파일 잠금 | 15초 진단 제한 중단 | 150.75초 | 완료 없음 | 45.70% | 28.36% |
| r382 | 실제 CLI, 증거 폴더 선언 파일과 기존 218개 입력의 합집합 1,262개 잠금 | STOP_STRICT_PRODUCT_WINDOW | 93.53초 | 완료 없음 | 60.55% | 51.28% |
| r383 | 증거 폴더 잠금 조건에서 worker 대기 스택 수집 시도 | CPU 경고 보호로 GO 이전 중단 | 9.02초 | GO 없음 | 81.64% | 51.07% |

r380은 기존 검증 실행 파일의 해시를 읽고, 원 CLI의 GO와 Job을 통해 실제 제품 테스트 하나를 실행했다. r381과 r382는 선언된 추가 파일의 크기와 잠금 identity를 확인했지만 전체 선언 파일의 바이트를 새로 해시하지 않았다. 이 진단의 잠금 집합은 전체 Native 바이트 경계 검사를 대신하지 않는다.

전체 입력과 증거 폴더 조건에서는 출력 수신이 0바이트였고, r382의 소유 Job 샘플에는 Python과 conhost만 관측됐다. 샘플 사이의 짧은 제품 실행까지 배제할 수 없으므로 중단 실행의 actual_product_child_executed는 null을 유지한다. 비교 결과는 증거 파일 잠금 조건으로 조사 범위를 좁히지만 특정 파일이나 외부 도구를 원인으로 확정하지 않는다.

## 실패 보존과 정리 수정

r381의 첫 시도는 원장 목록을 잠금 함수가 요구하는 경로별 사전으로 변환하지 않아 P206_LOCK_INPUT_COUNT로 GO 이전 중단됐다. 원 기록을 보존하고 2,850개 항목과 중복 없는 경로를 확인하는 변환을 추가했다.

r381 run002는 cleanup_confirmed=False로 보존했다. 진단 종료 뒤 해당 worker 및 제품 프로세스 잔여는 사후 조회에서 없었다. 진단의 정리 코드를 실제 실행기와 같은 순서로 수정했다. 소유 Job 전체를 먼저 종료하고, pipe reader를 닫은 다음 Job의 active_processes=0과 owned_processes=[]를 확인하며, handle 닫기는 별도 finally에서 수행한다. 수정 후 r382는 cleanup_confirmed=True와 빈 Job을 확인했다.

r383은 Python의 진단용 watchdog에서 5초 시점의 스택을 수집하도록 준비했으나 자원 보호가 먼저 중단해 worker를 시작하지 않았다. 스택과 제품 실행 결과는 없다. 스택 원문이나 전체 로그를 저장하지 않으며, 진단 wrapper와 추가 watchdog을 실제 CLI와 동일한 실행으로 표현하지 않는다.

## 자원 관측과 다음 작업

r383 중단 후 0.75초 간격의 읽기 전용 관측에서 Python 5개가 각각 약 6.29% CPU를 사용했다. 해당 명령 문자열에는 HWPX/P09 경로가 없었고 다른 검토 스크립트 이름이 포함됐다. 중단 당시 CPU 81.64%의 사용 주체를 이 후속 표본으로 확정할 수 없다. 다른 작업의 프로세스나 OS 설정은 변경하지 않았다.

다음 작업은 증거 폴더 잠금 조건에서 worker 대기 위치를 확인하고, 그 코드 경로의 충돌을 수정하는 것이다. 시스템 부하로 중단된 스택 시도는 같은 출력에 자동 재실행하지 않는다. 원 15/600/720초 제한, Job CPU/RAM 제한, 전체 제품 검사 범위와 독립 승인 체커를 유지한다. 기존 run006이나 이미 승인된 사례는 이번 진단으로 재실행하지 않았다.

## 근거 파일

- `implementation/p09/evidence/p09-361-case160-controller-worker-startup-r379.v1.json`
- `implementation/p09/evidence/p09-361-case160-exact-cli-held-product-r380.v1.json`
- `implementation/p09/evidence/p09-361-case160-exact-cli-full-held-product-r381.v1.json`
- `implementation/p09/evidence/p09-361-case160-exact-cli-full-held-product-r381-run002.v1.json`
- `implementation/p09/evidence/p09-361-case160-exact-cli-evidence-held-product-r382.v1.json`
- `implementation/p09/evidence/p09-361-case160-evidence-held-worker-stack-r383.v1.json`

원 제품 및 Native 후보의 상태는 `implementation/p09/evidence/p09-361-case160-current-runtime-run006.v1.json`과 별개다. 진단 통과를 공식 승인으로 승격하지 않았으며 PC 프리즈 해결 여부도 미증명이다.
