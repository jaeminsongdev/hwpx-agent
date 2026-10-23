# 개인정보 카탈로그 일치 문자열 마스킹

전체 개인정보 형식 카탈로그에서 선택한 종류의 모든 패턴을 한 번 검색해, 실제 일치한 원본 문자열만
마스킹하는 source 코어와 현재 저장 문서 서비스 경로를 구현했다. 원본 처리30개와 저장 서비스20개가
통과했다. 엄격한 제품 요청·공통 compiler의 신규42+영향3개도437에서 본문 재실행 없이 마감했다.
현재 카탈로그를 필수로 받는 공통 routing/manifest 연결은439의 고유14개로 확인했다.
원본 결속 저장 준비·실제 staged HWPX readback과 기존 암호화 저장/revision CAS 연결은444의 신규14개로 확인했다.
현재 설정/route의 최종 mutation guard와 실제 SQL job·disk AEAD·재시작 readback도446/448에서 연결했다.
카탈로그 요청의 공개 key→서버 ID와 기존 SQL job 결속은451의 고유15개 및 실제 SQL 관측으로 확인했다.
공개 요청의 cold lookup은457에서 실제 SQL24/권한 철회/재시작까지, 공통 진입점의 조회 우선 분기는459에서 확인했다.
신뢰 실행 자격·운영 저장/게시·key custody와 Native 의미 검증은 남는다.

키 보관의 읽기 전용 OS 연결은[462](evidence/p09-361-artifact-windows-key-custody462.v1.json)에서 별도 프로세스의 AES 복호화2건·HMAC 확인1건,
잘못된 용도/보관 범위/누락 거부와 전용 항목3개 삭제를 확인했다.461의 모델8개는 재실행하지 않았다.
새 SQL24 fixture의 OS 키 연결은[464](evidence/p09-361-catalog-windows-custody-sql464.v1.json)에서 마감했다.
키 설치기 종료 뒤 별도 seed/실행/DB 재시작 프로세스가 부모 AES/HMAC 환경변수 없이 원 HWPX compiler/guard3회/validator·job/CAS/AEAD와
서명 다운로드를 수행했다. 원본/결과/영수증/head·ciphertext6개 보존과 postmaster2회 정상 종료·키3개 삭제를 확인했다.
모델4개·SQL6probe·900fresh/final900·설정1final·산출물2final·cleanupTrue이며 과거 모델/공식 큐/이전 DB는 반복하지 않았다.
원 manifest 없는 등록 복구는467/468에서 별도로 연결했다. 새 공통 job은 canonical manifest를 암호화 intent v2에 보존하고,
readonly archive를 실행 manifest/승인으로 변환하지 않는다. 신규23+영향36개의 고유59개와 타입 거부2개를 수용했다.
실제 SQL24·OS 키 경로에서는 원본 fixture 파일3개를 사용할 수 없는 상태로 DB 재시작 전후 복구하고 원 bytes를 복원했다.
468은7probe·905fresh/final905·산출물2final·cleanupTrue·전용 키3개 삭제다. 운영 발급/키 유실·실제 scanner/신뢰 실행은 미완료다.
[v1→v2 복구 계약](../../protocol/migrations/p09-stored-commit-intent-v1-to-v2.md)을 따른다.
공개 요청 key→현재 job/attempt→정확한 등록 결과는470/471에서 구현 시험했고472에서 실제 SQL24/OS 키 재시작 전후에 확인했다.
원 공개 요청만 필요하며 원 manifest/claim/locator 파일을 사용하지 않는다. 마지막 SQL 요청/권한/상태 관측이 바뀌면 오류로 종료한다.
470의23pass/1fail 원본은 보존하고 시험 영수증 ID만 고정해471에서 실패1개만 통과했다.472는7probe·905fresh/final905·설정1final·산출물2final·cleanupTrue다.
원 파일4개는 bytes 그대로 복원했고 소유 DB 정상 종료2회·전용 키3개 삭제를 확인했다. 기존 metadata 조회는 그대로며 새 실행/재시도 권한은 아니다.
[키 보관 계약](../../protocol/migrations/p09-artifact-windows-key-custody-v1.md)을 따른다.

