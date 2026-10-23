# 원본 필드 의미 인덱스와 제품 평가

원본 HWPX의 필드 범위를 기존 HTTPS·표 수식 reader에 연결한다. 조회 결과는 원본에 결속된 의미 종류와
해시이며 URL 열기·외부 접근 승인·필드 갱신·전체 참조 검증이 아니다. 기존 reference-source v13과
incomplete·미해결4단계·report 없음·exit3 계약은 변경하지 않는다.

## 원본 의미 인덱스

`SourceFieldMeaningIndex::import`는 `ImportedDocumentFields`를 빌려 기존 `read_meaning`을 한 번씩 실행한다.
기존 `ImportedDocumentFieldSemantics`도 같은 읽기 루프를 사용한다. 인덱스는 의미 관측만 소유하며
기존 전체 의미 그래프를 추가 복제하지 않는다. 원래 graph attachment·HTTPS six-parameter tuple·수식 reader와
8,000,000요소의 보수적 aggregate work 한도를 유지한다.

현재 지원 의미는 원 HTTPS/current-tab profile과 표 수식 AST다. 수식 캐시의 `Unverified`를 평가 성공으로 바꾸지 않는다.
다른 필드 종류는 `Unsupported` 관측으로 남는다. 지원 종류의 잘못된 매개변수는 오류이며 Unsupported로 fallback하지 않는다.
구역/필드 개수, HTTPS URI 길이, 의미 전체의 유한 JSON hash 출력 예산을 검사한다. 수식의 구조·문자열·AST 예산은 원 reader가 유지한다.

receipt는 source package SHA, 원 field graph SHA와 의미 inventory SHA를 결속한다.
`verify_reconstruction`은 원 forms 객체에 결속된 전체 fresh reconstruction을 받아 원 범위·관측·receipt를 다시 비교한다.
같은 바이트를 별도로 import한 다른 원본의 reconstruction도 거부한다. 해시와 receipt는 접근/실행 권한이 아니다.

## HTTPS 토큰 검사 최적화

기존 컨테이너/문자열 검사는 각 매개변수마다 XML 토큰 전체를 훑었다. 이제 불변 parser의 요소별
start/end token 범위를 빌려 검사하며, 원 owner 조건과 허용/거부 token kind를 그대로 유지한다.
빈 태그·종료 태그·주석·엔티티도 원 parser가 관측한 범위를 사용한다. 전역 캐시·추가 XML parse는 없다.
522의 새3개 본문은 모든 admitted 요소의 원 전체 스캔과 동등성 및512개 leaf의 국소 검사량을 관측했다.
하지만 cfg(test) 공통 fixture2개가 원 사전 입력에서 누락돼 final fresh가 없으므로3개는 정식 마감 수에 넣지 않는다.
523에서 이들을 다시 실행하거나 현재 전체 unit PASS로 승격하지 않았다.

## 제품 API와 출력

`ReferenceValidationProductOperation::assess_package_field_semantics`는 실제 bytes·document ID·예상 package SHA에서 시작한다.
원본/구조/forms/fields를 import한 뒤 모든 XML part의 fieldBegin/fieldEnd coverage를 대조한다.
header 등 비본문의 시작/종료/균형 쌍도 무시하지 않고 거부한다. source drift·item/출력 한도 위반도 오류다.

출력 schema는 `hwpx-agent.product.reference-source-field-meanings/v1`이다. selection에는 source-derived reference ID,
field fingerprint, 원 reference와 typed meaning의 SHA, `https_target`/`table_formula_ast`/`unsupported`만 포함한다.
URI·Command·수식/캐시/본문 원문은 출력·Debug에 포함하지 않는다. JSON은 bounded writer로 작성하며 자르지 않는다.
새 CLI/MCP/raw action·stored ACL 우회·issuer·Native/외부 실행 경로를 추가하지 않는다.

## HTTPS 목적지 변경 후보 연결

별도 `prepare_package_https_target_changes`는 이 평가의 source reference ID·field fingerprint·meaning SHA를
실제 후보 편집에 사용한다. 기존 평가 함수는 계속 읽기 전용이며 URI를 열지 않는다.
목적지 정책·보호·원 preserving writer와 전체 readback을 묶는 [변경 후보 계약](p09-source-https-target-changes-v1.md)을 따른다.
후보는 현재 stored 서비스/issuer/Native 권한이 아니다.

## 검증 결과와 완료 경계

[523](../../implementation/p09/evidence/p09-361-source-field-semantics523.v1.json)은 신규9+직접 영향6=15개,
849fresh/final849·실제 dep-info2final·cleanupTrue를 마감했다. 186.015초·시스템 CPU 최고45.31%·
가용 RAM 최저31.925%이며 원1코어·BelowNormal·소유 CPU6.25%·RAM/commit95% 보호를 유지했다.
기록된 실제 compiler dep-info는 새 전용 host마다 하나이며, 과거의 다른 빌드 variant를 현재 실행 근거로 선택하지 않는다.

보존된 실제 HTTPS HWPX1개와 P06 manifest에 해시로 고정된 수식 입력/출력16개를 읽었다.
새 제품 API에서 실제 의미와 원 필드 결속·비노출·문서/패키지 SHA·정확한 출력 한도·unknown/malformed·
whole-source field coverage·수식 캐시 미검증과 기존 v13 미완료 경계를 확인했다. 원본은 수정하지 않았다.
522의 통과 본문3개/입력 누락 실패·final fresh 없음은 원본에 보존했다. 523은3개를 제외한15개만 수용한다.

전체 참조 edge의 대상 해석·cache validity·auxiliary state·문서/쪽 흐름·저장/재열기·target/Native 자격은 여전히 남는다.
새 API의 지원 의미 두 종류를 `ReferenceEdgeSemantics` 전체 종료나 전체 의미 검증으로 승격하지 않는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·P02 routing_allowed=false는 그대로다.
003/SQL520/Native·접근 허용·공식 큐는 실행하지 않았다.
