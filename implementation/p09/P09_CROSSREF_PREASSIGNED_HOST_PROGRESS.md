# CROSSREF 사전배정 소유자 통신 연결

현재 사전배정 소유자의 descriptor를 Python 호스트에서32비트 PowerShell worker로 전달하고,
worker가 돌려준 canonical identity를 같은 pending 소유자와 대조하는 private v2 연결을 구현했다.
새 검사25개가 통과했다. 실제 파이프로 고정8사례의152개 메시지를 왕복했지만, 소유자와 프로세스
수명은 모의 객체였다. 실제 한글 실행·ROT 연결·CROSSREF8종은 NOT_RUN이다.

## 기존 순서와 새 descriptor

`crossref_preassigned_host_protocol.py`는 원 v1의 요청 검증·고정16단계·admission·finish 순서와
`PreassignedSessionScope`를 조합한다. 기존 v1 소스나 호출자는 변경하지 않았다.
저장/재열기 생성 checkpoint의 성공 응답에만 현재 소유자의 PID·100ns 생성 시각·session·고정 image SHA와
case/label을 담은12필드 descriptor를 보낸다. 이는 COM 연결이나 실행 허가가 아니다.

`crossref-preassigned-host-channel.ps1`은 정확한 v2 응답 schema·자료형·canonical JSON과 case/sequence를
확인한다. 중복/추가 key·v1 응답·다른 단계의 descriptor·true authority flag를 거부한다.
admission 전에는 다음 제품 checkpoint를 보낼 수 없다. 호스트는 돌아온 canonical PID/session/birth/SHA를
현재 pending descriptor와 대조한 뒤 원 backend의 같은 process handle/window 결속을 호출한다.

실패는 stop을 고정하며 생성·resume·bind를 반복하지 않는다. 원 backend·native guard·case ports·
COM factory·고정8종과 이전 실패는 그대로 보존했다. 새 CLI나 실제 Native 실행 허가 경로는 추가하지 않았다.

## 새 검사와 자원 사용

[검증398](evidence/p09-361-crossref-preassigned-host398.v1.json)의 결과는 다음과 같다.

- Python 신규16개:8사례/16모의 세션, 생성 응답의 descriptor 제한, pending 차단, schema/순서/숫자 자료형,
  canonical identity 불일치, 생성/resume/bind 실패 보존, 실패 finish, live owner 차단, 크기/권한 경계.
- x86 PowerShell 신규8개: descriptor schema/authority, 생성 응답, escaped 중복 key, 구버전 응답,
  다른 단계의 descriptor와 추가 응답 key 거부.
- 실제 Python↔x86 PowerShell 파이프 검사1개:8사례·152요청/응답·16모의 owner admission과16모의 세션 정리.
  양쪽 실제 코드와 원 순서 기계를 사용했고 한글/COM/ROT API는 호출하지 않았다.

205fresh/final205·외부 PowerShell image1final·cleanupTrue이며 전체40.266초다.
PowerShell 모델 worker는2.000초·Job CPU1.609초·private최고68.67MiB였고,
파이프 worker는2.687초·Job CPU2.516초·private최고70.91MiB였다.
두 owned Job은 active0·empty·handle closed이며 IO thread도 종료됐다. 시스템CPU최고64.29%·
가용RAM최저22.2985%는 이 검증 구간의 관측이며 전체 PC 프리즈 원인을 판정하지 않는다.

원 한 코어·BelowNormal·Job CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%와
준비 CPU 보호를 유지했다. 프로토콜은 메시지당4096bytes·총152요청·queue8·readonly90초로 제한하고,
원 진단 출력32768bytes 상한은 유지한 채 프레임을 저장하지 않고 순차 처리했다.
양쪽 stderr는0이었다. 양성 모델의 실패 checkpoint가 같은 cursor를 계속 돌지 않도록 유한 횟수와
즉시 실패 조건도 넣었다. 기존 통과 시험·공식249·Native·396의 컴파일21개는 반복하지 않았다.

## 실제 세션 전에 남은 연결

후속 [객체 factory와 종료 경로](P09_CROSSREF_PREASSIGNED_OWNER_PROGRESS.md)는 기존 adapter의 lease를
명시적 successor에 연결하고 원 P58/CIM 검사와 canonical identity·불명 owner 보존·단1회 참조 해제를
구현했다.402의 현재 고유21개는 이전8보존+미실행/영향/신규13pass이며 실제 ROT/한글은 미실행이다.
다음은 이 successor와 제한된 worker/controller의 전체 통합이다. 원 case ports/COM factory와 실물
진입점은 그대로이며 현재 v2나 모의 결과만으로 실물 경로를 열지 않는다.

그 뒤 Native7%/worker1% 자원 분할과 실제 생성 시 Job 배정·정확한 기존 객체/창 결속·정상 종료를
별도로 자격 검증한다. 완료된 외부 검사001은 재실행하지 않으며 다음 호출의 live 자격으로 재사용하지 않는다.
전체 세션 자격 후에만 승인된 고정8종의 독립 저장/재열기와 의미 readback으로 진행한다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3와 개인정보 카탈로그 저장/제품 연결 미완료를 유지한다.
