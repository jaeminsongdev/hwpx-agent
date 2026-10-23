# 다중 그룹 정렬의 이동 목록과 공통 계획

다중 part·독립 부모의 실제 이동 목적 slot을 원본 anchor와 범위로 결속해 공통 계획으로 전달한다.
`hwpx-agent.source-paragraph-sort-group-splices/v1`은 기존 sealed SourceParagraphSortSpliceInventory를
재사용하며 다중 그룹의 원 receipt JSON은 바꾸지 않는다. 기존 단일 그룹의 v1 profile과 코드는 유지한다.

## 원본 이동 목록

원 part 경로와 원 XML 위치 순서의 전체 slot을 사용한다. 고정 slot·singleton·무변경 그룹은 편집에서
제외하지만 원 receipt에는 남긴다. 목적 anchor 유일성·범위 비겹침·전체 대상 수·이동 수와 전역 복사 byte
한도를 확인한다. 실제 치환 원문의 SHA와 크기를 결속하며 XML 조각을 복제하지 않는다.

원본 출력의 정확한 subtree/gap/tail readback 뒤에 메타데이터를 만든다. 같은 bounded streaming hash로
원 receipt SHA와 전체 목록 SHA를 계산한다. 목록은 임의 입력으로 역직렬화하거나 외부에서 생성할 수 없다.

## 공통 계획과 manifest

기존17개 schema를 유지하고 다중 그룹을18번째로 추가한다. 원 final_permutation_splices projection·
OperationPlanCompiler·실제 구조 소유자·12개 잠금 argument·manifest 본문을 재사용한다.
가상 document나 임의 첫 문단으로 편집을 대표하지 않는다. 원 현재 권한·source/head와 최종 consumer head
검사를 유지하며 plan 확인에서 정렬을 다시 실행하지 않는다.

이는 원자적 순열 후보 전체를 설명하는 계획이다. 개별 slot을 독립적인 순차 정렬로 실행할 수 있는 실행기를
추가한 것이 아니며 ingest/commit/CAS·영속 멱등·게시 권한은 없다. 실제 P02 routing_allowed=false는
새18번째 schema에서도 원본 읽기 전에 거부되며 원 RouteUnqualified를 유지한다.

## 검증과 저장 실패 보존

components248은 마지막 WORKSPACE_BOUNDED_RECEIPT 저장 실패로 완전한 결과와 자원 기록을 회수하지
못했다. 당시 관측은 별도 실패 파일에 보존하고 수용0으로 유지했다. 원본 실행 기록을 재구성하지 않는다.

compact249는 무압축 compact JSON envelope를 사용한다. 모든 값·순서·누락/null/false·source pin·trace를
보존하고 payload 크기/SHA·state와 canonical layout을 확인한다. 원 publisher의262144byte 상한은 그대로다.
compact_receipt_json.unpack으로 원래 row를 복원한다. 형식4계약 뒤 이번 범위만 재실행했다.

원본6+신규 compiler/manifest14+영향기존5=25pass·836fresh/final836·진단/경고없음·cleanupTrue다.
저장된 전체 결과는191499bytes다. 기존 다중 원본16/제품20·공식249는 반복하지 않았다.
두 part·셀·불연속/고정 slot·singleton·실제 원문 SHA/크기·원 receipt 결속·128이동·공통 dispatcher와
원 계획/manifest 대조·현재 권한/ACL/격리/AEAD·마지막 head 경합·보호/route 거부를 확인했다.

249는 warm 재실행이며 전체121.188초·명령0.875/10.375초·시험0.65/10.14초·Job CPU0.828/10.156초·
private최고53.91MiB/0.16919%·시스템CPU최고23.24%·가용RAM최저48.8148%다.
두 Job active0/empty/handle closed와 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·
명령300초/guard600초를 유지했다. 이 수치로 첫248 빌드의 최고 부하나 PC 프리즈 해결을 주장하지 않는다.

근거: implementation/p09/evidence/p09-361-sort-groups-compiler-compact249.v1.json 및
p09-361-sort-groups-compiler-publication-failure248.v1.json.

## 남은 실제 실행과 의미 검증

manifest 라우팅 시험은 합성 fixture이며 실제 target/registry·Native 보호·실행/ingest/commit/CAS·
영속 멱등/게시 자격이 아니다. 중첩 하위 트리·구조적 키·locale와 나머지 검색·참조 계약은 미완료다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
