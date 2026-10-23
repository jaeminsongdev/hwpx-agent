# 저장된 원본 HTTPS 목적지 변경 후보

현재 저장 문서의 권한·암호화 읽기·리비전 검사와 저장소가 선택한 정책 아티팩트를 원본 HTTPS 변경 후보에 연결한다.
후보는 메모리에만 존재하며 저장·게시·리비전 확정 권한을 제공하지 않는다.
엄격한 제품 요청·공통 중복 조회·작업 계획과 manifest 데이터·guard 자동 결속 작업 준비를 기존 coordinator에 연결한다.
전용 schema25의 SQL 정책 등록·최신 버전 선택·철회·쓰기 권한 검사를 구현하고, 격리 DB에서 실제 HTTPS 작업과 재시작 복구에 연결했다.
새 schema26 저장 진입점은 정책 확인과 원 CAS를 같은 트랜잭션에 결속한다. 운영 배포·외부 발급자 attestation·attested worker/실행 admission·
공개 제품 경로의 원자적 진입점 선택·장기 키 보관과 실제 한글 검증은 아직 확보하지 않았다.

## 현재 원본과 서버 정책 결속

`StoredImportedDocumentForms::prepare_https_target_candidate`는 인증된 provider의 `DocumentWrite` scope를
먼저 확인한 뒤 기존 서비스의 ACL·격리·AEAD·원본 해시·head 검사와 전체 원본 재구성 증명을 사용한다.
외부 요청이 정책 값이나 정책 아티팩트 ID를 선택하지 않는다.

`HttpsTargetPolicyRepository`는 provider 소유 tenant·subject·project·branch·document·현재 head·원본
아티팩트/해시로 만든 비역직렬화 scope를 받아 현재 정책 버전을 선택한다. 구현체는 매 조회마다 현재
프로젝트 쓰기 권한, 원본/정책 ACL, 최신 버전과 철회를 확인해야 한다. 이 인터페이스 자체는 issuer가 아니다.
기존 `SourcePolicyBinding`은 내용 결속 형식으로만 공유하며 form 정책 권한을 HTTPS 정책에 전용하지 않는다.

선택된 버전은 원본 revision/generation·artifact·package/provenance/graph 해시 및 문서 범위와 정확히 일치해야 한다.
정책 버전은 nil일 수 없고 generation은 양의 signed64 범위여야 하며 원본 아티팩트를 정책으로 사용할 수 없다.
정책은 실제 artifact service에서 Evidence·Verified·Available·격리 없음·정확한 digest와 크기를 확인하고 복호화한다.
매체 형식은 `application/vnd.hwpx-agent.source-https-target-policy+json`, 최대 크기는 1 MiB다.

정책 JSON은 `hwpx-agent.source-https-target-policy/v1`의 `schema_version`, `binding`, `policy`만 허용한다.
binding은 저장소가 선택한 버전과 같아야 한다. 중복·미지·필수 필드 누락·뒤따르는 JSON을 거부하며,
`ExternalLinkPolicy`의 기존 정렬·중복·개별 목적지 kind/digest 승인 규칙을 그대로 적용한다.

## 후보 생성과 전달

실제 원본 fields/meaning index에서 선택한 필드 전체를 기존 HTTPS lowerer의 한 transaction으로 처리한다.
그 경로의 보호·한도·Command/Path 두 leaf 편집·전체 출력 readback과 편집 밖 바이트 보존 검사를 유지한다.
정책 저장소와 실제 정책 아티팩트 및 원본은 후보 생성의 관측 구간 마지막에도 재확인한다.

저장 후보는 원본을 빌리거나 소유하고, 소유 output artifact와 비노출 receipt를 보관한다. 이 저장 후보 자체는 URI 원문·정책 값·요청을
별도 캐시에 복제하지 않는다. `verify`와 유일한 바이트 전달 경로 `with_verified_bytes`는 현재 쓰기 scope,
원본의 ACL/AEAD/head/전체 결속, 최신 정책과 철회, 정책 아티팩트의 ACL/AEAD를 다시 확인한다.
전달 직전 writer 무결성 callback 안에서도 정책 버전과 head를 확인한다.
검증 때 lowerer·writer·검색·목적지 실행을 반복하지 않는다.

이 확인들은 관측 구간을 한정할 뿐 원자적인 정책 lease나 revision CAS가 아니다.
정책 버전은 바뀌었는데 아티팩트가 같더라도 이전 후보를 거부한다. `require_current_product_route`는 fresh
검사를 마친 뒤에도 `RouteUnqualified`로 거부한다. 아래 명시적 JSON 준비 API 외에 CLI/MCP transport나 실행 우회는 추가하지 않았다.

## 제품 요청과 공통 중복 조회

`StoredProductRequest::prepare_https_targets_json`은 명시적 신뢰 정책 repository와
`hwpx-agent.product-https-target-request/v1` 요청을 받아 소유형 컴파일 후보를 반환한다.
원본은 기존 literal 후보와 같은 Borrowed/Owned 전환으로 이동하며 전체 graph나 후보 바이트를 복제하지 않는다.
파싱한 typed 요청은 제품 wrapper가 사적으로 보관해 요청 해시를 검증한다. receipt·Debug·작업 인자에는 URI 원문을 출력하지 않는다.

