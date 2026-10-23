# 검색 요청의 조회 우선 준비와 복구

일반 검색·치환·변환23계열에 이미 처리된 요청을 먼저 조회하는 제품 진입점을 연결했다.
완료/진행 중 요청의 상태를 찾으려고 원본 ZIP·문서 import·변경 후보·operation plan을 다시 만들지 않는다.
기존 strict parser, 현재 authenticated scope와 repository의 요청/ACL 확인은 그대로 실행한다.
상태 조회는 실제 결과의 독립 readback이나 실행·재시도 권한이 아니다.

## 조회와 준비 분기

`StoredProductRequest.prepare_search_lookup_json`은 원래23개 schema 분류와 각 계열의 기존 parser를 사용한다.
v2 atoms의 schema별 scoped hash, review/selector와 regex insertion의 wrapper 정규형도 원 제품과 동일하게 계산한다.
번호 컨트롤은 원 parser가 반환하는 요청/정규형 해시 쌍과 typed 값 검사, 원 scoped hash 함수를 사용한다.
번호 값 검사의 기본 예산은 기존 `SearchMutationLimits::standard`이며 미관측 준비에서는 서버가 제공한 현재 limits도 별도로 적용한다.
preview·다른 작업 kind·알 수 없는 키·escaped duplicate·초과 요청 크기는 조회 전에 거부한다.

준비된 조회는 원래 project/document와 현재 provider scope, 서버가 결속한 lookup을 보관한다.
canonical/scoped digest getter는 식별 데이터이며 권한이 아니다. 공개 생성자·역직렬화·source bytes·key claim은 제공하지 않는다.
`observe`와 `recover_registered`는 호출 시 provider scope를 다시 확인한다. 보관한 조회로 현재 write 권한 거부를 피할 수 없다.

`StoredProductRequest.prepare_search_or_observe_json`은 다음 두 분기를 제공한다.

- `Existing`: 원본/head 읽기·후보 준비·compiler 없이 기존 `StoredJobObservation`을 반환한다. 완료 상태도 독립적인 결과 readback으로 승격하지 않는다.
- `NotObserved`: 기존 `prepare_compiled_search_json`으로 원본/ACL/AEAD/head와 서버 limits를 다시 검사해 원 후보를 만든다. 이 결과도 `RouteUnqualified`다.

key conflict·조회 불확실·repository 오류는 그대로 반환하며 준비로 fallback하지 않는다.
`NotObserved`는 키 부재 lease가 아니다. 나중의 영속 claim이 동일 키의 경합과 전체 불변 binding 충돌을 계속 판정해야 한다.
기존 candidate/manifest/storage API를 제거하거나 원래23개 작업 parser·mutator를 변경하지 않았다.

## 명시적 결과 복구

`PreparedSearchRequestLookup.recover_registered`는 기존 provider의 등록 archive 복구 경로를 재사용한다.
caller에게 manifest·artifact locator·저장된 claim을 받지 않고 조회한 job/attempt에서 정확한 등록 locator를 유도한다.
현재 ACL/AEAD와 effect readback, 두 번째 요청 관측의 일치 검사는 원 복구 코드가 수행한다.

요청 부재·미시작 attempt·등록 자료 부재는 각각 기존 복구 관측 타입으로 남는다.
어느 경우도 no-effect·새 실행·retry·성공 판정이 아니다. 다른 job, 관측 변경, 등록 읽기 불확실은 오류이며 자동 재조회나 쓰기를 수행하지 않는다.

## 검증 결과

`implementation/p09/evidence/p09-361-search-lookup515.v1.json`은 신규30개 범위다.
23개 독립 계열에서 blob을 읽으면 실패하도록 설정하고 head/node 접근도 거부하는 repository로 완료/진행 중 조회를 확인했다.
기존 요청 조회 중 head/node·commit·intent 쓰기는0이었다. 미관측 분기는 실제 원본 후보를 준비하고,
조회 canonical/scoped digest와 원 제품 receipt, 저장 job identity에서 재구성한 SQL lookup의 동등성을 확인했다.
JSON 공백/pretty 형식 차이도 같은 요청으로 결속된다.

공통7개는 전 schema의 strict/duplicate/preview 거부, conflict/uncertainty/unavailable의 fallback 금지,
미관측 원본 AEAD 실패, 현재 write/provider scope, 미시작/부재 복구와 정확한 등록 locator,
외부 job·관측 변경·등록 읽기 불확실에서의 쓰기/재시도 금지를 확인했다.
등록 자료가 없는 모형 복구를 실제 저장 효과의 readback 성공으로 사용하지 않는다.