## 공통 제품 진입점의 조회 우선 분기

`StoredProductRequest::prepare_catalog_mask_or_observe_json`은 원 strict 요청/현재 scope의 조회를 먼저 수행한다.
기존 작업은 `CatalogRequestEntry::Existing`의 metadata 관측만 반환해 source/head/카탈로그/regex/compiler I/O를 하지 않는다.
미관측은 `Prepared`의 기존 compiler 후보로만 이어지고 source AEAD/readback·현재 카탈로그·원본 scope 검사를 생략하지 않는다.
조회 충돌/권한 거부/DB 불확정/가용성 실패에는 fallback이 없다. 미관측→준비 사이에 생긴 경합은 원 job claim이 처리해야 하며
이 분기는 부재 lease나 claim/자동 재시도/실행/게시 권한이 아니다. 기존 무설정 dispatcher와 제품 route 거부는 유지한다.

[459](evidence/p09-361-catalog-request-entry459.v1.json)은 새8개만 실행해 통과했다. 기존 완료/진행 상태의 무재계산·단일 조회,
충돌/불확정/가용성 실패의 비우회·미관측의 원 HWPX compiler/실제 마스킹 readback·카탈로그 drift·source AEAD 실패·strict/preview·write scope를 확인했다.
과거 제품/Rust/Python/SQL 본문은 반복하지 않았다.977fresh/final977·산출물1final·진단없음·cleanupTrue·140.844초,
시스템CPU최고85.34%·가용RAM최저22.932%이며 보호 중단은 없었다. 이 수치는 시스템 전체이며 검증 Job의 CPU 상한을 바꾸지 않았다.
[458](evidence/p09-361-catalog-request-entry458.v1.json)은 시험의 child module이 helper macro보다 먼저 선언돼 컴파일에서 실패한 본문0 결과다.
원본을 보존하고 선언 위치만 수정했으며 제품 구현과8개 시험 본문은 그대로다. PC 프리즈 해결이나 P09 Gate 완료로 판정하지 않는다.

## 원 claim 없는 기존 작업 조회

`prepare_lookup_json`은 원 strict16KiB 요청과 현재 read/write·5scope에서 동일한 서버 ID와 전체 지문을 만든다.
ZIP/source/head/카탈로그 읽기·regex·compiler·claim을 호출하지 않는다. 관측 직전 provider scope와 실제 SQL project/source ACL을 다시 확인한다.
`NotObserved`는 작업 부재/무효과의 증명이나 실행 허가가 아니며 `Existing`도 독립적인 AEAD/의미 readback 또는 완료 효과 증명이 아니다.

schema24는 명시적인 revision/artifact 연결에서만 받는다. 기존23 연결은24를 거부하고 원23의 전체 검증은24 경로에서도 유지한다.
전용 lookup 함수만 revision role에 부여하며 artifact role은 실행할 수 없다. 기존 PK의 정확한 tenant/project/key 및 tenant/project/job
결속을 검사하고, 원본·요청·head의 전체 지문이 다르면 고정 SQLSTATE/message에만 typed `KeyConflict`를 반환한다.
현재 권한 실패·DB 불확정은 미관측으로 바꾸지 않는다. 함수의 `STABLE` 선언과 별도로 repeatable-read READ ONLY transaction을 사용한다.

[457](evidence/p09-361-catalog-cold-request-lookup457.v1.json)은 Rust 신규16+영향6개, Python4개와 실제 SQL9개 probe를 마감했다.
기존 입력과 동일한 모델/제품 본문은454~456에서 수용해457에서 재실행0이다. head1→2 뒤 공개 요청 조회·내용 충돌·미관측·project/source
ACL 철회와 복원·별도 프로세스/DB 재시작 조회·원 HWPX/AEAD readback을 확인했다.968fresh/final968·설치 설정1final·산출물5final·cleanupTrue다.
183.485초·시스템CPU최고66.41%·가용RAM최저17.512%이며 기존 한 코어/낮은 우선순위·CPU cap·RAM/commit95% 보호를 유지했다.