필수 envelope는 schema·idempotency key·project/document·base revision·expected generation/source SHA·plan ID·operation이다.
operation kind는 `change_https_targets`이며 changes는 원 reference ID·field SHA·meaning SHA·HTTPS target만 받는다.
2 MiB/4,096개 상한과 서버의 auxiliary/target 예산을 적용한다. 모든 JSON 객체 수준의 중복·미지·필수 필드 누락과
뒤따르는 JSON, 객체 대신 배열을 넣은 envelope/operation/change/target, 중복 reference와 HTTPS 외 target을 원본 읽기 전에 거부한다.
SHA는 소문자 64자리, head generation은 양의 signed64 범위여야 한다. 실제 source SHA·현재 head/ACL 일치는 원본 서비스가 다시 확인한다.
요청에서 정책 값·정책 아티팩트·서버 승인·별도 branch를 선택할 수 없다.

raw JSON SHA와 typed canonical 요청 SHA를 구분한다. scoped SHA는 기존 provider의 인증된
tenant/subject/project/branch/document scope 및 스키마·canonical SHA에 결속한다.
JSON 공백/키 순서가 달라도 canonical 의미는 같지만, 목적지·선택 digest·원본/head·plan/key 변경은 요청 결속을 바꾼다.
제품 receipt는 이 세 요청 해시와 compiled receipt를 함께 보관하며, 바이트 전달 시 현재 provider 범위와 원본/정책 검사를 유지한다.

`prepare_https_targets_lookup_json`은 기존 공통 scoped lookup을 감싼 관측 전용 객체를 만든다.
`prepare_https_targets_or_observe_json`은 같은 엄격한 파서로 한 번 파싱하고 조회를 먼저 수행한다.
Existing이나 조회 오류에서는 head/source/policy 읽기·후보 생성·compiler·키 선점으로 넘어가지 않는다.
NotObserved에서만 원본 준비를 시작하며, 그 결과도 claim이나 부재 lease가 아니다. 실제 경쟁 조건은 별도 영속 claim/CAS에서 해결한다.
Existing은 실행 상태 관측이지 독립적인 저장 결과 readback/PASS 증거가 아니다.
`PreparedHttpsTargetLookup::recover_registered`는 원 공통 복구 경로에 위임해 현재 범위/ACL, 정확한 요청의
등록 intent/precommit과 암호화 archive·sealed revision·결과 아티팩트를 읽고 같은 관측을 다시 대조한다.
현재 정책으로 새 실행을 승인하는 API가 아니며, 누락·불명확·변경된 증거를 준비/실행/재시도 경로로 전환하지 않는다.

정책 repository를 받지 않는 원 공통 `prepare_json`은 새 스키마를 엄격히 분류한 뒤
`PolicyRepositoryRequired`로 거부한다. 기존 검색 전용 compiler/lookup으로도 새 요청을 통과시키지 않는다.
원 Form/Formula/검색 분류·파서·route 거부 본문은 변경하지 않았다.

### 서버 정책을 명시한 공통 후보 진입점

`StoredProductRequest::prepare_json_with_https_policy`는 인증된 provider와 서버의
`HttpsTargetPolicyRepository`, 검증된 `PolicyBoundOperationLimits`를 별도로 받는다.
요청 JSON이 정책 값/아티팩트/저장소를 선택하거나 기본 정책을 추정하도록 만들지 않는다.
기존 분류기를 한 번 호출한 뒤 HTTPS는 원 엄격한 제품 준비, 나머지는 본문이 동일한 공통
`prepare_classified`에 위임한다. 다른 계열을 위해 HTTPS 저장소를 읽지 않는다.

HTTPS는 legacy form bindings를 거부하고 `PreparedStoredProductOperation::HttpsTargets`에
원 소유 후보를 담는다. `as_https_targets`는 원 후보의 읽기 전용 참조이며, 소유 enum의 이
variant를 꺼내 기존 manifest/job 경로에 넘길 수 있다. 후보나 accessor는 실행·게시 권한이 아니다.

`with_verified_bytes_with_https_policy`는 원 후보의 현재 source/head/ACL/AEAD/정책 버전과
철회를 다시 확인한 뒤에만 바이트를 전달한다. `require_current_product_route_with_https_policy`도
동일한 현재 검사를 거쳐 원 `RouteUnqualified`를 유지한다. HTTPS가 아닌 variant는 기존 메서드에
그대로 위임한다. 정책 없는 기존 `prepare_json`과 공통 바이트/route 메서드는 HTTPS를 계속
`PolicyRepositoryRequired`로 거부하며 preview API도 후보 출력을 내보내지 않는다.

[562](../../implementation/p09/evidence/p09-361-https-common-dispatch562.v1.json)는 신규7+영향1의
고유8개를 현재 입력 경계에 마감했다. 실제 보존 HWPX·저장 ACL/AEAD·정책 재확인·원본 유지·
출력 readback, 엄격한 객체/중복/unsafe target 거부·철회/권한 상실 시 consumer 미호출과 원 route
거부를 확인했다. 저장소/scanner/key는 시험용이며 새 SQL·운영 issuer/registry·Native/Gate가 아니다.

원561은7개 본문이 통과했지만 schema만 있는 양식 시험의 외부 봉투가 기존 파서에서 먼저 거부돼
전체 FAILED/최종fresh0이었다. 원 실패는 보존했다.562는 필수 외부 필드가 있는 봉투로 시험 입력만
고치고 그1개만 실행했다. 제품/기대 거부 조건/다른7개 본문과 입력 동일성을 대조해 통과7개를
보존했으며 원561을 전체 PASS로 바꾸지 않았다.853fresh/final853·dep-info1final·경고없음·cleanup true다.

