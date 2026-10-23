# 실제 원본에 결속한 검색 operation compiler

## 현재 공통 경로

현재 공통 표는 기존22개 순서 뒤에 개인정보 선택 마스킹 변경 후보를 추가한23개다. 실제 변경 text anchor
inventory와 source/output/전체 receipt SHA를 실제 구조 owner·12개 잠금 인자에 결속한다. 별도 preview는
원본 읽기 전 compiler 진입을 거부한다. 기존 폰트 v1/v2의15개 자원 인자와 다른22개 경로는 그대로다.
[마스킹 공통 계획 계약](p09-compiled-personal-info-mask-v1.md)은 고유32개 결과와 별도 독립 hash 검증,
보호 중단/실행기 실패를 보존한다. 아래는 문단 스타일 v2 연결 당시 이력이다.

문단 스타일 v2 연결 당시 공통 표는 기존21개 순서 뒤에 문단 스타일 이름 v2 변경 후보를 추가한22개다. 실제 문단 owner와
전체 filtered/unfiltered receipt를 기존12개 잠금 인자에 결속하며 미리보기는 원본 읽기 전에 거부한다.
[v2 제품과 공통 계약](p09-named-paragraph-style-product-v2.md)은 실제 원27개 통과와 후처리 실패/
재실행 없는 대조를 구분한다. 아래는 문단 이름 v1 연결 당시 이력이다.

문단 이름 v1 연결 당시 공통 표는 기존20개 순서 뒤에 문단 스타일 이름 변경 후보를 추가한21개다. 새 후보도 실제 문단
anchor/구조 owner와 전체 이름 질의 output receipt를 아래12개 잠금 인자에 결속하며 별도 미리보기는
원본 읽기 전에 compiler 진입을 거부한다. 신규19+영향12 검증과 남은 경계는
[문단 스타일 이름 제품 계약](p09-named-paragraph-style-product-v1.md)을 따른다. 아래는 폰트 연결 당시 이력이다.

폰트 연결 당시 공통 표는 기존19개 뒤에 폰트 v2 변경 후보를 추가한20개다. 기존18개는 아래12개 인자 계약을
유지하고 폰트 v1/v2만 실제 본문 owner와 두 헤더 자원·적용 profile의15개 인자를 사용한다.
[폰트 자원 계약](p09-compiled-font-resources-v1.md)은 body_splices와 전체 inventory 지문을 구분한다.
[v2 공통 계약](p09-font-options-product-v2.md)은 필터 전체 receipt의 계획 결속과 별도 SearchPreview를
정의하며 preview의 compiler 진입을 원본 읽기 전에 거부한다. 신규23+영향12개 검증은 준비·계획·
preview 범위이며 실제 실행/저장·신뢰된 registry·Native/Gate는 남는다.
이하 초기16종과 후속 연결의 원본 검증 이력을 보존한다.

## 이전 연결 기록

`hwpx-agent.product-source-search-operation-compiler/v1`은 공통 후보준비 dispatcher의 기존
16개 치환·변환 스키마를 같은 원본 graph와 기존 SelectorSnapshot·OperationPlanCompiler에 연결한다.
원본의 실제 편집 anchor와 실제 구조 소유 node를 함께 결속하며, 이 계획만으로 실행·저장 권한을 열지 않는다.

## 요청과 원본 후보

StoredProductRequest::prepare_compiled_search_json은 기존 엄격한 분류·파서·서버 한도를 사용한다.
Form/Formula 또는 미지원 스키마는 원본 읽기 전에 거부한다. 이미 준비한 PreparedStoredSearchMutation도
compile로 같은 경로를 사용한다. 기존16개 schema는 [공통 준비 계약](p09-common-search-mutation-dispatch.md)의
목록 그대로이며, 새 wire schema나 caller XML/임의 capability 입력은 추가하지 않았다.

각 원 제품 객체에서 불변 원본·기존 request identity를 빌리고 typed receipt를 직접 projection한다.
문자열·정규식·Unicode·대소문자·폭·공백·번호는 실제 변경 목록을 사용한다. TextControl은 개별 제어 수가
아닌 최종 span_changes를 사용한다. CharacterStyle/TextStyle은 중첩 overlay 병합 후 실제 final_splices와
기존 receipt SHA를 확인한다. 누락·중복·초과·비어 있는 편집 목록을 계획으로 인정하지 않는다.

원 후보와 source 소유자를 이동하며 원본 clone/reimport·검색·치환 재실행은 추가하지 않는다.
동일 source graph에서 실제 node anchor를 색인하고 선택된 XML part별 parent map을 한 번 구성한다.
각 편집 anchor를 원 SourcePackage에서 resolve해 가장 가까운 실제 구조 소유 node를 찾는다.
위조·다른 원본·모호/누락 owner·잘못된 subtree 범위는 거부한다. 원 graph admission은 중복 anchor를
DuplicateIdentifier로 먼저 거부한다. 임의 첫 문단·가상 document node·caller 제공 owner로 대체하지 않는다.

## 소유 문맥과 정확한 편집 범위

