# P09-143 — heavy 검증 전 자원 안정 구간 확인

## 범위와 현재 결과

사용자의 CPU/RAM 보호 요구를 위해 heavy build/DB/native 실행과 별개의 읽기 전용 사전 검사 도구를 추가했다. 이 도구는 cargo, Rust 테스트, Docker/DB, 한글, 접근허용 창을 시작하지 않는다. 기존 P143 검사·오류·현재 NOT_RUN 상태를 변경하지 않으며 P09 Gate는 OPEN, product_complete false, 목표 active다.

`tools/p09/check_idle_resource_window.py`는 기존 Windows sampler의 GetSystemTimes/GlobalMemoryStatusEx를 사용한다. 자체 프로세스를 CPU1/BelowNormal로 제한한다. 2초 간격, 최대20초 동안 전체 CPU50% 이하와 available RAM8192MiB 이상이 3회 연속 관찰돼야 `ADMITTED_IDLE_WINDOW_ONLY_NOT_BUILD_OR_PRODUCT`가 된다. 중간 고부하는 연속 횟수를 reset한다. 기존 CPU85%3회/freeRAM4096MiB 중단 조건도 유지하며 start 직전 고부하를 허용하지 않는다. 사전 검사는 미래 무부하나 full hardware clearance를 보장하지 않는다. 기존 build/runtime 보호 장치를 대체하지 않는다.

실제 preflight-r1은 20.12초, 10회 측정 CPU76.79~88.43%, 가용 RAM12813.92~13868.50MiB, 연속 안정0회로 `DEFERRED_RESOURCE_PRESSURE_NO_HEAVY_WORK_STARTED`다. 이번 턴에는 P143 build-r6나 새 DB runtime을 시작하지 않았다. 처음과 후속 프로세스 점검에서 cargo/rustc/form_stored_provider/formula probe가 없었다. Windows formatted CPU와 별도 GetSystemTimes 측정 모두 고부하를 관찰했으나 전체 부하의 원인 또는 Codex 멈춤의 인과관계를 확정하지 않는다.

## 검사와 보존

순수 조건 unittest6: 연속3회 안정, CPU 초과 reset, RAM 부족 reset, 정확한 경계값, 단일 spike의 조기 허용 거부, heavy 실행 코드 부재를 확인했다. 실제 sampler 실행과 분리한 조건 테스트이며 Rust/DB/제품 PASS가 아니다. 출력 receipt는 검증 대상3개 소스의 bytes/SHA256와 실제 samples, 정책, 시작하지 않은 heavy 범위를 담고 exclusive create로 생성한다. 비밀값·전체 로그는 저장하지 않는다.

기존 P143 implementation-progress.v1을 readonly auditor로 다시 대조했으며 unchanged다. 기존 r1 컴파일 실패, r2/r3 역사적 빌드 성공, run01/run02 전체 실패, r4 CPU stop, r5 시작 전 defer, current NoChange fix 미실행을 그대로 보존한다. 새로운 사전 검사로 이 상태를 소급해서 승격하지 않는다.

## 다음 실행 경계

fresh receipt로 사전 검사가 통과한 시점에만 새 suffix P143 제한 빌드를 시작한다. 새 build의 원래 source freeze·whole workspace Rust coverage·기존 EXE 보호·resource guards를 계속 요구한다. 빌드 성공 후에도 CPU/RAM을 확인해 owned SQL22 runtime의 현재 consumer Changed/Unchanged 및 원래 denied route를 검증한다. 자원이 불안정한 동안 heavy 재시도를 반복하지 않는다. native·durable storage·key custody·atomic publication 및 전체 P09 acceptance는 별도 미완료다.