이는 공통 **후보** 선택의 연결이다. 인증된 운영 registry/worker admission과 공개 transport의
원자적 SQL 실행 선택·장기 custody·실제 한글의 의미 검증은 여전히 별도다.

## 공통 manifest와 저장 준비

제품 후보의 `prepare_execution_manifest`는 현재 source/policy 검사 안에서 원본 보호 관측과
기존 router/`ExecutionManifest::from_receipts`를 사용한다. 현재 source 아티팩트·크기·SHA와 compiled plan,
선택 route-set·target profile·시간을 결속한다. 서버가 준 route 정보의 출처를 이 컴포넌트가 독립적으로 attestation하지는 않는다.
보관한 manifest의 재사용 때도 전체 route-set·target/registry/health/시간과 현재 source/policy를 다시 확인한다.
기존 제품 route 거부는 유지한다.

검색과 HTTPS는 공통 원본 router/manifest 본문을 공유한다. 검색의 시간/보호/DirectHwpx/identity 조건은 바뀌지 않았다.
`with_verified_storage_preparation`은 임의 원본·출력·plan·검증 판정을 받지 않고, 현재 권한을 확인한
source/output callback 안에서 기존 `PreparedSearchStorage`를 HTTPS 이름으로 사용한다.
공통 생성기는 source/output 크기·해시, manifest/plan/base revision, 요청 identity와 아직 검증·권한이 아닌 receipt 상태를 대조한다.
기존 검색 저장 경로의 원 hash/검사기/job/CAS/guard 로직도 유지한다.

이 저장 준비는 기존 일회성 staged-byte 검사기와 `StoredCommitBinding`·`PreparedStoredJob`에 이어진다.
검사기는 전체 예상 출력 해시와 실제 source/forms/review import를 한 번 확인한다. HTTPS 목적지의 의미는
처음 후보 생성의 전체 readback과 그 정확한 출력 해시에 결속하며, staged 검사에서 변환·compiler를 반복하지 않는다.
Native 표시나 reference-source v13 전체 의미 검증은 아니다. `validation_executed=false`는 준비 시 예상 계약일 뿐 실제 검증 성공을 뜻하지 않는다.

현재 commit guard는 각 ingest/final-CAS 경계에서 서버의 새 route/time을 받고 현재 원본·정책·manifest를 확인한다.
첫 실패는 해당 guard에 고정해 정책을 복원해도 자동 재시도하지 않는다. 이미 ingest한 결과를 삭제하지 않으며,
final-CAS 전 철회가 관측되면 원래 head를 유지한다. 이 관측 구간 보호는 원자적인 정책 lease나 실행 권한이 아니다.
작업 ID 준비는 기존 요청 namespace를 쓰지만 등록·키 선점·lease·영속 작업 실행은 하지 않는다.

## guard 자동 결속과 공통 작업 coordinator

`with_verified_guarded_job_preparation`은 서버의 새 route/time을 먼저 받고 기존 저장 준비 callback 안에서
공통 `PreparedStoredJob`을 만든다. 현재 source/policy/route guard를 자동 부착하므로 호출자가 누락하거나
허용적인 guard로 교체할 수 없다. guard는 coordinator의 첫 claim 전과 기존 ingest/final-CAS 경계에서 적용된다.
새 경로 정보가 없으면 source/storage/job callback을 시작하지 않는다. source/output/검사기 borrow는 callback 밖으로 나가지 않는다.

그 뒤 등록·claim·lease·staged/executing/validating·CAS·completion은 기존 coordinator를 그대로 사용한다.
후보 생성·lowerer/compiler를 다시 수행하는 새 coordinator나 재시도 루프를 만들지 않는다.
이 API는 추가 제한을 결속하는 신뢰 서버용 저장 primitive이며, 실행 허가·worker 등록·현재 정책의 원자적 lease를 발급하지 않는다.
공개 transport는 별도의 실제 실행 admission을 통과해야 한다.

`prepare_https_targets_json_with_pinned_registry`는 엄격한 요청을 먼저 파싱하고 보존된 실제 P02 registry의
인증된 release 정책을 원본 준비보다 먼저 확인한다. 서명은 정상이어도 현재 `routing_allowed=false`이므로
`RoutingDisabled`로 거부한다. 오래된 signed support claim을 현재 지원/실행 허가로 바꾸지 않고, trust policy·키·registry도 수정하지 않는다.

## CAS 트랜잭션 안의 정책 잠금

`run_atomic_sql_job`은 현재 후보의 불변 정책 버전·원본·계획 해시를 SQL repository에 자동 결속하고
기존 guard/coordinator를 한 번 실행한다. 호출자는 별도 revision service·CAS callback·source/output·validator를 대체하지 않는다.
등록 callback은 capability digest 데이터만 받으며 SQL은 실제 worker/lease를 별도로 요구한다.
provider 서비스/인증 필드는 비공개로 유지하고, 실행 연결은 provider 내부 모듈에 둔다. 외부 모듈에는 읽기 전용 정책/계획 메타데이터만 전달한다.

schema26의 `require_https_policy_commit_v1`는 등록/철회/원 CAS와 같은 branch 잠금을 잡고 tenant/project·현재 멤버십·
원본/정책 아티팩트와 해당 ACL 행을 잠근다. 그 뒤 현재 editor/owner·양쪽 읽기 권한·활성 상태·정확한 source head·최신 미철회 정책을
재확인하고 version/generation·artifact/digest·source package/provenance/graph를 대조한다.
현재 요청의 tenant/actor/project/branch/head/source artifact·compiled plan도 Rust의 고정 결속과 일치해야 한다.