operation마다 원 실제 owner의 logical ID로 Selector를 구성하고 원 SelectorSnapshot의 expectation을
원 OperationPlanCompiler에 전달한다. owner는 문맥이며 전체 문단이나 개체를 다시 쓰라는 지시가 아니다.
원 후보 전체의 정확한 편집 목록과 요청 결속을 유지해야 하며 개별 operation을 다른 후보에 재사용할 수 없다.

필수 잠금 argument12개는 request_schema, source_package_sha256, output_package_sha256,
mutation_receipt_sha256, edit_inventory_sha256, raw_request_sha256, canonical_request_sha256,
scoped_request_sha256, source_anchor_json, source_edit_index, source_edit_domain,
owner_binding_profile이다. 마지막 profile은 actual_structural_owner_with_exact_source_edit/v1이다.
이 private catalog는 전체 제품 registry나 Native action catalog를 수정하지 않는다.

CompiledSearchReceipt는 source artifact/graph/package·revision/generation·plan·output·원 mutation
receipt·edit inventory·compiled plan·세 요청 지문과 operation/owner 수를 결속한다. 외부 생성자나
Deserialize가 없고 execution_authority는 false다. Debug는 원문/anchor/요청 내용을 출력하지 않는다.
compiled getter의 데이터는 실행 permit·게시 권한·멱등 key claim이 아니다.

## 현재 권한과 자원 한도

compile은 원 with_verified_bytes 안에서 현재 write/scope/head/ACL/quarantine/AEAD·원본/출력 integrity를
검사하고 compiler 직후 head도 확인한다. verify/with_verified_bytes는 보관한 plan/receipt integrity와
원 현재 접근을 다시 검사하되 원본 수입·owner map·snapshot·검색·compiler는 재실행하지 않는다.
byte 전달은 원 consumer 직전 최종 head 경로뿐이며 require_current_product_route는 fresh 검사 뒤
원 RouteUnqualified를 유지한다. 현재 write가 사라지거나 source/head가 바뀌면 이전 receipt로 우회하지 않는다.

최대4096개 편집·operation, argument12개/각2048byte·총8MiB, plan16MiB를 적용한다.
receipt/metadata는8MiB bounded streaming hash로 계산해 별도 대형 JSON 버퍼를 보관하지 않는다.
대상 graph의 원 불변 canonical SHA와 선택 part의 parent map을 공유한다.

## 실제 검증 범위

components213의 owner5pass/1fail, recovery214의 잘못된 parent/text anchor 동등성 기대 실패,
owner-admission215의 owner1pass·제품29pass/1fail은 원 실패 상태로 보존했다. 원 graph admission의
DuplicateIdentifier와 실제 anchor 포함 관계를 검사하도록 unit fixture만 수정했다. 마지막 제품 시험은
field cache를 포함한 본문 문단 전체 서식을 바꾸려다 FieldContent로 거부됐다. 기존 보호를 완화하지 않고
그 거부를 명시적으로 확인한 뒤 hidden/MEMO 문단을 대상으로 양성 서식 치환을 검사했다.

recovery216은 실패1개만pass·750fresh/final750·진단/경고없음·cleanupTrue다. 제품30+owner6=고유36개이며
현재36개 단일 실행이 아니다. 통과35개·이전50개·공식249를216에서 반복하지 않았다. 원16개 파서·접근·
전달·route 본문은 추가 getter/macro/분기 제거로 역변환했다. 시험은 모든16계열, 실제 다른 문단 owner,
hidden/MEMO·선택 창·정확한 anchor/12argument·지문·128편집·NoChange·현재write·외부5scope·ACL/
격리/AEAD·compiler 직후와 consumer 직전 head 경합·Control span 집계·번호 no-op subset을 포함한다.

216 전체109.578초·명령11.329초·시스템CPU최고21.48%·가용RAM최저27.3701%다. Job active0/empty/
handle closed와 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·
명령300초·guard600초를 유지했다. OS/Defender/다른 앱 변경이나 PC 프리즈 해결을 주장하지 않는다.
근거는 implementation/p09/evidence의 p09-361-source-search-operation-compiler-components213.v1.json,
p09-361-source-search-operation-compiler-recovery214.v1.json,
p09-361-source-search-owner-admission-recovery215.v1.json,
p09-361-source-search-review-compiler-recovery216.v1.json이다.

## 남은 실제 제품 경계

실제 target registry/route manifest·실행 dispatcher·ingest/commit/CAS·영속 멱등 실행·transport/게시와
전체 검색/참조·target match_set/semantic_diff/reopen·Native/Gate는 미완료다. source API v12는
incomplete/미해결4/report없음/exit3이며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·
P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

## 실제 원본 manifest 소비자

prepare_execution_manifest는 이 compiled 후보를 원 CapabilityRouter·ExecutionManifest::from_receipts에
연결한다. 원 provider 소유 source artifact/SHA/크기·revision·plan을 사용하며 현재 source/access와
routing 뒤 최종 head를 확인한다. capability별 같은 호출의 판정을 공유하고 다음 호출은 다시 판정한다.
신규26개 검증은 합성 routing evidence에 한정하며 실제 registry 신뢰나 원 RouteUnqualified를 바꾸지 않는다.
전체 source protection·실행/ingest/commit/CAS/영속 멱등/Native/Gate는 남는다.
[원본 실행 manifest 계약](p09-source-search-execution-manifest-v1.md)을 따른다.
