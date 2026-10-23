# 검색 변환 후보의 공통 저장 연결

현재 dispatcher의23개 검색·치환·변환 계열을 원본 소유 후보와 실행 manifest에서 기존 저장 엔진으로 연결한다.
`PreparedSearchExecutionManifest.with_verified_storage_preparation`은 같은 원본과 산출물을 빌려
validator·암호화 artifact 저장·revision CAS·영속 job 준비에 전달한다. 시험용 저장소에서는23계열 모두
실제 HWPX 산출물을 다시 읽고 암호화 저장한 뒤 CAS로 새 revision을 만들었다.
운영 SQL·실제 신뢰 registry·Native 실행 자격은 이 연결과 별도로 남아 있다.

## 원본과 저장 입력

공통 compiler view는 원래 strict request의 project와 idempotency key를 불변 참조로 추가 전달한다.
원본/계획/route를 다시 만들거나 caller가 다른 바이트·plan·검증 판정을 넣는 경로는 없다.
기존 router·source protection 관측·현재 write/ACL·격리·AEAD·head 확인 뒤, 같은 provider에서
원본을 빌려 크기·SHA·head generation을 manifest와 대조한다. 원 source와 output은 callback 밖으로 빌려 보관할 수 없다.

`SearchStorageReceipt`는 원본/산출물 SHA, schema, compiled plan, manifest와 validation contract의 식별자다.
원문·검색 조건·공개 요청 키·개인 키를 출력하지 않으며 Debug도 비노출이다.
`validation_executed=false`와 `execution_or_native_authority=false`는 준비 데이터가 검증 성공이나 권한이 아니라는 뜻이다.

## 산출물 검증과 commit 경계

`SearchOutputValidator`는 최초 호출에서 정확한 산출물 크기·SHA를 확인하고 실제 package/forms/review와
보호 신호를 한 번 읽는다. 준비 단계에서 산출물을 다시 import하거나 검색·정렬·compiler를 반복하지 않는다.
성공·거부 후 두 번째 호출은 `Failed`다. 다른 후보·원본·손상·빈/절단 바이트는 거부한다.
정확한 후보 바이트와 typed readback의 검증이며, 독립적인 Native 의미/렌더링 비교나 완전한 v13 import의 판정은 아니다.

`commit_binding`은 원 manifest/output/project/branch/head와 validation contract를 고정하고
서버가 선택한 commit/new revision만 받는다. 현재 revision을 새 revision으로 사용하는 입력은 거부한다.
기존 `StoredResultRevisionCas`·scanner·AEAD·workspace transaction을 사용하며 별도 저장 엔진은 만들지 않는다.

`current_commit_guard`는 저장 전과 최종 CAS 직전마다 서버의 현재 route/time snapshot을 다시 받아
원본/manifest와 대조한다. snapshot 부재·오래된 clock·target/registry/health drift·접근 거부가 발생하면
같은 시도의 guard는 실패 상태를 유지한다. guard를 교체해 실패를 지우는 경로는 기존 CAS가 거부한다.
저장 전 실패는 result를 만들지 않고, 저장 후 최종 CAS 실패는 head를 유지하면서 복구 artifact를 보존한다.

## 요청 키와 영속 job 준비

`prepare_bound_job`은 authenticated tenant/project와 strict 공개 요청 키에서 기존 `StoredRequestJobIdentity`를 만든다.
같은 project/key의 content·schema·plan이 달라져도 key/job/request UUID는 같고, canonical/scoped binding은 다르다.
바뀐 요청에 새 UUID를 주어 영속 충돌 검사를 피하지 않는다. retry/TTL 제한은 기존 job preparation이 검사한다.
이 메서드는 claim·등록·lease·재시도·ingest·CAS를 실행하지 않는다. 공개 요청 JSON은 서버 job UUID를 선택하지 못한다.

## 검증 결과

`implementation/p09/evidence/p09-361-search-storage513.v1.json`은 현재31개 범위를 마감했다.
23개 독립 계열은 각각 실제 후보 생성·manifest·typed 산출물 검증·암호화 저장/다운로드·두 번의 현재 guard·revision CAS·원본 보존을 확인했다.
나머지8개는 잘못된 산출물과 일회성 판정, 키 충돌 결속, 잘못된 job 정책, clock/route drift,
ACL·격리·AEAD 거부와 저장 전/최종 CAS 실패의 복구 자료 보존을 확인한다.

511의 안전/복구8개와512의 계열21개는 라이브러리·보호 코드·본문·영향 없는 fixture의 동일성을 확인해 재사용했다.
마지막에는 원본에 선언된 교체 글꼴을 따르도록 fixture를 수정한2개만 실행했다.
511의 묶음 시험 실패와512의 글꼴2개 실패는 원본/final fresh 누락을 보존했다. 계열별 독립 시험으로 나눠 이후 실패가 다른 계열 재실행을 요구하지 않도록 했다.

최종 결과는984fresh/final984·실제 dep-info1final·cleanupTrue,133.188초다.
최종 실행2개 명령은6.984초이며 나머지는 준비·입력/산출물 마감 등이다. CPU 최고25.45%·가용 RAM 최저38.794%·보호 중단 없음이다.
원1코어·낮은 우선순위·소유 Cargo CPU6.25%·RAM/commit95% 보호를 유지했다. 이전 실패에서 관측한 CPU 최고42.38%도 원본에 보존한다.
소스·변경 전 파일과 실패 당시 fixture/test는 `implementation/p09/source-archive/p361-search-storage511/`에 있다.

## 남은 실행 자격

라우팅 snapshot과 repository/scanner/key는 시험용 fixture다. 원 `require_current_product_route`의 거부를
23계열 모두 유지했고 실제 P02 `routing_allowed=false`를 변경하지 않았다. 실제 서버 dispatcher의 신뢰 registry/target·보호 자격,
운영 SQL의 claim/lease/충돌·crash/키 custody·게시/복구, 기능별 의미·저장/재열기 검증은 별도 요건이다.
공식158/249·잔여91·next165, source API v13 미해결4, P09/A12/A13 OPEN·P10미시작을 유지한다.
외부003·Native·한글/접근 허용·운영 DB는 실행하지 않았다.
