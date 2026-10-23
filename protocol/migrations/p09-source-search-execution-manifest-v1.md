# 실제 원본 계획의 실행 manifest 연결

현재23개 치환·변환의 PreparedCompiledSearchMutation::prepare_execution_manifest는 실제 source-bound
plan을 기존 CapabilityRouter·ExecutionManifest::from_receipts에 직접 연결한다. provider 소유 원본과
계획의 identity를 보존하는 데이터 경로이며, 실제 registry 신뢰나 실행 권한을 생성하지 않는다.

## 공통 저장 엔진 연결

일반23계열은 manifest를 다시 만들기 전에 `prepare_search_or_observe_json`으로 기존 요청부터 조회할 수 있다.
515의 신규30개는 완료/진행 중의 source/head 재준비 방지와 미관측의 원 hash/후보 결속, 오류/불확실에서의 fallback 금지를 확인했다.
상태와 등록 효과 readback을 구분하며 실제 실행 권한은 발급하지 않는다. [조회 우선 계약](p09-search-request-observation-v1.md)을 따른다.

일반23계열의 원 source-bound manifest를 `with_verified_storage_preparation`으로 기존 validator·암호화 artifact 저장·revision CAS·job 준비에 연결했다.
513은 원본 HWPX의23계열 저장/CAS와 안전/복구8개의 현재31개를 입력984개 전후 확인으로 마감했다.
직접 readback·현재 commit guard·복구 artifact 보존의 결과이며 운영 SQL·실제 registry·Native 실행 자격을 발급하지 않는다.
기존 RouteUnqualified와 P02 routing_allowed=false는 그대로다. [검색 변환 후보의 공통 저장 연결](p09-search-mutation-storage-v1.md)을 따른다.

## 원본과 계획의 결속

API는 원 prepared 후보를 소비하고 provider, server-owned RouteContext/CapabilityRouteCatalog,
TransactionId, 현재 service seconds를 받는다. caller가 source artifact/바이트/크기/SHA·다른 plan·
저장한 RouteDecision을 대신 넣을 수 없다. source artifact는 원 stored receipt의 public ID를 domain
ArtifactId로 변환하고 크기는 원 source_bytes에서 가져온다. 원 source SHA·revision·plan과 원 router의
전체 route 집합을 ExecutionManifest::from_receipts에 전달한다. 원본 package나 검색을 다시 수입하지 않는다.

PreparedSearchExecutionManifest는 외부 생성자/역직렬화가 없으며 원 compiled 후보·manifest와 그 SHA,
정확한 target profile SHA 및 route 집합을 보관한다. manifest/route getter는 데이터 조회이며 key claim,
실행 permit 또는 신뢰 registry가 아니다. 원 output SHA와 정확한 source edit inventory는 보관 후보에
계속 결속된다. Debug는 원문·요청·private key·anchor를 출력하지 않는다.

## 같은 snapshot의 route 공유

CapabilityRouter::route_plan은 원 route(operation, context, catalog)를 capability별 한 번 호출한다.
원 route 판정이 capability와 같은 context/catalog에만 의존하므로 이후 같은 capability의 결과는
원 결정에서 operation ID만 교체한다. 여러 capability를 하나로 취급하지 않으며 하나라도 실패하면
부분 route 집합을 반환하지 않는다. 원 단일 router의 정책·support·정확한 target·registry identity·
보호·보존·health/TTL·동률 거부는 변경하지 않았다.

cache는 한 호출의 불변 snapshot 안에만 존재한다. 보관한 manifest를 나중에 검증하거나 byte 전달할 때는
원 router를 현재 context/catalog로 다시 호출하고 모든 route와 manifest 지문을 비교한다. 새 health
generation·backend·registry·정확한 target build 변경은 기존 manifest에 재결속되지 않는다.
원 route가 나중에 capability 외 operation 내용에도 의존하도록 변경되면 이 공유 알고리즘도 함께 재검토해야 한다.

## 현재 접근과 시간

artifact service의 시간 단위는 seconds이고 router는 milliseconds다. now.checked_mul(1000)이
context.now_unix_ms와 정확히 같아야 하며 overflow나 오래된 clock snapshot은 거부한다. 서버는 같은
현재 시각으로 두 입력을 구성해야 한다. 이전 context를 들고 시간을 갱신하지 않은 채 사용하지 않는다.

prepare/verify/전달은 원 compiled with_verified_bytes의 현재 write/scope/head/ACL/quarantine/AEAD·
source/output integrity를 그대로 사용한다. routing과 manifest 대조 뒤 source 최종 head를 한 번 더 확인하고
그 다음 원 byte callback을 호출한다. 이 여러 읽기는 atomic CAS나 오래 유지하는 접근 lease가 아니다.
DirectHwpx 후보에 Hybrid/DesktopAutomation 경로를 연결하지 않으며 그 backend에는 별도 executor 자격이 필요하다.

## 검증과 보존

components218은 Deserialize가 없음을 설명한 주석을 금지 코드로 오인해 사전 정적 검사에서 실패했다.
Cargo0·시험0이며 원 기록을 보존했다. 제품 주석 표현과 새 시험 match 분기의 버려지는 반환값만 고쳤다.
recovery219는 신규26pass·756fresh/final756·진단/경고없음·cleanupTrue다. 기존 compiler36개·공식249는
반복하지 않았다. 원 single router/context 보안과 기존 compiler/제품/시험 본문은 역변환·불변 입력으로 확인했다.

