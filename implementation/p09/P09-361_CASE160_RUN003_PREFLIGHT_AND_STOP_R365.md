# P09 case160 run003 전체 preflight와 시간 중단

새29쌍 전체 Binding 및 DATA039의 전체 preflight를 통과하고 단일 run003 제품 실행을 진행했다. 제품 본문은 실행됐지만 최종 source freeze에서 공유720초 제한으로 중단돼 공식 승인을 늘리지 않는다. 공식153/249와 P09, A12, A13 OPEN, 목표ACTIVE를 유지한다.

## 전체 입력과 preflight

현재 자원을 확인한 뒤 보강한 단일 r825 검증을 실행했다. 실제29쌍과 이전 전체 oracle, 원Rust787, 두 선언 재사용, bounded21 입력 및 원64 reads/262144 bytes 상한을 유지했다. 계약43개, fresh 및 final1140개와 cleanup을 확인했고 원래600초 조건의 예상 비용은595.566609초였다. 시스템 CPU 최고60.8%, 부모 CPU 최고6.10316%, 사용 가능 RAM 최저50.14707%였다. 이전r823-r824 보호 중단 기록은 그대로 보존한다.

검증된 실제 source pin으로 DATA039를 고정했다. 전체 preflight039는 실제 import64개, fresh 및 final1139개, cleanup을 통과했다. 새 전체 범위의 예상 비용은599.529630초였고 시스템 CPU 최고51.47%, 사용 가능 RAM 최저51.14017%였다. 제품 및 Native 실행과 큐 증가는 없었다. 이를 `ea68187`에 먼저 커밋했다.

## 단일 run003 결과

case160 run003는 `FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE`으로720.02초에 중단됐다. 단계는 `final_source_freeze`였으며 제품 본문 및 실제 자식 실행이 관측됐다. GO부터 전체 capture까지1.731614초였지만 두 Native 읽기 중 하나만 완료돼 frame은 CLOSED다. 전체 제품 PASS, Native qualification이나 큐 승인을 부여하지 않는다.

실제 표현 입력은2801개,247714063바이트였고 핸들3173개가 모두 닫혔다. cleanup과 owned tree empty가 확인됐다. 시스템 CPU 최고62.81%, 사용 가능 RAM 최저49.35424%, 부모 CPU 최고5.61745%, 부모 private memory 최고78.88672MiB였다. 이번 중단은 CPU 보호가 아니라 시간 제한이었다.

입력 준비는343697750바이트를1262회 읽었고 file-open pacing 대기는47.31457초였다. Native 핸들 확보의 원래 reserve에는227.11640초가 쓰였으며 CreateFileW 자체 합계는0.33225초였다. 원래 Native600초 비용 통과만으로 bootstrap까지 포함한 공유720초 완료가 보장되지 않는다. 원본이나 속도·시간 제한을 완화하는 대신 큰 증거의 중복 승인 경로를 추가 검토해야 한다.

## 큰 증거 호출 지점

r831은 제품과 Native를 재실행하지 않고 실제 DATA039 및 preflight039를 승인하는 전체 Binding에서 과거 case158 run005와 case159 run001의 호출 경로를 집계했다. 두 경로에 대해서만 최대7단계 함수 위치와64개 이하 집계 entry를 보관하고 payload나 전체 로그는 기록하지 않는다.

fresh 및 final1141개와 cleanup을 통과했다. 최종 검사 전 읽기는343292792바이트였다. 시스템 CPU 최고56.81%, 부모 CPU 최고6.25255%, 사용 가능 RAM 최저50.06922%였다. 진단SELF가 실제 runtime 입력에 추가되므로 동일 runtime 성능율로 계산하지 않는다.

각 큰 증거는5회씩 읽혔다. case159는 successor context admission, manifest declaration, manifest 원본 fresh 검사, 원래 binding의 이전 row 읽기, 이전 전체 oracle의 frozen prepare로 나뉜다. case158은 과거 lineage admission, 이전 manifest admission 및fresh 검사, 현재 manifest fresh 검사, 이전 oracle의 inherited scope 읽기로 나뉜다. 실제 코드 위치는 r831의 bounded stack을 근거로 한다. 서로 다른 검증 목적을 단순 hash 또는 JSON 캐시로 대체하지 않는다.

## 다음 실행 경계

이번 호출 경로를 기준으로 같은 reader에서 동일한 승인 결과를 이미 확보한 중복 경로를 검토하고, 최초 전체 oracle과 최종 freshness 및 두 Native 읽기를 유지하는 연결을 검증한다. run003를 덮어쓰거나 자동 재실행하지 않는다. 새 제품 실행은 독립 identity와 변경 범위의 전체 비용 및 preflight가 준비된 뒤에만 진행한다.

권위153, 성공159, 실패160 run001·run002·run003와 사용자 변경은 보존한다. P10 새 구현, 접근 허용, UAC, OS 설정 변경, 외부 프로세스 종료, 삭제·이동 및 원격 push는 하지 않았다. PC 프리즈 해결은 입증되지 않았다.
