# P09 case160 과거 승인 재사용과 run003 준비

과거 lineage 승인 선언의 재사용을 실제 26쌍 전체 Binding에 연결했고, 별도로 run003의 단일 adapter와 두 실패 기록 검토를 확인했다. 큰 과거 증거 3개의 무손실 표현도 준비했다. 새 manifest와 controller 연결 및 제품 실행은 아직 미검증이다. 공식 승인은 153/249, P09, A12, A13 OPEN이며 목표는 ACTIVE다.

## 과거 승인 선언 재사용

현재 및 이전159 검증 경로가 같은 private `runtime_successor_binding_v1`을 공유하는지 확인했다. 원래 admission을 한 번 완전히 실행하고, 동일 reader와 API·failed-role dependency·checkpoint·원장 및 소유 process/thread가 유지되는 동안 과거159 선언만 재사용한다. 원래 원본 검토 함수와 최종 freshness는 유지하며 파일 바이트, runtime JSON 행이나 hash 계산은 캐시하지 않는다.

r817은 기존 failed160 review 재사용에 history 선언 재사용을 추가한 전체 Binding 검사다. 기존 review 연결 계약 22개, 신규 history 계약 12개, 원래 successor 계약 9개를 포함한 43개가 모두 통과했다. 원래 history 승인 1회와 중복 선언 재사용 1회, 원래 failed160 검토 1회와 중복 선언 재사용 2회를 확인했다. 검증 후 원래 두 함수는 복원했다.

Rust 입력 787개와 26쌍을 유지했고 fresh 및 final 1,128개와 cleanup을 확인했다. 최종 검사 전 읽기는 337,075,843바이트, 반복 읽기는 158,476,959바이트였다. 시스템 CPU 최고 37.55%, 사용 가능 RAM 최저 51.52322%였다. 진단 SELF와 입력이 이전 r815와 달라 전체 읽기량 차이를 동일 runtime 성능 개선율로 환산하지 않는다.

## 새 실행 identity

`reviewed_case160_attempt_v2.py`는 기존 run001과 run002를 덮어쓰지 않고 run003의 root, task, public run을 명시한다. 원래 template과 단일 engine adapter를 사용하며 실행 번호 관련 metadata projection은 원래 code로 역변환되는지 확인한다. 실제 관측 row나 기존 결과는 변경하지 않는다.

r818에서 기존 identity 계약 12개와 신규8개, 합계20개를 통과했다. 실제 원래 template을 구성하고 물리 실행 번호3의 adapter가 정확히 하나이며 원래 worker body와 engine globals를 유지하는지 확인했다. 원본 run001 및 run002와 해당 review를 직접 검사했고 run003 root는 없었다. engine 및 worker 호출은 0회다. fresh 및 final56개, cleanup 확인, 시스템 CPU 최고20.25%, 사용 가능 RAM 최저52.87543%였다. 새 제품 실행이나 GO를 승인한 결과는 아니다.

## Native 입력 표현 준비

기존 비용 진단에서 선택된 case133, case138, case137 원본이 실제 이전159 semantic scope에 포함되는지 확인하고 원래 CODE13 writer로 별도 표현을 생성했다. 각각 두 번 원본 바이트로 복원했고 원래 2MiB/s와 exclusive write 및 최종 freshness를 유지했다. 원본 삭제나 덮어쓰기는 없다.

| 원본 사례 | 원본 바이트 | 표현 바이트 |
| --- | ---: | ---: |
| 133 | 2,495,913 | 640,755 |
| 138 | 2,483,235 | 648,571 |
| 137 | 2,473,244 | 646,707 |

r819의 표현 차이는 합계5,516,359바이트다. decode6회, fresh 및 final27개, cleanup 확인, 시스템 CPU 최고35.23%, 사용 가능 RAM 최저51.54273%였다. 이 표현을 새 manifest나 제품 controller에 채택한 상태가 아니므로 실제 시간 절감이나 전체 비용 통과로 해석하지 않는다.

## 다음 실행 경계

run003 identity와 두 재사용 연결, 새 표현을 실제 manifest·capsule·controller DATA에 연결한다. 원래 16KiB capsule, import 및 helper 상한과 source scope를 유지하고, bootstrap 및 Native 작업을 포함한 공유720초와 Native600초 비용을 확인해야 한다. 전체 preflight를 통과한 뒤에만 단일 제품 실행과 두 Native 읽기 및 독립 승인을 진행한다. 원래 속도·시간 제한과 자원 보호를 완화하지 않는다.

권위153, 성공159, 실패160 두 회와 사용자 변경은 보존한다. P10 구현, 접근 허용, UAC, OS 설정 변경, 외부 프로세스 종료, 삭제·이동 및 원격 push는 수행하지 않았다. 컴퓨터 프리즈 해결은 입증되지 않았다.