454의 시험 trait scope 컴파일 오류와455의 기존 bind 거부 시점 단언 오류는 원본을 보존하고 시험만 고쳤다.
456은 제품/조회/project ACL 본문 뒤 source ACL 부정 fixture가 기존 last-manager 제약을 위반해 실패했다. 원 DB는 정상 종료해 보존했고
같은 job을 재실행하지 않았다.457은 별도 새 DB에서 backup manager를 보존한 정확한 ACL 제거/복원으로 검사하고 임시 ACL을 제거했다.
실제 사용자 DB/문서·한글·Native는 실행하지 않았다. 합성 scanner/route·부모의 임시 키를 사용한 범위로, 신뢰 제품 실행이나 운영 key custody가 아니다.

## 요청 key와 저장 job의 결속

`StoredRequestJobIdentity`는 strict 요청과 현재 authenticated provider에서만 만든다. 기존 SQL key의 tenant/project 범위를
유지하며 공용 key의 정확한 UTF8 bytes를 버전 고정·길이 구분 JSON tuple에 결속한다. full SHA에서 역할별로 분리한 custom
UUID를 만들고 요청 canonical/scoped 지문은256bit 전체를 별도로 보존한다. key/job/request는 서로 다르고 원문 key를 노출하지 않는다.

요청 내용·schema·source/head·actor/branch/document·manifest가 바뀌어도 같은 tenant/project/key에 새 ID를 발급하지 않는다.
서로 다른 내용은 DB의 원 immutable binding과 충돌해야 하며, 새 작업으로 우회할 수 없다. key bytes를 Unicode 정규화하거나
단순 연결하지 않는다. 이 ID는 claim·lease·실행·재시도 허가가 아니며 외부 constructor/deserialization은 없다.

현재 저장 준비 callback이 원 요청의 ID를 보관하고 `prepare_bound_job`은 호출자 key/job/request UUID 대신 그 ID와 원 canonical,
scoped,source/head,manifest/route-set을 사용한다. 서버 policy·새 commit/revision과 기존 job/SQL limit 검증은 유지한다.
기존 `prepare_job`은 별도 server primitive로 보존했다. 제품 연결은 bound 경로와 기존 current guard·staged validator를 사용한다.

[450](evidence/p09-361-catalog-request-identity450.v1.json)은 공통 unit6·제품 신규6+영향3의 본문15개와 SQL 실행 파일 빌드가 모두
exit0이었지만, 공통 unit의 컴파일 입력3개가 목록에 없어 DB 시작 전에 멈췄다. 보호 중단이 아니며 원 결과와 runner를 보존했다.
P02의 기존 unit fixture와 공개 attestation/signature를 읽기 전용 입력에 등록했고 그 내용·trust 정책은 변경하지 않았다.

[451](evidence/p09-361-catalog-request-identity451.v1.json)은 제품9개의 정확한 본문·실제 dep-info·원 입력 동일성을 확인해 재실행0으로
수용했다. unit6개만 완전한 입력 범위로 다시 확인했고 새 SQL fixture를 한 번 실행했다. 고유 신규12+직접 영향3개이며, 고정 독립
벡터·tenant/project namespace·변경 요청의 같은 ID 유지·UTF8 key 구분·digest/범위 거부·원 요청/claim 결속과 원 SQL policy를 다룬다.

실제 SQL에서는 bound ID로 claim/lease/등록/CAS/완료했다. 원 full claim을 다시 제출한 관측은 TerminalSuccess/attempt1을 반환했고,
같은 key의 요청 지문 변경은 거부됐다. 그 전후 원 완료 관측은 같았으며 새 workspace/실행/lease/CAS를 수행하지 않았다.
DB 재시작 전후 완료 job2/attempt2·등록 intent1·revision/head2·artifact6개와 ciphertext/원본·결과 HWPX/readback을 확인했다.
신규 전용 경로는 `D:/devdata/hwpx-agent-p09-pg18-catalog-identity-450`이며 기존 DB·설치 설정·원본은 수정하지 않았다.

451은935fresh/final935·설치 설정1final·산출물4final·경고없음·cleanupTrue, 전체171.969초다. unit0.468초·캐시 빌드0.235초·
SQL7.063초, 각각 Job CPU0.203/0.203/4.828초·private최고0.16844/0.16893/0.23927%였다. 시스템CPU최고40.62%·가용RAM최저17.616%이며
기존 자원 보호를 유지했다.450도 보호 중단은 없었고 시스템CPU최고75.2%·가용RAM최저15.995%였다.

