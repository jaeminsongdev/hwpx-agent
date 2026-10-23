# P09 제품 완료 실행 계획

2026-10-21 사용자의 구현 계획 수립과 계속 추진 요청에 따른 실행 순서다.
목표는 P09의 전체 제품 Gate 종료이며 P09~P20 목표를 일부 시험 통과로 축소하지 않는다.
기능 분류는 검색19개와 P09 소유 참조46개의65개다. 249개 저장 경로 시험의 공식 수용158개,
잔여91개는 그 기능 전체의 작업 수나 전체 완료율이 아니다. P09/A12/A13 OPEN, P10 미시작이다.

## 완료를 앞당기는 실행 원칙

- 제품 완료의 선행 조건을 해소하는 변경을 우선한다. 보조 계측·압축·문서 검사만으로 새 작업 주기를 만들지 않는다.
- 공통 router/compiler/저장 coordinator를 재사용한다. 기능별 별도 실행기와 검증 계보를 늘리지 않는다.
- 입력과 검증 조건이 그대로인 통과 결과는 보존한다. 변경 영향이 있는 사례와 미실행 사례만 실행하며,
  최종 현재 코드에 적용할 수 없는 과거 결과를 현재 결과로 승격하지 않는다.
- 본문 통과 뒤 입력 마감 실패는 본문 실패와 구분한다. 동일 제품 실행을 반복하지 않고 원본을 보존한
  별도 마감 판정으로 처리한다. PASS는 필수 입력·종료·자원 확인이 끝난 뒤에만 기록한다.
- CPU/RAM 보호 중단은 같은 명령의 자동 재시도 사유가 아니다. 중단 단계·소유 자원·관련 코드를 검토하고
  필요한 최적화 또는 선행 조건 해결 후에만 다음 실행을 설계한다. 자원 한도를 낮춰 성공시키지 않는다.
- 한 번의 변경 묶음에 구현·직접 영향 시험·문서 동기화를 합친다. 문서 동기화 때문에 제품 시험을 다시 돌리지 않는다.
- 실제 한글 작업은 자격을 갖춘 묶음으로 준비한다. 접근 허용을 자동 처리하거나 실패한 Native를 재실행하지 않는다.

## 실행 순서와 완료 조건

현재 실물 선행 작업의 코드·준비 마감은559/560에서 완료했다. 다음은 새004의 사용자1회 허가와 외부 PowerShell의 현재 세션 자격 검사이며, 통과할 때만 고정8종을 진행한다. 기존001~003/Native008~010과 Native011은 포함하지 않는다.
559는 현재 Python 프로필을004에만 연결했다. 이전 세대의 역사적 고정 guard는 변경하지 않고004의 exe/core 두 이미지와 실제 로드 경로를 현재 실행 경계마다 검증한다. 과거 자격 영수증은 묶음 시작·종료에 확인하고 사례별로 과거 이력을 재검증하지 않는다.
신규 수용/거부11+영향27의38모형·267fresh/final267·runtime2/shell1final·cleanup true·69.594초·CPU최고17.12%·가용RAM최저42.778%다. 변경 밖 entry/runtime 전체 본문과 worker/PS 입력은 원본과 일치했다. 기존 worker6/PS8/실제 ready 거부는 입력 대조로 보존해 반복하지 않았다.
새 공개 사전검사는 Python 해시 오류 없이232fresh/final232·runtime2/native1/shell1final·cleanup true로 마감됐다. Codex 상위 Job의 종료 정책만 기존 조건대로 거부했고 한글/COM/문서/접근 허용/claim은0이다.69.141초·CPU최고11.79%·가용RAM최저42.824%다. 이는 외부 세션 PASS가 아니다.
560은 코드559·새 공개 사전검사·변경 없는558 worker를 묶어272fresh/final272·runtime2/native1/shell1final·cleanup true로 마감했다.74.313초·CPU최고11.4%·가용RAM최저42.976%다. 모든 단계 보호 중단 없음·004 claim 미소비·새 Native 허가 없음이다.
558은 현재 exe/core 두 이미지·실제 로드 경로/64bit·동일 kernel과 기존 자원 제한·중단 생성/실행 전 Job 배정/사용자 CPU0·읽기 전용 자기검사 종료0·정리와004 worker의 첫 ready 거부를 확인했다.
통과한 핀 모형8/서명 관측/자기검사는 원 입력 동일성을 대조해 보존했고, 실패했던 종료 경합에는 신규4모형을 추가했다. 실제 Job 활성1→0 뒤 같은 핸들을 정상 해제했다.
마지막 worker에는 준비용 CPU guard를 허용하지 않는 기존 Native guard를 그대로 사용했다. 한글 생성자 호출0·worker 요청1/의도된거부exit2·I/O/Job 정리·260fresh/final260·runtime2/shell1/nativeimage1final·cleanup true다.
81.406초·CPU최고18.16%·가용RAM최저39.676%·보호중단없음이다. 555~557 원 실패/최종 fresh 누락과556 cleanup=false는 보존한다.
이는 두 고정 이미지와 제한된 host 경계 자격이며 로드 메모리 전체 해시·현재 Native/COM/8종 자격이 아니다. 역사적 runtime guard와 runtime/trust 파일을 수정하지 않았고004 연결은 별도559에서 검증했다.
551에서004 worker/공개 entry의 신규Python33·PS8과 실제 필수 플래그 누락 거부·245fresh/final245·shell1final·cleanup true를 확인했다.
원 entry/runtime 본문은004 추가 부분을 제거하면 전체 원본과 같고, PS 변환은 고정 경로/검사기 pin과 이름에 한정한다.
실제004 사전검사는 Python image 고정 바이트 불일치로 claim 전 중단됐다. 원27.735초/cleanup true/최종 fresh 누락을 보존하고 재실행하지 않는다.
현재 python.exe/dll은3.12.14·Windows 서명Valid지만 exe SHA가기존dea78bb…에서7a4102b…와 다르다. 서명만으로 현재 Native 자격을 부여하거나 기대해시를 덮어쓰지 않았다.
미사용552 대신 [현재 준비560](evidence/p09-361-capture004-entry-ready560.v1.json)을 사용한다. [관측554](evidence/p09-361-current-python554-observation.v1.json)와 [제한된 host 자격558](evidence/p09-361-current-python-runtime558.v1.json)의 범위를 확대하지 않으며 새 Native 허가는 아직 없다.
사용자가 한글 사용을 별도로 알리기 전까지 필요한 정리를 위임해550에서 정확한 원003 PID24780의 생성 시각/image/세션을 재확인한 held handle 하나를 종료했다.
Hwp/HwpTray0개를 확인했고 원003 FAILED/cleanup=false는 byte-exact 보존한다. Native runtime의 non-killing 정책·원 시험 결과는 바꾸지 않았다.
549는 새004 경로40개와 별도 readonly 검사기를 신규Python5/Rust4·848fresh/final848·실제dep-info2입력·실행파일/dep-info2final·cleanup true로 준비했다.
149.079초·CPU최고23.95%·가용RAM최저40.091%이며 기존 통과 사례/003/Native는 반복하지 않았다. 이후 worker/entry 코드 연결은551에서 검증했으나 현재 세션 자격/8종 허가는 아직 없다.
사용자가 허용한 초기 준비 대기는547의 신규8+영향2 모형 검증 뒤548에서 같은 후보 bytes로 최대15초를 적용했다.
50ms/남은 기한 내 sleep·원 CPU/RAM/PID/owner/입력과 제품10초 제한은 유지한다. 한글 정리 위임은 새 Native/8종 실행 허가가 아니다.
003은3초 input-idle 경계에서7회 조회 뒤 중단돼 고정8종/문서0회·claim 소비·원 cleanup=false·final fresh 누락이다.
실패 후 같은 PID의 input-idle은 관측됐지만 세션/COM 자격이 아니다.550의 사용자 위임 정리 뒤에도 새 Native는 현재 입력 자격과 별도 실행 허가 전까지 보류한다.
외부 Python 종료 확인 후 한글에 연결하지 않는 Cargo 전용 검증은 원 mutex·1코어·CPU/RAM 보호로 분리 실행했다.
002는 사례1 source_bind에서 중단됐고 소비됐으며,
기존 실패를 재실행하지 않는다. 원본 문서 결속 진단487 뒤488/490/491에서 별도 readonly 검사기·산출물40개 경로·
원 제한을 재사용하는 전용 worker와 실제 플래그 누락 거부를 검증했다.492는 공개003 연결의 신규25+영향5 계약30개·236fresh/final236,
실제 공개preflight는229fresh/final229·caller Job만 거부,493은 실제 원1% worker ready/kernel 확인 뒤 거부·Native constructor0회·239fresh/final239다.
494는 entry224개와 현재 준비 묶음의244fresh/final244·cleanupTrue를 확인했다. 원 시험·빌드·Native를 반복하지 않았고
그 준비 결과를 실제003 세션 자격으로 승격하지 않는다.003은 이후 실제 시도됐고 실패했으며 재실행을 금지한다.
상세 범위는 [현재 CROSSREF 준비](P09_CROSSREF_QUALIFIED_ENTRY_PROGRESS.md)를 따른다.
현재 공식158/249와 잔여91·source v13 미해결4·P09/A12/A13 OPEN을 변경하는 결과가 아니다.

