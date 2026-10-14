# P09 새 입력 선언과 단일 compact 연결

공식 승인은 153/249, 잔여 96개, 다음 사례는 160이며 generation 48이다. P09/A12/A13은 OPEN이다. 실제 저장된 34쌍 manifest와 parent 연결 검사는 통과했지만 새 run004 controller와 제품 실행은 아직 승인되지 않았다.

## 입력 크기 감소

완료된 원 준비 scope의 이전 사례136과130을 원 codec으로 무손실 표현했다. 각각 2461083→647763bytes, 2417619→625375bytes로 총3605564bytes 감소했다. 원본복원4회, fresh20/final20, cleanupTrue이며 원본은 보존했다. 증거는 p09-361-case160-prior136130-producer-r854.v1.json이다.

실제 manifest030은520bytes, compact capsule007은12008bytes로 원16384bytes 한도를 지킨다. 원32쌍을 모두 유지하고136/130을 추가했다. r855 생성검사는 당시소스에서 fresh66/final66, 비용596.710391초였다. 이후 연결수정의 현재소스 증거로 r855를 재사용하지 않는다.

## 중복 연결 수정과 현재 결과

r856은 이미 compact인 worker에 serializer를 다시 연결해 COMPACT_WORKER_CAPSULE_EXACT_ORIGINAL_JSON_FUNCTION으로 실패했다. 실패와 당시코드를 fae6dfa에 보존했다. 수정은 양쪽 encoder/decoder가 정확한 기존 compact interface를 공유할 때 그 interface를 한번만 재사용하며 한쪽만 compact인 상태는 거부한다.

r857은 내부34쌍을 검사했으나 최상위 source_pairs가32로 남았다. 단일 연결 수정과 이 관측을 e66bc4a에 보존했다. 현재 권위 있는 연결 결과는 수정후 r858이다.

r858은 source_pairs34, CODE5, Rust787개, inventory167회, fresh69/final69를 확인했다. bounded bootstrap은 단일Reader의28reads/133296bytes로 원64reads/262144bytes 이하이다. qualifier 포함 선언scope2864·physical2830에서 예상 Native 비용은 decoder5초 포함596.7805788585118초로 원600초 조건과 margin60초를 통과했다. CPU최대45.96%, 가용RAM최소70.2436064%, cleanupTrue, 경과38.8218502초이다. 이번변경4모듈 단위검사18개도 실패·오류·skip없이 통과했다.

## 실제 실행 연결

연결검사는 원run003 완료준비scope를 사용했다. 새run004 자체의 controller·전체 preparation/preflight·독립현재160oracle 및 두실제Native 바이트 경계는 여전히 필요하다. r858은 GO나 제품 승인이 아니다.

다음작업은 작은 보조래퍼를 계속 추가하기보다 실제controller의 준비·실행·결과판정 연결을 한 작업단위로 완성하는 것이다. 변경영향별단위검사와 실행전통합검사를 구분하되 fresh입력·Native경계·자원보호를 약화하지 않는다. 실패증거와 사용자변경은 보존하고 P10으로 넘어가지 않는다.