최종 결과는1017fresh/final1017·실제 dep-info1final·cleanupTrue,164.125초이며 실제 명령 단계는32.547초다.
CPU 최고38.67%, 가용 RAM 최저36.301%였고 보호 중단은 없었다. 원1코어·낮은 우선순위·소유 Cargo CPU6.25%·RAM/commit95% 보호를 유지했다.
514의 번호 parser 반환형 연결 오류는 컴파일 실패/시험0·cleanupTrue·final fresh 누락 상태로 보존했다.
원 번호 parser·mutator는 변경하지 않고 어댑터만 수정했다. 513의 이전 저장/CAS31개 본문은 반복하지 않았으며 당시 입력의 결과로 보존한다.
변경 전27개 소스와 실패 당시 번호 어댑터는 `implementation/p09/source-archive/p361-search-lookup514/`에 있다.

## 격리 PostgreSQL 저장과 재시작 복구의 관측

2026-10-22 새 격리 PostgreSQL schema24에서 일반 대소문자 변환 한 사례를 실행했다.
실제 원본 HWPX를 준비하고 claim·lease·등록 intent·revision CAS·완료를 거쳐 암호화 결과를 다시 읽었다.
기존 manifest/locator/핸들 파일4개의 원 경로를 비운 상태에서 공개 요청만으로 완료 작업과 등록된 결과를 찾았고,
서버 재시작 뒤에도 같은 job/attempt/revision을 복구했다. 파일4개는 byte-exact 복원했으며 복구 중 새 작업 실행은 없었다.
잘못된 AES 키 거부, source/result readback과 두 번의 DB snapshot 일치도 관측했다.
원본 관측은 `target/p09-common-search-sql24-observation-520.json`이며 두 postmaster의 정상 종료를 기록한다.
실제 DB의 artifacts6·jobs2·attempts2는 source bootstrap1회와 검색 작업1회다. 23계열 전체 SQL 검증은 아니다.

전체 실행의 마지막 발행은 기존 compact envelope의256KiB 외곽 한도를 초과했다.
`implementation/p09/evidence/p09-361-search-sql520-publication-failure.v1.json`은 이를 별도로 기록한다.
부모의 최종 입력·자원 표본 원장이 발행되지 않았으므로 본문 통과를 현재 전체 소스 마감 PASS로 승격하지 않는다.
운영 DB·신뢰 registry·실제 scanner/키 custody·Native 자격과도 구분한다. 본문을 다시 실행하지 않았다.

실행 준비에서 발견한 입력 경로 검사와 시계 문제도 수정했다. Cargo의 저장소 내부 절대경로 SQL 입력을
정규화하되 저장소 밖 경로는 거부한다. 이 Python의 `GetTickCount64` 단조 시계 해상도15.625ms 대신
`QueryPerformanceCounter` 기반0.1µs 단조 시계를 파일 열기/읽기 속도 조절에 사용한다.
초당 파일 열기20회·EXE2.5MiB/그 외4MiB·64KiB chunk와 전체 fresh SHA를 유지했다.
520 본문은3184회·366767631bytes를 읽었고 내용 캐시를 사용하지 않았다.
516~519의 사전 실패와 원520 검증기는 source archive와 원 영수증/관측으로 보존했다.

`implementation/p09/evidence/p09-361-search-sql-receipt521.v1.json`은 IO/시계7개와 증거 형식6개,
189fresh/final189·cleanupTrue를 마감했다. 반복 값 사전/시각 prefix를 무손실로 표현하며 모든 값·자료형을 복원한다.
입력1062개·자원1210표본·metadata12KB 모형은239427bytes로 원262144bytes 한도 안에 발행됐다.
표본 삭제·반올림·외부 carrier·한도 확대는 없다. 521은 모형 검증이며520의 잃은 부모 원장을 재구성하지 않는다.

## 남은 제품 실행 조건

515의 검증 repository는 모형이며520은 격리 DB 한 사례의 본문 관측이다. 운영 SQL 자격은 아니다.
현재 입력 마감이 결속된 실제 SQL ACL/claim/lease·경합·crash/키 custody·등록된 산출물의 독립 복구·게시,
현재 신뢰 registry/target·Native 보호·의미·저장/재열기 요건은 별도다.
공식158/249·잔여91·next165, source API v13 미해결4, P09/A12/A13 OPEN·목표ACTIVE·P10미시작을 유지한다.
P02 routing_allowed=false·RouteUnqualified와 외부003 실패/claim 소비·cleanup=false를 변경하지 않았고 새 Native·한글·접근 허용은 실행하지 않았다.