원 revision CAS 본문은 같은 `ReadCommitted` transaction closure에 재사용한다. 정책 precondition은 그 안에서 정확히 한 번,
원 SQL CAS보다 먼저 호출하며 잠금은 동일 transaction의 commit/rollback까지 유지한다. 원 lease·canonical request hash·
SQL 인자/함수·commit outcome 판정과 불명확한 커밋 응답 처리는 바뀌지 않았다. 기존 기본 CAS는 no-op precondition으로 같은 본문을 사용한다.
연결은 전용 exact26이며 기존23/24/25의 검사를 유지하고 이전 연결은26을 거부한다. 아티팩트 역할에는 정책 잠금 API를 허용하지 않는다.
이는 추가 저장 제한이지 P02 release·registry/worker·실행 권한이나 새 공개 transport가 아니다. 기존 준비/관측 API 자체를 원자적 lease로 해석하지 않는다.

[543](../../implementation/p09/evidence/p09-361-https-atomic-sql543.v1.json)은 새 소유 schema26에서 다음을 확인했다.

- 최신 정책이 철회된 상태의 SQL guard와 잘못된 version/generation/digest/원본 provenance 거부.
- 연결A의 guard transaction이 유지되는 동안 연결B의 철회·새 버전 등록·멤버십 변경·원본/정책 ACL 변경이 `55P03`으로 대기 중단됨.
  A rollback 후 B의 새 guard가 성공해 잠금 해제를 확인했다. 이는 guard의 두 연결 시험이며 전체 제품 CAS의 모든 경합 시점 시험을 대체하지 않는다.
- 아티팩트 역할에 guard 권한을 준 경우와 guard 함수 본문 변조 시 admission 거부, 복원 후 재인증.
- 새 진입점의 실제 guard/coordinator·claim/lease/barrier·등록 영수증·동일 transaction의 원 CAS·completion과 실제 HWPX/AEAD readback·원본 보존.
- 서버 재시작 전후 같은 공개 요청의 등록 효과 복구·4개 로컬 경로의 byte-exact 복원·잘못된 요청/키 거부와 실행 재시도 없음.

전후 policy versions2/revocations1/latest2와 artifact9/job2/attempt2/intent1/revision2/seal2/head2·ciphertext가 같다.
job2는 bootstrap1+HTTPS1이며 두 postmaster는 정상 종료했다.881fresh/final881·실제 example dep-info46개 사전 결속·실행파일/dep-info2final·경고없음·cleanup true다.
전체422.079초·Cargo15.063초·SQL worker245.375초(전체 런타임의 제한 속도 전후 해시 포함)다.
시스템 CPU최고41.73%·가용RAM최저36.379%·보호중단없음·소유 Job1코어/BelowNormal/CPU6.25%·RAM/commit 보호 유지,
최고 private compiler1089.02MiB/SQL94.57MiB·종료 소유 프로세스0개다. 과거 PC 프리즈 원인 해결이나 Native/Gate 완료를 뜻하지 않는다.

542는 provider 비공개 필드 접근 E0616 네 건으로 컴파일 단계에서 중단됐고 SQL0회·final fresh 없음이다. 실패 영수증과 원본을 보존했다.
필드 공개 범위를 넓히지 않고 실행 본문을 provider 내부로 옮겼으며, 원 CAS 본문과 나머지 원 검사들은 역복원 동일성을 확인했다.
이전 통과 시험·소비한 SQL root·SQL520/003/Native는 재실행하지 않았다.

## SQL 정책 발급과 철회

`prepare_https_policy_registration`은 인증된 쓰기 scope와 현재 원본을 확인하고 서버가 명시적으로 선택한
유한한 HTTPS 전용 정책을 원본 revision/generation·artifact·package/provenance/graph에 결속한다.
원 정책의 개별 목적지 hash·정렬/중복·한도 검사를 재사용하며 다른 종류 활성화·빈 승인 목록·잘못된 payload와 세대 초과를 거부한다.
정책 version UUID는 서버에서 생성한다. 공개 변경 요청이 정책 값/ID를 고르거나 발급하는 transport는 추가하지 않았다.

준비 객체의 `register`는 한 번 소비되며 실제 Evidence ingest와 ACL/AEAD·엄격한 payload readback을 확인하고 SQL에 등록한다.
SQL 실패 뒤에도 암호화 Evidence를 삭제하지 않고 오류에 retained artifact ID를 보관한다.
커밋 응답 유실이나 등록 응답 불일치는 `OutcomeUnknown`이며 자동 재시도나 확정적인 no-effect 판정으로 바꾸지 않는다.

schema25는 HTTPS 전용 불변 versions/revocations와 읽기·등록·철회 함수를 둔다. 현재 editor/owner 권한과 양쪽 아티팩트 읽기 권한,
등록 아티팩트 관리 권한, 정확한 source head, branch 잠금과 generation CAS를 검사한다. 읽기는 최신 버전만 선택하며 철회된 최신 버전에서
과거 버전으로 되돌아가지 않는다. 철회는 최신 version/generation을 잠금 아래 확인하며 원본 head 이동 후에도 가능하다.
`PostgresHttpsTargetPolicyProvider`는 이 SQL 결과를 실제 암호화 정책 소비자에 연결한다. form/formula 정책의 권한을 HTTPS에 전용하지 않는다.

