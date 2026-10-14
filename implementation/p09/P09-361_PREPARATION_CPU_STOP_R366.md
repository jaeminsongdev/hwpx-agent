# P09 입력 준비 검증과 자원 보호 결과

2026-10-14 현재 공식 승인은 153/249이며, 잔여 96개, 다음 사례 160, generation 48이다. P09/A12/A13은 OPEN이고 P10 구현은 시작하지 않았다. 입력 준비 결과는 제품 실행이나 Native 검증을 대신하지 않는다.

## 커밋과 입력 준비 경로

요청 후 먼저 `0f17bf2`에 직전 미커밋 P09 파일 2개를 커밋했다. 단위검사 10개가 통과했다. P08/P17/공유 Rust 및 다른 사용자 변경은 포함하지 않았다.

입력 준비 exporter는 전체 선행 oracle과 reader의 최종 재읽기가 완료된 경우에만 metadata를 반환한다. 이번에 최종 재읽기한 입력과 scope에 선언만 된 입력을 구분하고, projection 과정에서 입력 원장·scope·최종 검사 개수가 바뀌면 거부하도록 보강했다. 보강 후 단위검사 17개가 통과했다. Native 두 번의 실제 바이트 읽기, 새 실행 identity 및 독립 제품 oracle은 별도 검증 조건으로 남는다.

## 준비 검증 중단

`p09-361-case160-prepared-input-checkpoint-r833.v1.json`은 단 한 차례의 전체 metadata 준비 시도가 CPU 보호로 중단된 기록이다. 상태는 `FAILED_PREPARATION_NOT_ACCEPTED`, 오류는 `STOP_TERMINAL_METADATA_WARNING_BEFORE_MORE_WORK`, 승인 증가는 0이다. 제품·Native·GO 실행은 없었고, cleanup은 완료됐다.

| 기록 | 값 |
| --- | ---: |
| 경과 시간 | 254.305557초 |
| PC 전체 CPU 최대 | 95.83% |
| 검증 프로세스 CPU 최대 | 6.256602% |
| 가용 RAM 최소 | 10.575223% |
| 검증 프로세스 private RAM 최대 | 72.210938MiB |

한 코어 affinity와 BelowNormal 우선순위, 원 CPU/RAM 보호·읽기 속도 제한을 유지했다. 전체 CPU와 프로세스 CPU의 최대치는 같은 시점이라는 보장이 없다. 중단 이후의 별도 관측에서도 ChatGPT·MsMpEng·node 등이 부하를 보였지만, 그 관측만으로 중단 당시의 원인이나 검증과의 인과관계를 확정하지 않는다. PC freeze 해결은 미증명이다.

실패 증거와 당시 exporter·producer는 `a8023db`에 보존했다. 증거 SHA-256은 `9cd8df3ef9cbab837723aa186330d322b46f06787e9d60a728214b7466231dea`이다. 당시 producer의 6490bytes/SHA-256은 `016a68cef3f451a321af49335b0e30e3cff562c9ff88226d14e845533ec3220d`이다.

## 중단 이후 보강과 다음 조건

중단 위치를 재검토할 수 있도록 producer에 단계 이름과 기존 reader의 완료 카운터만 기록하는 terminal progress를 연결했다. 추가 파일 읽기, sampler, 재시도 없이 최종 검사 도중의 부분 완료도 구분한다. exporter 17개와 terminal progress 9개, 합계 26개 단위검사가 통과했다. 보강된 producer의 실제 전체 실행은 아직 검증하지 않았다.

다음 출력은 별도 `r834` 경로를 사용하며 기존 실패 증거를 덮어쓰지 않는다. 입력 준비 결과의 실제 생성·scope 일치 확인 후에만 새 실행 identity와 runtime handoff를 검토한다. 기존 Native 600초/shared metadata 720초, 전체 입력 scope, 두 실제 바이트 경계 및 독립 oracle을 완화하지 않는다. 목표는 ACTIVE이며 이번 중단을 제품 PASS나 목표 완료로 처리하지 않는다.
