# 공통 제품 요청의 검색 치환 후보 준비

## 현재 공통 경로

현재 변경 준비 표는23개 family이며 기존22개 순서 뒤에 개인정보 선택 마스킹 변경 전용 owner를 추가했다.
별도 PersonalInfoMaskPreview는 JSON만 전달하고 원본 읽기 전 mutation/compiler 진입을 거부한다.
실제 변경된 text anchor inventory를 전체 receipt와 실제 구조 owner·12개 잠금 인자에 결속한다.
[마스킹 공통 계획 계약](p09-compiled-personal-info-mask-v1.md)은 신규19+영향13과 독립 hash 영향1의 원 결과를
구분하며 실제 실행/저장·문서 전체 익명화·Native/Gate를 완료로 올리지 않는다. 아래는 문단 스타일 v2 연결 당시 이력이다.

문단 스타일 v2 연결 당시 변경 준비 표는22개 family이며 기존21개 순서 뒤에 문단 스타일 이름 v2 변경 전용 후보를 추가했다.
선택적 원본 서식 필터를 포함한 전체 output receipt를 계획에 결속하고 별도 NamedStyleOptionsPreview는
JSON만 전달한다. [v2 제품과 공통 계약](p09-named-paragraph-style-product-v2.md)은 원27개 통과와
후처리 실패 보존/재실행 없는 대조를 구분한다. 아래는 문단 이름 v1 연결 당시 이력이다.

문단 이름 v1 연결 당시 변경 준비 표는21개 family이며 기존20개 순서 뒤에 문단 스타일 이름 변경 전용 후보를 추가했다.
별도 NamedStylePreview는 JSON만 전달하며 mutation/compiler에 들어가지 않는다. 실제 문단 owner와
전체 이름 질의 receipt를12개 잠금 인자 계획에 결속한다. 신규19+영향12 검증과 경계는
[문단 스타일 이름 제품 계약](p09-named-paragraph-style-product-v1.md)을 따른다. 아래는 폰트 연결 당시 이력이다.

폰트 연결 당시 변경 준비 표는20개 family이며 기존19개 뒤에 폰트 v2 변경 전용 후보를 추가했다. 원 typed
parser/receipt·서버 한도·현재 접근/전달/route 거부를 유지한다. preview_only=true는 mutation이 아닌
별도 SearchPreview이며 JSON만 전달한다. [v2 공통 계약](p09-font-options-product-v2.md)은 preview의
compiler 사전 거부와 전체 필터 receipt 결속을 정의한다. 신규23+영향12개 검증에서 기존 네 경로의
12개 인자를 유지했고 폰트 v1/v2만15개다. 이하 초기16종과 후속 연결 기록은 이전 이력이다.

## 이전 연결 기록

StoredProductRequest는 기존 Form·TableFormulas와 함께 기존 치환·변환16개 스키마를 같은 준비
진입점에 연결한다. 기존 wire schema나 기능별 지원 범위를 넓히지 않는다. 이 연결은 후보 준비이며
실제 저장 트랜잭션·실행·게시 자격은 아니다.

## 허용 스키마와 원 구현

| 스키마 이름의 hwpx-agent 접두사 이후 | 버전 | 기존 기능 |
|---|---|---|
| product-literal-replacement-request | v1 | plain 문자열 치환 |
| product-literal-replacement-request | v2 | 혼합 text atom 문자열 치환 |
| product-literal-replacement-request | v3 | 숨은 설명과 MEMO 치환 |
| product-literal-replacement-request | v4 | selector와 review 문자열 치환 |
| product-regex-replacement-request | v1 | 정규식 캡처 치환 |
| product-regex-replacement-request | v2 | 명시적 빈 일치 삽입 |
| product-character-style-replacement-request | v1 | 부분 run 글자 모양 치환 |
| product-text-style-replacement-request | v1 | text style 참조 치환 |
| product-paragraph-style-replacement-request | v1 | 문단 모양과 이름 스타일 참조 치환 |
| product-unicode-normalization-request | v1 | 선택 범위 정규화 |
| product-unicode-normalization-request | v2 | 검색 일치 정규화 |
| product-case-conversion-request | v1 | 명시적 대소문자 변환 |
| product-width-conversion-request | v1 | 전각 반각 변환 |
| product-whitespace-normalization-request | v1 | 공백 탭 줄바꿈 정규화 |
| product-text-control-replacement-request | v1 | Tab과 LineBreak 치환 |
| product-number-control-replacement-request | v1 | AutoNumber와 NewNumber 저장 값 치환 |