### 원본 글꼴 선언 조건 구현과 제품 경로 검증

2026-10-22 외부003 실행 상태 확인 대기 중 고정 입력과 분리된 원본 글꼴 조건 검색을 연결했다.
7개 언어별19개 선언 속성을 기존 명시적 definition·v7·required direct v9 경로에 연결하고,
문자별 문자열·regex 재평가 대신 선언별 판정표를 사용한다. 결과와 변환 영수증에서는 원문 조건 대신 해시·언어만 출력하며 요청 정규형에는 원 조건을 결속한다.
변경 전 소스69개와 문서2개를 p361-font-definition503에 보존했고 소스 시험8개·제품 시험5개를 추가했다.
503은 원본23개 관측 뒤 ID 참조 검증 실패,504는 writer6/stored7 관측 뒤 v4 범위 기대값 오류를 보존했다.
font/substFont 바이너리 참조가 있으면 기존 명시적 font/text profile을 선택하고 누락된 manifest 대상을 거부한다. 그 참조가 없으면 원 v6/v9 profile을 유지한다.
v4 일반 본문과 v7 숨김·메모 포함 범위를 같은 입력의 필터 없는 대조로 구분한505는 현재source24+stored8=32개·944fresh/final944·dep-info2final·cleanupTrue다.
504의 통과31개와 라이브러리/검증기/fixture·다른 시험 본문 동일성을 대조해 수정1개만 실행했으며 큰798요청 행렬을 반복하지 않았다.
126.203초·CPU최고28.52%·가용RAM최저37.652%·보호 중단없음이다. 실제 시험 단계5.563초와 그 밖의 준비/입력 마감 시간을 구분한다.
502의 기존25개는 당시 결과로 보존하고 현재32개는505의 현재 입력 마감에 결속한다. 실제 표시·font payload·Native·P09 Gate의 수용은 아니다.
상세 요청·개인정보·검증 경계는 [원본 글꼴 선언 조건](../../protocol/migrations/p09-font-definition-search-v1.md)을 따른다.

### 실제 참조된 탭 정의 조건 구현과 제품 경로 검증

2026-10-22 문단 정의의 `tabPrIDRef`가 가리키는 자동 탭·탭 개수·순서별 위치/정렬/채움선/단위 조건을 기존 v3/v4/v7/v9에 연결했다.
직접/이름 붙은 문단 축과 호환 current/fallback 분기를 구분하고, 단위의 부재를 기본값으로 추정하지 않는다.
기존 typed 탭 reader는 그대로 사용하며 정의별 판정표로 문자별 XML/조건 재평가를 피한다.
[510](evidence/p09-361-tab-definition510.v1.json)은 현재source11+stored8=19개·968fresh/final968·dep-info2final·cleanupTrue다.
508에서 관측한10개는 입력/본문 동일성 및 변경된 helper의 영향 범위를 대조해 반복하지 않고 수정1개·미실행8개만 실행했다.
16종 양성/음성의96개 저장 요청, 네 범위, 실제 변환 후보 재import, strict 입력·개인정보·ACL/AEAD/RouteUnqualified를 확인했다.
186.422초·CPU최고24.41%·가용RAM최저33.723%·보호중단없음이다. 506~509 원 실패/final fresh 누락은 보존한다.
505의 글꼴32개는 당시 입력의 검증이며 새 코드 전체32개 재수용으로 승격하지 않는다. 이번 직접 영향 글꼴 조건은510의19개 범위에 포함된다.
상세 요청과 경계는 [원본 탭 정의 조건](../../protocol/migrations/p09-tab-definition-search-v1.md)을 따른다.
새 Native·공식249·외부003은 실행하지 않았으며 공식158/249·잔여91·P09/A12/A13 OPEN·P10미시작은 그대로다.

### 1 관측된 제품 시험 결과 마감

436에서 카탈로그 마스킹 신규42개와 공통 compiler 영향3개의 본문45개가 exit0으로 통과했다.
종료 후 입력 재확인에서 CPU90.82% 보호가 작동했으므로 현재는 정식 수용이 아니다.

1. 최종 입력 재확인 전 PASS를 넣는 recovery runner의 순서를 수정한다.
2. 실패 시 final fresh 진행량과 본문 관측 상태를 보존하고 비정상 결과는 nonzero로 종료한다.
3. 원436 bytes/SHA, 정확한45개 목록, 원 입력/실제 dep-info/설치 설정, 소유 Job 정상 종료를 확인한다.
4. 제품·시험 코드는 원436과 동일할 때만 별도 입력 마감으로 판정한다. 본문·Cargo·Native를 다시 실행하지 않는다.

완료 증거는 원436을 덮어쓰지 않는 새 결과의 전체 입력 전후 확인·cleanup과45개 수용 근거다.
이 결과로 공식249 큐나 Native 실행을 수용하지 않는다.

### 2 공통 실행과 저장 연결

2026-10-22 공통 공개 요청에서 실제 격리 PostgreSQL schema24까지 한 사례를 연결했다.
520 본문은 실제 claim/lease·등록 CAS·완료·HWPX/AES readback·manifest/locator 원 경로4개 부재에서의
재시작 전후 기존 결과 복구·잘못된 키 거부를 관측했다. 소유 postmaster 정상 종료와 DB/blob 불변도 기록했다.
그러나 부모 전체 마감 영수증의256KiB 발행이 실패해 현재 전체 소스 SQL 수용은 아니다.
[발행 실패 기록](evidence/p09-361-search-sql520-publication-failure.v1.json)과 원520 관측을 보존하며 본문은 반복하지 않는다.
다음 마감은 잃은 부모 표본을 추정하거나 재구성하지 않고 현재 소스/빌드의 증거 결속을 별도로 설계해야 한다.

Windows 시계 해상도와 저장소 내부 절대경로 입력 검사를 고쳤고, 증거 형식은 무손실 사전/시각 prefix로 최적화했다.
[521](evidence/p09-361-search-sql-receipt521.v1.json)은 IO/시계7+형식6=13개·189fresh/final189·cleanupTrue,
25초·CPU최고27%·가용RAM최저40.402%다. 입력1062개/자원1210표본 모형을239427bytes로 발행했으며
원256KiB 한도와 원 표본/자료형을 보존했다. 실제 SQL·Cargo·Native·공식249는521에서 실행하지 않았다.
521은520 전체 마감 PASS의 대용이 아니다. 23계열 전체 실DB·운영 registry/키·Native·Gate는 여전히 별도다.

