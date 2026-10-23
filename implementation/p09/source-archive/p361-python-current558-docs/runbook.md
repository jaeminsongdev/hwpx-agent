# 외부 CROSSREF 세션 자격과 고정 사례 실행

run001/002/003은 모두 소비됐으며 재실행을 금지한다. 현재 새 실행 허가는 없다.
2026-10-22 사용자가 초기 준비 대기만 재설계·검증 후 적용하도록 허용했다. 현재 코드는 검증된 최대15초 대기이며 제품10초 제한·CPU/RAM·정확한 PID/owner·원본 검사는 그대로다.
초기 대기 승인은 새 Native/8종 실행 허가가 아니다. 사용자는 이후 한글 사용을 별도로 알리기 전까지 필요한 한글 정리를 위임했고, 남은 PID24780은550에서 별도 OS 유지보수로 종료했다.
기존 준비 영수증은 변경된 입력의 새 세션 자격으로 쓰지 않는다. 새004의 경로/readonly 검사기는549, worker/공개 entry 코드는551에서 준비했다.
현재 실제 Python 런타임 고정 바이트가 달라004 공개 사전검사는 claim 전 실패했다. 현재 런타임 재자격과552 준비 마감 전 새 실행 명령을 안내하지 않는다.
사용자가 허용한002는 첫 사례의 `source_bind`에서 중단됐다. 사례1은 부분 실행, 사례2~8은 NOT_RUN이고8종 완료는0이다.
2026-10-22 허용된003은 초기 input-idle 기한에서 실패했고 한글 정리가 남았다. 고정8종은 시작하지 않았다.
사용자가 실행한 run001은 세션 연결 `exact_existing_owner`에서 실패했고,
고정8종은 시작하지 않았다. claim001은 소비된 상태이며, Ctrl+C 후 원 최종 기록은
`FAILED_EXTERNAL_QUALIFIED_ENTRY`, `cleanup=false`다. 같은 명령이나 완료된 사전검사001을 다시 실행하지 않는다.
원 기록: [외부 run001](evidence/p09-361-external-qualified-fixed-eight-run001.v1.json).

## 실행003 결과와 초기 입력 대기 실패

[실행003 원본](evidence/p09-361-external-qualified-fixed-eight-run003.v1.json)은125769bytes,
SHA256 `901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a`다.
한글을 시작했으나 session worker의 host_ready에서 P09_XREF_BIND_SESSION_HOST_DENIED로 끝났다.
handler의 실제 원인은 XREF_NATIVE_STARTUP_INPUT_IDLE_BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY다.
원3초 대기에서7회 조회했지만 input-idle을 관측하지 못했고 owner는 결속되지 않았다. 문서 열기·저장과 고정8종은0이다.

그 뒤 같은 소유 Native의 종료를 기다리다 중단돼 원 cleanup=false와 final fresh 누락을 보존한다.
전체109.812초·시스템CPU최고18.22%·가용RAM최저37.066%이며 최초 중단은 CPU/RAM 보호가 아닌 초기 준비 기한이다.
claim003은 소비됐다. 같은 명령을 다시 실행하거나 더 긴 대기·새 세션으로 실패를 덮어쓰지 않는다.

실패 후 PID24780의 생성시각·image가 원 기록과 같은지 확인하고 읽기 전용 WaitForInputIdle(handle,0)을 조회했다.
현재 반환은0이고 query handle을 닫았다. 이는 나중 시점의 input-idle 관측일 뿐 COM 준비·owner·세션 자격이 아니다.
당시 부모 Python은 종료됐지만 창 없는 해당 한글이 남아 있었다. 이후 사용자의 한글 정리 위임에 따라 아래550에서 정확한 같은 프로세스를 종료했다.
상세 관측은 [003 읽기 전용 진단](evidence/p09-361-external003-readonly-diagnosis.v1.json)을 따른다.
초기 대기 재설계·적용은 아래547/548로, 남은 프로세스 정리는550으로 마쳤다. 현재 입력 재자격·별도 실행 허가 전 새로운 Native 묶음은 실행하지 않는다.

## 잔여 프로세스 정리와 새004 준비

