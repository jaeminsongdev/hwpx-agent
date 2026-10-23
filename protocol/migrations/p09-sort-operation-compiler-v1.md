# 문단 정렬의 실제 이동 목록과 공통 계획

SEARCH-021의 원본 정렬 후보를 공통17개 schema dispatcher·operation compiler·manifest 데이터 경로에
연결한다. SourceParagraphSortSpliceInventory는 고정 slot을 제외한 실제 이동 목록이며 현재 실행 자격은 아니다.

## 실제 이동 목록

hwpx-agent.source-paragraph-sort-splices/v1은 원 source/output package SHA·기존 SourceParagraphSortReceipt
JSON의 SHA·실제 이동 목록과 canonical SHA를 보관한다. 각 항목은 목적 slot의 원본 anchor·원 part byte
범위와 그곳에 놓이는 원본 하위 요소의 치환 SHA/크기다. source_order[destination]==destination이면 항목이 없다.
목록은 이미 원 순열 patch와 독립 출력 readback을 통과한 같은 계획에서 만든다. 원문/fragment XML을
보관하거나 정렬을 재실행하지 않는다. 각 할당/누적 byte와 streaming hash는 기존 유한 상한을 유지한다.

목록과 항목의 필드는 외부 생성·역직렬화·수정이 불가능하다. 공개 원본 후보의 읽기 전용 metadata와
crate 내부 저장/제품 compiler view만 이 불변 목록을 참조한다. 기존 SourceParagraphSortReceipt JSON과
원 비교·선택 범위·보호/필드·patch·writer·readback은 바꾸지 않는다.

## 공통 dispatcher와 계획

기존16개 schema의 순서/처리 본문을 보존하고 ParagraphSort를17번째로 추가한다. 기존 닫힌 JSON parser와
현재 document.write·scope/head/ACL/quarantine/AEAD 검증은 같은 후보의 현재 전달 경로를 사용한다.
공통 projection의 final_permutation_splices는 원본/출력/legacy receipt·목록 지문을 기존12개 잠금 argument에
결속한다. 원 SelectorSnapshot·OperationPlanCompiler는 원본의 실제 구조 소유 node를 사용하고 임의 첫 문단이나
가상 document node를 만들지 않는다. subtree 범위는 같은 원본 요소의 outer span과 정확히 일치해야 한다.

각 operation은 하나의 실제 목적 slot을 가리키는 계획 자료다. 실제 적용은 원자적 순열 후보 전체와 같아야
하며 개별 operation마다 현재 출력에 재정렬하는 동작을 허용하지 않는다. 이 단계는 실행기를 제공하지 않는다.
계획/보관 후보의 verify와 byte 전달은 원 현재 권한/원본/마지막 head를 유지하며 컴파일이나 정렬을 반복하지 않는다.

## Manifest와 실행 경계

같은 후보는 원 CapabilityRouter와 ExecutionManifest::from_receipts에 source artifact·원 SHA/크기·plan·
실제 각 operation의 route를 결속한다. manifest 시험의 라우팅 증거는 합성 fixture이며 현재 registry/target/
Native 보호 자격을 입증하지 않는다. 현재 support/policy/protection/health가 바뀌거나 실제 문서 보호 신호가
있으면 거부하고 consumer 직전 마지막 head 검사도 유지한다.

17번째 schema도 실제 보존된 P02 서명 snapshot의 routing_allowed=false로 원본 접근 전에 거부한다.
그 서명을 현재 P09 실행 자격으로 바꾸지 않으며 기존 RouteUnqualified는 유지한다.

## 검증 결과

components237은 원본6pass 뒤 시험 helper 부모의 타입 import 누락 E0432로 제품 시험0이다. 실패 원본을
보존하고 시험 import 한 줄만 추가했다. recovery238은 신규 compiler/manifest12+영향기존3=15pass·
810fresh/final810·진단/경고없음·cleanupTrue다. 원본6+신규제품12+영향기존3=고유21개 통과이며
현재21개 단일 실행이 아니다. 통과 원본6·이전 source 정렬19/제품20·공식249는 반복하지 않았다.
원 비교/보호/patch/readback/receipt와 기존16계열 처리·compiler/owner/router/manifest 본문은 보존했다.

실제 원본/출력 span·치환 SHA/크기·고정 slot 제외·legacy receipt/목록 지문·NFC 안정성·128문단,
공통/개별 제품 출력 일치·실제 owner/12개 argument·scope/key/plan/policy·불완전 요청 거부·현재 write/ACL·
compile/verify/전달의 마지막 head 경합·실제 P02 정책 거부를 확인했다. 합성 fixture의 manifest는 원 source/
plan/route 일치·현재 route 정책/보호/health·실제 문서 보호 신호와 마지막 head 거부를 확인했다.

- implementation/p09/evidence/p09-361-sort-compiler-components237.v1.json
- implementation/p09/evidence/p09-361-sort-compiler-recovery238.v1.json

237/238 전체113.844/125.110초·명령26.110/34.656/20.063초·시험0.37/7.16초다. 시스템CPU 최고34.09%·
private 최고1804.04MiB/5.66222%·가용RAM 최저33.8663%이며 세 Job active0/empty/handle closed다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했다.
OS 변경이나 PC 프리즈 해결을 주장하지 않는다.

## 남은 제품 경계

실제 trusted 실행·ingest/commit/CAS·영속 멱등/게시·다중/중첩 그룹·구조적 키·locale/target/Native와
전체 SEARCH-021 계약은 미완료다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
