# P09 160번 재시도 identity와 부분 실패 역할 검증

160번의 별도run002를 원래 단일 physical 실행 어댑터에 연결하고, 실패한run001을 입력 표현에 포함하기 위한 역할을 검증했다. 공식 승인 수는153/249, 잔여 개별 사례는96개다. 실제 제품 재실행이나 새 실행 자격 판정은 아직 수행하지 않았다.

## 실제 단일 어댑터와 identity

run002 경로, task 및 공개 실행 번호2가 logical qualification run1과 일치하도록 기존 identity 코드를 private 의존성에 연결했다. template의 case metadata 역변환은 원래 전체 코드와 같으며 원래 engine·worker 본문, 기본값과 closure를 보존한다.

r780에서 원래 identity 검사8개와 추가4개가 모두 통과했다. 실제 실행 창 wrapper의7개 함수 안에서 actual adapter state를 캡처한 단일 어댑터1개를 확인했다. 이 어댑터는 원래run_owned와 정확히 같은 private 환경을 사용한다. physical run은2이며 실제 engine·worker 호출은0회다.

fresh와 최종 hash 확인은36개가 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은29.92%, 최소 가용 RAM은47.62325%였다.

## 검증기 연결 오류와 실패 보존

r778과r779는 identity12개가 통과한 뒤 private 환경 검사에서 실패했다. worker나 최외곽 실행 창 wrapper를 원래 실행 어댑터와 직접 비교한 것이 잘못된 검사 대상이었다.16개 이내의 제한된 wrapper 탐색으로 actual state를 캡처한 어댑터를 찾아 원래 engine의 코드와 global identity를 확인하도록 고쳤다.

r781은 기존158 그래프의 extension attribute를160 successor 그래프에도 기대해 실패했다. 실제160의 원래 lineage 객체, 원래 Projection·codec·Binding constructor 코드 및24개 descriptor 전체의 불변 여부를 확인하도록 검증기를 수정했다. 세 실패 기록은 모두 보존했다.

## 부분 실패의 명시적 역할

run001은 제품 캡처 후 전체 소스 확인이 미완료된 실패다. `STOPPED_NOT_ACCEPTED`, `final_source_freeze`, byte 경계1개, 잠금 핸들3,114개 완전 정리 및720초 metadata·600초 Native 기준을 원래 결과와 독립 검토에서 확인했다.

새 역할은 `preserved_same_case_partial_post_product_source_failure_not_accepted_product`다. 기존의 제품 실행 전 실패와 구분하며 승인된 이전 제품으로 승격하지 않는다. 새로운 descriptor는 이 실패의 정확한 원본 pin과 별도 physical 경로에만 적용하며 기존24쌍은 그대로 위임한다.

r782에서 새 역할 검사6개와 실제 메모리상의25쌍 bijection, 두 번의 정확한 복원이 통과했다. 원본4,128,024byte의 표현은1,535,747byte이며 SHA256은 `62f252f09fbe751789b0df6d3d13911ea1d6f617b8244d16331e996ea132d32e`다. 실제 파일은 publish하지 않았고 기존manifest024를25쌍으로 바꾸어 주장하지 않았다.

fresh와 최종 hash 확인은58개가 일치했고 cleanup은 true다. 시스템 CPU 최대 관측값은34.63%, 최소 가용 RAM은48.18468%였다. 이 결과는 실제 Native·제품·프리즈 해결을 입증하지 않는다.

## 다음 실제 실행 조건

실패 envelope를 실제로 publish하고 정확한25쌍 manifest와run002 capsule, controller 및DATA에 검증된 선언 재사용을 연결해야 한다.600초 Native와 전체720초 metadata 비용, 전체 preflight를 확인한 뒤 단일 제품 실행과 독립 승인을 진행한다.

P09, A12, A13은 OPEN이며 P10 새 구현은0이다. 기존 권위153·성공159·실패160과 사용자 소유 변경을 보존했다. 접근 허용·UAC·OS 설정 변경·외부 프로세스 종료·원본 삭제와 이동·원격 push는 수행하지 않았다.

근거는 `evidence/p09-361-case160-run002-identity-template-code12-r780.v1.json`, `evidence/p09-361-case160-partial-role-code6-r782.v1.json`과r778·r779·r781 실패 기록이다.
