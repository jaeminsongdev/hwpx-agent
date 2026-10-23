# CROSSREF 제한된 worker와 고정 사례 제어 연결

새 private owner factory와 case ports를 고정8종 controller에 연결하고, 원1% non-killing worker에서
첫 checkpoint 거부·실패 finish·정리까지 실제 왕복했다. 현재 계약24개와 실제 준비 통합1개가 통과했다.
이 경로는 한글을 시작하거나 실물 폴더를 만들지 않는 준비 전용이며 실제 Native 세션과 CROSSREF8종은 NOT_RUN이다.

## 고정 사례 제어와 기록 보존

`crossref-preassigned-controller.ps1`은 원 FixedBatchCore의8사례/16단계 순서와 stop-on-failure를 유지하고
새 사전배정 factory/ports를 호출한다. 원 probe·document/source 관측·producer trace·canonical sidecar
작성 함수를 유지한다. 실패 상태도 private RetainedStates에 보관하며 owner RCW를 외부 결과에 직렬화하지 않는다.
finish는 성공한 전체 callback 흐름에만 returned를 보내고 실패는 failed로 보낸다. callback 반환은
실제 실행·정리·상호참조 의미·Gate 통과 증거가 아니다.

`PreparationWorker`는 원 OwnedHostProcess의1% memory partition·한 코어·BelowNormal·CPU cap과
시작 전 bootstrap 대기/제한값 readback을 재사용한다. 실행 가능한 대상은 새 준비 전용 PowerShell 하나뿐이며
임의 command·subset·Native mode·kill 경로를 추가하지 않았다. 원1% Job은 kill-on-close·time limit·breakaway가 없다.

준비 worker는 adapter와 window/kernel identity bridge를 미리 컴파일하고 원 probe 실행 파일의 읽기 lease와
고정8행 packet을 확인한다. 새 TextReader gate는 첫 응답의 정확한 v2 거부만 통과시키며 성공 응답·
권한 flag·구버전·중복/추가 key·잘못된 순서·4096bytes 초과를 거부한다. 따라서 case의 prepare_slot IO 이전에
중단되고 실패 finish만 왕복한다. 실제 Native 실행을 허용하는 CLI는 이 준비 경로에 없다.

## 종료 시점과 실패 이력

[404](evidence/p09-361-crossref-preassigned-preparation404.v1.json)는 Python 신규12개와 reader 신규8개를
통과했다. 실제 새 worker도 exit0·2요청/응답·probe lease 정리와 owner/실물 폴더/trace0을 반환했지만
원 close가 LIVE_TREE_NO_FORCE_CLOSE로 거부해 전체 FAILED·cleanupFalse를 보존했다.
bootstrap의 종료는 Job 전체가 비었다는 증거가 아니며 이를 성공 정리로 바꾸지 않았다.

새 `DrainedPreparationWorker`는 bootstrap이 종료된 뒤 같은 Job의 active count를 관측해0이 된 후
원 close를 호출한다. 살아 있는 bootstrap은 원래대로 거부하고 handle을 유지한다. 강제 종료·새 worker
재시작·CPU/RAM 보호 완화 없이 관측하며 진단 prefix는 최대8개만 보관한다.

[405](evidence/p09-361-crossref-preassigned-preparation-drain405.v1.json)는 원12/reader8의20개를 보존하고
새 배출 순서4개를 통과했다. 영향받은 실제 준비 worker만1회 재실행해 현재 계약24개와 통합1개를 확인했다.
그 실행에서는 bootstrap 종료 뒤 같은 Job의 active count가1→0으로 변하는 두 표본을 관측했고,
추가 대기는0.047초였다. Job empty·handle closed·IO thread 종료·probe lease closed·stderr0·compiler 잔여0이다.
404는 실패 원본 그대로이며 예전 Native·공식249·398통신·402owner 시험은 반복하지 않았다.

## 실제 자원 관측

405는218fresh/final218·외부 PowerShell image1final·cleanupTrue·전체50.172초다.
실제 준비 worker7.188초·Job CPU1.766초·private최고75.34MiB였고,
1% Job의 private 상한318.5625MiB·동일 한 코어 mask4·BelowNormal·CPU cap6.25%를 읽어 확인했다.
이 Job에는 kill-on-close/time limit/breakaway가 없고 종료 시 active0이었다.
시스템CPU최고62.65%·가용RAM최저31.6489%는 해당 구간 관측이며 PC 프리즈 원인/해결 증거가 아니다.
원 준비 CPU 보호·RAM/commit95%·진단32768bytes/프레임4096bytes와 입력 확인을 유지했다.

## 실제 세션 전에 남은 경계

후속 [세션 자격 프로토콜](P09_CROSSREF_SESSION_QUALIFICATION_PROGRESS.md)은 신규 계약35개와 실제1% worker의
kernel/Job 결속·원 caller Job 거부·정리를 검증했다. 실제 Native constructor는0회다.
다음은 세션 candidate와 고정8종을 동일 외부 호출자에 연결할 Python 진입점과 최종 증거 결속이다.
준비 worker의 통과는 실제 Native7% 생성 시 배정이나 기존 ROT/COM owner·
window 결속·정상 종료를 대신하지 않는다. 원 native guard/backend와 old factory·고정8종 진입점은 그대로다.
실제 세션의 전제와 source를 다시 확인하며 완료된 외부 검사001을 재실행하거나 실행 permit으로 쓰지 않는다.
전체 세션 자격 후에만 승인된 고정8종의 저장/재열기·원본 보존·상호참조 의미 readback을 진행한다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3와 개인정보 카탈로그 저장/제품 연결 미완료를 유지한다.