`connect_with_https_policy`와 아티팩트의 `connect_schema25`만 정확한 schema1..25를 허용한다.
기존23/24 연결의 검사와 동작은 유지하며25를 거부한다. 새 연결도 기존 역할/RLS/lease/job/조회 보안 검사를 모두 수행한다.
HTTPS 함수의 definer·고정 search_path·원 본문 hash·PUBLIC/소유/직접 table/helper 권한 및 RLS/불변 trigger 경계를 확인한다.
아티팩트 역할에는 HTTPS 정책/job/조회 실행 권한을 허용하지 않는다. 연결 함수가 migration/grant를 자동 설치하지 않는다.

[541](../../implementation/p09/evidence/p09-361-https-policy-sql541.v1.json)은 새 소유 schema25에서 다음을 확인했다.

- 실제 AES 정책 등록·현재 SQL 선택·철회·다음 세대 발급과 원래 후보의 계속 거부.
- 오래된 세대의 발급 실패 뒤 Evidence 보존, 관리 권한 없는 사용자의 등록 거부, 고정 principal/원본 head·reader 역할·양쪽 ACL 상실 거부.
- 과도한 아티팩트 역할 권한·helper 실행 권한·강제 RLS 해제·함수 본문 변조의 연결 거부. 부정 시험의 권한/함수/RLS는 제품 작업 전에 복원·재인증했다.
- 실제 SQL 정책을 사용한 원 guard/coordinator의 claim/lease/barrier·등록 intent/precommit·단일 CAS·completion과 원 HWPX 보존.
- 재시작 전후 공개 요청의 같은 등록 효과 readback, 원 로컬 경로4개 부재/byte-exact 복원, 다른 요청의 conflict·없는 요청·잘못된 AES 키 거부와 재실행 없음.

전후 정책 versions2/revocations1/latest2와 artifact9/job2/attempt2/intent1/revision2/seal2/head2가 같다.
job2는 bootstrap1+HTTPS1이며 artifact9에는 거부된 발급의 보존 Evidence가 포함된다. ciphertext도 같고 두 postmaster는 정상 종료했다.
885fresh/final885·실제 example dep-info44개 입력 사전 결속·실행파일/dep-info2final·경고없음·cleanup true다.
전체409.391초·Cargo4.141초·SQL worker243.437초이며 worker에는 전체 런타임의 제한 속도 전후 해시가 포함된다.
시스템 CPU최고23.05%·가용RAM최저36.567%·보호중단없음이다.1코어/BelowNormal/CPU6.25%·RAM/commit 보호를 유지했고,
최고 private는 compiler772.0MiB/SQL86.41MiB·종료 소유 프로세스0개다. 운영 배포·외부 발급자/worker 자격·원자적 실행 정책 lease·장기 키 보관·Native/Gate의 증거는 아니다.

538은 컴파일 exit0 뒤 새 타입의 Debug 경고1개로 SQL 전 중단됐고,539/540은 seed 단계의 CHECK23514로 제품 작업 전에 중단됐다.
원 실패·final fresh 없음·데이터 root는 보존했다. 타입은 값을 숨기는 Debug를 구현했고, 시험의 역할명은 reader로,
관리 권한 부정 시험은 보조 관리자를 둔 상태로 고쳤다. 보조 행은 원 관리자 복원 뒤 정확히 제거하며 기존 최소 관리자 제약을 유지한다.
DB 제약·제품 SQL/권한·공통 coordinator는 완화하지 않았다. 이후 실패에는 원 값 없이 닫힌 시험 단계/오류 분류만 남긴다.
기존 통과 시험·실패 DB·SQL520/003/Native는 재실행하지 않았다. 이 SQL 구현은 아직 운영 배포나 외부 issuer attestation이 아니다.

## 이전 SQL 저장과 기존 효과 복구

[537](../../implementation/p09/evidence/p09-361-https-target-sql537.v1.json)은 새 소유 PostgreSQL schema24에서
보존된 실제 HWPX의 엄격한 HTTPS 요청을 원 guard 자동 결속·coordinator·claim/lease/barrier·등록 영수증·단일 CAS·completion에 연결했다.
실제 아티팩트 metadata SQL과 디스크 AES/readback, 등록 행과 intent/precommit의 일치, 새 head와 원 source 보존을 확인했다.
정책 내용은 실제 AES 아티팩트지만 선택자는 격리 fixture이며 route/scanner·키도 합성/임시다. 운영 issuer나 제품 admission 자격은 아니다.

서버 재시작 전후 각각 원 공개 요청만으로 같은 등록 효과를 복구했다. 요청·정책 선택·완료 핸들·원 상태의
4개 로컬 경로를 일시 보존한 상태에서 조회하고 바이트 그대로 복원했다. 상태 관측 경로에 정책 읽기를 거부하는 repository를
넣어도 Existing으로 끝나며 준비/claim/engine으로 돌아가지 않는다. 다른 plan의 같은 key는 정확한 KeyConflict,
없는 요청은 NotObserved로 처리했고 잘못된 AES 키는 거부했다. 기존 결과를 읽는 복구는 정책 재승인/재실행이 아니다.

재시작 전후 SQL 수는 아티팩트7·작업2·시도2·등록 intent1·revision/seal2·head generation2로 동일하다.
작업2에는 원 source bootstrap1과 HTTPS 작업1이 포함된다. ciphertext도 동일하며 두 소유 postmaster는 정상 종료됐다.
SQL520의 데이터 root/원 실패와003/Native는 재실행하거나 변경하지 않았다.536의8개와 이전 시험도 반복하지 않았다.
기존 공통 SQL fixture의 기본6개 아티팩트 경로와 원본 product/coordinator/lookup/recovery 본문은 역복원 동일성으로 확인했다.

