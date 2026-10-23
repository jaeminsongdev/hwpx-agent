# 다중 부모와 다중 part 문단 정렬

`lower_selector_paragraph_sort_groups_candidate`는 실제 불변 HWPX에서 완전히 선택한 문단을
원 part와 직접 부모별로 정렬한다. 별도 `hwpx-agent.source-paragraph-sort-groups-candidate/v1`이며
기존 단일 그룹 API의 다른 부모 거부와 receipt 형식은 바꾸지 않는다.

## 선택과 정렬

Document, Section, NodeSet, Selection의 실제 원본 창과 명시적 hidden/MEMO 정책을 사용한다.
부분 문단·여러 검색 블록으로 분리된 구조적 키·필드 cache·보호 구간은 선택 전체를 거부한다.
정렬 가능한 하위 셀만 남기려고 구조적 상위 문단을 조용히 제외하지 않는다.

그룹은 part 경로와 원 부모 인덱스로 결정적으로 나누고 각 그룹은 원 XML 순서로 정렬한다.
원 NFC Unicode scalar 비교와 오름/내림 안정 정렬을 재사용한다. 동등 키의 원문 순서와 원 XML
바이트를 유지하며 locale·숫자·구조적 정렬 키를 암묵적으로 적용하지 않는다.

singleton과 이미 정렬된 그룹도 보호 검사와 receipt에 남긴다. 모든 그룹이 singleton이면 NoMatches,
정렬 가능한 그룹이 있지만 이동이 없으면 NoChange다. 비교 byte 예산은 전체 그룹 누적이며
각 그룹마다 새 예산을 부여하지 않는다. 최대4096 선택 대상과 원 순열의 누적 복사 byte 상한을 유지한다.

## 하나의 원본과 출력 검증

현재 전체 Form proof·원본 index·field/review 문맥을 재사용한다. 관측된 보호 인덱스는 part마다
한 번 만들며 변경 없는 그룹도 검사한다. 원본 선택 span 전체의 겹침을 출력 생성 전에 거부한다.

그룹별 PermuteSiblingElements를 하나의 원본 기준 트랜잭션에 전달한다. 그룹마다 후보 패키지를
생성하거나 다음 그룹의 원본으로 다시 수입하지 않는다. 원 ID/참조·보존 profile·patch/writer 검사는
동일하다. 전체 출력 package/Form/field 수입과 review readback은 한 번이다.

원 part별 정렬된 목적 slot과 실제 이동 원문을 한 번 결속한 뒤 각 목적 하위 트리와 비선택 slot·gap/tail을
독립 byte 대조한다. 다른 part는 원 builder의 source/output SHA 검사로 보존한다.
receipt는 전체 source/index/scope/policy/spec, 그룹별 원 anchor·원문/키 SHA·순열·작업량,
전체 변경 수와 output SHA를 결속한다. 경로 타입은 검증된 PackagePath이고 직렬화만 패키지 상대
문자열로 한다. Debug와 receipt에는 검색 원문을 노출하지 않는다.

## 검증 결과

components242와 recovery243은 PackagePath Serialize 부재의 E0277로 컴파일 실패/시험0이다.
첫 Debug 미구현 추정은 잘못됐으며 해당 타입에는 Debug가 있다. 새 그룹의 비노출 Debug를 유지하고
직렬화만 추가했다. 두 실패 원본과 모든 시험 조건을 보존했다.

serialization-recovery244는 신규16pass·818fresh/final818·진단/경고없음·cleanupTrue다.
두 셀·두 part와 지역 ID, 오름/내림 안정성, 비연속 선택, singleton/무변경, 전체 비교 예산, 네 selector,
원본/proof·부분/오래된 범위 거부, 무변경 그룹의 보호, 구조적 상위 문단 거부, hidden 명시 정책,
비노출·결정성·한도·128문단을 검증했다. 기존 source19/제품20/공통연결21·공식249는 반복하지 않았다.

전체138.531초·명령32.970초·시험2.86초·Job CPU31.859초·private최고1798.73MiB/5.64557%·
시스템CPU최고62.52%·가용RAM최저44.7120%다. Job active0/empty/handle closed이며 한 코어·
BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초/guard600초를 유지했다.
시스템 전체 CPU는 검증 자체 CPU가 아니며 PC 프리즈 해결 증거가 아니다.

근거: `implementation/p09/evidence/p09-361-sort-groups-serialization-recovery244.v1.json`.

## 남은 제품 연결

새 다중 그룹 API의 현재 저장 서비스·엄격한 제품 요청·실제 이동 목록·공통 compiler 연결은 남는다.
선택된 중첩 하위 트리 합성·구조적 키·locale·실제 실행/ingest/commit/CAS·영속 멱등/게시는 미완료다.
기존 단일 그룹의 제품·compiler 증거를 새 API로 승격하지 않는다.

source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

## 현재 저장과 제품 요청 연결

위 원본 검증 이후 현재 저장 서비스와 별도 엄격한 제품 요청을 연결했다. components246에서 신규 제품20개가
통과했고, 기존 원본16개는 반복하지 않았다. 위 남은 제품 연결은 원본 검증 종료 시점의 경계이며 현재 저장과
제품 요청은 [다중 그룹 제품 요청 계약](p09-paragraph-sort-groups-product-request-v1.md)을 따른다.
실제 이동 목록·공통 계획과 실제 실행/commit/CAS·Native/Gate는 여전히 미완료다.