2026-10-22 일반23계열에 조회 우선 진입점과 원 등록 archive 복구 연결을 추가했다.
완료/진행 중 관측은 source/head/후보/compiler 없이 반환하고, 미관측일 때만 원 제품 준비를 수행하며 오류는 준비로 fallback하지 않는다.
[515](evidence/p09-361-search-lookup515.v1.json)은 신규30개·1017fresh/final1017·dep-info1final·cleanupTrue다.
23계열 모두 원 canonical/scoped hash 및 저장 job lookup 결속을 대조했고 공통7개로 strict/current scope·불확실/충돌·등록 locator·관측 변경 거부를 확인했다.
164.125초·CPU최고38.67%·가용RAM최저36.301%·보호중단없음이다. 514의 컴파일 실패/시험0과 final fresh 누락, 이전513의31개는 원본으로 보존했다.
등록 자료 부재 모형을 독립 효과 복구나 운영 SQL PASS로 승격하지 않는다. [조회 우선 계약](../../protocol/migrations/p09-search-request-observation-v1.md)을 따른다.

2026-10-22 일반 검색·변환23계열에 공통 저장 bridge와 현재 commit guard를 연결했다.
[513](evidence/p09-361-search-storage513.v1.json)은 계열별 실제 HWPX 검증·암호화 저장/다운로드·두 번의 현재 guard·revision CAS23개와 안전/복구8개의 현재31개·984fresh/final984·dep-info1final·cleanupTrue다.
511의 통과8개와512의 통과21개는 입력/본문과 변경 fixture 영향 범위를 대조해 보존하고 글꼴2개만 실행했다.
최종133.188초·CPU최고25.45%·가용RAM최저38.794%·보호중단없음이며 원 실패와 final fresh 누락은 보존한다.
원 strict key를 서버 tenant/project ID에 결속하는 job 준비, 일회성 실제 산출물 readback, 저장 전/최종 CAS 거부와 복구 자료 보존을 확인했다.
이는 시험 repository/scanner/key와 합성 routing snapshot의 실행이며 운영 SQL·현재 신뢰 registry·Native·실제 제품 실행 자격이 아니다.
[공통 저장 연결 계약](../../protocol/migrations/p09-search-mutation-storage-v1.md)을 따른다. 아래 목록은 실제 제품 Gate의 전체 완료 조건이며 이번31개로 닫지 않는다.

카탈로그의 현재 설정 dependency를 보존하면서 기존 operation compiler/router/manifest 경로에 연결한다.
공통 변경 후보에서 실제 executor·scanner·validator·저장 coordinator까지 한 수직 경로를 완성한 뒤
동일 경로에 다른 변경 family를 연결한다. context-free 요청에 설정을 추정해 넣지 않는다.

필수 작업은 다음과 같다.

1. 현재 source/ACL/head/카탈로그와 실제 plan/owner를 execution manifest에 결속한다.
2. 기존 router의 현재 target·신뢰 registry·backend health·보호·보존·시간 검사를 재사용한다.
3. 준비/preview/manifest 데이터가 실행·승인·key claim 권한을 발급하지 못하게 한다.
4. 실제 실행 결과를 scanner/의미 validator·artifact·revision·head CAS·게시로 원자적으로 연결한다.
5. 영속 멱등·job/attempt/lease·철회·경합·부분 반영 거부와 복구를 실제 저장 경로에서 검증한다.
6. 네트워크 단절·crash·키 유실 복구와 시험 임시 키 밖의 custody를 마감한다.

P02의 routing_allowed=false와 RouteUnqualified는 실제 자격 근거가 생길 때까지 유지한다.
합성 router 또는 DB fixture 통과를 신뢰 registry/실제 문서 의미/제품 실행 자격으로 쓰지 않는다.

### 3 원본 의미와 기능별 잔여 구현

2026-10-22 [545](evidence/p09-361-https-late-revoke-sql545.v1.json)의 새 격리 SQL26 사례는 마지막 앱 정책 읽기 직후 실제 정책을 철회했다.
원 coordinator/실제 claim·lease·등록 intent가 진행된 뒤 원 SQL CAS가 거부됐고 결과/intent/precommit AEAD 증거·원본·head1을 보존했다.
후속 집계가 미소비 authorization을0개로 기대해 전체545는 FAILED이며 finalfresh0·재시작 미실행이다. 통과 본문은 반복하지 않았다.
기록된191bytes 집계 stdout의 SHA와 정확히 일치하는 projection은 artifact7/job2/attempt2/authorization1/intent1/revision1/seal1/head1이다.
SQL23의 lease authorization은 원 CAS 전 거부 시 소비되지 않는다.547은 이 기대값과 실패 전 집계 보존 수정의5개 모형을 확인했으며 원545 전체 PASS로 승격하지 않았다.
같은547의 승인된 startup 후보 신규8+영향2를 포함해15개·213fresh/final213·cleanup true다.548은 검증 후보와 실제 파일의 일치를 확인해 준비 대기만15초로 적용했다.
215fresh/final215·cleanup true·CPU최고13.28%·가용RAM최저43.746%이며 제품10초·원 보호와 Native 미실행을 유지한다.

2026-10-22 신뢰 서버용 `run_atomic_sql_job`에서 원본/정책 버전·계획을 자동 결속하고 원 CAS transaction 안에 SQL26 정책 잠금 검사를 추가했다.
원 lease/canonical request/인자/SQL/outcome 본문은 그대로 재사용하며 기본 CAS는 no-op precondition을 쓴다. 정책/branch와 tenant/project/멤버십·아티팩트/ACL 잠금은 같은 commit/rollback까지 유지한다.
provider 비공개 서비스/인증 필드는 공개하지 않았고 읽기 전용 정책/계획 데이터만 전달한다. 별도 CAS·source/output/validator를 호출자가 고르는 인자는 없다. 공개 transport/실행 허가도 열지 않았다.
[543](evidence/p09-361-https-atomic-sql543.v1.json)은 새 schema26에서 철회·잘못된 정책 결속 거부, guard 두 연결의 철회/등록/멤버십/양쪽 ACL 변경 잠금 충돌55P03와 해제 뒤 재잠금,
과도 guard 권한/함수 변조 거부와 복원/재인증, 새 진입점의 실제 claim/lease/등록·동일transaction CAS·completion·AEAD/원본 보존·재시작 전후 같은 공개 요청의 등록 효과 복구를 확인했다.
전후 정책2/철회1/latest2·artifact9/job2/attempt2/intent1/revision2/seal2/head2·ciphertext가 같고 bootstrap1+HTTPS1이다. guard 두 연결 시험은 제품 CAS의 모든 경합 시점 시험과 구분한다.
881fresh/final881·실제 dep-info46개 입력 사전 결속·실행파일/dep-info2final·경고없음·cleanupTrue다. 전체422.079초·Cargo15.063초·SQLworker245.375초(전체 런타임 전후 해시 포함)다.
시스템 CPU최고41.73%·가용RAM최저36.379%·보호중단없음·Job1코어/CPU6.25%·최고private compiler1089.02MiB/SQL94.57MiB·종료프로세스0이다.
542의 비공개 필드 E0616 네 건/SQL0회/finalfresh없음은 보존하고 필드 공개 없이 실행 본문 위치를 고쳤다. 기존 통과 시험/소비DB/SQL520/003/Native는 재실행하지 않았다.
운영 배포·신뢰 registry/실제worker/admission·공개 제품 경로의 새 진입점 선택·장기 키 보관·Native/Gate는 남고 공식158/249·잔여91·v13미해결4·P09/A12/A13 OPEN·P10미시작을 유지한다.