검증은 모든16계열 실제 원본→계획→manifest,128개 편집과20개 혼합 capability의 원 개별 route 동등성,
부분 결과 거부·미지원/target/registry/policy/보호/보존/health/TTL/동률·잘못된 backend 거부, clock/overflow,
새 target/registry/health/backend drift·현재write/외부5scope·ACL/격리/AEAD·마지막head 경합,
transaction/key와 원 source/plan의 정확한 결속·비노출·원 source/head/ingest 보존을 포함한다.

219 전체176.375초·명령79.734초/시험15.56초·Job CPU77.125초·private최고1870.93MiB/5.8722%·
시스템CPU최고26.17%·가용RAM최저23.6163%다. Job active0/empty/handle closed와 한 코어 affinity4·
BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했다.
OS/Defender/다른 앱 변경이나 PC 프리즈 해결을 주장하지 않는다. 근거는 implementation/p09/evidence의
p09-361-source-search-manifest-components218.v1.json 및 p09-361-source-search-manifest-preflight-recovery219.v1.json이다.

## 남은 실행 자격

시험 routing evidence는 합성 fixture다. 제품 코드는 SignatureVerified/SupportState::Verified를
생성하거나 실제 서명 검증을 했다고 주장하지 않는다. P02의 routing_allowed=false를 승격하지 않으며
이 데이터 adapter는 실제 registry provenance·현재 target·전체 source protection을 증명하지 않는다.
require_current_product_route는 현재 source/route 검증 뒤에도 원 RouteUnqualified를 유지한다.

신뢰 registry와 target·전체 source protection 결속, 실제 실행 dispatcher·ingest/commit/CAS·영속 멱등
실행·transport/게시·전체 검색/참조·target match_set/semantic_diff/reopen·Native/Gate는 미완료다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

## 실제 원본 보호 신호 결속

manifest 준비는 같은 provider 소유 원본의 source-protection-signals/partial-v1을 원 현재 byte 검증
안에서 한 번 관측한다. 보수적 문서 신호가 있으면 caller Unprotected context로도 거부한다. 원 local
guard는 선택 밖 잠금을 전역 잠금으로 확대하지 않는다. 관측 결과는 document/source SHA/provenance와
전체 part/XML/element 수에 결속되며 이후 현재 검증에서는 재관측·추가 ZIP/원본 수입 없이 재사용한다.
고유44개 구성요소 검증은 Native 보호 없음이나 암호학적 서명·registry 신뢰 증명이 아니다.
[원본 보호 신호 계약](p09-source-protection-signals-v1.md)을 따른다.

## 보존된 P02 registry의 실제 서명 검증

별도 prepare_compiled_search_json_with_pinned_registry는 실제 보존된 P02의 envelope·공개 trust pin과
Ed25519를 확인한 불변 PinnedP02RegistryEvidence를 받는다. 닫힌 schema 분류 뒤 원본/후보 작업 전에
기존 routing_allowed=false로 거부하며 signed verified claim을 현재 route 자격으로 바꾸지 않는다.
고정 역사적 snapshot 소비자는 실제 P09 registry/target·Native 보호·실행 권한이 아니다. 기존 typed
context의 manifest 데이터 경로와 원 RouteUnqualified는 그대로다.
[고정 P02 서명 소비 계약](p09-pinned-p02-registry-evidence-v1.md)을 따른다.

## 문단 정렬의 실제 이동 목록과 공통 계획

공통 dispatcher의17번째 정렬 schema도 실제 후보·원본 소유자·source/output SHA와 이동 목록에서
OperationPlanCompiler 및 같은 manifest 경로로 연결된다. SourceParagraphSortSpliceInventory의
final_permutation_splices는 고정 slot을 제외한 실제 목적 anchor·원 part byte 범위·치환 SHA/크기다.
원본6+신규 compiler/manifest12+영향기존3=고유21개 검증이며 현재21개 단일 실행이 아니다.
이 manifest 시험의 라우팅 증거는 합성 fixture다. 실제 target/registry·Native 보호·실행·commit/CAS·
영속 멱등/게시 자격은 없고 routing_allowed=false와 RouteUnqualified는 유지한다.
[정렬 공통 계획 계약](p09-sort-operation-compiler-v1.md)을 따른다.

## 다중 그룹 정렬의 공통 계획 연결

공통 dispatcher의18번째 schema는 다중 part의 실제 이동 목적 slot을 원 source anchor·part byte 범위와
receipt/목록 SHA로 결속한다. 원 final_permutation_splices projection·compiler·manifest를 재사용하며
고정 slot과 무변경 그룹을 편집으로 세지 않는다. source6+신규 compiler/manifest14+영향기존5의25개와
무손실 기록 형식4계약을 compact249에서 확인했다. 첫248 저장 실패는 수용으로 사용하지 않는다.
합성 route fixture는 실제 trust/target/Native 자격이 아니며 P02 routing_allowed=false와
RouteUnqualified를 유지한다. [다중 그룹 공통 계획 계약](p09-sort-groups-operation-compiler-v1.md)을 따른다.