현재 replay 관측에는 보관한 full claim이 필요하다. 새 공개 요청의 cold lookup·전체 manifest 재구성/복구는 아직 없고, 현재 adapter는
변경 요청 거부를 일반 RepositoryFailure로 반환한다. 공개 충돌 오류 세분화·신뢰 실행/scanner·운영 key custody/게시와 Native 자격은 남는다.
합성 route/scanner·부모 보관 임시 키와 생성 HWPX의 통합 시험이며 공식249/P09 Gate와 PC 프리즈 해결의 통과로 계산하지 않는다.

## 최종 커밋 확인과 실제 SQL 저장

공통 `StoredPrecommitGuard`는 원 CAS의 결과 저장 전과 intent/precommit/등록 후 revision commit 직전에서 검사한다.
원 job coordinator는 claim 전에도 같은 guard를 검사하고 CAS로 전달한다. 현재 source/ACL/head·설정과 server가 매번
공급하는 route/시간을 원 manifest 검증으로 대조하며 matcher/compiler를 반복하지 않는다. factory의 실패는 해당 시도에
고정되고 기존 guard 교체는 거부한다. 기존 source/ingest/intent/등록/CAS와 job claim/lease/replay/unknown 본문은 보존했다.

등록 뒤 거부되면 이미 생긴 결과·intent·precommit을 복구 자료로 남기고 head는 커밋하지 않는다. 실패를 완료/무효과/새 실행
허가로 바꾸지 않는다. guard는 추가 제한이며 source 권한/실행 자격을 대신하지 않는다. 기존 guard 없는 server primitive의
선택 경로는 유지하고, 카탈로그 SQL 연결에서는 guard를 반드시 설치한다.

[446](evidence/p09-361-catalog-storage-commit-guard446.v1.json)은 신규15+직접 영향5개가 모두 통과했다. 실제 HWPX 검증과 두 커밋
확인, route/config/clock/ACL/quarantine/AEAD 변경·실패 고정, post-registration 복구 자료 보존, claim 전 차단과 replay/unknown
비재실행을 확인했다.879fresh/final879·산출물2final·경고없음·cleanupTrue, 전체141.422초·시스템CPU최고22.35%·가용RAM최저25.519%다.

[447](evidence/p09-361-catalog-actual-sql-storage447.v1.json)은 runner가 현재298 대신 과거290 SQL 지문을 선택해 비교 단계에서
멈췄다. Cargo/DB/본문0·cleanupTrue이며 원 결과와 runner를 보존했다. 현재298의 검증된 원본 지문으로 바꿨고 제품/보호 조건은
완화하지 않았다. [448](evidence/p09-361-catalog-actual-sql-storage448.v1.json)은 새 전용 DB에서 다음 경로를 실제 실행했다.

- 생성 HWPX 원본과 고정 설치 `PrivateInfo.ini`를 원 카탈로그 compiler/manifest에 결속하고 실제 원 후보를 job에 전달했다.
- 현재 확인3회와 원 staged HWPX validator, PostgreSQL23 claim/lease/등록/revision CAS/완료 및 disk AES-GCM readback을 수행했다.
- bootstrap 포함 job2개/attempt2개·완료2개·등록 intent1개·revision/head2·암호화 artifact6개를 DB 재시작 전후 대조했다.
- 재시작 뒤 원본/결과 HWPX와 전체 expected review receipt·등록 row·intent/precommit·head를 읽어 대조했다. 실행/claim/CAS를 재시도하지 않았다.
- 다른 AES 키는 거부됐고 암호화 파일6개의 bytes/SHA는 재시작 전후 같았다. 소유 postmaster 두 번 모두 정상 종료했다.

448은919fresh/final919·설치 설정1final·빌드 산출물2final·경고없음·cleanupTrue다. 전체178.469초 중 빌드10.437초/Job CPU10.0초,
SQL 묶음6.719초/Job CPU4.5초, 각각 private최고3.10571%/0.239113%였다. 시스템CPU최고56.06%·가용RAM최저25.932%이며
기존 한 코어/BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%와 IO/출력/시간 보호를 유지했다.

