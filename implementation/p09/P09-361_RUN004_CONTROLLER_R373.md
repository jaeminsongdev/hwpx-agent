# P09 새 실행 controller 연결과 사전 검사

공식 승인은153/249, 잔여96개, next160, generation48이다. P09/A12/A13은 OPEN이며 P10은 시작하지 않았다. 새 run004 controller는34쌍 입력을 engine·worker·독립 읽기검사에 연결하고 새 사전검사를 통과했다. 제품 승인과 공식 개수 증가는 아직 없다.

## 연결 수정

case160_run004_controller.py는 원run003 controller를 exact pinned private namespace로 보존하고 새 입력 선언과 단일compact 연결을 함께 연결한다. 새 helper를 일반 import로 누적하거나 sys.modules에서 숨기지 않는다. 원engine/worker 본체, Native600/shared720, wire16384, helper64, 자원·속도·두 실제바이트 경계 조건은 유지한다.

검사 초기화가 이미 설정된 현재사례를 다시 configure하여 실패한 r373 및 run002를 보존했다. 검사 초기화는 기존 설정이160/before153인지 확인하도록 수정했다. run003은 시스템CPU78.77%로 원보호조건이 중단했고 cleanupTrue였다. 이후 단계·자체CPU·메모리 진행 요약을 추가했으며 자동재시도나 보호조건 변경은 없다.

수정후 run004 연결검사는 CODE20, fresh96/final96, helper62, CPU전체41.67%·자체1.6761%, 가용RAM48.1943%, 자체private44.515625MiB, cleanupTrue였다. 실제 preflight040은 Rust 입력의 frozenset과 기존engine의 set 타입 차이로 실패했다. 기존 엄격비교는 유지하고 같은787개 이름을 controller 경계에서 기존 set 타입으로 전달하도록 수정했다.

## 현재 사전 검사

현재 code qualification은 p09-361-case160-run004-controller-r373-run005.v1.json이다. CODE22, fresh96/final96, helper62, CPU전체37.52%·자체1.9188%, 가용RAM43.5065%, cleanupTrue로 통과했다. qualification은 실제제품 실행이나 독립현재160 oracle의 완료를 뜻하지 않는다.

새 DATA041과 preflight041은 이전DATA039/preflight039/run003 준비기록과 구분한다. preflight041은 실제 선언2878개, import64개, fresh275/final275, 74.1465766초, CPU전체45.83%·가용RAM45.2298%, cleanupTrue로 통과했다. 전체 물리비용 모델은2844inputs, 예상runtime597.9405567714145초로 원600초 이하이며 margin60·decoder5·두실제바이트 경계를 유지했다. 이 예상은 완료보장이 아니다.

현재 root004는 기존실패root003과 별도이고 기존결과를 덮어쓰지 않는다. API.prepare는 독립된 선행권위와 fresh parent 선언을 기준으로 원frozen oracle에 연결했으나 실제성공candidate로 아직 검증하지 않았다. API.accept는 그 검증전까지 차단한다. 다음은 단일실제run004, 두Native경계, 독립read-only oracle, 공식승인 순이다. 접근허용·UAC·OS변경·외부종료·삭제이동·원격push는 없고 PCfreeze해결은 미증명이다.