사용자는 한글 사용을 따로 알리기 전까지 작업에 필요한 정리를 위임했다.550은003 원 기록의 PID24780·생성 FILETIME134370773797187988과
현재 held handle의 PID/생성 시각·설치 image 경로/2321432bytes/SHA·원/current 세션이 같은지 확인했다.
종료 가능한 GUI 창이 없고003은 owner 결속 전 실패·문서0회였으므로, 원 시험 밖의 OS 유지보수로 그 핸들 하나에 `TerminateProcess`를 호출했다.
같은 핸들의 실제 종료와 handle close, 이후 Hwp/HwpTray0개를 확인했다. 새 한글/COM/문서 조작이나 프로세스 이름 기반 일괄 종료는 없다.
[550](evidence/p09-361-external003-user-authorized-cleanup550.v1.json)은 이 사용자 위임 정리의 결과이며 원003의 FAILED/cleanup=false/final fresh 누락은 byte-exact 보존한다.
Native runtime의 non-killing 정책을 변경하거나 과거 실행의 cleanup PASS로 쓰지 않는다.

[549](evidence/p09-361-capture004-namespace549.v1.json)은 `20261022-g004-c01..08-attempt01`의40개 경로와 별도 readonly 검사기를 준비했다.
새 Python5/Rust4만 실행했고 original/003 검사기와 원 실패 결과는 보존했다. 원 parser/read/pin/summary/최종 reread 본문은 전체 역복원으로 동일성을 확인했다.
848fresh/final848·실제 example dep-info2입력 사전 결속·실행파일/dep-info2final·경고없음·cleanup true다.
149.079초·CPU최고23.95%·가용RAM최저40.091%·보호중단없음이다. 검사기5149696bytes/SHA256 `e64128bec14686aaecde8bafaf34458b59a4c694fe2b0a54f411d013b0a01551`다.
실제8개 사례 디렉터리는 만들지 않았다. 이후004 worker/공개 실행기 코드는551에서 연결했으나 현재 세션 자격·8종 실행 허가는 없다. 기존001~003 명령은 다시 실행하지 않는다.

## 004 코드 연결과 실제 런타임 재자격

[551](evidence/p09-361-capture004-entry-code551.v1.json)은 신규 Python33개·PS namespace5/worker program3과 실제 필수 플래그 누락 거부를 확인했다.
원 entry와 runtime은004 부분을 제거하면 전체 원본과 같다. 기존 bootstrap/worker의 시작·Job 제한·I/O·정리·handshake/사례 수명/원본 결속 본문을 재사용한다.
245fresh/final245·shell1final·cleanup true·66.625초·CPU최고23.7%·가용RAM최저39.736%다. 실제 Native/8종 실행은0이다.

[공개004 사전검사](evidence/p09-361-external-qualified-generation004-preflight.v1.json)는 `XREF_EXTERNAL_HOST_FIXED_PYTHON_RUNTIME_BYTES`로 실패했다.
claim 생성과 Native 실행 전이며 원 실패/cleanup true/최종 fresh 누락을 보존한다. 같은 사전검사 출력 경로를 재사용하지 않는다.
[554](evidence/p09-361-current-python554-observation.v1.json)는 현재 exe107312bytes/SHA7a4102b91959bb234507850ea584e1d31d300a6831b171e4aadc59ff592f0234와
python312.dll6985520bytes/SHAe39aa2da5ea2d310d89994f71bf913a0a137ebaf9f692a565b8c896081512f28·양쪽3.12.14/Windows 서명Valid·실행 중64bit를 관측했다.
기존 고정 exe SHA는dea78bb78043f0d53ef4a475f85fa0312b90fa93c136a0686d17946781c60e16이다. 변경 시점/원인을 확정하지 않았다.
서명Valid는 Native/session/worker 자격이 아니다. runtime·trust 파일이나 역사적 고정 guard를 수정하지 않았으며, 별도 현재 런타임 자격과 새 입력 준비 마감이 필요하다.

## 승인된 초기 준비 대기

초기 input-idle 판정 기한은15초이며 표본 간 대기는 원50ms와 남은 기한 중 작은 값이다.
매 관측 전에 원 Native 자원/parent/kernel/Job 검사를 수행하고 성공 뒤 같은 held handle의 커널/설치 image를 다시 확인한다.
guard/image 검사 시간도 같은 경과 시간에 포함한다. 이 기한은 동기 검사 함수를 강제 선점하는 장치가 아니며 input-idle도 COM/owner/실행 자격이 아니다.
오류·보호 중단·기한 만료 뒤 resume/wait/owner bind의 자동 재시도나 새 세션 fallback은 없다. 제품 실행10초 제한은 바꾸지 않았다.