기존 `D:/devdata/hwpx-agent-p09-pg18-storage-298`은 사용하지 않았고 새 `D:/devdata/hwpx-agent-p09-pg18-catalog-447`의 DB/산출물을
보존했다. 설치/private 설정 변경·한글/COM/Native·OS/Defender/WSL 변경은 없다. scanner/route는 합성이며 keys는 부모가 보관한 임시
시험 키다. 생성 HWPX는 실제 한글 저장/재열기 원본이 아니고, 재시작 관측은 완전한 manifest 재구성/등록 복구 자격을 부여하지 않는다.
신뢰 제품 route·운영 키 custody·공개 key 매핑과 전체 P09 Gate는 미완료다. 이번 결과는 PC 프리즈 해결 판정도 아니다.

## 원본 결속 저장 준비와 실제 HWPX 검증

`with_verified_storage_preparation`은 현재 manifest/route·설정·권한 검사를 거친 원 candidate에서만 준비한다.
기존 source 서비스의 전체 재구성·scope/head/ACL/quarantine/AEAD를 유지하는 crate-private helper가 fresh 원본 bytes와
project/branch/head를 callback에 빌려준다. caller source/artifact/plan/output/검증 verdict를 받지 않으며 마지막 설정/head
확인 뒤 consumer를 호출한다. callback bytes를 별도로 복사하거나 기존 원본 owner를 clone하지 않는다.

`CatalogMaskOutputValidator`의 기대값은 원 preserving candidate의 실제 출력 지문/크기와 원 output review receipt에서만
만든다. 크기/전체 SHA가 다르면 import 전에 거부하고, 맞으면 실제 staged HWPX를 bounded source/forms/review로 재수입해
전체 receipt와 원본 보호 관측을 대조한다. 한 validator는 한 번만 시도하며 두 번째 호출은 Failed다. matcher/index/mask/
operation compiler를 재실행하지 않는다. partial source/review의 Native author/time/visibility 의미를 완전한 상태로 올리지 않는다.

준비 receipt는 `validation_executed=false`와 실행/Native 권한false다. validation_contract_sha256는 manifest·실제 compiler
receipt·출력/크기·카탈로그와 expected readback에 결속된 계약 지문이며 검증 성공 보고서가 아니다. 원 WorkspaceTransaction이
실제 staged bytes로 validator를 호출해야 한다. commit binding은 원본/project/branch/head/출력과 이 계약만 사용하며,
job 준비는 caller의 canonical request/route-set 지문 불일치와 이전 revision을 거부한다. claim/lease/실행은 수행하지 않는다.
공개 문자열 idempotency key와 서버 UUID의 신뢰된 매핑도 이번 준비로 자격을 부여하지 않는다.

[442](evidence/p09-361-personal-info-catalog-mask-storage442.v1.json)는 시험 CAS closure 인자 타입 추론 오류로 컴파일 실패/본문0이다.
생산 코드는 그대로 두고 `&operation_engine::RevisionCommitRequest` 타입만 명시했다.
[443](evidence/p09-361-personal-info-catalog-mask-storage443.v1.json)는 runner의 잘못된 old dep-info 분기로 KeyError/Cargo0/본문0이었다.
분기를 고친 [444](evidence/p09-361-personal-info-catalog-mask-storage444.v1.json)는 신규14개를 한 번 실행해 모두 통과했다.
이전45개·manifest14·공식249는 반복하지 않았다. 기존 production/test 세 파일의 helper/export/include 밖은 inverse로 대조했고
기존 저장 coordinator/CAS/engine 구현은 변경하지 않았다. root 시험의 실제 의존 파일16개를 빌드 전후 대조했다.

