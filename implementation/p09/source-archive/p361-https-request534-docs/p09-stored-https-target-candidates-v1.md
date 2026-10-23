# 저장된 원본 HTTPS 목적지 변경 후보

현재 저장 문서의 권한·암호화 읽기·리비전 검사와 저장소가 선택한 정책 아티팩트를 원본 HTTPS 변경 후보에 연결한다.
후보는 메모리에만 존재하며 저장·게시·리비전 확정 권한을 제공하지 않는다.
공통 작업 계획 컴파일러까지 연결하며, 운영 SQL 정책 저장소·발급 주체, 등록 manifest/job/CAS 및 실제 한글 검증은 아직 연결되지 않았다.

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

후보는 원본을 빌리고 소유 output artifact와 비노출 receipt를 보관한다. URI 원문·정책 값·요청을
별도 캐시에 복제하지 않는다. `verify`와 유일한 바이트 전달 경로 `with_verified_bytes`는 현재 쓰기 scope,
원본의 ACL/AEAD/head/전체 결속, 최신 정책과 철회, 정책 아티팩트의 ACL/AEAD를 다시 확인한다.
전달 직전 writer 무결성 callback 안에서도 정책 버전과 head를 확인한다.
검증 때 lowerer·writer·검색·목적지 실행을 반복하지 않는다.

이 확인들은 관측 구간을 한정할 뿐 원자적인 정책 lease나 revision CAS가 아니다.
정책 버전은 바뀌었는데 아티팩트가 같더라도 이전 후보를 거부한다. `require_current_product_route`는 fresh
검사를 마친 뒤에도 `RouteUnqualified`로 거부한다. 공개 JSON/CLI/MCP dispatcher나 실행 우회는 추가하지 않았다.

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

운영 정책 등록/발급·SQL 최신 버전/철회와 프로젝트 쓰기 권한 구현, 공통 요청 정규형·idempotency·attested registry·등록 manifest·
영속 job·저장/CAS·정책의 원자적 실행 결속, 실제 Native protection/의미/갱신·저장·재열기와 전체 Gate는 남는다.
source v13 미해결 4종·공식 158/249·잔여 91·next165·P09/A12/A13 OPEN·P10 미시작은 그대로다.
외부003·SQL520·공식249·과거 Native를 재실행하지 않았다.