[547](evidence/p09-361-startup15-and-sql-snapshot547.v1.json)은 가상 시계의 신규8+영향2와 독립 SQL 집계5의15개·213fresh/final213·cleanup true다.
3초 이후 준비,15초 경계/남은 시간으로 sleep 제한, guard 비용·자원 중단·최종 image 검사와 재시도 금지를 확인했다.
[548](evidence/p09-361-startup15-applied548.v1.json)은 그 검증 후보와 적용 파일의2036bytes/SHA256 일치와 다른 자격 입력 보존을 확인했다.
215fresh/final215·cleanup true·28.031초·CPU최고13.28%·가용RAM최저43.746%다. 모형·SQL·Native는 반복하지 않았다.
실제 새 한글에서 준비가15초 안에 끝난다는 증거나8종/현재 세션 자격은 아직 없다. 원003의 실패/cleanup=false/final fresh 누락은 그대로다.

## 실행002 결과와 하위 오류 보존

[실행002 원본](evidence/p09-361-external-qualified-fixed-eight-run002.v1.json)의 SHA256은
`937f7e344845513faf0316e581a52657d803fce026ab6ae05f175dad353fe7da`다.
첫 session worker는 exit0·정확한 COM owner 관측·정상 Close/Quit·빈 소유 프로세스·닫힌 qualification 입력 경계를 마쳤고,
같은 호출의 handoff가 소비됐다. 전체 Native 자격/참조 의미나 P09 수용을 뜻하지 않는다.

고정 worker는 사례1에서 exit2·완료0·host message6개로 중단됐다. host의 cursor4와 원16단계 순서상
`source_open` 반환 뒤 `source_bind`가 진입했다. 첫 save session은 원 exact owner에 결속됐고 정상 종료됐으며,
force kill·세션 재생성·자동 재시도는 없었다. 최종 cleanup=true지만 사례/전체 입력의 최종 fresh는 닫히지 않았다.
141.781초·시스템CPU최고25.38%·가용RAM최저39.073%이며 기록된 중단 코드는 CPU 보호가 아닌 사례 미완료다.

원 사례1 디렉터리에는 target-trace.json과 owner-identities.json만 남았다. opened/saved/reopened HWPX와 SDK 삽입은 없고,
기존 디렉터리와 실패 원본을 보존한다. source_bind의 어느 getter/동일성/문서 수/Modified 조건이 실패했는지는 원 결과가 남기지 않았다.
당시 batch 요약에 있던 phase/하위 error_code를 최종 worker 결과가 누락했던 진단 결함을 수정했다.

[484](evidence/p09-361-crossref-case-diagnostics484.v1.json)는 Python6을483의 동일 입력에서 보존하고
새 PS6·영향 release10 모형을 실행했다.194fresh/final194·shell1final·cleanupTrue다.483의 PS 생성 전 실행기 거부·
cleanup=false/최종 fresh 누락은 보존하며 과거 PASS로 바꾸지 않는다. 원 active-source 관측·거부 조건은 변경하지 않았다.
현재 수정은 닫힌 사례 번호/단계/오류를 다음 결과와 조기 통지에 보존하는 코드이며 실제 source_bind 원인 해결 증거가 아니다.
원 문서 값·SDK 인자·RCW·임의 오류 문자열을 출력하지 않는다. Native008/009/010/001/002의 재실행이나 새003을 허용하지 않는다.

## 고정 실행003 준비 이력

2026-10-22 사용자는 “새003 묶음1회 실행 허용”을 선택했다. 외부 PowerShell의 같은 호출에서 현재 세션 자격을
검사하고 통과할 때만 고정 CROSSREF8종을1회 실행하는 범위다. 원 CPU/RAM·owner·입력 보호를 유지하고
001/002·Native008/009/010 재실행과 Native011·공식249 큐·문자 스타일6종은 제외한다.
승인 뒤 읽기 전용으로 현재 entry224개를 포함한230개 입력 전후 일치와8개 사례 디렉터리 부재를 확인했고 정상 정리했다.
이 확인은 Native/session 자격이나8종 PASS가 아니며 새003 claim을 만들지 않았다.

