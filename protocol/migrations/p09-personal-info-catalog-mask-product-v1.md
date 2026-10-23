# 개인정보 카탈로그 마스킹 제품 요청과 공통 compiler

전체 카탈로그의 실제 일치 문자열을 마스킹하는 제품 요청과 공통 변경 compiler 연결을 위한 구현 계약이다.
신규42+영향3개는436의 본문 통과 뒤437의 별도 입력 마감으로 수용했다. 현재 카탈로그를 필수로 받는
공통 router/실행 manifest 연결도439의 고유14개로 확인했다.444는 원본 결속 저장 준비와 실제 staged HWPX 검증·기존
저장 primitive 연결14개를 확인했다.446은 최종 mutation guard 신규15+영향5개,448은 생성 HWPX의 실제 SQL23 job/AEAD/재시작
readback을 확인했다.451은 원 요청 key의 서버 ID 결속과 실제 SQL 완료 관측/변경 요청 거부를 확인했다.
457은 공개 요청 cold lookup의 실제 SQL24/현재 ACL/typed 충돌/재시작을 확인했다.
459는 공통 진입점의 조회 우선 분기8개를 확인했다. 신뢰 실행·운영 저장/게시·key custody와 Native 자격은 남는다.
462의 읽기 전용 Windows 키 provider는 별도 프로세스의 AES/HMAC 읽기를 확인했고464는 새 SQL24 저장 경로에 연결했다.
부모 AES/HMAC 환경변수 없이 원 HWPX 저장·AEAD·서명 다운로드와 DB 재시작 readback을 확인했다.
[키 보관 계약](p09-artifact-windows-key-custody-v1.md)을 따른다. 운영 발급/키 유실 복구·실제 scanner/신뢰 route는 별도로 남는다.
467/468은 원 manifest 없는 readonly 등록 복구를 별도로 확인했다. 새 공통 job의 intent v2와 기존 v1의 명시적 원 manifest 요구는
[v1→v2 계약](p09-stored-commit-intent-v1-to-v2.md)을 따른다. 공개 key의 현재 job/attempt에서 등록 결과로 이어지는 명시적 복구는470/471에서 구현 시험했고472의 실제 SQL24/OS 키 재시작 전후에 확인했다.
이전 source30/저장20이나 설치 파일 읽기 결과를 새 변경 제품의 검증으로 대체하지 않는다.

## 요청과 현재 카탈로그

기존 작업 조회는 `StoredPersonalInfoCatalogMaskProductRequest::prepare_lookup_json`과 `PreparedCatalogRequestLookup::observe`를 사용한다.
동일 strict 요청을 현재 read/write·5scope와 서버 ID에 결속하며 source ZIP/import/head/카탈로그/regex/compiler를 실행하지 않는다.
현재 provider scope와 SQL project/source ACL은 관측마다 필수다. 이전 base head의 작업도 조회할 수 있지만 권한이 철회되면 거부한다.
`NotObserved`는 새 작업 실행 허가나 무효과 증명이 아니고 `Existing`은 metadata 관측이지 독립적인 완료 효과/AEAD/의미 readback 증명이 아니다.

`PreparedCatalogRequestLookup::recover_registered`는 별도의 명시적 결과 조회다. 현재 SQL 관측과 같은 key/job/attempt만
등록 locator로 사용하고 원 manifest·claim·locator·별도 ServiceRequest 없이 v2 영수증을 복구한다.
완료 metadata의 revision을 복구 결과와 대조하고, 마지막 SQL 관측에서 권한/요청/상태/시도가 바뀌면 오류로 종료한다.
읽기 전용 관측이며 새 실행·재시도·작업 상태 변경이나 Native 의미 증거가 아니다. 원 `observe`의 가벼운 조회는 그대로다.

`0024_p09_stored_request_lookup`은 additive migration이다. 자동 설치/권한 부여는 없으며 명시적 schema24 connector가 필요하다.
기존 schema23 connector는24를 거부한다. 새 connector도 원23 schema/privilege/RLS 검증 전체를 유지한다.
lookup 함수는 고정 search_path의 SECURITY DEFINER이며 PUBLIC 실행을 철회한다. revision role만 필요한 함수 실행 권한을 받고
artifact role은 받지 않는다. 기존 두 composite PK를 검사해 정확한 point lookup을 사용하며 job table 직접 grant는 추가하지 않는다.
요청의 immutable 전체 결속이 다를 때 고정 SQLSTATE23505+`STORED_REQUEST_KEY_CONFLICT`만 typed conflict다. 다른 오류/불확정은
미관측으로 바꾸거나 claim/lease/retry로 우회하지 않는다. SQL 변경/잠금·새 attempt·CAS는 조회 API에 없다.

