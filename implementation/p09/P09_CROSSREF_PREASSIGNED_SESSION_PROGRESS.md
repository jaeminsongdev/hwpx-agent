# CROSSREF 사전배정 세션 연결

사용자가 외부 터미널에서 완료한 검사001은 실제 jobless 호출자와 고정 실행 파일·빈 자원 Job 설정을
확인했다. 새 private 세션 scope는 이를 실제 실행 허가로 바꾸지 않고, 기존 사전배정 backend를
고정8종의 저장·재열기 순서에 연결한다. 현재 결과는 연결 코드의 모의 검증이며 Native 실행은 NOT_RUN이다.

## 외부 검사001 독립 대조

[원 영수증](evidence/p09-361-external-crossref-host-inspection-run001.v1.json)의 SHA256은
`a9598c11a234b96a602ac9d075c8af151a518e7ab2ba40d53fcab6ea93c068c7`이다. 원 전제5개·실제 jobless·
kernel PID/100ns birth/session/image 앞뒤 동일성·빈 두 Job 정리가 통과했다.200fresh/final200과
외부 Python/한글 image 각각1final·cleanupTrue이며, 한글·COM·자식·문서는 실행하지 않았다.
현재 코드/입력200개를 독립 대조했지만 완료된 외부 프로세스를 지금도 살아 있는 검증 호스트로
판정하지 않는다. 실제 세션은 같은 조건과 source를 다시 검증해야 한다. 검사001은 재실행하지 않는다.

## 새 세션 scope

`crossref_preassigned_session_scope.py`는 원16단계·8사례의 순서를 고정한다. 저장/재열기마다
원 `PreassignedNativeStartup`이 생성 시 제한 Job을 배정하고 suspended handle·image·birth·session을
확인한 뒤 단1회 resume한다. worker가 사용할 descriptor는 해당 현재 프로세스의 데이터이며
COM pointer·실행 permit이 아니다. pending owner 상태에서는 다음 제품 단계로 넘어가지 못한다.

owner 결속은 원 `bind_owner`가 이미 배정된 같은 process handle과 실제 window PID·정확한 birth/session,
현재 source와 제한값을 대조한다. COM을 먼저 만들고 나중에 Job에 배정하는 경로를 추가하지 않았다.
이전 세션은 실제 종료·빈 tree가 확인된 뒤에만 다음 세션을 만든다. 종료된 프로세스에 먼저 live
관측을 시도하지 않도록 retire 순서를 분리했다.16개 세션의 kernel lifetime 재사용도 거부한다.

생성/재개/결속 실패나 불명 상태는 stop을 고정하고 같은 backend와 handle을 보존한다. 시작·resume·
binding·finish를 자동 반복하지 않는다. 정리는 guard STOP 뒤에도 원 close 경계로 도달할 수 있지만,
살아 있는 owner를 강제 종료하거나 다른 COM 객체에 Quit을 호출하지 않는다.

## 검증 결과

[392](evidence/p09-361-crossref-preassigned-scope392.v1.json)는 신규 모의20개가 통과했다.
전체8사례·16개 nonoverlap 수명, 단계·admission 순서, pending 차단, 생성/재개/결속 실패·불명 보존,
살아 있는 이전 owner 차단, 종료된 owner의 관측 순서, 수명 재사용·잘못된 PID 거부, stop 후 정리와
조기 성공/중복 finish 거부를 확인했다. 실제 preparation guard도 Native constructor 전에 거부했다.

205fresh/final205·cleanupTrue·36.547초·시스템CPU최고58.01%·가용RAM최저23.4633%다.
원 한 코어·BelowNormal·준비 CPU 보호·RAM/commit95%와 입력 확인을 유지했다. 실제 Native guard는
완화하지 않았다. 원 backend·고정8종·기존 실패·개인정보 구현·공식249는 재실행하거나 바꾸지 않았다.
이 결과는 실제 Native startup/COM binding이나 PC 프리즈 해결 증거가 아니다.

## 실제 실행 전에 남은 연결

한컴의 개발자 답변은 ROT에서 이미 실행 중인 HwpObject를 가져오는 예를 제공한다.
2022 예시와 별도 사용자의2020 이름 변경 경험을 현재 exact2020 build의 검증으로 보지는 않는다.
ROT 이름·창 수를 process identity로 추정하지 않고 원 kernel/window 결속이 필요하다.
[한컴의 기존 객체 연결 예](https://forum.developer.hancom.com/t/topic/564)와
[객체와 프로세스 및 창 수의 구분](https://forum.developer.hancom.com/t/rot/1701)을 참고한다.

Microsoft의 `IRunningObjectTable::GetObject`는 등록돼 실행 중인 객체의 포인터를 조회한다.
새 instance 생성으로 fallback하지 않고 정확한 원 프로세스에 연결하는 worker를 구현·자격 검증해야 한다.
[Microsoft GetObject 계약](https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject).

후속 [기존 객체 연결부](P09_CROSSREF_EXISTING_OWNER_PROGRESS.md)는 x86 C# 컴파일·모의20·현재 worker kernel1과
parser3을 검증했지만 실제 ROT/한글 COM은 조회하지 않았다. [새 private v2 통신](P09_CROSSREF_PREASSIGNED_HOST_PROGRESS.md)은
398에서 Python16·PowerShell8·실제 파이프1과8사례/152메시지/16모의 admission을 통과했다.
다음은 기존 객체 lease의 참조 소유권/정리와 worker1% 자원 Job·owner factory의
전체 통합과 실제 세션 자격이다. 그 뒤 승인된 고정8종의 저장·재열기·원본 보존·의미 readback을
독립 검증한다. 이 scope 자체에는 CLI·COM 생성·문서 실행·새 원격 route가 없다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3와 개인정보 카탈로그 저장/제품 연결 미완료를 유지한다.
