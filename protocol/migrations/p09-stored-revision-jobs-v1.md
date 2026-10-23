# P09 Precommit receipt와 저장 job 경계

P09 현재 저장 원본은 이전 sealed revision의 Result다. 기존 P14 v2 claim/lease는 Source만 받으므로
그대로 연결할 수 없다. 또한 v2 완료 판정은 intent envelope가 아닌 엔진 precommit JSON의 SHA를 요구한다.
Rust는 이 precommit Receipt를 실제 저장하며, SQL23은 Result 원본과 영속 job 결속을 위한 별도 구현이다.
PostgreSQL18.6 전용 시험 DB에서 migration1..23을 실제 적용하고 버전/SHA와 정상 재시작 보존을 확인했다.
ArtifactService SQL23 profile·전용 RevisionService connector·CAS 전 등록 callback·1회성 typed job
coordinator의 모델/서비스 component는 통과했다. 두 서비스 계정의 실제 admission·Artifact 행 RLS와
고정 tenant/subject의6개 검사·권한/메타데이터 변조15개의 거부/복구도 확인했다.
실제 서비스 계정으로 SQL23 claim/lease/단계 전환과 거부를 포함한15개 검사와 DB 재시작 후 한 시도 보존도 확인했다.
별도 시험에서 실제 디스크 AEAD·SQL23 의도 등록/결과 CAS/성공 완료와 DB/Rust 재시작 후 커밋 관찰도 확인했다.
호출자 경계의 합성 응답 유실4개도 실제 SQL/AEAD에 연결해 재시작 후 unknown 보존/committed 복구를 확인했다.
등록 행과 암호화 영수증만 사용하는 읽기 전용 복구도 구현하고 실제 DB 재시작 후 별도 요청 파일 없이 확인했다.
관측된 attempt 이력 보존은 기존 P14의 terminal/immutable 계약과 일치한다. 입력/route/scanner/validator는 합성이며
실제 네트워크/crash/키 유실 복구·전체 거부 경계와 실제 P09 제품 실행 자격은 미완료다.

## 등록 영수증 기반 읽기 전용 복구

reconcile_registered_stored_commit는 별도 ServiceRequest 파일 없이 DB 조회 키/등록 행과 현재 ACL/AEAD가 확인된
intent/precommit 및 서버 manifest로 복구한다. RegistrationNotObserved·Registered(NotObserved)·Registered(Committed)를 구분하며
missing은 no_effect/재시도 허가가 아니다. 실행/lease/ingest/등록/CAS/작업·시도 변경을 하지 않는다.

신규10+영향 기존12=22pass·297은674fresh/final674·진단없음·cleanupTrue다.
새 전용 DB의298은681fresh/final681·실제3개 검사·진단없음·cleanupTrue다.
요청 fixture를 별도 이름으로 보존해 원 경로가 없는 재시작 후 커밋/결과 관측·등록 부재 구분·다른 manifest 거부를 확인했다.
전후 도메인 상태와 암호화 객체6개 SHA는 같고 재실행하지 않았다. 전체116.672초·시스템CPU최고20.90%·
가용RAM최저43.0679%·postmaster2회 정상 종료·두 Job active0/empty/handle closed다.
CPU cap6.25%·private8%/stop7%·RAM/commit95%는 유지했고 프리즈 해결을 주장하지 않는다.

cas_after의 attempt unknown_outcome 보존은 기존 P14 계약에 부합하며 이력/SQL migration은 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[구현·검증과 남은 경계](../../implementation/p09/P09_REGISTERED_RECOVERY_PROGRESS.md)를 따른다.
아래296까지는 이 읽기 전용 복구 진입점 전 이력이다.

## SQL23 응답 유실과 복구

register_after/cas_before는 커밋 미관측과 SQLSTATE55000 거부 뒤 unknown을 유지한다.
cas_after는 근거로 성공 복구하고 complete_after는 기존 성공 상태만 읽는다. 호출자 경계의 합성 주입이며
실제 네트워크 장애 증거가 아니다. 이전1개 재사용+이번3개이며 모두 attempt1/fence1,
no_effect 추론·실행 재시도 없음이다. cas_after 성공 뒤 attempt_state=unknown_outcome 이력 정합성은 후속 검토한다.