SEARCH_MUTATION_REQUEST_SCHEMAS와 분류·준비·검증·전달·route 분기는 단일 닫힌 표에서 생성한다.
기능별 원 엄격한 파서가 필수 operation·scope/selector·review·중복/nested/미지 속성·범위/버전을
검증한 뒤 현재 원본을 읽는다. 검색 요청의 상한은16KiB다. 공통 외부 envelope의2MiB 상한이나
다른 schema를 이용해 이 한도 또는 기능별 거부 조건을 우회할 수 없다. 원 Form/Formula의 파서·
분기·bindings·전달·route 본문은 보존했다.

## 서버 한도와 후보 소유권

prepare_json은 표준 한도를 쓰고 prepare_json_with_search_limits는 서버가 이미 검증한
SearchMutationLimits의 search/auxiliary/writer를 전달한다. NumberControl은 별도
ReferenceAuxiliaryLimits도 받는다. 요청 JSON의 limits/approved를 실행 권한으로 해석하지 않는다.
Form bindings는 검색 요청의 준비·전달·route 검사에서 읽기 전에 거부한다.

PreparedStoredSearchMutation은 원 prepared 객체를 Box로 소유한다. 별도 source clone/reimport·
matcher/치환 재실행은 추가하지 않는다. SearchMutationReceiptRef는 원 typed receipt를 빌리며
후보 수명 밖으로 나갈 수 없다. Debug는 내용을 출력하지 않는다. receipt 조회는 검증이나 권한이
아니며 verify/with_verified_bytes/require_current_product_route가 원 기능의 현재 검사를 수행한다.

현재 document.write·다섯 scope·head·ACL·quarantine·AEAD·source/출력 integrity와 consumer 직전
최종 head는 그대로다. 원 오류는 SearchMutationError의 family variant에 보존한다. 모든 family는
fresh 검증 뒤에도 원 RouteUnqualified를 반환한다. key claim·실제 ingest/commit/CAS·영속 멱등
실행·실행 dispatcher·CLI/server transport·Native·게시 권한은 생성하지 않는다.

## 연결 시험과 실패 보존

components205는16pass/10fail·경고1이다. 공용 fixture에 넣은 t.charStyleIDRef는 기존 문자열/
정규식/run 서식 계열에서 미지원이므로 해당0~6 입력에서만 제거했다. 원 기능별 제품과 dispatch
실행 본문은 바꾸지 않았으며 borrowed receipt의 Debug 비노출 구현만 추가했다. recovery206은
실패10pass·732fresh/final732·진단/경고없음·cleanupTrue다.

fixture 수정의 영향을 받는 서버 한도 시험에는 정상 한도 성공/전달 대조를 추가했다. budget207은
이1개만pass·733fresh/final733·진단/경고없음·cleanupTrue다. 검색/출력/번호 서식의 좁은 한도 거부가
잘못된 원본 때문인 것으로 오인하지 않는다. 다른25개·기존 제품292·공식249는207에서 반복하지 않았다.
고유 연결26개이며 현재26개 단일 실행이 아니다. 원205 실패와 두 성공 증거를 모두 보존했다.