003 실행 명령은 이미 사용됐으며 재실행 금지다. 당시 명령 전문은 변경 전 보관본에 남겨 두었다.

003 전용 readonly 검사기와8사례의40개 산출물 경로를 분리했다.
새 경로는 `implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261021-g003-c01-attempt01`부터
`c08-attempt01`까지다. 원 source/packet, 기존001/002 claim/run/사례1 흔적과 원 probe 실행 파일은 보존한다.
당시 공개 실행기에 고정003 선택을 연결했다. 실제003은 사례 실행 전에 실패했으며 준비 영수증은 재실행 허가가 아니다.

[488](evidence/p09-361-capture003-namespace488.v1.json)은 Python5·Rust4·새 별도 실행 파일 빌드와732fresh/final732·cleanupTrue다.
[490](evidence/p09-361-capture003-powershell490.v1.json)은7개 함수의 고정 경로/실행 파일 pin 변경만 허용하고 원 함수 전체 역복원,
40개 IO/trace/sidecar 경로·readonly probe lease의5개 모형과201fresh/final201·cleanupTrue를 확인했다.
[489](evidence/p09-361-capture003-powershell489.v1.json)의 실패 원본은 보존한다. 동적 함수의 원 파일 문맥과 매개변수를 보존하도록 수정했다.
[491](evidence/p09-361-capture003-worker491.v1.json)은 Python6·PS3·실제 새 worker의 플래그 누락 거부와224fresh/final224·cleanupTrue다.
원 worker의 전체 release/result/EOF/정리 본문과1% non-killing 제한을 유지한다.

[492](evidence/p09-361-capture003-entry-code492.v1.json)은 공개003 namespace/manifest/claim/결과와 매 사례·최종 산출물 연결의
신규25+영향5 계약30개·236fresh/final236·cleanupTrue다. 원 전체 런타임 AST의 역복원 대조를 통과했다.
[공개 preflight003](evidence/p09-361-external-qualified-generation003-preflight.v1.json)은 원5개 전제 중 caller Job만 거부했고,
229fresh/final229·Native/shell/runtime 각1final·cleanupTrue·claim/한글/문서0회다.
[493](evidence/p09-361-capture003-worker-denial493.v1.json)은 실제003 worker의 ready/kernel/원1% Job 확인 뒤
첫 요청에서 거부했다. Native constructor0회·요청1·exit2·정상 정리·239fresh/final239·cleanupTrue다.
[494](evidence/p09-361-capture003-entry-ready494.v1.json)는 entry224개와 현재 준비 증거를 닫은244fresh/final244·cleanupTrue다.

003 claim/run/notice/cleanup_notice는 실제 실행의 보존 대상이다. 원 caller·자원·입력·owner 조건과 실패 기록을 유지한다.
현재003은 세션 자격 미통과·문서/고정8종0회이며002의 source_bind 원인은 별개로 미확정이다. 준비 결과를 permit으로 쓰지 않는다.

## 고정 실행002 준비 이력

현재 코드에는 원본 문서 결속의 닫힌18개 진단 코드와 getter 직후 null 거부가 추가돼 있다.
실제 문서 값이나 임의 예외 문자열은 남기지 않는다. 기존 owner/COM identity/source hash/단일 문서/clean 상태 조건은 유지한다.
[487](evidence/p09-361-source-bind-diagnostics487.v1.json)은 기존77개 판정 비교를 재실행하지 않고 보존했으며,
변경된 getter 오류9종을 포함한3개 모형 그룹·202fresh/final202·cleanupTrue를 확인했다.
[485](evidence/p09-361-source-bind-diagnostics485.v1.json)와
[486](evidence/p09-361-source-bind-diagnostics486.v1.json)은 실패 원본이다.
이 결과는 실제 source_bind 원인 확정이나 새 실행 허가가 아니다. 기존002 명령을 다시 실행하지 않는다.

남은 한글 PID29824는 사용자의 명시적 종료 요청 뒤[477](evidence/p09-361-user-authorized-retained-owner-close477.v1.json)에서
원 생성 시각·세션·image/window/version을 대조하고 한 번의 정상 Quit으로 종료했다. 같은 held process의 실제 종료·참조 해제를 확인했다.
Close(false)·저장·내용 버리기·강제 종료나 새 한글 실행은 없었고, 종료 뒤 Hwp/HwpTray가0개였다.
이는 원 run001의 cleanup=false를 과거 PASS로 바꾸는 것이 아니다.