850fresh/final850·실제 example dep-info42개 입력 사전 결속·실행 파일/dep-info2개 final·diagnostics 없음·cleanup true다.
전체410.875초 중 Cargo13.812초·SQL worker241.329초이며 worker에는 원 PostgreSQL 런타임 전체의 제한 속도 전후 해시 검사가 포함된다.
시스템 CPU최고32.83%·가용RAM최저35.194%·보호중단없음이다. 소유 Job의1코어·BelowNormal·machine CPU6.25%와 RAM/commit 보호를 유지했고,
최고 private는 compiler1085.79MiB/SQL77.41MiB·종료 소유 프로세스0개다. PC 프리즈 원인 해결이나 Native/P09 Gate 완료의 증거는 아니다.

## 이전 coordinator와 admission 검증

[536](../../implementation/p09/evidence/p09-361-https-target-job536.v1.json)은 신규8개를 실행했다.
기존 공통 coordinator·검사기·등록/CAS·요청·route 본문 및 기존 시험의 동일성을 확인하고 저장8개/요청22개는 반복하지 않았다.
실제 보존 P02 envelope/정책/공개키의 서명 인증과 source/policy/claim 전 routing 거부를 확인했으며 private signing key를 읽지 않았다.
메모리 lifecycle 모델과 합성 route/scanner/policy에서 다음을 확인했다.

- 자동 guard는 교체할 수 없고, claim 직전 정책 철회면 workspace/claim 없이 멈춘다.
- 원 coordinator가 claim→lease→staged→executing→validating→registered receipts→단일 CAS→completion을 수행한다.
  실제 AES 저장/readback과 원 HWPX 보존, intent/precommit/archive 및 등록 응답 결속을 확인했다.
- Replay·불명확한 claim·다른 agent lease는 workspace/validator/register/CAS로 넘어가지 않는다.
- validating 응답 불명확/lease 뒤 정책 철회는 원 head를 보존하며 등록·CAS나 자동 재시도를 하지 않는다.
- completion 응답 유실은 실제 commit/readback 증거를 유지하고 재실행·재claim하지 않는다.
- 등록 거절/등록 응답 불명확은 이미 만든 결과·intent/precommit을 보존하고 revision CAS를 하지 않는다.
- 현재 route snapshot을 얻지 못하면 정책/source를 추가 조회하거나 job callback을 호출하지 않는다.

이 모델의 등록/lease 응답은 실제 SQL·등록된 worker·발급자/attested registry·durable job 증거가 아니다.
coordinator의 Completed는 해당 저장 primitive의 상태이며 P09/Native 완료를 뜻하지 않는다.
현재838fresh/final838·실제dep-info1final·diagnostics 없음·cleanup true다.
전체131.984초·Cargo24.235초·본문7.95초이며 시스템 CPU최고44.32%·가용RAM최저35.797%·보호 중단 없음이다.
1코어·BelowNormal·machine CPU6.25% Job cap·RAM/commit 보호를 유지했고 최고 private1085.75MiB·종료 소유 프로세스0개다.
과거 PC 프리즈 원인 해결이나 실제 Native/운영 자격으로 승격하지 않는다.

## 저장 경로의 이전 검증

[535](../../implementation/p09/evidence/p09-361-https-target-storage535.v1.json)은 HTTPS6개와 변경된 공통 경로의
기존 literal 문서/문단 범위2개, 총8개를 실행했다. 앞서 마감한 요청22개는 runtime/본문 동일성을 대조해 보존하고 반복하지 않았다.
보존된 실제 HWPX의 새 목적지 출력이 원본 workspace engine·일회성 validator·실제 AES 저장/복호화·메모리 revision CAS를 지나
새 head와 readback에 결속됨을 확인했다. 원 source 아티팩트는 그대로 보존했다.

추가로 바이트 변경/검사기 재사용, target/registry/health/시간/capability 변경, 현재 정책 철회와 guard 고정 거부,
ingest와 final-CAS 사이 철회 때 원 head 및 ingest 결과 보존을 확인했다. 기존 검색 문서/문단 범위의 저장·암호화 readback도 통과했다.
이 시험은 합성 route/scanner/policy repository와 메모리 저장소를 사용한다. 운영 SQL/발급자/attested 등록·durable claim/job·제품 route/Native/Gate 자격은 아니다.

현재833fresh/final833·실제dep-info1final·diagnostics 없음·cleanup true다. 전체124.813초·Cargo18.578초·본문1.86초다.
시스템 CPU 최고69.73%·가용RAM최저44.335%이고 보호 중단은 없었다. 소유 Job의1코어·BelowNormal·machine CPU6.25%
cap·RAM/commit 보호를 확인했고 최고 private1085.46MiB·종료 소유 프로세스0개다.
peak 근처 CPU는11.07→69.73→60.35→50.98→38.48%였으며 상승의 프로세스별 기여는 미확정이다. PC 프리즈 해결로 판정하지 않는다.

## 요청 경로의 이전 검증

[534](../../implementation/p09/evidence/p09-361-https-target-request534.v1.json)는 수정 1개 실행과
533의 동일 런타임 코드·본문/입력 통과 17개를 마감하고, 기존 조기 거부 4개를 보존한다. 고유 22개이며 22개 단일 실행은 아니다.
최초 실행은 새 요청 8개와 source 소유권 표현 변경의 영향 10개만 선택했다. 공식249와 관련 없는 기존 조기 거부4개를 반복하지 않았다.