292 보호 중단과293 slug 오류를 보존하고 단일 cluster/schema·tenant 분리·즉시 사례 checkpoint를 적용했다.
294의684fresh/final684로 첫 사례를 마무리했고295는685fresh/final685·진단없음·cleanupTrue다.
initdb1회/schema23 적용1회·새 checkpoint3개·postmaster7회 정상 종료·전체123.438초·
시스템CPU최고21.63%·가용RAM최저41.8705%·두 Job active0/empty/handle closed다.
CPU cap6.25%·private8%/stop7%·RAM/commit95%는 유지했고 프리즈 원인/Defender 인과는 미확정이다.

RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[사례·자원·원 증거](../../implementation/p09/P09_SQL23_ACK_RECOVERY_PROGRESS.md)를 따른다.
아래291까지는 이 응답 유실 검증 전 이력이다.

## 디스크 AEAD와 SQL23 등록 CAS 완료

sql23_storage는 새 전용 D:/devdata/hwpx-agent-p09-pg18-storage-288에서 실제
ArtifactService/LocalEncryptedBlobStore/PostgreSQL23/PreparedStoredJob를 연결한다.
합성 artifact 행은0개로 시작해 서비스가 실제 AES-GCM 객체와 메타데이터를 만든다.
Source용 실제 lease/CAS/성공 완료로 초기 Result를 만든 뒤 SQL23 job이 실제 의도 등록/조회·
결과 CAS·precommit 영수증을 쓰는 성공 완료를 수행했다. 기존 서비스/엔진/migration과 기존 시험 본문은 바꾸지 않았다.

288은 실행기 observer 연결 AttributeError로 Cargo/DB0,289는 새 probe와 공용 helper의
Result 별칭 충돌 E0107/미사용 import로 DB0이었다. 원 실패를 보존하고 실행기 연결 및 새 probe의 두 선언만 수정했다.
290은675fresh/final675·빌드 진단없음·cleanupTrue다. fixture/초기 저장/SQL23 실행/잘못된 키/재시작 관찰의5회 probe이며
SQL23 작업 실행은1회다. 실제 암호화 객체6개를 DB의 ciphertext SHA/평문 크기+16과 대조했고 잘못된 AES 키는 CryptoFailure로 거부했다.

DB와 Rust 프로세스 재시작 뒤 실제 결과/원본/영수증 복호화·등록 행과 요청 결속·read-only 커밋 복구·
terminal_success replay를 확인했다. 전후 artifact6/available6·job2/성공2·attempt2·authorization0·intent1·
revision2/seal2·head2와 암호화 파일6개 SHA가 같다. 초기 작업과 SQL23 작업 모두 시도1이며 재실행하지 않았다.
키는 부모가 메모리에 보관한 임시 시험 키이므로 운영 KMS/키 복구 자격이 아니다.

290 전체114.422초·빌드2.422초/Job CPU1.922초/private최고704.79MiB·
실제 DB 명령5.938초/Job CPU3.609초/private최고73.33MiB다. 시스템CPU최고27.81%·가용RAM최저43.2051%이며
postmaster2회 정상 종료와 두 Job active0/empty/handle closed를 확인했다. 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했고 원 runtime/DB/실패를 보존했다. 시스템 표본은 PC 프리즈 해결 증거가 아니다.

입력 bytes/route/scanner/validator는 합성이다. 실제 HWPX 의미 검증·scanner/issuer·확인 유실/unknown 복구·
전체 거부 경계·자격 있는 P09 dispatcher/제품 실행/Native/Gate는 미완료다. 다음은 확인 유실 복구와 거부 경계 및 실제 제품 경로 연결이다.
한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
근거: implementation/p09/evidence/p09-361-sql23-real-storage-compile290.v1.json; target/p09-sql23-storage-observations-288.json.
아래287까지는 실제 디스크 AEAD와 SQL23 등록/CAS/성공 완료 검증 전 이력이다.

