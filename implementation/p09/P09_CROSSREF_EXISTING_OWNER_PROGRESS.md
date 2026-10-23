# CROSSREF 기존 COM 객체 연결부

새 private C# adapter는 이미 실행 중인 한글 ROT 객체를 정확한 사전배정 프로세스에 연결하기 위한
기반이다. 실제 x86 컴파일과 모의20·현재 worker kernel1·결과 parser3을 검증했다.
아직 실제 ROT/한글 COM에 접속하지 않았고 기존 owner factory나 고정8종 실행 경로를 바꾸지 않았다.

## 객체 선택과 정체성

`crossref-existing-owner.cs`의 Attach는 x86/STA를 요구한다. ROT를 최대256개까지 완전히 열거하고
이름은 최대1024문자로 제한한다.110 후보군의 숫자 suffix는 첫 객체/고정1이라고 가정하지 않는다.
이름은 후보 분류일 뿐이며 정확한 PID·100ns 생성 시각·세션·고정 실행 파일·실제 창 PID·버전
11.0.0.9136을 확인한다. 선택 후 같은 객체를 다시 읽어 창과 정체성이 같은지도 대조한다.

후보 없음·중복·불완전/초과 열거·없어진 GetObject 결과·정체성 변경은 거부한다. 새 ProgID instance,
moniker BindToObject, process launch·늦은 Job 배정·문서 action·Quit으로 fallback하지 않는다.
비대상 이름의 객체는 GetObject로 가져오지 않는다. 조회 handle은 query/synchronize 권한만 사용한다.
ROT/moniker/후보 RCW·kernel handle은 각 보유 범위에 맞춰 정리하며 COM 참조 해제는 프로세스 종료 요청이 아니다.

반환 lease와 descriptor는 데이터/참조 소유권이며 Native 실행 허가가 아니다. 원 사전배정 backend의
같은 handle/window/fresh image 최종 검증과 자격 있는 worker/host가 별도로 필요하다.
110 이름 분류는 현재 exact build의 실제 ROT 동작을 검증한 것으로 표시하지 않는다.

Microsoft의 [GetObject 계약](https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject)은
ROT에 등록돼 실행 중인 객체를 조회하는 의미를 제공한다. 한컴의
[기존 객체 연결 예](https://forum.developer.hancom.com/t/topic/564)는 구현 참고이며 현재 환경의 Native 자격은 아니다.

## 컴파일과 시험

별도 `ModelsAndSelfOnly` 시험 worker에서 production adapter와 모델을 같은 assembly로 실제 컴파일했다.
worker는 Attach/NativeCatalog/ROT/한글 COM을 호출하지 않는다.20개 모델은 후보 분류·상한·유일성·
완전 열거·PID/세션/생성시각1tick/image/version/window 거부·선택 전후 변경·정확한256/초과257·
GetObject 없음·정리 실패·입력·비대상 객체 미조회·lease 단1회 해제를 확인한다.
추가1개는 현재 x86 worker의 실제 kernel PID/session/birth/image를 두 번 읽고 이를 한글 소유자로
승격하지 못함을 확인한다.21개 결과가 모두 실제 수집됐으며 ignored는 없다.

[394](evidence/p09-361-crossref-existing-owner394.v1.json)는 주석의 BindToObject 언급을 금지 호출로 오인해
worker/시험0·12fresh/final12·cleanupTrue로 중단됐다. 원 driver의 invalid escape SyntaxWarning도
보존했고 실행하지 않는 과거 driver를 고쳐 증거를 덮지 않았다.
[395](evidence/p09-361-crossref-existing-owner-recovery395.v1.json)는 C# 원문을 바꾸지 않고 호출 구문만 검사했다.
컴파일/worker exit0·21성공 요약·stderr0이었으나 CRLF parser가 개별 결과를0개 수집해 전체 FAILED를 유지했다.

LF/CRLF parser만 분리한 [396](evidence/p09-361-crossref-existing-owner-capture396.v1.json)은 parser3과
영향받은 readonly worker의21개 실제 결과가 모두 통과했다. 같은 C# production/시험 본문은 변경하지 않았다.
변경된 결과 수집기 검증 때문에 이 작은 worker를1회 반복했고 원 Native·공식249·기존 scope20은 반복하지 않았다.
193fresh/final193·외부 shell1final·cleanupTrue·전체27.610초·worker1.188초·Job CPU0.969초·
private최고67.20MiB·시스템CPU최고22.39%·가용RAM최저29.3230%다. Job active0/empty/handle closed와
compiler 임시 잔여0을 확인했다. 원 한 코어·BelowNormal·CPU cap6.25%·readonly Job private8%/stop7%·
RAM/commit95%와 입력 확인을 유지했다. 실제 Native Job7%/worker1% 통합 자격이나 프리즈 해결 증거가 아니다.

## 다음 통합

[사전배정 소유자 통신](P09_CROSSREF_PREASSIGNED_HOST_PROGRESS.md)은 원 세션 scope의 descriptor를
새 private v2로 전달하고 canonical pending owner를 대조한다.398에서 신규 Python16·PowerShell8·실제 파이프1,
8사례/152메시지/16모의 owner admission이 통과했다. 실제 ROT/한글은 실행하지 않았고 원 adapter는 그대로다.
후속 [사전배정 객체 factory와 종료 경로](P09_CROSSREF_PREASSIGNED_OWNER_PROGRESS.md)는 lease의 RCW와 원
FinalRelease가 중복되지 않는 정리·canonical identity·불명 owner 보존을 명시적 successor에 구현했다.
402는 현재 고유21개=이전8보존+이번13pass이며 실제 ROT/COM/한글은 미실행이다. 다음은 제한된 worker와
고정8종 controller에 이 successor를 연결하고 실제 세션 자격을 확인하는 것이다. 이어서
원 owner 검사·canonical kernel identity·source/producer/cleanup 증거를 보존하는 명시적 successor factory와
고정8종의 전체 경로를 통합·자격 검증한다. 그 뒤에만 실제 세션과 저장/재열기·의미 readback으로 진행한다.
외부 검사001은 완료된 호출의 관측이며 새 실행 허가가 아니고 재실행하지 않는다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3와 개인정보 카탈로그 저장/제품 연결 미완료를 유지한다.
