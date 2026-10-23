> 최신 2026-10-22 / 005 whole FAILED·006 준비 PASS(not Native/Gate)·외부006 결과 대기 PAUSED. 005 최종 결과는 FAILED_EXTERNAL_QUALIFIED_ENTRY / case1 source_bind의 P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_SHARING_VIOLATION, completed0/8·수용0·cleanup true이며 원본115450B/SHA05f1d0e2c5d38a9aa41fc358e2d9cbef8b584d7f08c1ace0d244651297b3e1db를 보존한다. CPU 보호 중단은 아니었고005 전체 관측 CPU최고34.38%/가용RAM최저44.093%다. 새006은 고정 원본의 Read/FileShare.Read 잠금을 기존 Open보다 먼저 확보하고 사례 완료·owned 정리까지 유지한다. 원본 경로·digest·한글 Open/Save/owner/COM 관측·전후입력·자원/비강제종료 조건을 바꾸거나 쓰기 공유를 허용하지 않는다. 원본 파일 경계 확인→잠긴 stream의 SHA 검증으로 사전 중복 Get-FileHash도 제거했다. 006 준비는 전용 readonly probe586(Python5/Rust4,853fresh/final853), code588(Python50/Windows11,259fresh/final259), READY거부589(264fresh/final264,요청1·실제사례0·Native생성trap0·cleanup true), 실제 공개loader590(243fresh/final243·cleanup true·CPU최고13.79%/가용RAM최저46.360%)로 확인했다. 50개 Python과6개 잠금 모델은 동일한 입력을 fresh 대조해 기존 body PASS를 유지했고 실패 audit001~009는 원 상태로 보존했다. Codex 내 사전검사는 상위Job 종료정책 하나로만 정상 차단됐으며 이를 Native 세션 자격/P09 PASS로 해석하지 않는다. 기존005 binary도 byte-exact 확인했다. 외부006/claim/run/spool/8종 실물/의미결속은 NOT_RUN이며, 잠금 하 한글 열기 및 활성 SaveAs 산출물의 실제 호환성은 아직 미검증이다. 006은 사용자가 별도 외부 PowerShell에서1회 실행할 새 묶음이며 에이전트가 실행하지 않는다. 사용자 요청에 따라 명령 전달 후 목표를 외부006 결과 대기 PAUSED로 두고 구현·자동 재검증을 멈춘다. 기존001~005/Native008~010 재실행·자동재시도·Native011은 금지한다. P09/A12/A13 OPEN·P10미시작·공식249대기열158수용/91대기는 그대로다. 근거 [005](evidence/p09-361-external-qualified-fixed-eight-run005.v1.json), [586](evidence/p09-361-capture006-namespace586.v1.json), [588](evidence/p09-361-capture006-entry-code588.v1.json), [589](evidence/p09-361-capture006-entry-ready589.v1.json), [590](evidence/p09-361-capture006-handoff590.v1.json). 아래 NOT_RUN/승인/ACTIVE 표현은 당시 관측 이력이다. BLOCKED 전환 도구가 신뢰된 CCA 실행 맥락 부재로 거절하여, 사용자 중지 요청을 확실히 적용하는 PAUSED로 전환한다.

> 최신 2026-10-22 / 005 승인583: 사용자 '실행해도 됨'으로 새005 고정8종1회 범위를 승인했다. 실제 공개 loader의 현재 code578/ready580/고정 입력240개 전후 일치·cleanup true·CPU최고21.68%/가용RAM최저44.996%·보호중단없음·Hwp0을 확인했다. 외부 PowerShell 실행 명령 전달 단계이며 실제005/claim/run/spool/사례0·수용0이다. 세션 현재자격·원 보호/입력/owner/source/non-killing 조건을 유지하고001~004/Native008~010 재실행·Native011은 제외한다. 실제 결과를 받기 전 NOT_RUN/unverified를 유지하며 승인/캡처를 의미결속/Gate PASS로 바꾸지 않는다. 근거 [583](evidence/p09-361-capture005-approved-inputs583.v1.json). 이하 미승인 표현은 과거 관측 이력이다.