## SQL23 작업의 실제 claim과 lease

p09_sql23_jobs는 새 전용 D:/devdata/hwpx-agent-p09-pg18-job-286에서 실제 서비스 계정과
StoredJobLifecycleRepository를 사용한다. 합성 SQL 메타데이터를 초기화하고 기존 Source용 함수의
실제 worker 등록/claim/lease/단계 전환/CAS로 첫 Result revision을 만든다. revision/seal 직접 삽입·
guard 비활성화·애플리케이션에 legacy 실행 권한 부여는 하지 않았다. 이 초기 CAS는 합성 fixture 준비이며
암호화 blob이나 실제 HWPX 제품 검증이 아니다.

새 SQL23의 claim/replay·변경된 요청/비봉인 Source 거부·미등록/잘못된 profile/capability/draining worker 거부·
실제 lease/authorization·중복 lease/다른 execution/단계 생략 거부·순서대로3단계 전환·미커밋 결과의 완료 거부·
최종 replay의15개 검사를 통과했다. 거부10개는 adapter 오류뿐 아니라 같은 요청의 실제 SQLSTATE도 독립 확인한다.
정상 종료/재시작 후 새 Rust 프로세스에서 replay를 확인했고 전후 실제 SQL 상태는 validating/in_progress·
시도1/fence1·attempt행1·authorization행1·intent0·revision1·job2로 같다. 재실행/시도 증가/허위 완료는 없다.

286은228fresh/final228·빌드 진단없음·cleanupTrue다. 전체48.547초·시스템CPU최고20.08%·
가용RAM최저44.8425%이며 postmaster2회 정상 종료와 두 소유 Job active0/empty/handle closed를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했고 원 runtime/DB/실패를 보존했다.
시스템 표본은 PC 프리즈 해결 증거가 아니다.

실제 blob/AEAD/scanner/issuer·SQL23 intent 등록/결과 CAS/성공 완료/확인 유실 복구와
제품 dispatcher/실행 자격은 미완료다. 다음은 실제 파일 저장과 이 등록/CAS 경로다.
한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
근거: implementation/p09/evidence/p09-361-sql23-job-lifecycle286.v1.json; target/p09-sql23-job-observations-286.json.
아래285까지는 실제 SQL23 job 경로 검증 전 이력이다.

## SQL23 서비스 계정의 실제 접속과 거부

p09_sql23_admission은 별도 ASCII 전용 DB에 고정된 migration1..23/최소 권한 fixture/
두 tenant의 합성 SQL 메타데이터를 적재하고 실제
LocalPostgresMetadataRepository::connect_schema23_diagnosed와
LocalPostgresStoredRevisionJobsRepository::connect를 호출한다. Rust 프로토콜로 원 SQL 바이트를
전달해 prosrc 해시를 유지한다. 기존 migration·서비스 구현과 공식 시험은 바꾸지 않았다.
D:/devdata/hwpx-agent-p09-pg18-role-284만 새로 만들었으며 원 runtime/실패/이전 DB는 보존했다.

한 번 컴파일한 probe를35회 호출했다. fixture 적재/본문 주입·복구3회를 뺀 실제 접속 판정은32회다.
정상 두 계정 접속과 Artifact own/foreign tenant 조회·실제 artifacts 행 RLS·Revision 현재 head와
고정 tenant/subject의6개 검사를 확인했다. 과도한 job 표/column/함수 권한과 replication,
revision column write/직접 intent 조회/필수 claim 누락/legacy claim/기존 control search_path/
새 trigger/RLS/함수 본문 SHA, schema 이름/SHA/미래24의15개 변조를 거부하고 각각 정상 상태
복구를 확인했다. 원284의 actual_profile_probe_calls=35는 전체 호출수이며 접속 판정32회와 구분한다.