STABLE 함수가 쓰기 helper를 호출할 가능성까지 막기 위해 별도로 repeatable-read READ ONLY transaction을 요구한다.
이는 [PostgreSQL 함수 volatility 계약](https://www.postgresql.org/docs/18/xfunc-volatility.html)과
[함수 권한/search_path 지침](https://www.postgresql.org/docs/18/sql-createfunction.html)을 따른다.
검증 범위와 실패 원본은 [457 및 제품 현황](../../implementation/p09/P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md#원-claim-없는-기존-작업-조회)을 따른다.

schema_version은 `hwpx-agent.product-personal-info-catalog-mask-request/v1`이다. 요청은 idempotency_key,
project_id,document_id,base_revision,expected_head_generation,expected_source_package_sha256,
expected_catalog_sha256,plan_id,selector,operation을 요구한다. selector는 기존 revision 결속
document/section/node_set/selection과 정확한 NFC scalar 좌표를 사용한다.

operation은 kind=`mask_personal_info_catalog`,families,mask_policy,max_matches,max_changed_components,
review_policy,preview_only가 필수다. families는 기존11종의 중복 없는 문자열 배열이며 원 선택 패턴을
모두 사용한다. mask_policy는 `per_original_scalar_preserve_slots` 또는 `three_asterisks_per_text_group`이다.
각 수량은1~10000이며 서버가 검증한 더 작은 예산을 늘릴 수 없다. 일치 수와 변경 구성요소 수는 별개로
검사한다. 예를 들어 두 run에 걸친 하나의 일치는 두 구성요소를 변경할 수 있다.

요청 상한은16KiB이며 중복·이스케이프 중복 key, 뒤따르는 JSON, 알 수 없는 필드/버전/종류, enum 객체,
원문 패턴·임의 파일 경로·승인 필드를 거부하도록 작성했다. 현재 구현은 서버의 유한 예산으로 생성한
불변 결과가 요청의 두 수량 상한을 만족하는지도 반환 전에 검사한다. 요청 상한으로 공통 서버 예산을
줄여, 허용된 다중 구성요소 일치를 잘못 거부하지 않는다. 초과 결과는 외부 소비자에게 전달하지 않는다.

`StoredPersonalInfoCatalogMaskProductRequest::prepare_json`은 호스트가 제공한 현재 카탈로그 로더를
명시적으로 받는다. 합성/설치 로더는 하나의 빌린 어댑터를 사용하며, 카탈로그 bytes를 캐시하거나 설정
경로를 요청에서 받지 않는다. raw/canonical/scoped 지문에 원본·카탈로그·종류 순서·정책·key·plan·scope를
결속하고 현재 `document.write`·head/ACL/quarantine/AEAD를 기존 저장 경로에서 확인한다. 전체 metadata
직렬화 뒤 현재 카탈로그와 최종 head를 확인하는 경로를 유지한다.

profile은 `hwpx-agent.product-personal-info-catalog-mask-preparation/v1`, capability_id는
`search.personal_info_find_replace`다. profile/capability는 실행 자격이나 설치 vendor 인증이 아니다.

## 공통 compiler와 preview 경계

명시적 `StoredProductRequest::prepare_catalog_mask_or_observe_json`은 원 strict 조회를 먼저 호출한다.
`CatalogRequestEntry::Existing`은 기존 job metadata만 반환하며 source/카탈로그/regex/compiler를 호출하지 않는다.
`NotObserved`일 때만 기존 `prepare_compiled_catalog_mask_json`을 한 번 호출해 `Prepared`를 반환한다.
조회 실패/typed conflict/unknown outcome을 미관측으로 바꾸지 않는다. 새 실행·완료 효과·부재 lease·자동 retry 권한은 없다.
새 작업과 경합하면 원 SQL claim/immutable binding 검사를 여전히 통과해야 한다. 기존 무설정 dispatcher는 그대로다.
459의 신규8개는 이 분기의 직접 제품 검증이며457의 SQL 묶음과 과거 전체 시험은 반복하지 않았다.

`StoredProductRequest::prepare_compiled_catalog_mask_json`은 현재 카탈로그를 별도 인자로 받는 진입점이다.
기존 무설정 dispatcher는 새 schema를 거부하며 이전 선택 마스킹이나 보관 카탈로그로 대체하지 않는다.
preview 요청은 이 진입점에서 문서/카탈로그 접근 전에 거부한다. 준비된 preview도 변경 inventory나 출력
bytes를 복원하거나 compilation으로 전환할 수 없다.

새 compiler adapter는 원 candidate를 이동해 기존 source-owner 해석과 OperationPlanCompiler를 호출한다.
원본·출력·receipt·inventory와 실제 XML text anchor를 대조하고, 기존12개 고정 인자를 가진 변경 작업을
실제 구조 owner에 결속한다. 새 edit domain은 `catalog_matched_mask_text_splices`다. 기존 공통 receipt
본문은 view를 받는 함수로 추출했으며 기존 caller는 같은 본문으로 위임하도록 변경했다.

컴파일이 끝난 뒤에도 현재 카탈로그와 최종 head를 다시 확인하도록 작성했다. 보관된 compiled plan의
조회/bytes 전달은 현재 카탈로그를 필수로 받으며 원 후보의 검증 경로를 사용한다. 검색·마스킹·compiler를
재실행하는 전달 경로를 추가하지 않았다. plan/receipt는 데이터이며 실행·key claim·승인·CAS·ingest·게시나
Native 권한을 발급하지 않는다. routing manifest 연결은 아래와 같고 실제 변경/저장 통합은 남아 있다.

## 현재 카탈로그를 유지하는 공통 manifest

`PreparedCompiledCatalogMask::prepare_execution_manifest`는 현재 형식 카탈로그 source와 `RouteContext`,
`CapabilityRouteCatalog`,transaction을 명시적으로 받는다. 기존 검색 manifest의 router·실제 원본 보호·시간·
DirectHwpx backend·source/plan binding 본문을 `make_for_view`로 공유하고 원 wrapper는 같은 본문에 위임한다.
호출자 source/bytes/plan/routes receipt를 받는 새 우회 생성자는 없다.

`PreparedCatalogMaskExecutionManifest`는 원 candidate·plan·보호 관측을 보관한다. 생성 시 manifest 지문 계산 뒤
현재 카탈로그와 마지막 head를 확인하며, 보관 결과의 verify/bytes 전달은 현재 접근·설정·route health와 target/
registry/backend identity·전체 manifest 지문을 다시 대조한다. 모든 계산 뒤 카탈로그/최종 head 확인이 consumer보다
앞선다. 검색·마스킹·compiler를 재실행하지 않는다. preview에는 이 타입이나 진입점이 없다.

439의 고유14개는 신규13+기존 selected-mask adapter 영향1이다. 독립 router/from_receipts 대조, 기존 호출 경로,
원 거부 조건·유효하나 달라진 route identity·시간·현재/최종 설정·실제 원본 보호·write/5scope·ACL/quarantine/AEAD·
최종 head 경합·transaction·비노출·원본/ingest/head 불변과 route denial을 검증했다. 합성 route evidence가 신뢰 registry나
실행/승인 권한을 발급하지 않으며 P02 routing_allowed=false와 실제 제품 route 거부는 그대로다.

## 원본 결속 저장 준비와 staged readback

`PreparedCatalogMaskExecutionManifest::with_verified_storage_preparation`은 현재 형식·routing evidence와 source 접근을
확인하고 원본 source/output·project/branch/head·manifest만 callback에 빌려준다. 마지막 설정/head 검사 뒤에만 호출한다.
`PreparedCatalogMaskStorage`는 외부 constructor/deserialization이 없고 caller 원본·출력·검증 verdict를 받지 않는다.

원 preserving candidate의 실제 output review receipt와 전체 출력 SHA/크기가 `CatalogMaskOutputValidator`의 유일한 기대값이다.
실제 staged HWPX를 source/forms/review로 재수입하고 원본 보호 관측·전체 receipt를 대조한다. 임의 bytes는 크기/지문으로 먼저
거부하며 한 validator의 두 번째 호출은 Failed다. Native 의미·완전한 문서 상태·새 접근/설정 lease를 만들지 않는다.

`CatalogMaskStorageReceipt` profile은 `hwpx-agent.catalog-mask-storage-preparation/v1`이다. `validation_executed`와
`execution_or_native_authority`는false다. 계약 지문은 실제 validation 성공 보고서가 아니며 원 engine의 validator 호출을
생략할 수 없다. `commit_binding`은 서버 새 commit/revision만 받고 원 source/head/output/validation 계약은 교체할 수 없다.
`prepare_job`은 기존 StoredJobOptions의 request SHA가 원 canonical request, capability SHA가 원 route-set과 같아야 한다.
기존 durable job 기대값을 준비할 뿐 claim/lease/재실행을 허가하지 않으며 문자열 key→서버 UUID의 신뢰 매핑은 별도다.

444의 신규14개에는 실제 engine의 staged 검증→AEAD artifact 저장/readback→revision CAS와 검증/scanner 거부가 포함된다.
합성 scanner/keys와 메모리 repository의 server primitive 통합이며 실제 SQL·신뢰 registry·제품 route/Native 자격이 아니다.
준비 receipt는 최신 접근/설정 lease가 아니다. 실제 제품 경로는 아래 guard 설치와 별도의 신뢰 실행 자격을 요구한다.

## 최종 커밋 guard와 실제 SQL job 경계

`StoredPrecommitGuard`는 원 저장 CAS에 추가하는 server restriction이다. `require_precommit_guard`는 실행 전에 한 번만
설치할 수 있고 교체/실행 후 설치를 거부한다. 원 job coordinator는 claim 전 검사 뒤 동일 guard를 원 CAS의 결과 저장 전과
revision commit 직전으로 전달한다. 원본 확인·암호화 저장/readback·intent/precommit·등록과 최종 source/result 대조는 유지한다.

`PreparedCatalogMaskExecutionManifest::current_commit_guard`는 현재 provider와 카탈로그 source, 매 검사마다 현재
`RouteContext`/`CapabilityRouteCatalog`/시간을 공급하는 server callback을 받는다. 원 manifest verify로 source/ACL/head,
현재 형식·원 보호 관측·route target/registry/backend/health/시간/보존과 전체 지문을 확인한다. 한 번 실패한 guard는
상태가 되돌아와도 같은 시도에 재사용할 수 없다. callback의 신뢰 출처 자체를 인증하거나 거부된 제품 route를 열지는 않는다.

최종 guard가 등록 뒤 실패하면 원 결과·intent·precommit/등록 영수증을 남기고 revision CAS를 호출하지 않는다. 삭제/rollback,
자동 재시도·unknown/완료 승격을 하지 않는다.446의 신규15+영향5개는 이 경계와 기존 replay/ack-loss 경로를 검증했다.

448은 새 소유 PostgreSQL23 DB와 disk AES-GCM에서 원 카탈로그 후보·staged HWPX validator·guard3회·job/lease/등록/CAS/완료를
실제 연결했다. 재시작 전후 artifact6개·완료 job2개/attempt2개·등록 intent1개·revision/head2와 ciphertext를 대조했고,
원본/결과 HWPX/review receipt·등록 영수증/head readback 및 다른 암호키 거부를 확인했다. 재시작 후 실행 재시도는 없다.
생성 HWPX·합성 scanner/route·부모 보관 임시 키의 통합 fixture이며 실제 한글 원본/저장·신뢰 registry/scanner·운영 키 custody는 아니다.
원 manifest 전체 재구성에 의한 등록 복구와 공개 요청의 cold lookup은 별도로 마감한다. 원 key의 ID 결속은 아래451 범위다.

## 공개 key와 원 요청의 server job 결속

`PreparedCatalogMaskStorage::job_identity`는 원 strict 요청과 authenticated provider에서 생성한 불변 `StoredRequestJobIdentity`다.
버전 고정 namespace는 기존 SQL과 같은 tenant/project/public-key 범위다. 내용을 바꾸거나 다른 actor/branch/document/head/schema를
사용해 같은 key에 새 ID를 얻을 수 없다. 역할별 key/job/request UUID는 분리하고 canonical/scoped 지문은 전체256bit로 보존한다.
원 key bytes를 정규화·노출하지 않으며 ID/Debug가 claim·lease·재시도 권한을 만들지 않는다.

`prepare_bound_job(StoredJobPolicy,commit,new_revision,limits)`은 key/job/request UUID를 입력받지 않는다. 원 private ID와 canonical/
scoped request·source/head·원 route-set을 결속하고 기존 retry policy 범위와 새 revision·job 검사를 적용한다. 현재 guard 설치와
staged HWPX 검증은 별도 필수다. 낮은 수준의 `prepare_job`은 기존 server primitive로 유지되며 외부 요청의 key 매핑을 대체하지 않는다.

451의 고유15개와 새 SQL fixture는 key 안정성/구분·원 claim 결속·scope/정책 거부 및 완료 관측·같은 key의 변경 요청 거부를 검증했다.
제품9개는450에서 입력/본문 동일성 확인으로 재사용하고 누락 입력3개를 등록한 공통 unit6개만 다시 실행했다. 원 full claim의 반복은
관측일 뿐 lease/실행/새 attempt가 아니다. source/head가 바뀐 새 공개 요청에서 현재 compiler를 재실행하는 것으로 replay를 구현하지 않는다.
그 요청의 cold lookup·영속 full claim/manifest 복구와 공개 충돌 오류 세분화는 미완료다. 기존 SQL/scanner/route/Native 자격 범위는 그대로다.

## 초기 검증 이력과 자원 관리

신규42개는 합성41개와 명시적 설치 카탈로그 fixture1개다. 별도 feature
`p09-installed-format-fixture`를 사용하며 고정 설치 파일을 읽기만 한다. 실제 한글은 실행하지 않는다.
기존 공통 receipt 위임의 영향3개도 선택했다. 이45개는 후속436/437에서 마감했다. 아래431~433은 그 전의 이력이다.

[431](../../implementation/p09/evidence/p09-361-personal-info-catalog-mask-product431.v1.json)은 한 코어/낮은
우선순위·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%에서 실행했다. 시스템 가용RAM이4.881%로
내려가 원 보호가 작동했고 검증 Job을 정리했다. Job CPU3.016초/private643.83MiB,시스템CPU최고25.78%였으며
시험 시작은 관측하지 못했다. 최종 fresh 누락도 그대로 보존한다.

그 뒤 새 코드의 로더별 중복 monomorphization을 줄이는 어댑터와 수량 예산 분리를 추가했다. 메모리 감소
효과는 아직 실측하지 않았다. 재시도 준비는 먼저 현재 가용RAM과 비교 가능한 완료 빌드의 관측 peak를
대조한다. 실제95% 보호는 유지하며, 이 작업의 예상 점유분을 뺀 여유가 부족하면 Cargo와 전체 입력 검사를
시작하지 않는다. 이 예측은 메모리 예약이나 Native 실행 허가가 아니다.

[432](../../implementation/p09/evidence/p09-361-personal-info-catalog-mask-product-recovery432.v1.json)는
가용RAM6.999%와 이전 완료 빌드 peak6.037%를 관측해, 기존95% 보호를 유지하려면 필요한 가용11.037%에
미달한다고 판정했다.3.031초·11fresh/final11·cleanupTrue이며 Cargo0/제품시험0이다.4개 사전검사 모델 묶음은
제품 검증이 아니다. 이후436은 본문45개 통과 뒤 CPU 보호로 입력 마감에 실패했고437에서 본문 재실행 없이 마감했다.

[433](../../implementation/p09/evidence/p09-361-catalog-mask-product-source-syntax433.v1.json)은 읽기 전용
rustfmt로 신규 Rust 파일3개의 문법을 파싱했다. exit0·stderr0·4fresh/final4·도구1final·cleanupTrue다.
12.468초·시스템CPU최고8.74%·가용RAM최저10.723%이며 파일을 포맷하거나 변경하지 않았다. 이 결과는
타입 검사·링크·제품 시험의 대체가 아니다. 현재437/439 수용과 실패 원본·자원 수치는
[제품 현황](../../implementation/p09/P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md)의 현재 검증 절을 따른다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다. 실제 한글/Native와
문서 변경·저장·게시, P09 Gate는 이 계약의 코드 작성이나 자원 사전검사로 완료되지 않는다.