2026-10-22 HTTPS 정책을 서버의 실제 AES 발급·전용 SQL25 등록/최신 선택/철회·editor/양쪽 ACL/관리 권한·branch 잠금/generation CAS에 연결했다.
기존23/24 연결은 그대로25를 거부하며 새 연결도 원 보안 검사와 HTTPS 함수 본문/권한/RLS/불변 경계를 확인한다. 공개 발급 transport나 실행 권한은 열지 않았다.
[541](evidence/p09-361-https-policy-sql541.v1.json)은 새 소유 schema25에서 발급/철회/다음 세대, 오래된 후보 거부, 실패 발급의 Evidence 보존,
reader/권한·ACL 상실/세대·head·principal 거부와 과도 권한/RLS 해제/SQL 본문 변조 거부를 검증했다. 시험 권한·함수·RLS는 제품 작업 전 복원/재인증했다.
그 실제 정책으로 원 coordinator의 claim/lease/등록CAS/completion과 재시작 전후 공개 요청의 같은 효과 복구를 확인했다. 원 HWPX·암호문·4개 로컬 경로를 보존했고 제품 실행을 재시도하지 않았다.
정책 versions2/revocations1/latest2, artifact9/job2/attempt2/intent1/revision2/seal2/head2가 전후 동일하며 bootstrap1+HTTPS1과 실패 발급의 보존 Evidence를 포함한다.
885fresh/final885·실제 example dep-info44개 사전 결속·실행파일/dep-info2final·경고없음·cleanupTrue다. 전체409.391초·Cargo4.141초·SQL worker243.437초(전체 런타임 전후 해시 포함)다.
시스템 CPU최고23.05%·가용RAM최저36.567%·보호중단없음·Job1코어/CPU6.25%·최고private compiler772.0MiB/SQL86.41MiB·종료프로세스0이다.
538의 경고/SQL0회와539/540의seed CHECK23514/제품0회·final fresh 없음은 보존했다. Debug·reader 역할명·마지막 관리자를 지키는 시험을 고쳤으며 제품/DB 제약을 완화하지 않았다.
기존 통과 시험·소비한 DB/SQL520/003/Native는 재실행하지 않았다. 운영 배포·외부 issuer/worker/admission·원자적 정책 실행 결속·장기 키 보관·Native/Gate는 남는다.
공식158/249·잔여91·next165·source v13미해결4·P09/A12/A13 OPEN·P10미시작을 유지한다.

2026-10-22 HTTPS의 관측 wrapper에 기존 등록 효과의 읽기 전용 복구를 연결하고 새 소유 PostgreSQL schema24로 검증했다.
[537](evidence/p09-361-https-target-sql537.v1.json)은 실제 보존 HWPX의 엄격한 요청→자동 guard→원 coordinator→실제 claim/lease/barrier→등록 intent/precommit→단일CAS→completion을 확인했다.
실제 metadata SQL/디스크 AES와 원 source 보존을 확인했고, 서버 재시작 전후 원 공개 요청만으로 같은 등록 효과를 복구했다.
상태·정책 선택·완료 핸들·요청4개 원 경로는 조회 중 보존했다가 byte-exact 복원했다. 같은 key의 다른 요청은 KeyConflict, 없는 요청은 NotObserved,
틀린 AES 키는 거부하며 복구에서 claim/engine/CAS를 재시도하지 않았다. SQL 수는 전후 artifact7/job2/attempt2/intent1/revision2/seal2/head2로 같고 bootstrap1+HTTPS1이다.
850fresh/final850·example 실제dep-info42개 입력 사전 결속·실행파일/dep-info2final·경고없음·cleanupTrue이며536의8개/기존 시험/SQL520/003/Native는 반복하지 않았다.
전체410.875초·Cargo13.812초·SQL worker241.329초이며 worker에는 PostgreSQL 전체 런타임의 제한 속도 전후 hash 검사가 포함된다.
시스템CPU 최고32.83%·가용RAM최저35.194%·보호중단없음·Job1코어/CPU6.25%·최고private compiler1085.79MiB/SQL77.41MiB·종료프로세스0이다.
정책 아티팩트는 실제 AES/SQL이지만 선택자/route/scanner는 격리 fixture이고 키는 임시다. 운영 policy SQL/issuer·attested worker/admission·원자적 정책 결속·장기 키 보관·Native/Gate는 남는다.
공식158/249·잔여91·next165·source v13미해결4·P09/A12/A13 OPEN·P10미시작·003/SQL520실패는 유지한다.

2026-10-22 HTTPS 작업 준비에서 현재 source/policy/route guard를 공통 coordinator에 자동 부착했다.
현재 snapshot 실패 시 callback 전 거부하고 guard 교체를 막으며, 원 coordinator가 claim 전·ingest/final-CAS 검사를 수행한다.
실제 보존 P02 서명 인증이 되어도 현재 routing 금지로 source/policy/claim 전 거부한다. trust/키/registry와 기존 runtime 본문은 바꾸지 않았다.
[536](evidence/p09-361-https-target-job536.v1.json)은 신규8개·838fresh/final838·실제dep-info1final·경고없음·cleanupTrue다. 저장8개/요청22개는 반복하지 않았다.
메모리 lifecycle 모델에서 등록영수증/archive→단일CAS→완료, replay/불명확응답/다른lease/정책철회 시 재시도 차단과 원head/실제효과/영수증 보존을 확인했다.
실제 SQL·worker 등록·발급자/운영 durable job/제품 route/Native/Gate 자격이 아니다. Completed는 저장 primitive 상태만 뜻한다.
전체131.984초·CPU최고44.32%·가용RAM최저35.797%·보호중단없음·Job1코어/CPU6.25%·최고private1085.75MiB·종료프로세스0이다.
운영 policy SQL/issuer·attested 등록·실제 영속claim/job/CAS·Native/Gate는 남고 공식158/249·잔여91·next165·P10미시작은 그대로다.

2026-10-22 HTTPS의 현재 source/policy 결속을 원본 공통 router/manifest·저장 준비·검사기·job ID/commit binding에 연결했다.
새 저장 실행기를 만들지 않고 공통 로직을 공유하며 검색의 기존 hash/job/CAS/guard 본문을 유지한다.
각 ingest/final-CAS 경계에서 원본·정책·최신 route/time을 확인하고 첫 guard 실패를 고정한다. manifest/job 준비는 등록/키 선점/제품 실행 허가가 아니다.
[535](evidence/p09-361-https-target-storage535.v1.json)은 HTTPS6+기존검색 문서/문단 범위2=8개·833fresh/final833·실제dep-info1final·경고없음·cleanupTrue다.
원 HWPX의 engine→일회성 staged 검사→실제 AES/readback→메모리 revision CAS와 중간 철회 시 원head/ingest결과 보존을 확인했다.
기존 요청22개는 동일성을 대조해 보존하고 반복하지 않았다. 합성 route/scanner/policy·메모리 저장소로 운영 SQL/등록/durable job/Native/Gate에 승격하지 않는다.
전체124.813초·CPU최고69.73%·가용RAM최저44.335%·보호중단없음·Job1코어/CPU6.25%·최고private1085.46MiB·종료프로세스0이다.
CPU peak의 기여와 과거 프리즈 원인은 미확정이다. 운영 policy SQL/issuer·attested 등록·영속claim/job/등록CAS·Native/Gate는 남으며 공식158/249·잔여91·next165·P10미시작은 그대로다.