284는224fresh/final224·진단/경고없음·cleanupTrue다. 전체55.313초·빌드1.813초/
Job CPU0.984초/private최고311.95MiB, 실제 DB 명령11.406초/Job CPU8.906초/
private최고62.76MiB다. 시스템CPU최고25.05%·가용RAM최저46.1495%이며 postmaster 정상 종료와
두 Job active0/empty/handle closed를 확인했다. 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했다. DB는 동기 I/O·병렬 worker0·
fsync/synchronous_commit/full_page_writes on이며 시스템 표본을 PC 프리즈 해결 증거로 해석하지 않는다.

메타데이터는 합성이고 실제 blob/AEAD/scanner/issuer·worker 등록/lease·job 함수/trigger의
실제 실행·등록/CAS·완료/확인 유실/재시작 복구와 P09 제품 실행 자격은 미완료다.
다음은 이 실제 worker와 저장 job 경로다. schema 접속과 변조 거부를 제품 실행 수용으로 올리지 않는다.
비밀번호 원문/전체 로그는 보관하지 않았고 시스템/Defender/WSL 설정·운영 DB·한글/접근 허용 창은 건드리지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
근거: implementation/p09/evidence/p09-361-sql23-service-admission284.v1.json;
target/p09-sql23-role-observations-284.json.
아래283까지는 서비스 계정의 실제 접속/거부 검증 전 이력이다.

## 네이티브 PostgreSQL의 SQL 적용과 재시작

PostgreSQL18.6-5 전용 ZIP에서 bin/lib/share의1583개·147885345bytes를 수입하고
postgres/initdb/psql의18.6 --version을 확인했다. ZIP384620317bytes의 관측 SHA는
e2246ba91d22345bc3d017586c09ede52d9df180b1eeb480f050445f1cad84e2다.
HTTPS 배포 원본과 로컬 해시를 고정한 것이며 vendor 서명/checksum 자격은 아니다.
278은 raw ZIP 이름/파일 부모 충돌의 모델2fail 뒤 네트워크 없이 종료했다.
실패를 보존한279는 두 경계를 수정해 모델12pass·버전3·156fresh/final156을 확인했다.

280의 새 cluster 명령/인증 모델10pass 뒤 한글 경로 initdb가 실패했고 SQL migration과
listener는 시작하지 않았다.281의 새 초기화 전용 진단은 UTF8 invalid byte sequence/0xb0를
확인했다.282는 원 ZIP·runtime·실패 data를 보존하고 동일1583개 SHA와 HBA를
D:/devdata/hwpx-agent-p09-pg18-ascii-282에 복사했다. ASCII 경로에서 initdb 성공·SCRAM
loopback 인증·원 migration1..23 실제 적용·전후 버전/SHA23개·정상 종료/재시작 뒤 표식 보존을
확인했다. 실제 함수 내부 SQL/권한/제품 실행의 완료 판정은 아니다. SQL23을 포함한 migration
파일은 변경하지 않았다. 기존 모델10·Rust·공식249는282에서 재실행하지 않았다.

279 전체97.171초·수입/버전 명령48.922초·Job CPU3.734초·private최고51.21MiB다.
282 전체32.625초·실제 DB 명령8.500초·Job CPU5.953초·private최고54.45MiB·
시스템CPU최고14.07%·가용RAM최저45.7678%·181fresh/final181이다.
두 postmaster 정상 종료와 모든 소유 Job active0/empty/handle closed를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
시험 DB만 shared_buffers16MB·work_mem1MB·연결12개·동기 I/O/병렬 worker0·
fsync/synchronous_commit/full_page_writes on으로 실행했다. Windows/Defender/언어·locale/
서비스/WSL 설정은 바꾸지 않았으며 PC 프리즈 해결을 주장하지 않는다.

SQL23은 이 전용 시험 DB에 실제 생성됐지만 ArtifactService/RevisionService 계정 admission·
실제 RLS/권한 거부·worker·job 함수/trigger·등록/CAS·완료/확인 유실 복구 검증은 미완료다.
다음은 검증된 ASCII 경로의 실제 서비스 계정과 저장 job 실행이다. 비밀번호 원문/전체 로그는
보관하지 않았고 원본·실패 폴더와 정상 종료한 전용 DB는 보존한다. Docker/WSL/시스템 서비스/
한글/접근 허용 창·기존 운영 DB는 시작하거나 접근하지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
근거: implementation/p09/evidence/p09-361-native-postgres-runtime-boundary-recovery279.v1.json;
implementation/p09/evidence/p09-361-native-postgres-init-diagnostic281.v1.json;
implementation/p09/evidence/p09-361-native-postgres-ascii-campaign282.v1.json.
아래277까지는 실제 SQL 생성/재시작 전 이력이다.