새002는 기존001과 code/ready/claim/run/notice/임시 경로가 분리된 고정 실행 범위다. 임의 run 번호·사례 일부·호출자 경로는 받지 않는다.
새 입력 idle helper를 전체 묶음과 각 사례 시작/종료의 fresh 입력 집합에 모두 넣었다.
원 고정8종 source/packet/probe·16개 저장/재열기·152메시지·원 exact owner/Native 보호·같은 invocation의 일회 handoff는 유지한다.
한 번 소비한002 claim/run도 재사용하지 않는다.001 claim/run과 Native008/009/010은 계속 보존·재실행 금지다.

[478](evidence/p09-361-crossref-generation-code478.v1.json)은 신규18+영향5 모형23pass·233fresh/final233·shell1final·cleanupTrue다.
실제 새002 공개 preflight는 Codex의 원 caller Job 정책만 거부했다. 나머지 설치/입력/기존 Hwp0 전제는 통과했고,
223fresh/final223·Native/shell/runtime 각각1final·cleanupTrue이며 한글/claim 생성은0이다.
[480](evidence/p09-361-crossref-fixed-worker-denial480.v1.json)은 변경된 전송 코드로 실제1% worker의 첫 ready 요청을 받고
정확한 kernel/Job 결속 뒤 사례 실행 전에 거부했다. Native constructor trap0회·요청1개·exit2·정상 빈 Job/handle/I/O 정리를 확인했다.
235fresh/final235·shell1final·cleanupTrue이며 과거 성공 본문을 반복하는 제품 시험이 아니다.

[479](evidence/p09-361-crossref-generation-ready479.v1.json)는 위 현재 코드/공개 preflight/실제 거부 자료의 모든240개 입력을
전후 대조했고 cleanupTrue다. 현재 entry 의존219개·각 사례 idle helper 결속, 새002 claim/run 미소비와8개 사례 디렉터리 부재를 확인했다.
원 PS10과 idle12 모형은 반복하지 않았다. 이 준비 영수증은 Native/session 허가가 아니다.
별도로 연 외부 PowerShell의 같은 호출에서 현재 전제를 다시 확인하고 실제 세션 생성·소유권·정상 종료를 통과해야만8종으로 진행한다.
2026-10-21 사용자는 현재 질문의 “새002 묶음1회 실행 허용”을 선택했다.
허용 범위는 외부 PowerShell의 같은 호출에서 현재 세션 자격을 검사하고 통과할 때만 고정8종을1회 실행하는 것이다.
실패한001·Native008/009/010 재실행과 Native011·공식249 큐·문자 스타일6종은 포함하지 않는다.
이 허용은 위 실행002에서 소비됐다. 준비478/479/480과 현재 진단 수정484를 조합해 재실행 허가로 쓰지 않는다.
새 실행은 현재 입력 재자격과 기존 사례 산출물을 보존하는 새 고정 경로, 별도 실행 범위를 먼저 준비해야 한다.

## 현재 세션 관측과 초기화 대기

2026-10-21 사용자는 남은 PID29824에서 문서를 사용하지 않는다고 확인했고, 기존 프로세스의 창/PID/생성 시각/버전 읽기만 허용했다.
한글 시작·종료·문서 동작·접근 허용·새8종 실행은 허용 범위에 포함하지 않았다.

[474](evidence/p09-361-crossref-current-rot-catalog474.v1.json)는 x86 STA의 ROT 이름11개 중 한글 후보1개를 관측했다.
이름 원문·문서 값은 출력하지 않았고 GetObject/객체 생성은 호출하지 않았다. 모형8개·4fresh/final4·shell1final·cleanupTrue다.
[475](evidence/p09-361-crossref-existing-owner-readonly475.v1.json)는 승인된 읽기 전용 연결에서 기존 PID29824의
창·커널 생성 시각/세션/image·버전과 원 어댑터 Read를 확인했다. HWND는 System.Int32였고 원 exact owner 검사를 통과했다.
전후 같은 프로세스가 살아 있었고 모든 연결 참조를 해제했다. 새 한글/문서/종료/activation은 호출하지 않았다.
오류 비노출 모형3개·4fresh/final4·shell1final·cleanupTrue다. 이것은 현재 읽기 관측이지 소유 Job/Native 세션 자격이 아니다.

