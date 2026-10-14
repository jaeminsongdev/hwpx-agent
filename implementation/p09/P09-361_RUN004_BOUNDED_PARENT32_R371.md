# P09 새 bounded graph와 parent 입력 승인 연결

2026-10-14 공식 승인은 153/249, 잔여 96개, 다음 사례 160, generation 48이다. P09/A12/A13은 OPEN이고 P10은 시작하지 않았다. 이번 작업은 새 입력 선언·원 bounded reader·parent 전체 manifest 승인 경로의 연결이며 새 controller·runtime·제품 승인을 대신하지 않는다.

## 한 Reader의 bounded32 bootstrap

successor_bounded_graph_bootstrap_v6.py는 원 v5 loader 함수와 Reader 메서드를 유지하고, 새 manifest029·compact capsule006·작은 producer metadata 2개만 허용 목록에 추가한다. 기존 입력과 추가 입력은 같은 Reader의 카운터를 사용한다.

실제 r851은 25 reads/114,588bytes로 원 64 reads/262,144bytes 제한 안이었다. 이 Reader는 historical runtime·review 본문을 읽지 않는다. 작은 metadata 선언만으로 전체 parent 승인이나 fresh Native 검사를 수행했다고 주장하지 않는다.

32개 descriptor와 실제 manifest029·capsule006 byte pin 및 정확한 case160-current-r004-tests를 확인했다. 원 parent access·frame factory·worker raw policy·full oracle은 같은 private binding module을 공유했다. CODE5 검사와 최종 재읽기 34/34가 통과했고, CPU 최대 14.64%, 가용 RAM 최소 63.979013%, cleanup True, 경과 시간 5.329484초였다.

## 전체 parent 승인과 worker 선언 일치

successor_current_binding_v6.py는 독립된 새 private29 graph에서 완료된 원 준비 checkpoint를 무손실 carrier로 읽는다. 원본 byte/hash·전체 scope·현재 권위·원 성공159·compiled Rust 집합을 대조한 뒤 실제 새 manifest loader를 호출한다. 두 실패 runtime·독립 review와 실제 이전132·물리 표현을 fresh 읽기·검토하는 full manifest admission을 유지한다.

별도 bounded32 graph를 구성해 parent와 worker의 모든 descriptor 및 manifest pin이 정확히 같음을 확인한다. 원 predecessor whole oracle을 이 함수에서 다시 실행하지 않으며, 이미 완료된 준비 결과의 의미와 pending Native 조건을 구분한다. 의미 입력 scope를 줄이지 않는다.

실제 r852에서 CODE9 검사, manifest 32쌍, Rust 집합 787개·inventory 요청 167회, 최종 재읽기 64/64가 통과했다. qualifier 포함 선언 scope는 2,861개, physical scope는 2,829개다. CPU 최대 12.64%, 가용 RAM 최소 64.519166%, cleanup True, 경과 시간 33.225383초였다. 제품·worker·Native는 실행하지 않았다. 전체 결합 단위검사 143개도 통과했다.

## 추가 코드 이후 비용 거부

이 parent 연결 단계의 예상 Native 비용은 원 decoder 5초 포함 **600.148056초**로 600초 조건을 충족하지 못했다. 원 margin 60초 및 ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5 검사를 유지했다. 앞선 생성 단계의 599.769495초 통과는 입력이 추가된 이번 경로의 비용 통과가 아니다.

다음은 실제 이전 scope의 추가 미압축 증거를 독립 검토·무손실 표현해 충분한 비용 여유를 확보하는 작업이다. 새 manifest/capsule을 재검증하고 실제 run004 controller·전체 import closure·새 whole preparation/preflight·독립 case160 acceptance 경로를 연결해야 한다. 이후에만 단일 engine 실행, 실제 두 Native 바이트 경계와 독립 제품 oracle을 통해 공식 승인을 진행한다.

원 Native600/shared720·의미 입력 전체·원본·실패·자원 보호·helper/wire 한도·worker GO/Job 본체·사용자 변경은 유지했다. 기존 run003 재실행·접근 허용·UAC·OS 설정·외부 종료·삭제·이동·원격 push는 없었다. 목표는 ACTIVE, PC freeze 해결은 미증명이다.