신규14개는 실제 source/output/manifest 결속, staged reimport·한 번의 검증, 손상/다른 크기/원본 출력 거부, 기존 engine의
실제 AEAD artifact 저장·readback/revision CAS, 검증/scanner 거부 시 비커밋, job claim 기대값과 위조 지문 거부,
현재/최종 카탈로그·최종 head 경합, write/5scope·ACL/quarantine/AEAD·비노출과 route denial을 다룬다.
저장 성공 시험은 합성 keys/scanner와 메모리 repository를 사용한 원 server primitive 검증이다. 실제 PostgreSQL·신뢰 scanner/
registry·영속 job·Native 또는 사용자 문서 실행의 통과가 아니다. 임시 workspace는 시험이 정리하고 원본·실패 기록은 보존한다.

444는867fresh/final867·빌드 산출물1final·진단/경고없음·cleanupTrue, 전체125.875초·명령13.828초/Job CPU13.547초·
private최고860.13MiB/2.69965%·시스템CPU최고59.0%·가용RAM최저26.737%다. 한 코어/BelowNormal·CPU cap6.25%·
readonly private8%/stop7%·RAM/commit95%·원 IO/출력/시간 보호와 active0/empty/handle closed를 확인했다.

444 다음의 최종 guard와 실제 SQL job 연결은 위446/448에서 검증했다. 현재 validator나 준비 객체는 접근/설정/health lease가 아니며
신뢰 제품 route는 계속 거부한다. 공개 key 결속·운영 key custody와 실제 Native 자격은 별도로 남는다.

## 현재 제품과 manifest 검증

[435](evidence/p09-361-personal-info-catalog-mask-product-recovery435.v1.json)는 새 시험의 macro textual scope 오류로
컴파일 실패/본문0이었다. 새 시험에서 원 stored API를 직접 호출하도록 고쳤고 기존20개 본문은 변경하지 않았다.
[436](evidence/p09-361-personal-info-catalog-mask-product-recovery436.v1.json)은 신규42+영향3의 본문45개를 모두 통과했으나
최종 입력 재확인에서 시스템CPU90.82%로 중단됐다. 원436의 잘못된 PASS label은 수용 근거가 아니며 오류/마감 누락을 보존한다.

실행기는 모든 final fresh와 최종 guard가 끝난 뒤에만 PASS를 넣도록 수정했다. 실패 때 부분 fresh 집계를 보존하고,
PASS label이 있어도 오류 또는 마감 누락이 있으면 nonzero다. 원 실행기는 source-archive에 bytes/SHA 그대로 보존했다.
[437](evidence/p09-361-catalog-product-retained-final437.v1.json)은 원45개·입력·실제 dep-info·설치 설정·Job 종료를 확인하고
마감 계약24pass·857fresh/final857·설치 설정1final·cleanupTrue로 수용했다. Cargo/시험/Native 재실행0,
109.156초·시스템CPU최고23.61%·부모CPU최고0.390625%·가용RAM최저23.043%다.

새 manifest는 원 candidate를 이동해 기존 router/protection/manifest 본문을 공유한다. 현재 형식 카탈로그와 routing
evidence는 별도 필수 dependency다. 실제 보호·시간·target·registry binding·backend health·보존 조건과 동일 route 집합을
확인하고, 모든 manifest hash 계산 뒤 카탈로그/최종 head를 다시 확인해 consumer를 호출한다. 보관 결과에서 matcher/compiler를
재실행하지 않는다. manifest/합성 route는 실행·key claim·ingest·CAS·게시나 Native 권한이 아니다.

[438](evidence/p09-361-personal-info-catalog-mask-manifest438.v1.json)은13pass/1fail이다. 보호 문서가 router 이전 원 core에서
이미 거부되는데 시험은 compiler 생성 성공을 기대했다. 보호 코드를 바꾸지 않고 정확한 기존 Protection 오류 단언으로 고쳤다.
원 runner/시험을 보존하고 다른13개 본문/fixture helper 및 전체 생산 입력의 동일성을 확인했다.
[439](evidence/p09-361-personal-info-catalog-mask-manifest439.v1.json)는 수정1개만pass·이전13개 재사용의 고유14개다.
862fresh/final862·빌드 산출물1final·진단/경고없음·cleanupTrue, 전체117.313초·명령6.453초/Job CPU6.094초·
private최고844.89MiB·시스템CPU최고31.32%·가용RAM최저23.892%다. 원45개·공식249·한글은 실행하지 않았다.
Cargo 소유 dep-info는 재빌드 가능한 산출물로 구분하고 빌드 뒤 실제 bytes를 별도 fresh 확인했다.