현재 후보 존재와 원 어댑터의 읽기 성공은 등록 객체 부재 또는 영구적인 어댑터 고장 가설을 지지하지 않는다.
원 run001은 상세 HRESULT를 남기지 않아 과거 실패를 단일 원인으로 확정할 수 없다.
다만 기존 resume은 초기 스레드를 재개한 직후 descriptor를 반환했고 초기 입력 처리를 기다리지 않았다.
창/COM 초기화 경쟁이 가능한 이 순서에 제한된 초기화 대기를 추가했다.

`crossref_startup_input_idle.py`는 원 한 번의 ResumeThread 뒤 같은 held process handle에 WaitForInputIdle(handle,0)을 관측한다.
당시476/003은 최대3초·표본 간50ms였다. 현재는 위547/548의 검증된 최대15초·남은 기한 이내 sleep을 적용했으며 원 Native 자원/parent/kernel/Job 검사와 성공 후 커널/image 재확인을 유지한다.
오류/시간 초과/보호 중단은 실패로 남고 같은 resume/wait/owner bind를 재시도하지 않는다. 강제 종료나 COM activation fallback도 추가하지 않았다.
이 API는 임의 스레드의 초기 입력 idle 관측일 뿐 COM 객체·창의 준비 완료나 실행 허가가 아니다.
원 ROT 전체 열거와 PID/생성 시각/session/image/version/창의 정확한 소유권 검사는 그대로 필요하다.
근거: [Microsoft 초기 입력 대기](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-waitforinputidle),
[실행 서버 class table](https://learn.microsoft.com/en-us/windows/win32/com/registering-a-running-exe-server),
[ROT 객체 등록](https://learn.microsoft.com/en-us/windows/win32/com/registering-objects-in-the-rot).

[476](evidence/p09-361-crossref-startup-input-idle476.v1.json)은 신규10+영향2의 순수 모형12개를 통과했다.
190fresh/final190·cleanupTrue·25.516초·시스템CPU최고43.86%·가용RAM최저43.902%다.
실제 WaitForInputIdle/Hancom/COM/ROT/Native/8종 실행은0이다. 원 backend는 import1줄과 resume 이후 호출1줄만 바뀌었다.
남은 프로세스 정리는477에서 완료했고 이후 허용된002도 위와 같이 종료됐다. 다음 실행에는 현재 변경 입력의 재자격과 새 고정 경로·별도 범위가 필요하다.
원 claim001/run001·claim002/run002·Native008/009/010은 다시 쓰거나 재실행하지 않는다. 다음 새 실행 명령은 아직 발급하지 않았다.

오류 보고·중단 처리의 [모의 검증426](evidence/p09-361-crossref-failure-diagnostics426.v1.json)은 Python16과
PowerShell10을 통과했다. 실제 세션 연결·정상 종료·CROSSREF8종의 통과 증거가 아니며, 코드 변경으로 기존
411/413의 실행 입력은 현재와 달라졌다. 새 실행에는 남은 세션 정리 확인, 원인 검토, 현재 입력 재자격과
별도 실행 범위 확인이 필요하다. 새 명령은 아직 발급하지 않았다.

최종 [429](evidence/p09-361-crossref-failure-diagnostics-final429.v1.json)는 Ctrl+C의 이중 대기 방지와 조기
HRESULT 통지의 영향2+신규2를 통과했다. 이전24개를 보존한 현재 고유28개이며 실제 Native 실행은0이다.

## 이미 실행한 명령 이력

아래는 run001에 사용한 과거 절차다. 현재 다시 실행할 지시가 아니다.

1. 열려 있는 한글 문서를 사용자가 필요한 대로 저장하고 모든 한글 창을 닫는다. 실행기는 기존 한글을 종료하지 않는다.
2. Codex 실행 패널이 아닌 별도로 연 PowerShell에서 아래 명령을1회 실행하고 콘솔을 유지한다. 현재 폴더는 상관없다.
3. 접근 허용 창이 나오면 직접 처리한다.8종 전체를 순차 처리하므로 권한 창이 여러 번 나올 수 있다.
   하나의 권한 창으로 합치거나 접근 허용을 자동으로 누르지는 않는다. 실행 중 문서·소스·설정을 변경하지 않는다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_external_crossref_fixed_batch.py' --execute-qualified-fixed-eight
```

끝나면 마지막 JSON 결과만 채팅에 알려준다. 전체 로그·문서 내용·시스템 정보는 붙여넣지 않는다.
결과는 `implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run001.v1.json`에 저장한다.
단일 claim은 `implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim001.v1.json`이며 덮어쓰지 않는다.

`CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED`는8종 캡처가 끝났다는 뜻이다.
상호참조 의미·독립 readback·P09 완료는 후속 검증이다. `DENIED_` 또는 `FAILED_`이면 마지막 결과를
알리고 같은 명령을 다시 실행하지 않는다. claim 생성 뒤 실패는 새 실행 허가가 아니다.

`WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL`이 나오면 콘솔을 유지한 채 채팅에 알린다.
실행기가 보유한 정확한 세션의 정리를 확인하기 전 다른 한글을 강제 종료하거나 작업 관리자로 일괄 종료하지 않는다.
`WAITING_SAME_WORKER_EXIT_NO_FORCE_KILL`도 같은 worker의 실제 종료 대기이며 새 검증 시작 신호가 아니다.
접근 허용 대기·보호 중단·시간 초과를 재실행 또는 제한 완화 허가로 쓰지 않는다.

승인 범위는 세션 자격 후 기존 고정8종1회다. Native011·기존 Native 재실행·문자 스타일6종을 포함하지 않는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작 상태는 실제 수용 전까지 유지한다.

## 완료된 사전검사 절차 이력

이 명령은 Codex 밖의 PowerShell에서 현재 호출자의 Job 소속과 고정 실행 파일, 비어 있는 자원 제한
Job을 확인한다. 관리자 권한은 필요 없으며 한글·COM·자식 프로세스·문서·접근 허용 창을 열지 않는다.
통과 결과는 현재 사전 조건의 관측일 뿐, 실제 Native 세션이나 고정8종 실행 허가가 아니다.

## 완료된 외부 검사

사용자가 검사001을 실행해 `OBSERVED_EXTERNAL_JOBLESS_PREREQUISITES_EMPTY_LIMITS_NOT_NATIVE_OR_SESSION`을 받았다.
원 영수증 SHA256은 `a9598c11a234b96a602ac9d075c8af151a518e7ab2ba40d53fcab6ea93c068c7`이며
200fresh/final200·외부 image/runtime 각각1final·cleanupTrue다. 원 전제5개와 kernel identity 앞뒤 동일성,
실제 jobless와 빈 두 Job 정리를 확인했다.31.688초·시스템CPU최고28.02%·가용RAM최저30.0088%다.
[392의 독립 대조](evidence/p09-361-crossref-preassigned-scope392.v1.json)는 당시 코드/입력200개를 재확인했다.
검사001은 다시 실행하지 않는다. 아래 명령은 사용한 절차이며 다음 Native 실행 명령이 아니다.

## 과거 사전검사 명령

아래는 이미 완료된 검사001에 사용한 명령이며 다시 실행할 명령이 아니다. 당시 현재 폴더는 상관없었다.
한글이 이미 열려 있으면 이를 종료하거나 수정하지 않고 사전검사 결과에 거부 사유를 남긴다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\inspect_external_crossref_host.py' --inspect-only --inspection-run 1
```

결과는 [검사001 영수증](evidence/p09-361-external-crossref-host-inspection-run001.v1.json)에 저장돼 있다.
이미 존재하는 결과를 덮어쓰지 않는다. 사용자는 마지막 JSON을 전달했고 원 영수증을 독립 대조했다.
전체 로그나 시스템 정보는 붙여넣지 않는다. 검사 번호2~8도 입력 형식상 존재하지만 자동 재시도하지
않는다. 개발 검증용007과 실패008은 보존돼 있으며 사용자용001과 구분한다.

## 결과 해석

| 상태 | 의미와 다음 단계 |
|---|---|
| `OBSERVED_EXTERNAL_JOBLESS_PREREQUISITES_EMPTY_LIMITS_NOT_NATIVE_OR_SESSION` | 현재 호출자가 실제 jobless이고 고정 등록/image·기존 Hwp0·빈 자원 Job 설정을 확인했다. 이후 Native factory와 COM owner의 별도 자격 검증이 필요하다. |
| `DENIED_EXTERNAL_HOST_PREREQUISITES_NO_NATIVE_STARTED` | 실제 상위 Job 또는 다른 전제가 맞지 않는다. 한글은 실행하지 않았다. 영수증의 제한된 실패 목록을 검토한다. |
| `FAILED_EXTERNAL_HOST_INSPECTION_NOT_NATIVE` | 코드 증거/파일 변경·자원 보호·OS 관측 등의 실패다. 기존 영수증을 보존하고 실패 단계부터 검토한다. |

종료 코드0은 첫 상태에만 해당한다. 거부/실패는 코드2이며 PowerShell에서는 `$LASTEXITCODE`로 확인할 수 있다.
이것은 고정8종 성공 여부가 아니다. 결과를 얻기 위해 상위 Job을 없애거나 보안 설정을 바꾸지 않는다.

## 검사 범위

현재 Python 3.12.14 실행 파일은107312bytes,
SHA256 `dea78bb78043f0d53ef4a475f85fa0312b90fa93c136a0686d17946781c60e16`로 고정했다.
원 root-anchor의 과거 SHA는 변경하지 않았고 새 파일 해시를 vendor authenticity나 전체 런타임 자격으로
표시하지 않는다. 로컬 코드 증거389와 실제 import 의존 파일은 시작/마지막에 같은 바이트인지 확인한다.
현재 프로세스의 kernel PID·100ns 생성 시각·세션·image도 앞뒤로 대조한다.

원 `parent_without_prompt_kill`은 실제 jobless인 호출자만 허용한다. immediate Job의 breakaway 표시는
이를 대체하지 못한다. 원 고정 한글 등록/image, 기존 Hwp 프로세스 부재도 확인한다.
전제가 맞으면 프로세스가 없는 Native7%/worker1% Job을 생성해 동일 한 코어·BelowNormal·CPU cap,
합계8% 이내 private memory·no kill/time/breakaway를 읽고 닫는다. 실제 프로세스 배정은 하지 않는다.
이 childless 준비 단계에만 기존 준비 CPU 정책을 사용하고 RAM/commit95%와 원 mutex/입력 확인을 유지한다.
실제 Native에는 기존 Native guard와 시작 전 배정·정확한 window/COM owner 검증이 별도로 필요하다.

## 검증 증거와 보존한 실패

- [386](evidence/p09-361-external-crossref-host-code386.v1.json): 새 계약22pass 뒤 과거 Python SHA 불일치. 실패 원본을 보존했다.
- [387](evidence/p09-361-external-crossref-host-recovery387.v1.json): 영향12+신규1pass·이전10보존, 실제 현재 kernel identity와 Job 거부 확인,195fresh/final195·cleanupTrue.
- [CLI008](evidence/p09-361-external-crossref-host-inspection-run008.v1.json): 압축 proof를 일반 JSON으로 읽는 진입점 KeyError. 한글/자식 실행 전 실패했다.
- [388](evidence/p09-361-external-crossref-host-entry388.v1.json): 일반 JSON까지 허용한다고 잘못 기대한 새 시험1error·영향AST1pass. 원 strict decoder는 완화하지 않았다.
- [389](evidence/p09-361-external-crossref-host-packed389.v1.json): 실패 시험1pass·이전23보존의 현재 고유24개,200fresh/final200·cleanupTrue.
- [CLI007](evidence/p09-361-external-crossref-host-inspection-run007.v1.json): 실제 사용자 진입점의 현재 Job 거부,200fresh/final200·cleanupTrue·31.688초·시스템CPU최고37.98%·가용RAM최저31.4314%.
- [390](evidence/p09-361-external-crossref-empty-limits390.v1.json): 실제 빈 두 Job의 제한/정리,12fresh/final12·cleanupTrue·2.500초·시스템CPU최고5.11%·가용RAM최저33.2249%.

과거 계약·공식249·Native008/009/010을 다시 실행하지 않았다. PC 프리즈 원인 규명/해결 증거도 아니다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기를 유지한다. 이후 실제 실행 조건은
[세션 자격 현황](P09_CROSSREF_EXECUTION_READINESS.md)을 따른다.