실제 보존 HWPX에서 소유 요청→서비스/정책→compiler→후보 readback을 확인했다. 25개 엄격한 요청 변형과
잘못된 범위/쓰기 scope/head/source, canonical/scoped 결속, 상이한 branch scope, 같은 key의 다른 전체 요청 결속을 확인했다.
합성 관측 repository에서 pending/terminal Existing·key conflict·outcome unknown·repository failure는 source/head/policy/compiler/CAS 없이 끝났고,
NotObserved만 원래 준비 경로에 들어갔다. 소유형 제품의 전달에서도 양쪽 ACL·정책 철회·쓰기 scope 변경 시 callback을 실행하지 않았다.
운영 SQL 저장소·실제 발급자/스캐너나 영속 claim의 자격 검증은 아니다.

533의 17pass/1fail·경고2·final fresh 없음은 원본 보존한다. 실패한 시험은 공통 조회기가 금지하는
all-zero source digest를 유효한 변경값으로 사용했다. 다른 비제로 해시의 결속 검사와 all-zero 거부 검사를 분리했고,
원 조회기의 거부 조건을 바꾸지 않았다. limits의 Debug 구현과 미사용 import 경고를 고쳤으며 요청/저장 런타임 본문은 같다.

현재 입력은 834fresh/final834·실제 dep-info1final·diagnostics 없음·cleanup true다.
최종 전체122.390초·Cargo15.750초·본문0.01초, 시스템 CPU최고23.05%·가용RAM최저34.322%였다.
원1코어·BelowNormal·machine CPU6.25% Job cap과 RAM/commit 보호를 유지했고 보호 중단은 없었다.
최고 Job private1082.65MiB·종료 소유 프로세스0개다. 과거 PC 프리즈 원인 해결로 판정하지 않는다.

## 공통 작업 계획 컴파일

후보의 `compile`은 원본 후보를 이동해 `PreparedCompiledHttpsTargetCandidate`를 만든다.
새 전체 graph 복제나 field 의미 import 없이, 후보 생성 중 이미 읽은 fields에서 선택한 begin 앵커만 보관한다.
기존 검색 컴파일러의 소유자 판정 본문을 그대로 공유한다. source graph의 실제 앵커와 XML 부모 관계로
각 필드의 가장 가까운 구조 소유자를 구하며, 문단의 자식 순서나 ID 문자열로 소유자를 추정하지 않는다.
원 importer가 별도로 보존한 `hp:ctrl`이 가장 가까우면 그 실제 노드를 사용한다.

기존 `OperationPlanCompiler`는 REF-034의 `ref.hyperlink_edit`로 필드당 한 작업을 만든다.
base revision은 현재 source head에서 유도하고 source graph SHA, 정책 아티팩트/버전/generation/digest,
원본/출력/저장 receipt 해시와 각 원본 필드 앵커·meaning/target digest를 결속한다.
새 URI·원문 표시 텍스트·전체 정책 값은 작업 인자로 넣지 않는다. 필드 선택 순서와 서로 다른 실제 ctrl
소유자를 보존하며, 후보의 Command/Path 두 leaf transaction을 개별 저장 작업으로 분리하지 않는다.

계획은 최대 4,096개 작업·작업당 13개 필수 text 인자·인자당 2,048 bytes·인자 합계 8 MiB·계획 16 MiB다.
기존 bounded streaming hash를 공유하고, 현재 저장소/원본/정책 검사를 컴파일 전후에 유지한다.
컴파일된 후보의 검증/바이트 전달은 계획 무결성과 기존 저장 후보의 fresh 검사를 사용하며 compiler/lowerer/writer를 재실행하지 않는다.
원본 저장과 head 확정은 없으며 `require_current_product_route`는 계속 거부한다.
로컬 capability catalog는 계획을 구성하는 데이터이지 attested registry나 실행 권한이 아니다.

## 컴파일 경로의 이전 검증

[532](../../implementation/p09/evidence/p09-361-https-target-compiler532.v1.json)은 현재 수정 1개 실행과
입력·제품 코드·나머지 시험 본문이 같은 531의 통과 9개를 마감하고, 530의 변경 전 조기 거부 4개를 보존한다.
합계는 고유 14개이며 14개 단일 실행이나 과거 대기열 재실행이 아니다. 후보 생성의 선택 앵커 보관 경로가
추가돼 그 경로를 지나는 기존 5개만 영향 대상으로 다시 실행했다. 새 컴파일 시험은 5개다.
기존 조기 거부 경로는 추가된 앵커 보관 호출 전에 끝나며, 기존 본문·helper와 모든 원 source/compiler/보호 로직의 동일성을 확인했다.

531은 9pass/1fail·final fresh 없음으로 원본 보존한다. 실패한 시험은 그래프 자식 위치를 문단 순서로 가정했다.
기존 importer가 `hp:ctrl`을 별도 노드로 보관하는 실제 구조를 확인하고, 원본 XML의 포함 범위에서 최소 소유자를
독립적으로 구하는 시험으로 수정했다. 제품 소유자 판정기는 바꾸지 않았다. 같은 문단의 두 필드도 서로 다른
ctrl 소유자로 남아야 함을 확인한다. 소스 밖 첫 문단으로 치환하거나 소유자 조건을 완화하지 않는다.