한 코어·BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%와 원 IO/출력/시간 보호를 유지했다.
437/439는 PC 프리즈 원인 규명이나 해결 증거가 아니다. 전체 실행 순서는 [P09 제품 완료 계획](P09_COMPLETION_EXECUTION.md)을 따른다.

## 구현 범위

`crates/hwpx-package/src/document_import/search/replacement/atoms/personal_info/catalog.rs`는 원 Form의
전체 원본 proof와 하나의 field/review/index를 사용한다. 카탈로그 SHA·선택 종류·패턴 순서·검색 결과·
scope·body 정책·마스크 정책을 영수증에 결속하고 실제 일치 좌표를 원본 scalar에 대응시킨다.
주변 텍스트나 선택 영역 전체를 가리지 않으며, 인접한 별도 일치도 각각의 마스크 그룹으로 유지한다.

원본 scalar마다 별표를 넣는 정책과 일치 그룹마다 별표3개를 넣는 정책을 지원한다. 기존 Unicode 변경
compiler·보존 writer·전체 출력 readback을 재사용하고 원 run shell·style·control·참조와 선택 밖 슬롯을
검사한다. 부분적으로만 대응되는 Unicode 원본, 보호 영역이나 field cache, 불일치 원본, 무일치·무변경은
부분 산출물 성공으로 바꾸지 않는다. 출력과 변경 anchor 목록은 source/output/receipt 지문에 결속한다.

`crates/product-cli/src/form_stored_provider/actual_import/source_search/personal_info_catalog/mask.rs`는
현재 `document.write`, tenant/subject/project/branch/document, head·ACL·quarantine·AEAD와 원본 proof를
확인한다. 생성 시와 보관 결과 전달 시 현재 카탈로그를 다시 읽고, 소비자 호출 직전에 카탈로그와 최종
head를 대조한다. 결과 조회 때 검색·마스킹을 반복하지 않는다. preview로 전환하면 출력 bytes와 변경
inventory를 버리며, metadata에서 변경 실행 capability를 복원하지 않는다.

새 profile은 `hwpx-agent.source-personal-info-catalog-mask/v1`,
`hwpx-agent.stored-personal-info-catalog-mask/v1`,
`hwpx-agent.stored-personal-info-catalog-mask-preview/v1`이다. 원문·패턴 본문·개별 값 지문은 공개하지 않는다.
원본 문서·head·ingest 수는 변경하지 않으며 문서 전체 익명화나 Native 실행 자격으로 표시하지 않는다.

## 검증 결과

| 증거 | 실행과 결과 | 입력과 정리 |
|---|---|---|
| [427](evidence/p09-361-personal-info-catalog-mask427.v1.json) | source30 PASS. 저장 서비스 시험은 include 파일 첫 줄의 inner doc comment E0753으로 컴파일 실패, 실행0. 실패 원본 보존 | 842fresh/final842,cleanupTrue |
| [428](evidence/p09-361-personal-info-catalog-mask-recovery428.v1.json) | 해당 주석만 일반 주석으로 변경하고 저장20 PASS. source30은 동일 코드/시험 입력으로 보존, 재실행0. 현재 고유50 PASS | 844fresh/final844,진단·경고없음,cleanupTrue |

두 integration test의 실제 dep-info를 사용해 기존 입력과 신규 시험 파일을 빌드 전에 선언하고, 빌드 후
의존 파일 집합을 대조했다. 서로 다른 입력의 합집합18개에 raw XML을 포함했다. production source와
검증 실행 입력도 시작·종료에 확인했다. 기존 네 파일의 변경은 module export/test include 추가뿐이며
기존 알고리즘과 시험 본문은 inverse 대조로 보존했다.