> 최신 2026-10-22 / 578·580:005 공개 entry/runtime 준비를 완료했다. 신규 코드모형34 PASS·266fresh/final266와 실제005 worker READY 거부·271fresh/final271·cleanup true를 기록했다. 요청1/exit2/사례0/Native0/constructor trap0/IO join/Job tree0/no force를 확인했고 CPU최고21.68%·가용RAM최저47.504%·보호중단없음이다.240fresh/final240의 실제 사전검사는 Codex 상위 Job 수명 정책만 거부했다. 이전 통과 본문 재실행과 실제005 Native/claim/run/spool/사례폴더 생성은0이다. 실제005는 사용자미승인/NOT_RUN이며 원004 sourceReadLease 실제원인은미확정이다. 세션/고정8종 단계별 실패 notice와 원문선보존/인라인최종저장만 강화하고 원 source-share/CPU/RAM/owner/PID/EOF/정리조건은 유지했다.001~004 실패·004 원 최종영수증유실·Native008~010 소비·Native011 미승인을 보존하고 P09/A12/A13 OPEN/P10미시작이다. 근거 [578](evidence/p09-361-capture005-entry-code578.v1.json), [580](evidence/p09-361-capture005-entry-ready580.v1.json). 이하 상태는 각 과거 관측 당시 이력이다.

# CROSSREF 외부 세션 자격과 고정 사례 실행

최신005 경로/probe/worker 준비574/577: 원본과003/004 경로에 겹치지 않는40개 산출물 경로와 별도 probe5150720bytes/SHA9c07898c40bb95ce1ed60b42d10481152bda8aaf7bb68e9c453fffef736756d9를 신규Python5/Rust4로 확인했다.574는852fresh/final852·cleanup true다.577은 Python6(576 통과5 보존+수정1)·PS8·실제 필수 플래그 누락 거부,256fresh/final256·shell1final·cleanup true다. 두 마감 모두 보호중단없음이며 실제Native/COM/캡처0이다. 공개005 entry/runtime/handoff/claim/최종저장573 연결과 새code/readiness/실행 허가는 여전히 미완료다. 원575/576 실패·finalfresh0, 원001~004 entry와 이전 바이너리/산출물은 보존한다.

최신 준비573:005 전용 최종 저장 API에 원256KiB writer와 무손실 인라인567을 연결하고10개 임시 통합모델을 통과했다. 최종형식 실패 시에도 원문을 별도4MiB bounded forensic spool로 보존하되, 이는 수용/실행 허가가 아니고 정식 packet은 self-contained다.186fresh/final186·cleanup true·CPU최고14.84%/가용RAM최저47.630%·Native/SQL/제품 실행0이다. 실제005 실행기/namespace/자격/허가는 아직 없고 claim/run/spool도 미생성이다. 기존entry001~004 바이트와 원003실패SHA/004 유실 상태를 보존했다. [573](evidence/p09-361-generation005-publication573.v1.json)을 단순 포맷 검증 이상의 실물 PASS로 승격하지 않는다.

최신 로컬 진단570: 원 lease 플래그와 owner/source 판정을 유지하면서 닫힌 HRESULT 분류를 추가했고 모델6개를 현재 입력에서 확인했다(569 보존3+새3). 실제004에서 해당 HRESULT가 기록된 것은 아니므로 원인은 미확정이다. 같은 묶음에서 공통 조회우선 제품 API5개를 새로 검증했으나 CROSSREF 실물 수용은0이다.859fresh/final859·cleanup true·CPU최고30.11%/가용RAM최저48.379%·보호중단없음·실제Native0이다. active 입력 변경으로 기존004 준비559/560은 새 실행 자격이 아니며004 재실행/005 허가는 없다. [570](evidence/p09-361-source-lease-and-common-recovery570.v1.json)과 보존된 원004 사후 관측567을 구분한다.