실제 보존 HWPX의 compile/readback, 원본 graph/revision/plan digest, canonical plan 재읽기,
URI 비노출, 선택 순서와 실제 소유자, 컴파일 전·후 정책 철회 및 전달 전 양쪽 ACL/쓰기 scope 변경을 확인했다.
현재 입력은 831fresh/final831, 실제 dep-info 1개 final, diagnostics 없음·cleanup true다.
최종 전체 108.641초·Cargo 단계 2.531초·본문 0.07초이며 시스템 CPU 최고 22.57%, 가용 RAM 최저 35.898%다.
보호 중단 없이 1코어·BelowNormal·machine CPU 6.25% Job cap과 RAM/commit 보호를 유지했다.
최고 private memory 756.55 MiB·종료 소유 프로세스 0개다. 프리즈 원인 해결이나 운영 SQL/issuer/Native 자격의 증거는 아니다.

## 저장 후보의 이전 검증

[530](../../implementation/p09/evidence/p09-361-stored-https-target530.v1.json)은 수정한 head 시험 1개 실행과
본문·helper·제품 코드·입력이 동일한 528의 통과 8개를 보존해 고유 9개 범위를 마감한다. 9개 단일 재실행은 아니다.
이전 원본 test/driver 및 당시 compiler dep-info를 보존했고, 현재 831개 입력의 fresh/final 해시와
실제 컴파일 dep-info 1개의 최종 해시를 확인했다. diagnostics는 없고 cleanup은 true다.

실제 보존 HTTPS HWPX의 AES 암호화 서비스 읽기·수정 후보 readback·원본 보존을 확인했다.
합성 repository/scanner를 사용하는 시험에서 다음을 확인했다. 운영 repository/issuer/scanner 자격의 증거는 아니다.

- 여러 필드의 변경과 미선택 필드 보존, 한 구성원의 승인 누락 시 전체 거부.
- 쓰기 scope 및 현재 원본 읽기 권한이 없으면 정책 조회 전 거부.
- 다른 tenant/project/branch/document/source revision·generation·artifact·package/provenance/graph 결속 등 15개 변형 거부.
- 엄격한 정책 payload 9개 변형과 잘못된 매체·종류·크기·ciphertext·격리 상태 거부.
- 전달 시 양쪽 ACL, 정책 철회·최신 버전, 쓰기 scope 변경을 재확인하고 callback 미실행.
- 준비 중 철회와 마지막 전달 검사 중 철회를 거부.
- 후보와 독립적으로 새 revision을 만든 뒤 오래된 후보 전달을 거부하고 새 head 보존.

527은 시험 코드의 match arm 타입 불일치로 본문 0회였다. 528의 head 시험은 같은 source/result ID,
529는 같은 내용에 다른 파일명을 지정한 ingest 중복 충돌로 실패했다. 원 저장 규칙을 바꾸지 않고
별개 내용의 미래 원본을 만드는 fixture로 수정했다. 실패 원본·final fresh 없음과 528의 통과 8개를 보존했다.

최종 실행은 전체 110.203초, Cargo 단계 3.688초, 시험 본문 0.05초다. 시스템 CPU 최고 41.9%,
가용 RAM 최저 35.804%였고 보호 중단은 없었다. 소유 Job의 1코어·BelowNormal·machine CPU 6.25%
hard cap과 RAM/commit 보호를 유지했으며 최고 private memory는 755.23 MiB, 종료 시 소유 프로세스는 0개였다.
실패한 528의 CPU 최고 72.85% 관측도 보존하며, PC 프리즈 원인을 해결한 것으로 판정하지 않는다.

## 마지막 앱 검사 뒤 실제 정책 철회

[545](../../implementation/p09/evidence/p09-361-https-late-revoke-sql545.v1.json)의 새 격리 사례에서 마지막 앱 정책 읽기 직후 실제 SQL 정책을 철회했다.
원 coordinator의 실제 lease/등록 intent가 진행된 뒤 같은 transaction의 정책 precondition이 원 CAS를 거부했다.
결과물/intent/precommit은 AEAD로 읽을 수 있었고 원본과 head1·실행 시도1을 유지했다. 완료·새 revision은 없었다.

그 뒤 집계 시험이 lease authorization을0개로 기대해 전체545는 FAILED다. 원 CAS 전 거부 시 미소비 authorization1개가 남는 SQL23 동작을 고려하지 못했다.
기록된191bytes stdout SHA와 정확히 일치하는 집계는 artifact7/job2/attempt2/authorization1/intent1/revision1/seal1/head1이다.
[547](../../implementation/p09/evidence/p09-361-startup15-and-sql-snapshot547.v1.json)의5개 순수 모형은 수정 기대값과 오류 시에도 실제 집계를 먼저 보존하는 동작을 검증했다.
통과한 SQL 본문/소비DB를 반복하지 않았고 원545의 finalfresh0·재시작 NOT_RUN을 전체 PASS로 바꾸지 않았다.
소유 postmaster1회 정상 종료와 부모 소유 Job cleanup true는 원 기록에 남는다. 운영 키 custody/실제 issuer·Native/Gate의 수용은 아니다.

## 남은 제품 연결

SQL 정책 등록/발급·최신 버전/철회·쓰기 권한과 격리 SQL의 claim/job/등록CAS·재시작 효과 복구는541에서, 새 저장 진입점의 정책 잠금과 원 CAS transaction 결속은543에서 확인했다.
운영 배포·외부 issuer attestation·attested registry/worker·등록 manifest·운영 idempotency/job·공개 제품 경로의 새 원자적 진입점 선택과 장기 키 보관,
실제 Native protection/의미/갱신·저장·재열기와 전체 Gate는 남는다.
source v13 미해결 4종·공식 158/249·잔여 91·next165·P09/A12/A13 OPEN·P10 미시작은 그대로다.
외부003·SQL520·공식249·과거 Native를 재실행하지 않았다.
