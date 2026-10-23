# CROSSREF 사전배정 객체 연결과 종료 경로

원 사전배정 descriptor와 기존 ROT adapter를 연결하는 private owner factory와 case ports successor를
구현했다. 실제 한글 실행 없이 초기화·모의 lease·원 함수 보존·실패 정리의 현재 고유21개를 검증했다.
실제 ROT/COM 연결과 Native7%/worker1% 전체 실행 자격은 아직 미검증이며 CROSSREF8종은 NOT_RUN이다.

## 원 소유자 검사와 새 연결 순서

`crossref-preassigned-owner.ps1`은 고정 C# 원문의 해시·파일 경계를 확인해 x86/STA에서 먼저 컴파일한다.
같은 type을 다시 초기화할 수 있지만 해당 worker가 소유하지 않은 기존 type은 거부한다.
factory가 실행될 때는 컴파일이 끝나 있어야 하며 현재 channel의 pending descriptor만 받는다.
COM 생성·새 process launch·늦은 Job 배정·다른 객체 fallback을 추가하지 않았다.

factory는 owner 기록을 먼저 state에 설치한 뒤 원 adapter의 Attach를 단1회 호출한다.
원 P58의 CIM/session/image/window predicate와 원 dual identity 관측을 유지하고, admission에는 CIM 시각을
덮어쓰지 않은 별도의 canonical100ns kernel identity를 보낸다. 실제 현재 pending PID/birth/session/SHA와
맞아야 host admission을 받으며 그 뒤에만 RegisterModule/Visible을 호출한다.
중간 실패 시 owner·원 프로세스 backend·실패 기록을 보존하고 새 연결을 반복하지 않는다.

## 참조 소유권과 정리

기존 adapter의 lease가 application/windows/window RCW를 소유한다. 새 종료 경로는 같은 참조를 원
Close-P58Owner의 FinalRelease로 다시 해제하지 않는다. 별도로 얻은 documents collection은 자신의
ReleaseComObject1회, adapter 소유 참조는 lease.Dispose1회로 구분한다. 한 참조의 실패가 lease 정리를
건너뛰게 하지 않으며 불명/실패 기록과 실패 참조는 남기고 해제·Close·Quit을 자동 반복하지 않는다.

실제 Close(false)/Quit 전에 원 소유자 predicate와 현재 보유한 COM lease의 일치 여부를 확인한다.
확인되지 않은 소유자에 Quit·force kill·암묵적 저장을 요청하지 않는다. 정확한 종료와 참조 정리가 확인된
경우에만 case state의 owner를 비운다. 불명 상태는 same owner를 유지해 성공 정리로 표시하지 않는다.

`crossref-preassigned-case-ports.ps1`은 해시가 고정된 원 case ports의4개 함수를 명시적 새 이름으로
구성한다. 원 함수는 재정의하지 않고 source/document/probe/producer/trace 동작은 보존한다.
교체 범위는 새 factory·종료 함수·실패 owner 보존·새 workflow 이름과 연결 전에 cleanup latch를
초기화하는 순서다. 재열기 연결 실패가 이전 저장 세션의 종료 상태를 상속해 정리를 막지 않도록 했다.
본문 밖 선언 매개변수도 새 ScriptBlock의 param에 보존한다. 새 CLI나 Native 실행 permit은 없다.

## 검증과 실패 이력

[400](evidence/p09-361-crossref-preassigned-owner400.v1.json)은 실제 adapter 초기화1개와 모델 앞7개가
통과한 뒤 시험 보조 코드의 static New 호출에서 실패했다. PowerShell의 특별한 ::new 생성자 binding과
이름이 충돌한 것으로 별도 managed 진단에서 확인했고 시험용 factory만 CreateLease로 바꿨다.
원 production adapter·owner 연결 코드·기존 증거는 변경하지 않았다.

[401](evidence/p09-361-crossref-preassigned-owner-recovery401.v1.json)은 새 이름 충돌 진단1개가 통과했지만,
시험 helper의 함수 본문만 설치하면서 선언부 매개변수를 누락해 실패했다. 같은 구성 방식의 successor
Close/Complete에도 매개변수를 명시적으로 보존하도록 고쳤다.400/401은 FAILED 원본으로 유지한다.

[402](evidence/p09-361-crossref-preassigned-owner-parameters402.v1.json)는 미실행이었던 lease/정리11개,
영향받은 함수 설치1개,새 매개변수 보존1개의13개가 모두 통과했다. 현재 고유21개는 이전 유효8개
보존+이번13개다. 이전 함수 설치 결과만 영향 검증으로 대체했고 영향 없는 통과 시험은 반복하지 않았다.

검사는 정확한 descriptor tick·권한 거부·pending 이전 attach 차단·원 predicate/함수 보존·단1회 해제·
해제 실패 시 기록 보존·document 참조 오류 후 lease 정리·managed 객체의 COM 권한 거부·CIM 원본을
보존하는 canonical proxy·1tick 불일치·불명 owner 유지·중복 Quit 차단·completion 실패 보존·
재열기 cleanup latch 초기화·함수 매개변수 보존을 확인한다. 실제 Attach/ROT/COM/한글은 호출하지 않았다.

402는217fresh/final217·외부 PowerShell image1final·cleanupTrue·전체31.063초다.
worker1.782초·Job CPU1.406초·private최고70.93MiB·시스템CPU최고23.69%·가용RAM최저29.4358%였고,
Job active0·empty·handle closed·stderr0·compiler 임시 잔여0이다. 원 한 코어·BelowNormal·CPU cap6.25%·
readonly private8%/stop7%·RAM/commit95%·readonly90초·진단32768bytes와 입력 확인을 유지했다.
이 수치는 실제 Native7%/worker1% 통합이나 PC 프리즈 해결의 증거가 아니다.

## 다음 실행 경계

후속 [worker와 고정 사례 제어 연결](P09_CROSSREF_PREASSIGNED_WORKER_PROGRESS.md)은 준비 전용1% worker에서
새 controller의 첫 checkpoint 거부/실패 finish/정리를 확인했다.405는 이전20보존+새 tree 배출4와
실제 준비 통합1개가 통과했으며 한글/실물 폴더/owner/trace는0이다. 다음은 독립 입력 대조 뒤 외부
jobless Native 자격 연결/진입점과 실제 Native7% 사전배정·기존 객체/창 결속·정상 종료 검증이다.
원 고정8종 진입점·native backend/guard·기존 COM factory와 공식249는 그대로다. 외부 검사001을
재실행하거나 다음 호출의 live 자격으로 재사용하지 않는다. 전체 세션 자격 후에만 승인된 고정8종의
저장/재열기·원본 보존·상호참조 의미 readback을 실행한다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3와 개인정보 카탈로그 저장/제품 연결 미완료를 유지한다.