현재004 결과: 실행 종료·claim 소비. 첫 사례 source_bind/read lease 실패로 사례1 부분·수용0·사례2~8 NOT_RUN이다. 원 최종 영수증은 outer256KiB 한도 초과로 발행되지 않았고 cleanup/final fresh는 원 기록 기준 미검증이다. [사후 관측567](evidence/p09-361-external004-postmortem567.v1.json)은 기존 증거4개·사용자 콘솔·종료 후 원본 읽기/프로세스 관측만 별도로 보존하며 원 영수증을 대체하지 않는다.004 재실행/새005 허가는 없다. 이하 실행 중/미승인 표현은 각 관측 당시 이력이다.

2026-10-22 현재: 사용자 `004 실행하자`로 새004 1회 승인, 외부 PowerShell 명령 안내 완료. 실제 세션/8종 결과는 아직 NOT_RUN/unverified이며 승인만으로 PASS 처리하지 않는다. 아래 미승인 표현은 각 준비 당시 상태다. entry 의존230개 동일성과004 미소비를 확인했으며 기존001~003/Native008~010/Native011은 실행하지 않는다.

003은 실제 한글을 시작했으나3초 input-idle 경계에서 세션 자격을 통과하지 못했다. 고정8종과 문서 열기·저장은0이다.
claim003 소비·원 cleanup=false·final fresh 누락을 보존한다. 실패 후 같은 PID24780에서 input-idle은 관측됐지만 COM/session PASS가 아니다.
사용자가 허용한 초기 준비 대기 재설계는547의 신규8+영향2 모형과548의 검증 후보/적용 파일 byte-exact 대조 뒤 최대15초로 적용했다.
원50ms cadence·CPU/RAM·PID/owner·입력 검증과 제품10초 제한은 유지하며 남은 기한보다 길게 sleep하지 않는다.
새 Native/8종 실행 허가는 없다. 이후 사용자의 한글 정리 위임에 따라550에서 원003과 같은 생성 시각/image/세션의 held process 하나를 OS 수준으로 종료하고 Hwp/HwpTray0개를 확인했다.
원003 FAILED/cleanup=false/final fresh 누락은 보존하고 Native runtime의 non-killing 정책도 바꾸지 않았다.001/002/003은 재실행하지 않는다.
549는 새004의40개 고정 경로와 별도 readonly 검사기를 Python5/Rust4·848fresh/final848·dep-info2final·cleanup true로 준비했다.
원 parser/read/pin/summary/최종 reread 본문과 original/003 binary는 보존했다.
551은004 worker/공개 entry의 신규Python33/PS8·필수 플래그 누락의 실제 조기 거부를245fresh/final245·shell1final·cleanup true로 검증했다.
같은 세대의 claim/ready/notice/실행 경로를 분리하고 원 handoff/사례 순서·16개 수명·40개 산출물 결속과 non-killing worker를 재사용한다.
공개004 사전검사는 Python 고정 바이트 불일치로 claim 전 실패했다. 현재3.12.14 exe/dll 서명은Valid지만 exe SHA는기존고정값과 다르다.
554는 읽기 전용 관측이며 서명만으로 runtime/Native 자격을 주거나 검사를 완화하지 않았다.
558에서 두 고정 Python 이미지와 이미 로드된 경로/ABI, 동일 kernel/원 자원 제한, 실행 전 배정된 읽기 전용 자식의 자기검사·종료, 실제004 worker ready 거부 경계를 마감했다.
입력260fresh/final260·runtime2/shell1/nativeimage1final·cleanup true·CPU최고18.16%·가용RAM최저39.676%·한글 생성자0이다.
핀 모형8·서명/자기검사 통과는 입력 대조로 보존했고 종료 경합 신규4모형과 실제1→0 Job drain을 확인했다.555~557 실패와 최종 fresh 누락·556 cleanup=false는 그대로다.
559에서 현재 프로필을004 공개 entry와 세션/고정묶음/각 사례 경계에 연결했다. 이전 세대는 역사적 고정 검사 그대로이며 runtime/trust 파일을 수정하지 않았다.
과거 자격 영수증은 묶음 시작·종료에만 확인하고, 각 실행 경계는 현재 두 이미지와 로드 경로·원본/owner 입력을 fresh/final 검증한다.
신규11+영향27의38모형·267fresh/final267·runtime2/shell1final·cleanup true·CPU최고17.12%·가용RAM최저42.778%다. 변경 밖 entry/runtime 전체 본문과 worker/PS 입력을 대조했고 worker6/PS8/실제 ready 거부는 반복하지 않았다.
새 공개 사전검사는 Python 해시 오류를 해소하고232fresh/final232·runtime2/native1/shell1final·cleanup true로 마감했다. Codex parent lifecycle 하나만 거부했으며 한글/COM/문서/접근 허용/claim은0이다. 이는 외부 세션 자격 PASS가 아니다.
560 준비 묶음은272fresh/final272·runtime2/native1/shell1final·cleanup true·74.313초·CPU최고11.4%·가용RAM최저42.976%다.004 claim은 아직 소비하지 않았다. 다음은 사용자 새004 1회 허가 후 외부 PowerShell에서 현재 세션 자격 검사이며, 통과할 때만8종을 실행한다.
현재 코드 [559](evidence/p09-361-capture004-entry-code559.v1.json), [공개 사전검사](evidence/p09-361-external-qualified-generation004-runtime559-preflight.v1.json), [준비560](evidence/p09-361-capture004-entry-ready560.v1.json)을 따른다. 준비 완료를 새 Native 허가나 P09 Gate PASS로 바꾸지 않는다.
입력이 바뀌었으므로 기존 ready/실패 영수증을 새 자격으로 쓰지 않는다.
현재 원인과 보존 경계는 [실행003 결과](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md#실행003-결과와-초기-입력-대기-실패)를 따른다.

외부 run001은 실제 한글을 시작했으나 기존 세션 연결 `exact_existing_owner`에서 실패했다. worker exit2,
`COM_owner_observed=false`이며 문서 열기·저장과 CROSSREF8종은 실행하지 않았다. 이후 동일 Native의 종료를
기다리다 사용자가 Ctrl+C로 중단했다. 최종 기록의 `cleanup=false`와 누락된 최종 fresh 검사는 그대로 보존한다.
claim001은 소비됐으며 동일 명령 재실행은 금지한다.

당시 남은 PID29824는 사용자의 종료 요청 뒤477에서 정확한 생성 시각·세션·image/window/version을 확인해 정상 Quit했다.
강제 종료·저장·내용 버리기 없이 실제 같은 프로세스 종료와 Hwp/HwpTray0개를 확인했다. 원001의 실패/cleanup=false는 보존한다.
새 고정 실행002는478의 신규18+영향5 모형23개와 실제 공개 preflight·480 worker 첫 요청 거부/정리를 확인했다.
479는 당시240fresh/final240·cleanupTrue로219개 entry 입력과 각 사례 idle helper를 닫았다.
기존001과 새002의 code/ready/claim/run/notice/임시 경로를 분리했고 arbitrary retry 번호/사례 subset/사용자 경로는 받지 않는다.
사용자가 허용한002는 소비됐다. 첫 session worker의 정확한 COM owner/정상 종료와 입력 경계 후 handoff가 소비됐고,
사례1의 원본 열기 다음 source_bind에서 중단됐다. 완료0·나머지7개 NOT_RUN·최종 cleanupTrue이며 원 실패와 흔적을 보존한다.
하위 오류 누락을 고친484는 보존 Python6·새 PS6·영향 release10·194fresh/final194·cleanupTrue다.
이는 source_bind의 실제 실패 조건을 확정하거나 고친 Native 증거가 아니며 원 관측·거부 조건을 낮추지 않았다.
001/002 재실행 금지다.003의 전용 검사기·고정 경로·worker·공개 실행기 연결과 준비 검증은494에서 마쳤고, 실제003은 실행하지 않았다.
2026-10-22 사용자가 새003 묶음1회를 허용했다. 현재 entry224개를 포함한230개 입력 전후 확인·8개 사례 디렉터리 부재·정상 정리를
읽기 전용으로 확인했으며 claim은 미소비다. 실제 세션 자격·8종은 아직 미실행이다.
외부 PowerShell의 같은 호출에서 현재 자격을 통과할 때만8종을1회 실행한다. 상세 명령과 범위는 [외부 실행 절차](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)를 따른다.

## 원본 문서 결속 진단의 현재 상태

[487](evidence/p09-361-source-bind-diagnostics487.v1.json)은 원 거부 조건의77개 판정 비교를485에서 보존하고,
수정된 속성 오류 주입9종·최초 실패 뒤 후속 getter 미조회·원 소유권 함수 복구의3개 그룹만 실행했다.
202fresh/final202·shell1final·cleanupTrue이며29.234초·시스템CPU최고40.82%·가용RAM최저41.343%다.
485/486의 실패와 최종 fresh 누락은 보존한다. 두 실패는 모형 속성 예외가 PowerShell에서 null로 관측되어
최초 실패 코드가 소실되는 진단 결함을 드러냈다. 현재 코드는 각 getter 직후 null도 거부한다.

소유권/COM 동일성/경로/version/hash와 실제Int32 문서 수1·Modified0의 조건은 유지한다.
닫힌18개 코드(불리언8·getter9·파일 읽기 lease1)가 조기 통지에 전달되고 실행 권한을 만들지 않음을 확인했다.
실제 run002의 실패 속성이나 조건은 여전히 미확정이며, 새 한글·문서·8종은 실행하지 않았다.
별도 고정003의 입력/산출물 경계는 아래 준비 결과를 따르며, 기존 사례1 산출물과 실패 원본을 보존한다.
003의 사용자1회 허용은 확인됐지만 현재 실물 세션 자격은 아직 없으며001/002를 다시 실행하지 않는다.

## 고정003 경로와 worker 준비

003은 원본 source/SDK packet을 바꾸지 않고 산출물40개만 `20261021-g003-c01..08-attempt01`에 분리한다.
기존 시도 디렉터리와 원 검사기 실행 파일을 이동·삭제·덮어쓰지 않는다. 임의 경로·세대 번호·사례 subset·자동 retry는 받지 않는다.

- [488](evidence/p09-361-capture003-namespace488.v1.json): 신규 Python5·Rust4와 별도 readonly 검사기 빌드,
  732fresh/final732·산출물2final·cleanupTrue. 원 read/parse/source/packet hash/출력·최종 reread 본문을 보존했다.
- [490](evidence/p09-361-capture003-powershell490.v1.json): 고정7개 함수의 경로/검사기 pin만 변환한 전체 역복원·40개 경로·readonly lease의5개 모형,
  201fresh/final201·shell1final·cleanupTrue.489의 함수 파일 문맥 누락 실패와 최종 fresh 누락은 보존했다.
- [491](evidence/p09-361-capture003-worker491.v1.json): Python6·PS3와 실제 새 worker의 고정 플래그 누락 거부,
  224fresh/final224·shell1final·cleanupTrue. 원1% non-killing worker의 시작·Job 제한·readback·I/O·정리를 재사용한다.

위 세 검증의 시스템CPU 최고는 각각35.11/13.49/17.42%, 가용RAM 최저는38.585/40.599/41.375%다.
003 실제 문서 열기·저장·CROSSREF 삽입은0회다. 공개 실행기 연결과 실제 거부 검증은 아래494 준비 묶음에서 마쳤다.

## 공개003 준비 묶음 검증

[492](evidence/p09-361-capture003-entry-code492.v1.json)은 신규25·직접 영향5의30개 계약과236fresh/final236·cleanupTrue다.
원 런타임의 전체 AST를 고정003 경로·입력·worker 선택 추가 전 상태로 역복원해 기존 실행·검사·정리 흐름을 대조했다.
매 사례의003 profile/program/probe 입력과 최종40개 산출물을 같은 namespace에 결속한다.

[공개 preflight003](evidence/p09-361-external-qualified-generation003-preflight.v1.json)은229fresh/final229·외부 실행 파일3종 각1final·cleanupTrue다.
원 자원 정책·설치 등록·실행 파일·한글0개는 통과했으며 Codex caller Job의 원 종료 정책만 거부했다. claim/Native/문서0회다.
[493](evidence/p09-361-capture003-worker-denial493.v1.json)은 실제003 worker의 정확한 kernel/원1% Job 확인 후 첫 ready에서 거부했다.
요청1·exit2·Native constructor0회·사례0개·query/IO/빈 Job/handle 정상 정리·239fresh/final239·cleanupTrue다.

[494](evidence/p09-361-capture003-entry-ready494.v1.json)는 위 현재 입력과 entry224개를 닫은244fresh/final244·cleanupTrue다.
시스템CPU 최고는492/preflight/493/494 순서로26.76/10.52/27.73/13.09%, 가용RAM 최저는41.383/43.204/41.994/43.385%다.
실제8종·Native/상호참조 의미 자격·P09 Gate PASS가 아니라 현재 구현 준비 결과이며, 기존 시험·빌드·Native는 반복하지 않았다.
003 claim/run은 미소비다. 별도 사용자 허용 후 외부의 같은 호출에서 원 caller/resource/input/owner 조건을 다시 만족해야만
세션 자격과 고정8종을1회 진행한다. 실패한001/002와 Native008/009/010·미승인Native011은 이 범위에 포함하지 않는다.

오류 보고·중단 처리 변경은 Python18과 PowerShell10의 현재 고유28개 계약을 통과했다. worker 결과와 handler 상태를
종료 대기 전에 기록하고, 실패 통지 원본을 별도 저장한다. `P09_XREF_ROT_*`를 일반 오류로 소실시키지 않고
고정 오류 종류와 숫자 HRESULT만 기록한다. Ctrl+C는 명시적인 실패 종료로 처리하며 원 claim과 미정리 상태를
보존한다. 실제 COM 연결의 근본 원인 해결이나 새 Native 실행 자격은 아직 검증하지 않았다.

최종429에서는 보유 세션 대기 중 Ctrl+C를 누르면 `finally`에서 같은 무기한 대기로 재진입하는 경로를
막았다. 초기 실패와 `cleanup_pending`을 보존하고 강제 close/kill 없이 중단한다. 조기 통지에도 고정
오류 종류와 숫자 HRESULT를 포함한다. 기존14개 Python과 PowerShell10은 원 코드/시험 대조로 보존했고,
영향받는 기존2개와 신규2개만 실행했다. 실제 Native 종료 대기의 소유권 이전이나 새 종료 정책은 추가하지 않았다.

## 실행 순서와 일회성 경계

`run_external_crossref_fixed_batch.py`는 현재 실행 파일·등록·jobless caller·입력과 준비 증거를 확인한 뒤
단일 claim을 새로 만든다. 현재1% worker와 정확한 한글 kernel/Job/window/COM owner를 결속하고 실제
종료·빈 Job·입력 최종 대조를 마쳐야 메모리 내 일회용 handoff를 발급한다. 같은 guard·caller·입력에만
소비할 수 있고 저장된 영수증을 permit으로 쓰지 않는다. qualification은 문서 Open/Save·삽입을 하지 않는다.

다음 worker는 원8사례·16개 저장/재열기 수명·152메시지 순서를 그대로 사용한다. 각 사례 시작/종료에
현재 실행 입력과 외부 실행 파일을 fresh 확인하고 매 메시지에는 held kernel identity·Job·제한값을 확인한다.
동일 PowerShell image를152번 재해시하지 않으며, 한글 image의 생성/resume/bind fresh 검사는 유지한다.
전체 입력은 묶음 경계에서도 대조한다. 과거 통과한 공식 시험은 다시 돌리지 않는다.

원 Native guard의600초, Native7%/worker1% non-killing Job, 동일 한 코어/BelowNormal·CPU cap6.25%,
RAM/commit95%와 입력/진단 상한을 유지한다. 준비 CPU 완화 정책을 실제 Native에 쓰지 않는다.
실패하면 작업을 중지하고 정확한 동일 Native handle과 Job을 보존해 실제 종료를 기다린다.
force kill·timeout reset·재생성·자동 retry·불명 owner의 Close/Quit 반복은 하지 않는다.

## 완료한 준비 검증

| 증거 | 검증한 범위 | 결과 |
|---|---|---|
| [410](evidence/p09-361-crossref-qualified-entry-code410.v1.json) | 과거 코드 보존 inverse 검사 | 공백 복원 오류로 FAILED 보존, 시험/Native0 |
| [411](evidence/p09-361-crossref-qualified-entry-code411.v1.json) | 신규36+영향 kernel6의 Python42, 고정 release PowerShell10 | PASS,228fresh/final228,cleanupTrue |
| [공개 preflight001](evidence/p09-361-external-qualified-entry-preflight001.v1.json) | 실제 공개 CLI와 외부 실행 파일3종 | 원 caller Job만 거부,222fresh/final222,각 image1final,claim/Native0 |
| [412](evidence/p09-361-crossref-fixed-worker-denial412.v1.json) | 실제1% worker 준비와 kernel/Job 결속 뒤 무조건 거부 | PASS,첫 요청1개,exit2,Native constructor0,230fresh/final230,cleanupTrue |
| [413](evidence/p09-361-crossref-qualified-entry-runtime-ready413.v1.json) | 위 증거와 현재234입력 대조 | 구현 준비 PASS,234fresh/final234,cleanupTrue,시험 재실행0 |
| [외부 run001](evidence/p09-361-external-qualified-fixed-eight-run001.v1.json) | 실제 세션 연결 | FAILED,worker exit2,고정8종0,cleanupFalse,claim 소비 유지 |
| [426](evidence/p09-361-crossref-failure-diagnostics426.v1.json) | 결과 선기록·대기 구분·중단·오류 비식별화 Python16/PowerShell10 | PASS,227fresh/final227,cleanupTrue,새 Native0 |
| [429](evidence/p09-361-crossref-failure-diagnostics-final429.v1.json) | Ctrl+C 이중 대기 방지·조기 숫자 오류 통지의 영향2+신규2 | PASS,이전24보존의 현재28,229fresh/final229,cleanupTrue,새 Native0 |

411은64.110초·시스템CPU최고15.28%·가용RAM최저30.1921%다.412는50.328초·시스템CPU최고23.77%·
가용RAM최저29.0357%이며 query handle·Job tree·IO thread와 probe lease를 닫았다.
413은42.000초·시스템CPU최고32.65%·가용RAM최저29.1362%다. 프리즈 원인이나 해결 판정은 아니다.
외부 검사001의 원 영수증과410 실패, 영향 없는 기존 성공 시험 및 Native008/009/010 원본도 보존했다.

## 다음 복구 단계와 산출물 판정

426은51.532초·시스템CPU최고18.89%·가용RAM최저43.038%이며 모의 검사 Job과 IO 정리를 확인했다.
429는43.094초·시스템CPU최고16.57%·가용RAM최저12.074%이며 Python 모의 검사만 수행했다.
다음은 남은 동일 Native의 정리 범위 확인과 연결 실패 진단이다. 원 기록은 세부 오류를 일반 코드로 바꿨기 때문에
실제 HRESULT나 정확한 ROT 실패 조건을 복원할 수 없다. 새 실행 없이 대기 시간이나 특정 COM 원인을 확정하지 않는다.
동일 Native handle/Job 보존을 위해 종료 대기 자체는 유지하되, 대기 메시지는 작업 진행이 아닌 수동 해결 필요 상태로 표시한다.
426은 비동기 정리 소유권 이전이나 종료 기한 정책을 새로 자격 검증한 결과가 아니다.

[외부 실행 안내](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)의 기존 명령은 과거 이력이며 다시 실행하지 않는다.
완료된 사전검사001도 반복하지 않는다. 실제 고정8종은 현재 입력/세션 재자격과 별도 실행 범위 확인 뒤에만 진행한다.

완료 시8개 고정 폴더의 opened/saved/reopened HWPX·원 trace·canonical sidecar 총40개를 실제16개
kernel 수명·producer identity·원본 hash·정상 종료에 결속한다. 성공 상태도 캡처 완료일 뿐,
필드 target/명령·cache·상호참조 의미와 독립 readback은 후속 검증이다. 공식 수용이나 P09 Gate로 올리지 않는다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·
source API v13 incomplete/미해결4/report없음/exit3를 유지한다. 개인정보 카탈로그의 읽기 제품은417을 보존하며,
새 마스킹 source/저장 코드 검증과 strict 제품/공통 compiler 연결은 별도 작업이다.
