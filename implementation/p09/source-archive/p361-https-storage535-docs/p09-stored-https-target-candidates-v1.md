# 저장된 원본 HTTPS 목적지 변경 후보

현재 저장 문서의 권한·암호화 읽기·리비전 검사와 저장소가 선택한 정책 아티팩트를 원본 HTTPS 변경 후보에 연결한다.
후보는 메모리에만 존재하며 저장·게시·리비전 확정 권한을 제공하지 않는다.
엄격한 제품 요청·공통 중복 조회·작업 계획 컴파일러까지 연결하며, 운영 SQL 정책 저장소·발급 주체,
등록 manifest·영속 claim/job/CAS 및 실제 한글 검증은 아직 연결되지 않았다.

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
NotObserved에서만 원본 준비를 시작하며, 그 결과도 claim이나 부재 lease가 아니다. 실제 경쟁 조건은 향후 영속 claim/CAS에서 해결해야 한다.
Existing은 실행 상태 관측이지 독립적인 저장 결과 readback/PASS 증거가 아니다. HTTPS용 등록 결과 복구를 새로 허용하지 않았다.

정책 repository를 받지 않는 원 공통 `prepare_json`은 새 스키마를 엄격히 분류한 뒤
`PolicyRepositoryRequired`로 거부한다. 기존 검색 전용 compiler/lookup으로도 새 요청을 통과시키지 않는다.
원 Form/Formula/검색 분류·파서·route 거부 본문은 변경하지 않았다.

## 현재 요청 경로 검증

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

## 현재 컴파일 경로 검증

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

## 남은 제품 연결

운영 정책 등록/발급·SQL 최신 버전/철회와 프로젝트 쓰기 권한 구현, attested registry·등록 manifest·영속 idempotency claim·
영속 job·저장/CAS·정책의 원자적 실행 결속, 실제 Native protection/의미/갱신·저장·재열기와 전체 Gate는 남는다.
source v13 미해결 4종·공식 158/249·잔여 91·next165·P09/A12/A13 OPEN·P10 미시작은 그대로다.
외부003·SQL520·공식249·과거 Native를 재실행하지 않았다.
