# P09 160번 전체 Binding 연결 검증

기본 설정을 160번에 유지한 상태에서 실제 manifest 24쌍과 공통 Binding을 연결하고, 이전159의 전체 oracle을 원래 Binding 검사 경로에 적용했다. 공식 승인 수는 153/249, 잔여 개별 사례는 96개이며 다음 대상은 160번이다.

## 원래 검사 경로의 유지

원래 Binding AST에 독립159 전체 검사 callback을 연결했다. 이미 저장된159 결과와 컴파일된 테스트 목록이 원래 관측값과 일치하는지 확인하며, Rust 소스·컴파일 실행 파일·bootstrap·archive 검사를 유지한다.

manifest는 별도 private159 설정으로 원래159 admission을 수행한 뒤 실제160의 24쌍을 구성한다. 기본160 설정을 임시 교체하지 않는다. parent, frame, worker와 전체 oracle은 동일160 Binding 모듈을 사용한다. 최종 scope는 독립 검사와 원래 소스의 의미 합집합으로 구성하며, 현재 실행에서 관측한 frame으로 기대값을 생성하지 않는다.

## 전체 Binding 검사 결과

r765는 `PASS_ACTUAL160_FULL_BINDING_PRIVATE159_WHOLE_ORACLE_NOT_CONTROLLER_PREFLIGHT_NATIVE_OR_GO`다. 전체 scope 2,757개, Rust 소스 787개 및 24쌍을 연결했다. 입력1,068개의 fresh 및 최종 hash 확인이 모두 일치했고 cleanup은 true다.

동일 reader의 context 선언은 실제 한 번 수행하고 중복 한 번을 회피했다. 파일 내용이나 hash를 캐시하지 않으며 최종 fresh 검사를 유지한다. 시스템 CPU 최대 관측값은41.38%, 최소 가용 RAM은41.40697%, 검사 프로세스의 machine CPU 최대값은5.01211%, private 메모리 최대값은69.64453MiB였다. metadata warning 중단은0회였다. 이는 해당 실행의 관측이며 PC 프리즈 해결을 의미하지 않는다.

근거는 `evidence/p09-361-case160-full-binding-r765.v1.json`이다.

## 남은 실행 조건

전체 Binding 통과는 실제160 controller, DATA, 전체 import inventory와 실행 비용, preflight를 대신하지 않는다. 다음 단계에서 이 조건을 검증한 뒤 단일160 제품 실행과 독립 승인을 수행한다. 이번 검사에서는 Native나 제품을 실행하지 않았고 이전159 실행도 반복하지 않았다.

P09, A12, A13은 OPEN이며 P10 새 구현은0이다. 기존 권위·성공·실패 증거와 사용자 소유 변경을 보존했다. 접근 허용 창, UAC, OS 설정 변경, 외부 프로세스 종료, 원본 삭제·이동 및 원격 push는 수행하지 않았다.
