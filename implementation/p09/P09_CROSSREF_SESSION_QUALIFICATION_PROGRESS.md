# CROSSREF 세션 자격 프로토콜과 실제 worker 결속

외부 jobless 생성자에서 원 Native backend를 호출할 private 세션 프로토콜과 worker 진입점을 구현했다.
새 계약35개와 실제1% worker의 kernel/Job 결속·현재 상위 Job 거부 경로를 검증했다.
실제 한글 생성·ROT/COM 연결·Native 세션 자격·고정8종은 아직 NOT_RUN이다.

## 현재 worker와 Native 소유자 구분

`SessionWorker`는 원 native guard와1% non-killing envelope를 요구하고 고정 qualification worker만 실행한다.
임의 command·다른 source root·재시작·force kill을 받지 않는다. 준비 전용 CPU 정책을 실제 Native guard로
대체하지 않는다. 원 waiting bootstrap과 시작 전 Job/affinity/priority 제한값 확인도 유지한다.

`WorkerKernelLease`는 실제 worker의 query/synchronize 권한 handle을 보유한다. 그 handle의 PID·정확한
100ns 생성 시각·현재 session·고정 x86 PowerShell image·현재1% Job 소속·한 코어/BelowNormal과
실행 파일의 fresh hash를 대조한다. 같은 PID의 다른 수명이나 문자열 descriptor만으로 결속하지 않는다.
살아 있는 worker의 query handle을 버리지 않고, worker가 끝난 뒤 한 번 닫는다.

`SessionQualifier`는 ready→admit_owner→closed의 한 수명만 허용한다. 정확한 worker 결속 뒤 원
jobless caller 조건을 확인하고, 그 뒤에만 원 PreassignedNativeStartup의 생성 시 Job 배정·suspended 검증·
단1회 resume을 호출한다. 반환된 원 process handle과 canonical kernel identity/window를 결속한다.
worker의 Close/Quit 주장만으로 통과하지 않고 같은 Native handle의 실제 종료와 Job empty를 확인한 뒤
원 close를 호출한다. 실패/불명은 같은 backend/handle을 보존하고 시작·resume·bind·finish를 반복하지 않는다.

protocol reply의 실행 허가와 Native qualification flag는 항상 false다. 모의 성공이나 완료된 lifecycle
candidate는 final source/image/runtime closure 및 독립 수용을 대신하지 않는다.

## 문서 작업 없는 qualification worker

`run-crossref-session-qualification-worker.ps1`은 x86 adapter와 window/kernel bridge를 미리 준비하고
자신의 실제 kernel identity를 호스트에 보낸다. 호스트가 반환한 현재 descriptor로 기존 객체만 연결하며
원 P58/CIM predicate와 별도 canonical identity를 함께 보존한다. qualification에서는 RegisterModule·Visible·
문서 Open/Save·삽입·실물 폴더/trace 생성을 하지 않는다. 검증된 owner의 Close(false)/Quit와 참조 정리만 한다.

이 파일은 private worker 진입점이며 직접 실행하지 않는다. 외부 사용자가 실행할 전체 Python 진입점은
후속 [전체 진입점 현황](P09_CROSSREF_QUALIFIED_ENTRY_PROGRESS.md)에 연결됐고 구현 준비 검증을 완료했다.

## 계약과 실제 거부 경로 검증

[407](evidence/p09-361-crossref-session-qualification-code407.v1.json)은 Python25개와 x86 통신/source10개의
새35개가 통과했다. 순서·중복·추가 key·자료형·정확한 birth/session/image·wrong worker role·query 권한·
상위 Job 거부 이전 Native constructor0·생성/resume/결속 실패·live native/query handle 보존·
정상/실패 finish·source/descriptor가 권한으로 승격되지 않음을 확인했다.
206fresh/final206·외부 shell1final·cleanupTrue·41.610초·시스템CPU최고36.91%·가용RAM최저28.3468%다.

[408](evidence/p09-361-crossref-session-ready-denial408.v1.json)은 같은 코드의 실제1% worker를 실행했다.
실제 kernel PID/birth/session/image와 정확한 Job 소속·fresh 실행 파일이 일치했다. 그 뒤 원 caller Job
검사가 PARENT_LIFECYCLE_NOT_NATIVE_SAFE로 거부했고 실패 finish까지2메시지를 왕복했다.
검증용 Native constructor trap은 설치됐지만 호출0회였으며 실제 Native backend도 생성하지 않았다.

worker exit2는 기대한 거부 결과이며 Native 세션 성공으로 바꾸지 않았다. COM owner 미관측·문서0·
정리 주장 false/remaining-1도 그대로 보존한다. 반면 worker의 query handle·process/Job·IO thread는
실제 종료·empty·closed를 확인했다. 기존35개나 공식249·이전 Native/통신/owner 시험은 반복하지 않았다.

408은209fresh/final209·외부 shell1final·cleanupTrue·30.234초다. worker1.938초·Job CPU1.547초·
private최고72.04MiB·시스템CPU최고24.65%·가용RAM최저30.1071%·compiler 임시 잔여0이다.
원 한 코어·BelowNormal·CPU cap6.25%·worker1%·no kill/time/breakaway·Native guard·RAM/commit95%와
입력/진단 상한을 유지했다. 실제 한글 자격이나 PC 프리즈 해결의 증거가 아니다.

## 다음 실행 경계

후속 Python 진입점은 이 세션 candidate와 고정8종 controller를 동일한 외부 jobless 호출자에 연결한다.
411의 Python42·PowerShell10pass, 실제 공개 preflight의 원 caller Job 거부,412의 실제 worker 첫 요청 거부와
413의234fresh/final234 입력 대조를 완료했다. 다음은 사용자가 [외부 실행 안내](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)의
전체 진입점을1회 실행하는 것이다. 실제 호출의 Native7% 사전배정·ROT/COM/window 결속·정상 종료·
fresh source 최종 대조를 마친 뒤에만 승인된 고정8종으로 진행하며 실제 세션/8종은 아직 NOT_RUN이다.
완료된 외부 검사001은 재실행하지 않으며 다음 호출의 permit으로 재사용하지 않는다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3와 개인정보 카탈로그 저장/제품 연결 미완료를 유지한다.