시험은16종 각각의 실제 공통 진입점·원 요청 drop·typed receipt/전체 bytes 동등성과 원 route 거부,
엄격한 envelope/operation·중복/escaped key·16KiB·외부5scope·write/ACL/격리/AEAD·세 단계
최종 head 경합·review 선택 창·서버 한도·legacy bindings/스키마 혼용·비노출/미게시를 포함한다.
원 Form/Formula 분기와 기존292개 제품 시험 본문은 역변환·불변 입력으로 확인했으며 해당292개를
새로 실행했다는 뜻은 아니다.

206은 전체115.078초·명령21.780초/시험5.03초·Job CPU19.703초·private최고926.55MiB/2.9081%·
시스템CPU최고50%·가용RAM최저27.4006%다. 207은 전체104.125초·명령10.282초/시험0.94초·
Job CPU8.828초·private최고929.96MiB/2.9188%·시스템CPU최고74.91%·가용RAM최저27.2428%다.
두 Job active0/empty/handle closed와 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/
stop7%·RAM/commit95%·명령300초·guard600초를 유지했다. OS/Defender/다른 앱은 변경하지 않았다.
시스템 표본은 검증 단독 CPU·성능 비교·PC 프리즈 해결 증거가 아니다.

근거는 implementation/p09/evidence/p09-361-search-mutation-dispatch-components205.v1.json,
p09-361-search-mutation-dispatch-recovery206.v1.json,
p09-361-search-mutation-dispatch-budget207.v1.json이다.

## 남은 P09 완료 경계

공통 후보준비 이후 실제 transaction/route manifest·저장/commit/CAS·영속 멱등 실행·실행 dispatcher/
transport/게시, 다른 제어·참조/ID 보존·전체 query/replacement/selector/filter/유효 서식과
target match_set/semantic_diff/reopen·Native/Gate는 남는다. source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

## 서식 후보의 실제 splice 전달

CharacterStyle/TextStyle 분기의 제품 객체는 with_verified_splice_inventory로 실제 최종 patch 목록을
전달한다. 원 product binding과 현재 stored with_verified_bytes의 source/access/integrity/최종 head를
재사용한다. 원본 바이트 범위와 치환 지문, source/output·기존 receipt의 결속을 보관하며 fragment XML은
반환하지 않는다. 원 요청/receipt JSON과 공통 분류 표는 그대로다. 신규12+영향38=50pass는 이 목록과
기존 두 경로의 검증이며 operation compiler/route/실제 transaction 성공이 아니다.
[최종 splice 계약](p09-style-splice-inventory-v1.md)을 따른다.

## 실제 원본 operation compiler 연결

기존16개 스키마는 prepare_compiled_search_json 또는 준비된 후보의 compile로 같은 원본 graph와
원 SelectorSnapshot/OperationPlanCompiler에 결속된다. typed receipt의 실제 편집 anchor마다 가장
가까운 실제 구조 소유 node를 해석하며 소유 node를 편집 범위로 확대하지 않는다. 원 후보 이동·현재
접근·byte 전달·최종 head와 RouteUnqualified는 유지한다. 제품30+owner6 고유36개 구성요소 검증은
실제 route·저장/commit/CAS·영속 멱등 실행·Native/Gate 자격이 아니다.
[공통 compiler 계약](p09-source-search-operation-compiler-v1.md)을 따른다.

## 원본 계획의 실행 manifest 연결

준비된 compiled 후보는 원 CapabilityRouter와 ExecutionManifest::from_receipts로 연결된다.
원본 artifact/크기/SHA·revision·plan은 provider 후보에서만 가져오며 기존 source/security/최종 head와
원 RouteUnqualified는 유지한다. 같은 snapshot의 capability별 route 공유와 신규26개 검증은 실제
registry 신뢰·전체 source protection·실행/transaction/Native/Gate 자격이 아니다.
[원본 실행 manifest 계약](p09-source-search-execution-manifest-v1.md)을 따른다.