원본 처리 시험은 실제 일치만 변경, 인접/여러 run/조합 문자/제어 문자, 네 scope, 숨김·메모·보호·field
cache, 전체 선택 패턴 사용, 보존 readback, 한도와 비식별 영수증을 다룬다. 저장 시험은 합성64개 패턴,
현재 설정 변경·읽기 실패, 권한과 외부 scope, 원본 무결성, 네 최종 head 경합, preview 분리와 전달 직전
설정 경합을 다룬다. 후속436/437의 명시적 설치 fixture는 실제 고정 카탈로그의 전화8패턴과 전체64패턴 metadata를
사용한 합성 문서 마스킹/공통 compiler를 확인했다. 실제 한글 변경 시험은 아니며417의 읽기 결과도 변경 증거로 재사용하지 않는다.

427은 전체175.422초, source 명령33.781초/Job CPU31.844초, 실패한 저장 컴파일34.781초/CPU33.688초다.
private 최고1923.40MiB·시스템CPU최고34.94%·가용RAM최저42.739%였다.428은 전체122.797초,
저장 명령15.672초/CPU13.250초·private815.89MiB·시스템CPU최고63.87%·가용RAM최저10.719%였다.
두 실행의 모든 검증 Job은 active0·tree empty·handle closed를 확인했다. 원 한 코어/BelowNormal·CPU
cap6.25%·readonly private8%/stop7%·RAM/commit95%를 유지했다.428 뒤 현재 관측은 CPU14%·가용RAM11.06%·
commit54%였고 추가 Cargo 작업을 시작하지 않았다. 이 수치는 시스템 전체 관측이며 PC 프리즈 해결 판정은 아니다.

## 제품 요청과 공통 compiler의 초기 검증 이력

새 엄격한 요청은 원본·카탈로그 지문과 선택·정책·preview/key/plan/provider를 결속하도록 작성했다.
현재 카탈로그를 명시적으로 받는 진입점에서 기존 source-owner 해석·OperationPlanCompiler·공통 receipt
본문을 재사용한다. 무설정 dispatcher의 거부와 preview의 무출력/컴파일 거부는 유지한다.
상세 계약: [카탈로그 마스킹 제품 요청](../../protocol/migrations/p09-personal-info-catalog-mask-product-v1.md).

[431](evidence/p09-361-personal-info-catalog-mask-product431.v1.json)은 전체58.282초 중 Job CPU3.016초,
private643.83MiB에서 가용RAM4.881%로 내려가95% 보호가 작동했다. 시험0·cleanupTrue이며 최종 fresh 누락을
보존한다. 코드 검토 후 새 로더별 중복 컴파일을 줄이는 어댑터와 일치/구성요소 예산 분리 회귀 사례를
추가했다. 최적화의 실측 효과와 새 제품42개·영향3개 시험 결과는 아직 없다.

[432](evidence/p09-361-personal-info-catalog-mask-product-recovery432.v1.json)는 가용RAM6.999%와 비교 가능한
완료 빌드 peak6.037%를 먼저 대조해 Cargo를 시작하지 않았다.3.031초·11fresh/final11·cleanupTrue이며
사전검사 모델4묶음만 수행했다. 전체 입력검사/컴파일/제품시험·설치 fixture는 실행하지 않았다. 시스템/다른
앱 설정과 프로세스를 변경하지 않았으며, 실제 RAM/commit95% 보호를 낮추거나 끄지 않았다.

[433](evidence/p09-361-catalog-mask-product-source-syntax433.v1.json)은 새 Rust 파일3개의 문법만 읽기 전용으로
파싱했다.12.468초·4fresh/final4·도구1final·exit0·stderr0·cleanupTrue이며 CPU최고8.74%·가용RAM최저10.723%다.
파일 변경·타입 검사·제품 시험은 하지 않았다. 당시 미확인이던 제품/설치 fixture45개는 위436/437에서 별도로 마감했다.

## 남은 연결과 검증

1. 준비 이후 실제 커밋 직전의 현재 카탈로그/route guard와 신뢰 자격·실제 scanner 연결.
2. 공개 요청 key의 v2 등록 결과 조회 연결은472에서 확인했다. 운영 custody·키 유실·게시/장애 경계와 실제 실행 자격은 남는다.
3. 실제 target의 일치·마스킹·저장/재열기 의미와 필요한 Native 대조.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다. CROSSREF8종은
NOT_RUN이고 외부 run001 실패/claim 소비와 Native011 미승인·미실행은 별개로 보존한다.