2026-10-22 엄격한 HTTPS 제품 요청과 공통 scoped 중복 조회를 연결했다.
객체 형태/중복/미지 필드·source/head/선택 hash·HTTPS 값을 원본 읽기 전에 검사하고, raw/canonical/scoped 해시를 provider 범위와 compiled receipt에 결속한다.
기존 Borrowed/Owned 패턴으로 원본을 이동해 소유 후보를 반환하며 전환에 따른 추가 graph/출력 복제는 없다. 정책 repository 없는 원 API는 명시적으로 거부한다.
관측 우선 entry는 Existing/조회 오류에서 원본/head/policy/compiler/CAS를 실행하지 않고 NotObserved에서만 준비한다. 관측은 키 선점·독립 효과 증거가 아니다.
[534](evidence/p09-361-https-target-request534.v1.json)은 수정1개+533동일런타임/본문17개 마감+기존조기거부4개 보존의 고유22개,
834fresh/final834·실제dep-info1final·경고없음·cleanupTrue다. 새8개+소유권 영향10개만 선택했으며 수정 때17개를 반복하지 않았다.
533의 all-zero fixture 실패/17pass/경고2/final fresh 없음을 보존하고 비제로 변경 결속/zero 거부를 분리했다. 공통 조회 guard는 바꾸지 않았다.
최종122.390초·CPU최고23.05%·가용RAM최저34.322%·보호중단없음·Job1코어/CPU6.25%·최고private1082.65MiB·종료프로세스0이다.
운영 policy SQL/issuer·attested registry/manifest·영속claim/job/CAS·Native/Gate가 남고 공식158/249·잔여91·next165·P10미시작은 그대로다.

2026-10-22 저장 HTTPS 후보를 원본 `OperationPlanCompiler`와 공통 실제 소유자 판정기에 연결했다.
선택한 필드 앵커만 보관하고 후보를 이동하므로 추가 전체 graph 복제·field 의미 import·lowerer/writer 재실행은 없다.
REF-034 계획은 현재 source graph/revision·정책 버전/아티팩트·원본/출력/receipt·선택 field/meaning/target digest를 결속하며 URI 원문을 넣지 않는다.
컴파일 전후와 전달 전 현재 정책/원본 권한을 유지한다. 로컬 catalog/계획은 attested registry나 실행 권한이 아니다.
[532](evidence/p09-361-https-target-compiler532.v1.json)은 수정1개+531동일본문9개 마감+원조기거부4개 보존의 고유14개,
831fresh/final831·dep-info1final·경고없음·cleanupTrue다. 새5개와 앵커 보관 영향5개만 선택했고 원 조기거부4개/249는 반복하지 않았다.
531의 잘못된 그래프 위치 가정 실패/9pass/final fresh 없음을 보존하고 실제 ctrl 구조의 독립 XML 범위 대조로 시험1개만 수정했다.
최종108.641초·CPU최고22.57%·가용RAM최저35.898%·보호중단없음·Job1코어/CPU6.25%·최고private756.55MiB·종료프로세스0이다.
운영 policy SQL/issuer·요청/idempotency·attested registry/manifest/job/CAS·Native·전체Gate는 남으며 공식158/249·잔여91·next165·P10미시작은 그대로다.

2026-10-22 현재 저장 원본의 ACL/AEAD/head와 저장소가 선택한 불변 HTTPS 정책 아티팩트를 변경 후보에 연결했다.
쓰기 scope·정확한 source/policy 결속·엄격한 정책 JSON·다중 필드 원자적 거부를 유지하고, 전달 시 양쪽 ACL/철회/최신 정책과
원본/head를 fresh 확인한다. writer 무결성 callback 안의 마지막 정책/head 검사도 유지하며 lowerer/writer는 반복하지 않는다.
[530](evidence/p09-361-stored-https-target530.v1.json)은 수정1개 실행+본문/입력이 같은528의 통과8개 보존·고유9개,
831fresh/final831·dep-info1final·경고없음·cleanupTrue다. 527 컴파일 실패와528/529의 잘못된 미래 revision fixture 실패를 보존했다.
최종110.203초·CPU최고41.9%·가용RAM최저35.804%·보호중단없음이며 소유 Job1코어/CPU6.25%·종료프로세스0을 확인했다.
운영 정책 issuer/SQL·프로젝트 쓰기 권한 repository·원자적 policy lease·공통 실행/job/저장/CAS·Native/Gate는 남는다.
route는 계속 거부하며 공식158/249·잔여91·next165·P10미시작을 변경하지 않는다.
[저장된 원본 HTTPS 후보 계약](../../protocol/migrations/p09-stored-https-target-candidates-v1.md)을 따른다.

2026-10-22 원본 HTTPS 필드의 실제 목적지 변경 후보를 연결했다.
평가 API의 원 reference/field/meaning 결속에서 정확한 새 HTTPS policy 승인과 기존 patch/writer로 이어지며,
한 transaction에서 Command/Path만 변경하고 전체 출력 의미·미선택/편집 밖 바이트를 확인한다.
정책은 한 번 검증한 borrowed view에서 binary search하고, 기존 tracking/lock guard와 파트별 prefix를 공유한다.
[526](evidence/p09-361-source-https-target526.v1.json)은 현재14+보존 policy3의 고유17개·836fresh/final836·dep-info3final·cleanupTrue다.
원 policy3은 반복하지 않았으며 실제 정책/보호 코드가 바뀐 source7은 영향 범위로 다시 확인했다.
524의 잘못된 보호 fixture/3경고/실패와525 사전 대조 오류/명령0을 원본에 보존했다.
전체258.5초·CPU최고81.42%·가용RAM최저29.777%·보호중단없음이다. CPU 순간 peak는 간접/외부 기여 미확정이며
소유 Job1코어/CPU6.25% 제한 readback을 확인했다. 프리즈 해결로 승격하지 않는다.
이 bytes 후보 자체는 stored ACL/head 권한이 아니며 위 별도 stored 연결과 구분한다.
운영 서버 policy·compiler/job/저장/CAS·Native update/reopen은 남고 원본/기존Gate는 변경하지 않았다.
[원본 HTTPS 변경 후보 계약](../../protocol/migrations/p09-source-https-target-changes-v1.md)을 따른다.

2026-10-22 원본 필드 의미의 별도 제품 API와 빌린 의미 인덱스를 연결했다.
기존 HTTPS six-parameter·표 수식 reader를 공유하고 인덱스에서 전체 graph 추가 복제를 없앴다.
원본 전체 field coverage·정확한 source SHA/출력 한도·미지원/잘못된 지원 의미의 구분과 비노출을 유지한다.
토큰 검사는 불변 요소 범위만 읽되 원 token-kind/owner 조건은 그대로다.
[523](evidence/p09-361-source-field-semantics523.v1.json)은 신규9+영향6=15개·849fresh/final849·dep-info2final·cleanupTrue,
186.015초·CPU최고45.31%·가용RAM최저31.925%다. 실제 보존 HTTPS1개와 수식16개를 읽기 전용으로 확인했다.
522의 unit3 본문 관측/공통 fixture2개 누락/final fresh 없음은 보존했고3개를 재실행하거나 정식 수용으로 올리지 않았다.
원 v13과 미해결4·전체 flow/edge/cache/Native·Gate는 그대로다.
상세 API와 한도는 [원본 필드 의미 평가](../../protocol/migrations/p09-source-field-meaning-assessment-v1.md)를 따른다.

원본 참조 API v13의 OtherTargetFamilies, ReferenceEdgeSemantics, CompleteAuxiliaryState,
DocumentFlow를 실제 원본 관측으로 채운다. 불완전한 import를 완전한 state/flow로 기본값 처리하지 않는다.

검색19개는 전체 필터·유효 서식 cascade/visibility·다른 제어·실제 쪽/흐름 이동·중첩 정렬·전체 폰트/스타일
옵션과 실행/저장/target 계약을 마감한다. 기존 core·현재 저장·strict JSON·compiler의 수용분은 재사용한다.

참조46개는 필드10, 양식8, 각주/미주/숨은 설명6, 메모4, 책갈피/하이퍼링크/상호참조5,
차례/색인5, 인용/메일머지2, 보조 참조6의 실제 의미·변경·저장·readback 경계를 기능 계약에 대조한다.
전체 목록은 FEATURE_COVERAGE_MATRIX.csv의 phase=P09와 아래 기능별 현황을 따른다.
P11 소유 REF-016/020/036/040/043/045/047 및 SEARCH-011/012/015~018은 P09 잔여에 합치지 않는다.