배포 원본은 [EDB Windows binaries](https://www.enterprisedb.com/download-postgresql-binaries)에서 확인했다.
시험 DB의 io_method=sync는 [PostgreSQL18 I/O 설정](https://www.postgresql.org/docs/18/runtime-config-resource.html#RUNTIME-CONFIG-RESOURCE-ASYNC-IO)에 따른다.

## SQL23 작업 처리와 1회성 coordinator

ArtifactService SQL23 profile과 예상 precommit 준비는270의 모델6+신규9+영향26=41pass다.
예상값은 실제 봉인된 CAS 요청으로 변환할 수 없다. StoredJobLifecycleRepository는
claim/lease/단계 전환/완료/결과 불명/committed 복구를 기존 SQL23·P14 함수에 연결한다.
기존 migration23개와 저장·등록·CAS 본문은 유지했다. Source 판정이 없는 P14 control2개의
권한·본문 SHA·definer·search_path·PUBLIC·owner 검사를 기존 접속 검사 뒤에 추가했다.

PreparedStoredJob는 manifest와 보관된 후보에서 source/plan/target/예상 효과·precommit을 결속하고
run_once에서 소비된다. 기존 scope 검사를 claim보다 먼저 수행하며 replay는 lease·workspace 생성 없이
반환한다. 새 작업은 실제 받은 lease를 같은 repository의 CAS에 결속한다. 원 엔진/validator 뒤에만
validating을 확인하고 기존 수입·등록·CAS·완료로 이어진다. 완료에 쓰는 Receipt는 intent envelope가 아닌
precommit이다. 단계/CAS/완료 확인 유실은 원 실패·산출물·요청·receipt를 보존하며 자동 재실행하지 않는다.
이 서버 저장 primitive는 P09 제품 route나 Native 실행 허가가 아니다.

271은 음성 SQL 문자열을 실행 코드로 오인한 checker 오류로 Cargo/시험0,272는 decoder 경로 누락
E0425로 시험0이었다.273은 경로만 명시해 신규 lifecycle15pass·914fresh/final914다.
274는 prepare receiver를 잘못 적은 checker 오류로 Cargo/시험0이고275는 제품/시험 변경 없이
checker를 수정해 신규 coordinator9pass·919fresh/final919다. 신규 고유24개이며 기존 lifecycle15와
저장38·engine35·공식249는275에서 반복하지 않았다. 원 실패271/272/274를 보존했다.

273/275 전체119.406/132.782초·명령1.828/14.328초·Job CPU1.641/12.328초·
private최고375.15/876.22MiB·시스템CPU최고24.95/26.56%·가용RAM최저45.1297/44.6472%다.
두 Job active0/empty/handle closed와 scratch 하위 정리를 확인했다. 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 시스템 표본은 검증 단독 부하나
PC 프리즈 해결 증거가 아니다.

실제 서비스 암호화·수입·CAS 코드를 사용했지만 저장소/worker/manifest/scanner/validator는 모델·합성이다.
SQL23 구문·실제 catalog/권한·worker·함수·trigger·DB/프로세스 재시작과 자격 있는 제품 dispatcher
연결은 미완료다. 다음은 이 실제 DB 검증과 실행 자격 결속이다. Docker/DB/한글과 접근 허용 창은
시작하지 않았다. RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
근거: implementation/p09/evidence/p09-361-stored-job-lifecycle-compile-recovery273.v1.json;
implementation/p09/evidence/p09-361-stored-job-coordinator-checker-recovery275.v1.json.
아래269까지는 coordinator 구현 전 이력이다.

## SQL23 접속 검사와 CAS 전 등록

LocalPostgresStoredRevisionJobsRepository는 별도 loopback 접속에서 schema1..23의 이름/SHA·안전한 role·
기존 guards·강제 RLS/불변 trigger·직접 표/column 권한·11개 새 함수의 본문 SHA/definer/search_path/
PUBLIC 권한을 검사하도록 구현했다. 기존 SQL19~22 접속 함수는 바꾸지 않았다.
받은 lease는 구문만 검사하며 실제 권한은 SQL이 판정한다. 등록/조회와 동적 요청별 lease 결속을
컴파일했지만 SQL23은 여전히 미적용·실제 catalog/권한/함수 실행 미검증이다.
기존 profile의 권한/RLS/guard 검사도 호출하며 migration/role/GRANT를 설치하거나 자동 재접속하지 않는다.

bind_registered는 CAS와 정확히 같은 repository를 registrar로 사용한다. 이미 readback한
result/intent/precommit과 받은 lease·정확한 요청을 등록하고 반환 행을 대조한 뒤 현재 원본/head/결과를
재확인한다. 등록 실패·확인 유실·잘못된 행은 CAS를 호출하지 않는다.
확인 유실은 revision 실행 증거가 아니며 자동 재시도하지 않는다.
registration_response는 거부 응답도 진단용으로 보존하고 registered_job_intent는 검증 뒤에만 채운다.
기존 plain bind는 여전히 실행 자격 없는 저장 primitive다.

components265는 READ_TABLES import 부재 E0425로 시험0, recovery266은 이전 빈 scratch 충돌로
Cargo/시험0이었다. fresh-temp267은 수정된 import와 새 전용 scratch로
모델5+등록9+영향29=43pass·903fresh/final903이었다.
기존 컴파일 migration21개를 새 입력으로 등록해 전체23개를 전후 확인했다.
confirmed268은 진단/확인 결과 분리를 보강하고 단일 음성 assertion을 강화한 뒤
등록9pass·901fresh/final901·진단/경고없음·cleanupTrue다. 모델5/기존29=34개는 재실행하지 않았다.
접속 모델은 schema 누락/미래 버전/이름/SHA, 위험 role, 함수 권한/본문/경로/PUBLIC,
RLS/표 권한/trigger를 검사한다. 등록 모델은 호출 순서·두 receipt/요청 결속, 실패/확인 유실·다른 행,
등록 뒤 source 재확인, CAS 유실 뒤 조회·읽기 전용 복구, single use·lease/lookup/descriptor 한도와
비노출을 검사한다. 실제 SQL23 catalog/권한/등록/CAS/DB 재시작 증거가 아니다.

268 전체128.313초·명령12.000초·시험0.06초·Job CPU10.312초·private최고877.45MiB/2.75400%·
시스템CPU최고26.95%·가용RAM최저46.5261%다. Job active0/empty/handle closed와
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 시스템 전체 CPU를 검증 자체 CPU나
PC 프리즈 해결 증거로 해석하지 않는다.
접속5는 순수 모델이고 등록 repository/manifest/scanner/validator는 합성·in-memory다.
ArtifactService SQL23 profile·typed claim/lease/complete coordinator·실제 DB 검증은 미완료다.
Docker/DB/한글을 시작하거나 시스템 설정을 바꾸지 않았다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행, RouteUnqualified/P02 routing_allowed=false를 유지한다.

근거: implementation/p09/evidence/p09-361-stored-job-registration-fresh-temp267.v1.json 및
p09-361-stored-job-registration-confirmed268.v1.json. 아래263은 이 connector/등록 callback 전 검증이다.

## 두 receipt의 역할

RevisionCommitRequest::canonical_json은 기존 digest와 같은 결정적 bytes를 반환한다.
StoredResultRevisionCas는 workspace-precommit.json을 Receipt/application/json으로 저장하고64KiB 상한,
Available/Verified·SHA·AEAD readback을 확인한다. 큰 hwpx-agent.stored-revision-commit-intent/v1은
서비스 요청과 원본/결과·manifest를 보존하는 별도 receipt다. 두 UUID/SHA를 혼용하지 않는다.
precommit 미확인/손상은 intent/CAS 전에 거부하며 알려진 실패나 결과 불명확 상태에도 증거를 보존한다.

## 미적용 SQL23

0023_p09_stored_revision_jobs.up.sql은 기존 v2 함수와 전역 Source 판정을 바꾸지 않는다.
새 claim/lease/retry/complete/reconcile와 효과 검사6개는 원 v2의 상태·fence·worker·attempt·backoff·
expiry·트랜잭션 절차를 유지하고 source 판정만 별도 sealed Result 조건으로 대체한다.
Result는 기대 revision의 정확한 결과여야 하며 project/editor·head·seal/receipt 결속·ACL·격리·크기/SHA를
검사한다. 완료/재조정의 기존 결과/head 조건도 유지하므로 읽기 전용 역사적 커밋 관측을 job 완료로
자동 승격하지 않는다.

stored_revision_commit_intents는 job/attempt/fence/authorization·commit/revision·result·validation·요청 SHA에
intent ID/SHA와 별도 precommit ID를 결속한다. 등록은 실제 validating lease와 미소비 authorization,
기대 원본/결과 및 두 receipt를 확인한다. Result 원본 커밋에는 정확한 등록 행을 요구하는 trigger를 추가한다.
기존 Source job에는 기존 규칙을 유지한다. 표는 강제 tenant RLS·불변이며11개 새 함수의 PUBLIC 권한은
회수한다. 앱 GRANT나 connector 자격을 자동 설치하지 않는다. 조회는 역사적 intent를 읽으며 누락을
무효과나 재실행 허가로 해석하지 않는다.

down.sql은 intent나 Result 원본 v2 job이 하나라도 있으면 거부한다. 산출물·원본을 삭제하는 rollback은
제공하지 않는다. 이번에는 up/down을 어느 DB에도 적용하지 않았다.

## 검증과 실패 보존

components261은 새 범위 P14 SQL의 이전 pin 부재, recovery262는 역변환 checker의 줄바꿈 경계 오류로
Cargo/시험0이었다. 원 P14 SQL은 단일 읽기 전용 Git HEAD blob과 일치했다. checker-recovery263은
제품 입력을 바꾸지 않고 checker만 수정하고 저렴한 delta 검사를 전체 source walk 앞으로 옮겼다.
Rust 신규4+영향25=29pass·872fresh/final872·진단/경고없음·cleanupTrue다.
기존25개 시험 본문은 유지했고 intent 음성 scanner만 해당 파일명에 한정했다.
별도 신규 시험은 정확한 precommit JSON/digest·구분된 intent, 미확인 scanner·AEAD 차단, Unknown 뒤
두 receipt 보존을 확인했다. engine26·공식249는 재실행하지 않았다.

SQL 정적 소스 계약13개(6개 역변환 포함)는 SQL parsing/runtime 증거가 아니다.
미적용 SQL의 역할/형태와 원 절차 보존을 확인했을 뿐 DB 함수·trigger·권한·RLS가 실제 작동했다고
주장하지 않는다. schema23 connector는 모든 선행 schema/hash와 기존·새 권한/guard를 검증해야 하며
그 뒤 등록 callback·실제 job/lease/CAS/완료·중단/재시작을 전용 DB에서 검증해야 한다.

전체125.531초·명령12.469초·시험0.19초·Job CPU10.656초·private최고875.66MiB/2.74838%·
시스템CPU최고22.99%·가용RAM최저45.7716%다. Job active0/empty/handle closed와
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 이 값은 PC 프리즈 해결 증거가 아니다.

Rust 저장소는 in-memory이고 manifest/bytes/scanner/validator는 합성이다.
영속 job 등록·실제 DB/프로세스 재시작·P09 실행/Native/Gate는 미완료이며
Docker/DB를 시작하거나 시스템 설정을 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: implementation/p09/evidence/p09-361-stored-revision-jobs-checker-recovery263.v1.json.
compact_receipt_json.unpack으로 원래 row를 복원한다.
