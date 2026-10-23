# 다중 그룹 문단 정렬의 현재 저장과 제품 요청

`StoredParagraphSortGroupsProductRequest::prepare_json`은 현재 저장 서비스에서 읽은 실제 원본의
다중 그룹 정렬 후보를 준비한다. 요청은 별도 `hwpx-agent.product-paragraph-sort-groups-request/v1`과
`sort_paragraph_groups`이며 기존 단일 형제 그룹 요청의 의미나 다른 부모 거부를 바꾸지 않는다.

## 요청과 현재 원본

중복 없는16KiB JSON, project/document/revision/head/source SHA, key/plan, 네 selector,
명시적 spec/review 정책을 요구한다. 미지/중복 키·배열·후행 값·잘못된 정책·지원하지 않는 grouping,
단일 그룹 schema/kind와의 혼용은 원본 접근 전에 거부한다. 검색 graph·원본 bytes·승인 bits는 받지 않는다.

현재 document.write·scope/head/ACL/quarantine/AEAD·전체 Form proof를 유지하며 한 번의 다중 그룹 정렬
출력에 연결한다. 그룹별 순열과 anchor 유일성, 전역4096 대상·비교 예산, 이동 수·변경 그룹/part 수를 확인한다.
singleton과 이미 정렬된 그룹도 receipt에서 제외하지 않는다.

Borrowed/Owned는 같은 원본 소유자를 재사용한다. 보관한 후보의 verify/전달은 현재 접근·원본·writer와
consumer 직전 최종 head를 확인하지만 정렬이나 원본 수입을 반복하지 않는다. 기존 오류 타입을 재사용하며
새 타입·schema와 별개인 원 RouteUnqualified 거부를 유지한다. key는 결속 정보이며 영속 실행 권한이 아니다.

## 검증 결과

components246 신규 제품20pass·824fresh/final824·진단/경고없음·cleanupTrue다.
실제 두 구역과 지역 ID, NFC 양방향 안정성, singleton/무변경 그룹, 네 selector와 부분/오래된 범위 거부,
닫힌/중복 JSON, 정확한16KiB, key/plan/spec/policy 결속, 현재 write/외부5scope, ACL 철회/재부여,
격리/AEAD, prepare/verify/전달의 최종 head 경합, 전역 비교 예산/한도, hidden/MEMO 두 그룹과 cache 보존,
비노출/미게시, 128문단을 확인했다. 기존 다중 원본16·단일 source19/제품20/공통연결21·공식249는 반복하지 않았다.

원 source/정렬/reader/보호/기존 제품/시험 본문은 불변이다. 두 root child와 새 시험 child만 추가했고
그 외 코드와 이전 원본·실패 증거는 유지했다. 후보 준비는 source/head를 변경하거나 결과를 수입·게시하지 않는다.

246 전체159.687초·명령52.782초·시험8.14초·Job CPU50.344초·private최고1809.18MiB/5.67837%·
시스템CPU최고59.72%·가용RAM최저46.6415%다. Job active0/empty/handle closed와 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초/guard600초를 유지했다.
시스템 전체 CPU는 검증 자체 CPU나 PC 프리즈 해결 증거가 아니다.

근거: `implementation/p09/evidence/p09-361-sort-groups-product-components246.v1.json`.

## 남은 실행 연결

새 다중 그룹의 실제 이동 목록·공통 dispatcher/compiler/manifest 연결, 선택된 중첩 하위 트리 합성·구조적 키·
locale·실제 실행/ingest/commit/CAS·영속 멱등/게시는 미완료다. 기존 단일 그룹의 공통 계획 증거를 새 API로
승격하지 않는다. P02 routing_allowed=false와 실제 Native 보호·target/registry 자격의 기존 경계를 유지한다.

source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