### 4 실물 검증의 선행 장애 해소와 묶음 실행

이 준비는 순서3 전체가 끝날 때까지 미루지 않는다. 실물 관측이 참조 의미 구현의 선행 조건이므로,
로컬 구현 중에도 세션 장애를 먼저 검토하고 준비가 끝나는 즉시 묶음 실행 범위를 확인한다.

외부 CROSSREF run001은 exact_existing_owner에서 실패했고 claim001은 소비됐다. 먼저 남은 세션 상태와
실패 진단을 확인하고 현재 코드의 세션 자격을 다시 판정한다. 기존 외부 명령·Native008/009/010은 재실행하지 않는다.
Native011은 별도 승인과 현재 자격이 필요하다. 문자 스타일6종은 사용자 선택·실행 범위가 필요하다.

현재 남은 PID29824는 사용자 확인과 별도 읽기 승인 뒤474/475에서 관측했다. ROT 한글 후보1개와 원 어댑터의
창/커널/version 일치 읽기는 성공했으며 한글/문서/접근 허용/새8종은 실행하지 않았다. 과거 run001의 원인 확정은 아니다.
초기화 대기 없이 resume 직후 연결하던 순서에 같은 held process의 최대3초 입력 idle 대기를 추가했고476에서 신규10+영향2 모형을 통과했다.
476 당시 실제 Native 적용은 NOT_RUN이었다.002에서는 초기 입력 idle과 exact owner 결속이 관측됐지만 전체 Native/참조 의미 자격은 아니다.
원 exact owner/자원/재실행 금지는 유지한다.
남은 세션 정리는 아래477에서 완료했다. 다음 실물 경계는 현재 입력 재자격·새 실행 범위 확인이다.
사용자의 종료 요청 뒤477에서 같은 PID29824를 정상 Quit했고 Hwp/HwpTray0개를 확인했다. 원 실패는 보존한다.
새 고정 실행002의 준비는478 모형23개·실제 공개 preflight의 원 caller Job 거부·480 실제 worker 첫 요청 거부/정리를 마쳤다.
479는240fresh/final240·cleanupTrue이며 현재219개 entry 입력과 각 사례 idle helper를 결속했다.
사용자가 허용한002 claim/run은 소비됐다. 정확한 COM owner/정상 종료와 qualification 경계 뒤 첫 사례 source_bind에서 중단됐다.
사례1은 부분 실행·완료0·나머지7개 NOT_RUN이며 최종 cleanupTrue다. 전체/사례 최종 fresh 누락을 보존한다.
484에서 사례 하위 오류를 버리던 반환 경로를 수정하고 Python6 보존·새 PS6·영향 release10 및194개 입력 전후 확인을 마쳤다.
실제 source_bind 원인은 아직 미확정이다. 다음 실물 실행은 현재 입력 재자격·새 고정 산출물 경로·별도 실행 범위가 필요하며001/002를 재사용하지 않는다.

검증할 고정 사례·산출물·저장/재열기·독립 readback·정상 종료 조건을 실행 전에 한 묶음으로 준비하고,
새 실행 범위와 필요한 사용자 조작을 모아서 요청한다. 승인 또는 세션 자격이 없을 때는 구현3을 진행한다.
단순 캡처·SDK callback·JSON/해시를 참조 의미와 Native 저장/재열기 PASS로 승격하지 않는다.

### 5 잔여 회귀와 최종 Gate

기능/공통 경로 변경을 안정화한 단위로 회귀를 수행한다. 공식 큐는158/249·next165에서 재개하되
새 실행 권한과 현재 runtime 자격이 전제다. 기존 통과분은 원 입력 세대에 보존하고, 변경 영향이 있으면
해당 부분만 현재 코드로 검증한다. 최종 통합 감사에서 적용 범위·누락·중복과 필수 부정/복구/보호 사례를 대조한다.

완료에는 실제 match_set·semantic readback·field/reference update·저장/재열기·필요 렌더/차분,
현재 신뢰 registry/실행 경로·원자적 저장/게시·복구, 기능별 required fixture와 negative 조건이 필요하다.
계약/schema/migration·capability registry·ROADMAP_STATUS·CURRENT_STATE·handoff를 같은 완료 범위에 맞춘다.
모든 요건의 권위 있는 증거가 있을 때만 P09/A12/A13을 닫고 P10으로 진행한다.

## 현재 실행 위치

