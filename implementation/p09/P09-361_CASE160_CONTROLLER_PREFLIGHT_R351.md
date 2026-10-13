# P09 160번 controller와 전체 실행 전 검사

실제160 controller V28, 고정 DATA036 및 전체 preflight036을 연결하고 검증했다. 공식 승인 수는153/249, 잔여 개별 사례는96개이며 다음 실행 대상은160번이다. 이 결과는 실제 제품 실행이나 P09 Gate 완료가 아니다.

## 구현과 기존 검사 보존

기존159 controller의 함수군은 case와 목적지 metadata만 별도 환경에서 변경했다. 역변환이 원래 전체 코드와 동일한지 확인하며 기본값, closure 및 keyword 기본값을 유지한다. 모든 기존·신규 helper 소스는 실제 입력 pin으로 보존한다. 이미 import한 모듈을 숨기거나 helper 상한64개를 늘리지 않는다.

원래 engine과 worker를 실제160 설정, 공통 Binding 및24쌍에 연결했다. bootstrap은 원래 reader 코드를 사용하며64회 읽기와262,144byte 상한을 유지한다. 역사 receipt는 bootstrap에서 읽지 않고 전체 admission에서 검증한다. 독립159 전체 oracle, 원래15초 window의 모든 검사와 metadata 역변환도 유지한다.

## 실패 수정과 controller 검사

첫 r767의16개 검사 중 DATA fixture 함수가159에 남은 오류와 preflight 목적지034·035 연결 차이로 error1개, failure1개가 발생했다. 실패 증거를 보존하고 실제 DATA fixture 함수 및035에서036으로의 metadata 연결을 수정했다.

r768은16개 검사를 모두 통과했다. fresh와 최종 hash 확인은42개가 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은24.8%, 최소 가용 RAM은43.28874%였다. engine·frame·worker dispatch를 실행하지 않은 상태에서 연결을 검사했다.

## 전체 preflight 결과

preflight036은 원래 전체 실행 전 검사를 통과했다. 입력2,765개, 디렉터리372개와 원본 입력310,090,610byte를 확인했고 Rust 소스787개와 실제 helper64개가 포함됐다. fresh와 최종 hash 확인은1,076개가 일치했다.

전체 물리 입력 비용 계산은 입력2,741개, binary28,433,408byte, other220,285,885byte를 포함한다. 전체 예상 실행 비용은596.570556초로600초 상한 안에 들어왔다. 기존60초 여유분, acquisition14회/초, byte/native20회/초, 두 실제 byte pass,15초 capture와 공유 decoder5초 기준을 유지했다. 이 계산은 알 수 없는 OS 지연을 포함한 실제 완료 시간 보장이 아니다.

해당 실행의 시스템 CPU 최대 관측값은36.49%, 최소 가용 RAM은41.27160%이며 cleanup은 true다. 이 결과는 PC 프리즈 해결을 입증하지 않는다.

근거는 `evidence/p09-361-case160-controller-code16-failed-r767.v1.json`, `evidence/p09-361-case160-namespace-controller-code16-r768.v1.json`, `evidence/p09-361-case160-envelope-controller-data036.v1.json` 및 `evidence/p09-361-case160-envelope-controller-preflight036.v1.json`이다.

## 다음 단계와 상태

다음은 단일160 제품 실행과 별도의 전체 oracle 승인이다. 이번 단계에서는 Native·제품 실행, 이전159 실행 반복 및 큐 승인을 수행하지 않았다. P09, A12, A13은 OPEN이며 P10 새 구현은 시작하지 않았다.

기존 권위·성공·실패 증거와 사용자 소유 변경을 보존했다. 접근 허용 창이나 UAC를 호출하지 않았고 OS 설정 변경, 외부 프로세스 종료, 원본 삭제·이동 및 원격 push도 수행하지 않았다.