- HTTPS 서버 정책을 명시한 공통 후보 선택은562에서 연결했다. `prepare_json_with_https_policy`와 공통 enum의 정책-aware 바이트/route 메서드는 원 준비·현재 정책·ACL/AEAD를 재사용한다. 정책 없는 기존 API는 계속 거부하고 원 `RouteUnqualified`도 유지한다.
  공통 분류는 한 번 수행하고 다른 계열은 전체 본문이 동일한 private helper로 위임하며 HTTPS 저장소를 읽지 않는다. 원 소유 후보를 기존 manifest/job에 넘길 수 있지만 실행·게시 권한은 아니다.
  신규7+영향1의 고유8개 중561의 통과7개는 제품/본문/입력 동일성을 대조해 보존했다. 원561은 불완전한 양식 외부 봉투 시험1개 실패/최종fresh0이며,562는 봉투만 고친1개를 실행했다. 원 실패/거부 기대를 유지하고 다른7개는 반복하지 않았다.
  853fresh/final853·실제dep-info1final·경고없음·cleanup true·112.390초·CPU최고14.26%·가용RAM최저40.298%다. 실제 보존 HWPX와 현재 저장 서비스/정책 재확인까지며 저장소/scanner/key는 시험용이다.
  새 SQL·운영 issuer/registry/worker·공개 transport의 원자적 실행 선택·장기 custody·Native/Gate는 아직 별도다. [공통 후보 계약](../../protocol/migrations/p09-stored-https-target-candidates-v1.md#서버-정책을-명시한-공통-후보-진입점)과 [562](evidence/p09-361-https-common-dispatch562.v1.json)을 따른다.
- HTTPS 새 저장 진입점은543에서 정책 최신/철회·권한을 원 CAS transaction에 잠금으로 결속했다. 원 CAS/lease/outcome 본문은 유지하고 같은 SQL transaction 안에서 정책 guard를 실행한다.
  다음은 신뢰 registry·실제 worker/admission과 공개 제품 경로의 새 진입점 선택을 연결하는 단계다. 장기 키 보관·Native/Gate는 별도이며 그 전까지 기존 route 거부를 유지한다.
  한글 종료 승인은 대기로 두며 이전 실행을 재실행하지 않는다. 아래는 각 입력 세대의 이력이다.
- HTTPS는541에서 실제 SQL 정책의 발급/최신 선택/철회·현재 쓰기/관리 권한을 원 작업 coordinator와 재시작 복구에 연결했다.
  당시 남았던 정책/CAS transaction 결속은543의 새 저장 진입점에서 확인했다. 기존 fresh guard만 사용하는 준비 경로는 원자적 lease로 승격하지 않는다.
  운영 배포·외부 발급자와 실제 worker/admission 자격·장기 키 보관·Native/Gate는 별도다. 한글 종료 승인은 대기로 두고 이전 실행은 재실행하지 않는다.
- HTTPS는537에서 새 격리 SQL의 실제 claim/lease/등록CAS/completion과 재시작 전후 공개 요청의 등록 효과 복구까지 확인했다.
  원 상태/정책 선택/완료/요청4개 경로 부재 상태에서도 복구했고 모두 byte-exact 복원했다. 같은 작업/시도·ciphertext·head를 유지하며 재실행하지 않았다.
  537 당시의 시험용 정책 선택자는541에서 실제 SQL 발급/최신 선택/철회·쓰기 권한으로 연결했다. 운영 배포와 외부 issuer/admission/worker 자격·임시 키 밖의 custody·Native/Gate는 별도다.
  한글24780 종료 승인은 대기 상태로 두며003/SQL520/이전Native는 재실행하지 않는다. 아래 항목은 해당 입력 세대의 이력이다.
- 순서3의 실제 글꼴 선언 조건을 연결하기 전에 공통 matcher의 반복 정의 비교를 최적화했다.
  큰 필터를 참조로 빌리고 마지막 선택 정의 쌍만 보관해 전역/heap 캐시 없이 연속 비교를 재사용한다.
  [502](evidence/p09-361-style-predicate502.v1.json)은 원19개를 반복하지 않고 새 review1·미실행 제품5를 확인해
  현재25개·854fresh/final854·실제 compiler dep-info2final·cleanupTrue다.500의 fixture 경고와501의 시험 helper 실패는 보존한다.
  최종502의 CPU최고26.67%·가용RAM최저37.825%·보호 중단없음이며 공식 큐·Native·003은 실행하지 않았다.
  이어진 글꼴 선언 조건은505에서 당시32개를 마감했고, 탭 정의 조건은510에서 현재19개를 마감했다. 각 결과의 입력 세대와 범위는 위 두 구현 절을 따른다.
- 순서3의 참조된 테두리 정의 검색을 글자·문단 세부 조건과 기존 v3/v4/v7/v9 제품에 연결했다.
  [499](evidence/p09-361-border-definition499.v1.json)은 원본8·신규제품5·직접영향4의17개,
  824fresh/final824·실제 compiler dep-info2final·cleanupTrue다.498의 입력 거부 실패/최종 fresh 누락은 보존한다.
  시스템CPU 최고38.02%·가용RAM 최저35.323%이며 기존 자원 보호를 유지했다.
  ID 자체와 실제 참조 정의를 구분하며 같은 위치에서 원본 XML/ZIP을 반복 판독하지 않는다.
  gradient/image·전체 유효서식·실제 실행/저장·Native/Gate는 미완료이고003은 사용자1회 허용 뒤 외부 실행 전이다.
- 순서3의 글자24/문단27 세부 조건을 명시적 v3/v4와 네 범위 v7 제품에도 연결했다.
  공통 v1~v4 parser의 정규형16KiB 검사를 원본 접근 앞으로 옮겨 한도 초과를 먼저 거부하며 기존 사후 identity 검사는 유지한다.
  [497](evidence/p09-361-detail-axes-recovery497.v1.json)은496의 본문10개 중 원9개를 보존하고 독립 AEAD 보호를 보완한1개만 실행했다.
  현재10개·809fresh/final809·dep-info1final·cleanupTrue다. 원496 fixture 경고 실패/final fresh 누락과495의36개는 보존했다.
  세부 조건 제품 연결의 수용이며 전체 유효 서식·실제 실행/저장/Native/Gate의 완료는 아니다.
- 순서3의 글자 모양 세부 조건24개를 기존 원본 matcher/현재 저장 strict v9 제품에 연결했다.
  [482](evidence/p09-361-character-detail-focused482.v1.json)는 신규제품5+직접 영향20·layout6·883fresh/final883·cleanupTrue다.
  원 fixture/시험 본문을 보존한 전용 호스트로 명령21.860초·private753.49MiB였고,481의 발행 실패/core43 미수용을 보존했다.
  설치/대체 글꼴·전체 유효 cascade/visibility와 실제 실행/저장/Native 계약은 남는다.
- 순서4의 외부002는 첫 owner/정상 종료·입력 경계 후 사례1 source_bind에서 중단됐다. 원본과2개 흔적을 보존한다.
  [484](evidence/p09-361-crossref-case-diagnostics484.v1.json)는 하위 오류 반환 누락만 수정·검증했고 실제 실패 조건은 미확정이다.
  001/002 재실행 없이 새 고정 경로와 현재 입력 자격을 준비해야 한다. 새 Native 실행 허용은 아직 없다.
- 순서1 완료: [437](evidence/p09-361-catalog-product-retained-final437.v1.json)에서 원45개 본문 재실행0,
  마감 계약24pass·857fresh/final857·설치 설정1final·cleanupTrue로 수용했다. 원436의 CPU 중단과 잘못된
  PASS label은 보존하며 현재 실행기의 PASS 순서·오류 종료·부분 fresh 집계를 수정했다.
- 순서2의 manifest 연결 완료: 기존 router 본문을 공유하고 현재 카탈로그/보호/target/health/시간/최종 head를
  결속했다. [439](evidence/p09-361-personal-info-catalog-mask-manifest439.v1.json)는 이전13개 재사용+
  수정 보호 사례1개 통과의 고유14개,862fresh/final862·빌드 산출물1final·cleanupTrue다. 신규13+기존 adapter
  영향1의 범위이며45개와 공식249는 반복하지 않았다. 실제 executor/저장/게시/신뢰 자격은 아직 미완료다.
- 순서2의 source-bound 저장 준비와 staged HWPX validator 연결 완료:
  [444](evidence/p09-361-personal-info-catalog-mask-storage444.v1.json)는 신규14pass·867fresh/final867·빌드 산출물1final·
  cleanupTrue다. 기존 engine의 실제 staged readback/AEAD artifact 저장/revision CAS와 검증/scanner 거부를 연결했다.
  이전45개·manifest14·공식249는 반복하지 않았다. 메모리 repository/합성 keys·scanner의 server primitive이며 실제 SQL/제품 route는 아니다.
- 순서2의 최종 mutation guard 연결 완료: [446](evidence/p09-361-catalog-storage-commit-guard446.v1.json)의 신규15+직접 영향5개가 통과했다.
  원 CAS의 저장 전·revision commit 직전과 원 job의 claim 전에서 현재 상태를 확인한다. 실패한 guard는 복구해 같은 시도에 재사용할 수 없고,
  등록 후 거부되면 결과/intent/precommit을 보존하며 head를 바꾸지 않는다.879fresh/final879·cleanupTrue이며 전체 큐는 반복하지 않았다.
- 순서2의 실제 SQL job/암호화 저장 연결 완료 범위: [448](evidence/p09-361-catalog-actual-sql-storage448.v1.json)에서 생성 HWPX와 고정 설치 카탈로그를
  원 compiler/manifest→현재 확인3회→실제 staged validator→SQL23 claim/lease/등록/CAS/완료와 disk AEAD에 연결했다.
  DB 재시작 뒤 원본/출력/readback·등록 영수증/head와 잘못된 키 거부를 확인했다.919fresh/final919·설치 설정1final·산출물2final·cleanupTrue다.
  새 전용 DB만 사용했고 기존 DB/한글/이전 시험은 실행하지 않았다. scanner/route와 임시 keys는 fixture이며 신뢰 제품/Native·운영 key custody는 아니다.
- 카탈로그의 공개 key→서버 UUID 결속 연결 완료 범위: [451](evidence/p09-361-catalog-request-identity451.v1.json)에서 신규12+직접 영향3개를 수용했다.
  원 요청의 tenant/project/key로 안정적인 key/job/request ID를 만들고 요청 내용·head·scope는 별도 전체 지문으로 대조한다.
  실제 SQL에서 원 claim의 완료 관측·변경 요청 거부와 재시작/readback을 확인했다.935fresh/final935·설치 설정1final·산출물4final·cleanupTrue다.
  450의 제품9개 본문은 보존해 재실행하지 않았다. 공통 unit의 누락된 컴파일 입력3개를 등록한 뒤 unit6개만 다시 확인했다.
- 원 claim 없는 공개 요청 조회 완료 범위: [457](evidence/p09-361-catalog-cold-request-lookup457.v1.json)은 명시적 schema24 경로의
  현재 project/source ACL·typed key conflict·미관측·head 전진 뒤 조회와 DB 재시작을 확인했다. 기존 schema23 연결은24를 계속 거부한다.
  신규 Rust16+영향6개와 Python4개를 입력 동일성에 따라 보존하고457에서 본문을 재실행하지 않았다.968fresh/final968·설정1final·산출물5final·cleanupTrue다.
  456의 SQL ACL fixture 제약 위반과 정상 종료 원본은 보존했다. 임시 암호 키를 잃은 기존 DB/job을 재시도하지 않고 새 전용 DB에서9개 probe를 마감했다.
- 공통 진입점의 조회 우선 분기 완료 범위: [459](evidence/p09-361-catalog-request-entry459.v1.json)의 신규8개가 통과했다.
  기존 작업이 있으면 ZIP/import/regex/compiler를 생략하고 관측만 반환하며, 미관측일 때만 기존 compiler를 한 번 호출한다.
  조회 실패/충돌/불확정은 새 작업으로 우회하지 않고 source readback/현재 카탈로그/write scope 거부와 RouteUnqualified를 유지한다.
  458의 새 시험 모듈 macro 선언 순서 컴파일 실패/본문0은 보존했다. 선언 위치만 수정했고 과거 시험·SQL은 재실행하지 않았다.
  977fresh/final977·산출물1final·진단없음·cleanupTrue다. 준비 결과는 claim/실행 허가가 아니다.
- 바로 다음은 공통 경로의 실제 제품 실행/게시와 신뢰 registry/scanner 자격을 연결하는 일이다.
  원 P02 서명 snapshot은 historical/routing_disabled이므로 최신 실행 권한으로 재사용하지 않는다. 운영 키/manifest 복구를 함께 마감하고
  순서3의 원본 의미와 순서4의 실물 세션 선행 장애 해소를 늦추지 않는다.
- 키 보관의 읽기 전용 연결 완료 범위: [462](evidence/p09-361-artifact-windows-key-custody462.v1.json)에서 Windows의 새 전용 항목3개를
  별도 프로세스가 다시 읽어 이전/현재 AES 암호문2건과 HMAC 서명1건을 확인했다. 정확한 본문 완료 handshake와 삭제를 확인했고
  모델8개는461에서 수용해 재실행하지 않았다.235fresh/final235·산출물1final·진단없음·cleanupTrue다.
  키 유실/운영 발급·운영 DB·신뢰 route의 완료는 아니다.
- 실제 SQL24 저장의 OS 키 연결 완료 범위: [464](evidence/p09-361-catalog-windows-custody-sql464.v1.json)는 부모의 AES/HMAC 환경변수 없이
  새 scope에서 원 compiler/guard3회/staged HWPX validator·SQL job/등록/CAS/완료·disk AEAD·서명 다운로드를 연결했다.
  DB 재시작 뒤 별도 프로세스가 OS 키로 원본/출력/영수증/head와 서명 다운로드를 대조했고 새 시도/실행은 없었다.
  모델4개·SQL6개 probe·900fresh/final900·설정1final·산출물2final·cleanupTrue와 postmaster2회 정상 종료·시험 키3개 삭제를 확인했다.
  과거 모델8개/공식249·이전 DB/job은 반복하지 않았다. 합성 scanner/route와 전용 키이며 운영 제품 자격은 아니다.
- 원 manifest 없는 등록 복구 완료 범위: [467](evidence/p09-361-archived-manifest-recovery467.v1.json)의 신규23+영향36·타입 차단2개를 수용했다.
  엔진8개는466의 본문/실제 binary·현재 입력 동일성을 확인해 재실행하지 않았다.879fresh/final879·산출물4final·cleanupTrue다.
  새 공통 job은 canonical manifest를 암호화 intent v2에 보존하고, 별도 읽기 타입으로 원 precommit·요청·봉인 node/result 검사를 공유한다.
  기존 v1은 보존하며 원 manifest가 필요한 legacy 관측과 미관측을 구분한다.
- [468](evidence/p09-361-archived-manifest-sql468.v1.json)은 새 SQL24/OS 키 scope에서 실제 v2 저장과 DB 재시작 전후 복구를 확인했다.
  복구 중 원 handles/state/요청 파일3개는 없었으며 보존·복원 후 bytes/SHA가 같았다. 새 claim/CAS/시도는 없었다.
  SQL7probe·905fresh/final905·설정1final·산출물2final·postmaster2회 정상 종료·시험 키3개 삭제·cleanupTrue다.59개/타입2개/키 전달4개는 반복하지 않았다.
- 공개 요청 key의 등록 결과 복구 연결: 현재 scope·key/job/attempt와 정확한 locator를 결속하고 복구된 revision/receipt/result 가용성을 대조한다.
  470의 신규10+영향14 본문은23pass/1fail이었고,
  시험 영수증 ID만 고정해[471](evidence/p09-361-catalog-request-recovery471.v1.json)에서 실패1개만 통과했다. 원23개/실패/final fresh 누락은 보존했다.
  [472](evidence/p09-361-public-request-recovery-sql472.v1.json)는 원 공개 요청만으로 실제 SQL24/OS 키의 재시작 전후
  같은 job/attempt·등록 결과를 복구했다. 원 manifest/claim/locator를 받지 않고, 원 파일4개의 bytes 복원·변경 요청 충돌·없는 key의 미관측을 확인했다.
  7probe·905fresh/final905·설정1final·산출물2final·소유 DB 정상 종료2회·키3개 삭제·cleanupTrue다. 이전 본문은 반복하지 않았다.
  기존 metadata-only fast path와 비실행/비재시도 경계를 유지한다.
  [v1에서 v2로의 저장·복구 계약](../../protocol/migrations/p09-stored-commit-intent-v1-to-v2.md)을 따른다.
  새 DB 연결을 다른 family마다 복제하지 않고 이미 검증한 공통 compiler/job 경로를 사용한다. 통합에 필요한 변경을 먼저 묶고 입력 전후 확인은 묶음당 수행한다.
  순서3/4의 원본 의미·실물 선행 장애를 함께 해소하고 마지막으로 순서5를 마감한다.
  다음 실행 중심은 미해결 원본 의미4종과 실물 세션 장애다. 공통 조회/복구를 또 별도 재검증 묶음으로 만들지 않는다.
  현재 신뢰 registry/scanner·운영 custody와 제품 실행/게시 자격은 순서2의 미완료 경계로 함께 마감해야 한다.
- 이전 읽기 전용 재관측에서 남아 있던 원 Hwp29824/동일 생성 시각은 사용자 종료 요청 뒤477에서 정상 Quit으로 종료했다.
  같은 held process의 실제 종료·참조 해제와 Hwp/HwpTray0개를 확인했다. 강제 종료·문서 저장/폐기·새 Native 실행은 없었다.
  원 run001 실패는 보존하며 새 실행에는 현재 입력·세션 자격과 새002 실행 범위 확인이 필요하다.
- 순서2 나머지와3~5는 미완료다. 기존 OPEN/NOT_RUN/실패·승인 경계를 변경하지 않았다.
- 구현과 검증 결과는 해당 단계가 끝날 때만 갱신하며 예상 완료일이나 전체 완료율을 임의로 확정하지 않는다.

## 기준 자료

- [P09 phase와 hard gate](../../docs/09_roadmap/P09_fields_forms_notes_references.md)
- [기능 소유권](../../FEATURE_COVERAGE_MATRIX.csv)
- [검색19개 현황](P09_SEARCH_SOURCE_INDEX_PROGRESS.md)
- [카탈로그 마스킹](P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md)
- [참조 원본 API](P09-10_REFERENCE_VALIDATION_PRODUCT_API_PROGRESS.md)
- [외부 세션과 재실행 경계](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)
- [현재 복구 경계](P09_REGISTERED_RECOVERY_PROGRESS.md)
