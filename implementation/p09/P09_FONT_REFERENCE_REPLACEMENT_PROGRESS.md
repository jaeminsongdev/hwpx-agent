# P09 원본 폰트 참조 치환 진행

## 폰트 v2 공통 계획과 비변경 미리보기

v2의 변경 전용 `PreparedStoredFontOptionsMutation`을 공통20번째 family로 연결했다. 기존19개
순서/준비/전달과 v2의 엄격한 파서·바인딩·현재 접근 검사는 유지했다. 준비와 바인딩 검사 본문은
공유하며 원본/후보 소유자를 이동한다. 추가 원본 수입·폰트 matcher/writer 반복은 없다.

preview_only=true는 별도 `SearchPreview`다. mutation 전용 요청과 compiler는 원본 읽기 전에
미리보기를 거부한다. 공통 미리보기는 JSON만 현재 권한/source·consumer 최종 head를 거쳐 전달하며
bytes/편집 inventory/compile/실행 manifest API가 없다. 변경 후보에 preview JSON을 요청해도 거부한다.
빈 출력이나 가짜 plan으로 preview를 변경 후보처럼 취급하지 않는다.

v2 계획은 기존 font resource validator와 실제 source owner를 재사용해 두 헤더 효과와 본문을
결속한다. 폰트 v1/v2만15개 잠금 인자이고 다른 기능은12개다. inventory는 원 v1 source receipt에
계속 결속하며, v2 mutation_receipt_sha256는 필터/정의 metadata를 포함한 전체 output receipt에
결속한다. 같은 출력/편집 inventory라도 조건이 다르면 계획 지문은 다르다.

335는 신규23+영향 공통6+영향 v2 제품6=35pass·779fresh/final779·진단/경고없음·cleanupTrue다.
두 모드·preview compile 사전 거부·실제 두 번째 owner/공유 자원·정의/text/NFC·전체 필터 지문·
서버 한도/현재 권한/변조·최종 head 경합5개를 확인했다. 기존108개 본문과 giant suite는 보존했고
두 기존 시험의 schema 개수/새 슬롯 기대만20으로 갱신했다. giant suite·공식249·원본24개는 실행하지 않았다.

전체133.906초·명령32.094초·Job CPU30.016초·private최고900.62MiB/2.8267%·
시스템CPU최고30.18%·가용RAM최저42.1103%다. Job active0/empty/handle closed와 원 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. PC 프리즈 해결이나 CPU 귀속 증거는 아니다.

남은 폰트/서식 옵션·유효 서식/fallback·전체 보호 의미와 신뢰 registry·실제 실행/저장/게시·Native/Gate는
미완료다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [공통 v2 신규23개와 영향12개](evidence/p09-361-compiled-font-options335.v1.json),
[v2 공통 및 미리보기 계약](../../protocol/migrations/p09-font-options-product-v2.md).
아래334까지는 v2 공통 연결 전 이력이다.

## 폰트 필터와 미리보기의 저장 및 제품 준비

현재 저장 서비스는 선택적 원본 style_filter를 기존 whole-source proof와 폰트 후보에 연결한다.
원본 소유자는 준비 후 이동하며 source clone이나 matcher/writer 재실행을 추가하지 않는다.
필터/inspection/정의와 원 후보 receipt를 별도 저장 receipt에 결속하고 현재 document.write·
scope/head/ACL/quarantine/AEAD 및 consumer 직전 head 검사를 유지한다.

엄격한 v2 JSON은 필수 preview_only와 선택적 style_filter를 받는다. 누락된 필터는 무필터 경로이고
명시적 null/배열/빈 조건·잘못된 축은 거부한다. v1은 새 옵션을 계속 거부하며 기존 저장/제품
알고리즘은 module 선언 외에 바꾸지 않았다. 원본 scalar 상한 max_changed_scalars 1..10000과 더 작은
서버 상한을 유지하며 카탈로그 max_replacements 100000 지원으로 바꾸지 않는다.

미리보기는 같은 후보 생성·writer/readback을 거친 뒤 출력 artifact를 버리고 원본 owner와 예측
메타데이터만 보관한다. 저장 preview 타입에는 bytes/inventory/compiler API가 없고 제품의 파일
요청은 PreviewOnly로 거부한다. 메타데이터는64KiB 한도이며 재전달마다 현재 원본/권한과 최종 head를
확인한다. idempotency key claim·ingest·CAS·게시나 빈 출력/가짜 plan을 만들지 않는다.

333은 신규28+영향 v1 제품4=32pass·774fresh/final774·진단/경고없음·cleanupTrue다.
필터/양 축·선택 창·무필터 v1 출력과 receipt 일치·미리보기 예측값/파일 거부·원본/head/ingest 불변·
엄격한 JSON/16KiB·요청/서버/writer 상한·현재 권한/변조·양 모드의 준비/verify/JSON 전달 마지막 head
경합6개를 확인했다. 기존80개 시험 본문은 보존했고 그중4개만 실행했다. 공식249·원본24개는 반복하지 않았다.

전체150.563초·명령49.891초·Job CPU47.766초·private최고1874.33MiB/5.8828%·
시스템CPU최고31.76%·가용RAM최저46.7797%다. Job active0/empty/handle closed와 원 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. PC 프리즈 해결이나 CPU 귀속 증거는 아니다.

다음은 v2 변경 후보의 공통 준비/계획과 별도 비변경 preview dispatch다. 전체 옵션·유효 서식/fallback·
신뢰된 registry·실제 실행/저장/게시·Native/Gate는 남는다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [저장 및 v2 제품32개](evidence/p09-361-font-options-product333.v1.json),
[v2 필터와 미리보기 계약](../../protocol/migrations/p09-font-options-product-v2.md).
아래332까지는 필터 저장/제품·미리보기 연결 전 이력이다.

## 원본 서식 조건으로 선택한 폰트 대체

별도 `SourceFontFilteredReplacementCandidate`는 선언된 run/text/문단 참조 또는 명시한 원본 정의값
조건을 폰트 선택에 결합한다. 기존 `SourceReviewStyleFilter`의 엄격한 판정기를 사용하며 빈 조건·
축 없는 정의값·미지/중복 JSON 필드는 거부한다. 숨은 cascade나 빠진 참조를 기본값으로 만들지 않는다.
기존 v1 후보·영수증과 엄격한 제품 요청은 바꾸지 않았으며 새 후보의 profile/hash에 필터·inspection·
정의 receipt·선택 수와 원본 후보 receipt를 함께 결속한다. 같은 출력이라도 조건이 다르면 새 hash는 다르다.

한 index에서 inspection을 만들고 정의 조건이면 정의를1회 결속한다. 판정은 원본 segment마다1회
캐시하며 NFC 단위의 모든 기여 원본이 만족할 때만 선택한다. 같은 원본이 수용 단위와 제외 단위에
동시에 기여하면 Selection으로 거부해 원본 scalar 일부를 서식 변경하지 않는다. 기존 필드·추적 보호,
비선택 보존·writer/readback·원본 scalar 상한은 그대로다. 원본 전체 보호·유효 서식/fallback은 미완료다.

331은 신규18+영향 v1 원본6=24pass·769fresh/final769·진단/경고없음·cleanupTrue다.
선언/정의 조건·두 서식 축·문단 조건·조건 결합·빈 조건 거부·NFC 합성/공유 원본·선택 창·추적 표시·
stale source·scalar 상한과 기존 v1 동일 선택의 원 receipt/출력 bytes/inventory 일치를 확인했다.
기존 원본20개 시험 본문은 그대로이며 그중 영향6개만 실행했다. 무관한 저장/제품 묶음·공식249는 반복하지 않았다.

전체133.719초·명령33.875초·Job CPU32.25초·private최고1855.82MiB/5.8248%·
시스템CPU최고35.55%·가용RAM최저35.8527%다. Job active0/empty/handle closed와 원 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. PC 프리즈 해결이나 CPU 인과 귀속 증거는 아니다.

다음은 필터의 현재 저장 서비스·엄격한 제품 JSON과 preview_only 연결이다. 이번 검증은 원본 core이며
제품 옵션 전체·신뢰된 registry·실제 실행/저장·Native/Gate는 미완료다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [원본 필터24개](evidence/p09-361-font-style-filter331.v1.json),
[필터 후보 계약](../../protocol/migrations/p09-filtered-font-source-v1.md).
아래330까지는 필터 연결 전 이력이다.

## 메모와 필드 및 추적 변경 보호

폰트 후보가 상위 run의 charTcId 또는 문단의 paraTcId를 상속하지 않던 누락을 수정했다.
328은 일반 본문·숨은 설명·MEMO 선택의3개 사례에서 실제 후보 반환을 확인한 FAILED 원본이며
763fresh/final763·수입 거부4pass를 보존한다. 각 실패는 첫 ID0에서 발생했으므로 수정 전 ID1 결과를
추정하지 않는다. 수정 후에는 각 part의 기존 parent map 순회에서 추적 표시를 하위 요소로 전파하고
선택된 text의 관측 표시가 있으면 이름 matcher·서식 복제·writer 전에 Protection으로 거부한다.
ID0은 unlocked Boolean으로 처리하지 않는다. 선택마다 부모를 재탐색하거나 XML을 다시 파싱하지 않는다.

326의9pass/7fail과327의14pass/6fail도 보존한다. scope helper는 빈 블록을 피하도록 수정했다.
현재 typed admission이 지원하지 않는 p.lock과 합성 중첩 DATE/MEMO 입력은 source/body/review 수입
거부로 구분했다. 이 거부를 정상 편집이나 nested-cache 의미 검증으로 승격하지 않는다.
유효한 기존 표/셀 fixture에서 table lock·cell protect·table size protect의 선택 거부와 비선택 보존을 별도로 확인했다.

329는 실패3+영향13+신규 text 축/공통 compiler4=20pass·765fresh/final765·진단/경고없음·cleanupTrue다.
앞서 수입 단계에서 확인한4개는 그대로 보존해 대표 review/field/protection 고유24개다.
24개 단일 실행이 아니며 기존56·공식249는 반복하지 않았다. MEMO의 editable=0 payload와 캐시를
구분하고 원 metadata/제어·캐시/비선택 서식 보존, 제외 정책·outer DATE 거부, 두 서식 축과 공통 계획의
추적 표시 거부를 확인했다. 표의 protect/lock 판정과 기존 source/field/patch/writer/readback/receipt는 유지했다.

329 전체143.11초·명령44.406초/시험7.22초·Job CPU42.547초·private최고1860.77MiB/5.8403%·
시스템CPU최고70.90%·가용RAM최저37.5717%다. Job active0/empty/handle closed와 원 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 시스템 표본은 소유 검증 Job의 CPU 비율이나
인과 귀속이 아니며 프리즈 해결을 주장하지 않는다. 이후에는 문서 감사만 수행했다.

다음은 style_filter/preview_only와 나머지 전체 옵션, 유효 서식/fallback·신뢰된 registry·실제 실행/저장이다.
관측한 보호 조합의 검증이지 전체 보호/추적 변경·Native 자격이 아니다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [원16개 묶음](evidence/p09-361-font-review-components326.v1.json),
[입력 수정과 표 보호](evidence/p09-361-font-review-fixture-recovery327.v1.json),
[수정 전 실제 후보 반환3개](evidence/p09-361-font-tracking-diagnostic328.v1.json),
[수정 후20개와 수입4개 보존](evidence/p09-361-font-tracking-recovery329.v1.json),
[관측 보호 계약](../../protocol/migrations/p09-font-review-tracking-guard-v1.md).
아래325까지는 이 상위 추적 표시 누락 수정 전 이력이다.

## 폰트 공통 준비와 계획 컴파일러

엄격한 폰트 요청을 공통 준비 표의19번째 family로 연결했다. 원 typed parser·receipt·현재 접근/
출력 전달·route 거부와 서버 한도를 재사용하며 원 source/candidate 소유권을 이동한다.
공통 계획은 실제 본문 splice의 원 anchor와 가장 가까운 실제 구조 소유자를 결속한다.
헤더 count/append는 본문이나 가상 node로 만들지 않고 필수 잠금 자원 인자2개와 적용 profile로 보관한다.
동일 inventory SHA 그룹의 두 헤더 효과는 후보 전체에1회 적용할 자원이며 개별 본문 operation마다
반복 실행할 편집이 아니다. 이 실제 실행기는 아직 연결하지 않았다.

폰트의 잠금 인자는15개, 기존18개 family는 원12개다. 인자별2048byte·총8MiB·plan16MiB와
원본 전체 편집4096개 상한을 유지한다. 헤더 인자는 작은 bounded 직렬화 후 공유하고 복제 전에
추가 인자 총량을 검사한다. 원 owner resolver·snapshot·컴파일/보관 검증·최종 head와 원 receipt는 유지했다.
caller가 header 인자나 승인 bits를 넣는 요청은 원본 읽기 전에 거부한다.

323은 과거 스키마 목록 시험이 직전 입력 원장에 없어 Cargo 전에 중단됐다.249의 정확한 과거
18종 시험 pin을 추가해 원 시험의 두 개수와 새 구성원 기대만 수정한 것을 역변환 대조했다.
production은323과 동일하다.324의 신규 폰트16+영향 기존4=20pass·753fresh/final753·진단/경고없음·
cleanupTrue다. 기존36·공식249는 반복하지 않았다. 별도의 width/style/regex/sort 네 기존 경로는
계속12개 인자로 컴파일한다. 과거 대형 시험 모듈 자체는 실행하지 않았다.

검증은 공통/독립 receipt·출력 동일성, 정확한 두 헤더 자원·15개 인자, 두 번째 문단의 실제 owner,
공유/별개 원형·NFC 선택·text 축·요청/plan 지문·비노출, 현재 write/foreign scope·ACL·격리/AEAD·
compiler/verify/consumer 직전 head 경합과 서버 검색/출력 한도를 포함한다.
전체120.562초·명령22.797초/시험10.00초·Job CPU21.234초·private최고894.05MiB/2.8061%·
시스템CPU최고25.57%·가용RAM최저40.2436%다. Job active0/empty/handle closed와 원 한 코어·
BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 프리즈 해결을 주장하지 않는다.

다음은 남은 전체 옵션/review·field·protection 조합과 신뢰된 registry/manifest·실제 실행/저장 연결이다.
전체 유효 서식/fallback·유효 폰트·Native도 남는다. RouteUnqualified·P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [원 입력 원장 중단](evidence/p09-361-compiled-font-components323.v1.json),
[공통 계획20개](evidence/p09-361-compiled-font-recovery324.v1.json),
[폰트 공통 계획 계약](../../protocol/migrations/p09-compiled-font-resources-v1.md).
아래322까지는 폰트 공통 계획 연결 전 이력이다.

## 폰트 헤더 자원과 본문 편집 목록

SourceFontEditInventory는 실제 헤더의 itemCnt 속성 치환과 마지막 기존 charPr 뒤 정의 추가를
본문의 최종 run/text Subtree splice와 구분한다. 모두 실제 원본 part/anchor·byte 범위·치환 SHA/
크기·fragment 수를 기록하며 헤더 원/출력 정의 수와 추가 수를 결속한다. 헤더를 본문 소유자나
임의 첫 문단으로 바꾸지 않는다. 기존 patch가 소비하는 최종 편집을 관측할 뿐 검색·렌더·patch/
writer/readback과 원 영수증 JSON은 바꾸지 않았다.

편집 수4096·목록8MiB 상한, 중복 anchor·범위 겹침 거부와 기존 compiled_edits_sha256 동일성을
검사한다. canonical hash는 별도 JSON 복제 없이 streaming으로 계산하며 fragment XML을 보관하지 않는다.
원본 후보의 불변 metadata와 현재 저장/제품의 with_verified_edit_inventory를 제공한다.
저장/제품 전달은 기존 현재 접근·원본 무결성·consumer 직전 head 검사를 공유하며 검색/치환을 반복하지 않는다.

319의 영향 원본9pass와 제품 시험 helper의 E0624 컴파일 실패/시험0을 보존했다. helper만 공개된
원본 byte 범위로 고쳤고 production은319와 동일하다.320은 신규12+영향 제품24=36pass·
745fresh/final745·진단/경고없음·cleanupTrue다. 원본9개를 반복하지 않았으며 고유45개 사례다.
단일45개 전체 실행이 아니고 이름/사전 거부 위주 원본11개·바이너리24·공식249는 반복하지 않았다.
실제 헤더 속성/추가 위치·원본 anchor·전체 편집 밖/치환 bytes·양 서식 축·부분/NFC/엔티티·
공유/별개 원형·원 catalog 보존·지문/비노출·borrowed/owned/core/제품 동일성·현재권한/격리/AEAD·
최종 metadata consumer head 경합을 확인했다.

320 전체115.36초·명령19.437초/시험13.94초·Job CPU17.438초·private최고735.09MiB/2.3072%·
시스템CPU최고27.44%·가용RAM최저41.0091%다.319 원본 명령30.656초/시험3.32초와 실패 제품 빌드를
포함한 private최고1861.88MiB/5.8438%·시스템CPU최고25.00%·가용RAM최저36.3992%도 보존한다.
두 실행의 모든 Job은 active0/empty/handle closed이며 기존 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했다. 프리즈 해결이나 실제 한글 성능을 증명하지 않는다.

다음은 이 헤더 자원 의존성과 실제 본문 소유자를 공통 operation compiler에 함께 결속하고
dispatcher에 연결하는 작업이다. 편집 목록은 CompiledOperationPlan이나 실행 자격이 아니다.
전체 옵션·풍부한 review/field/protection·cascade/fallback·실제 실행/저장/게시·Native는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.

근거: [원본9개와 helper 컴파일 실패](evidence/p09-361-font-edit-inventory319.v1.json),
[신규12개와 영향 제품24개](evidence/p09-361-font-edit-inventory-recovery320.v1.json),
[헤더와 본문 편집 목록 계약](../../protocol/migrations/p09-font-edit-inventory-v1.md).
아래318까지는 이 편집 목록 연결 전 이력이다.

## 현재 저장 서비스와 폰트 제품 요청

폰트 이름과 네 selector의 run/text 축 후보를 현재 저장 서비스와 별도 엄격한 제품 JSON에 연결했다.
document.write, provider scope, 현재 head와 원본 SHA, ACL·격리·AEAD와 whole-source proof를 확인한다.
보관 후보의 검증과 전달도 현재 접근을 다시 검사하며 consumer 바로 전 마지막 head를 확인한다.
후보 소유권은 이동하고 전달 시 폰트 검색·lowering을 반복하지 않는다.

요청은16KiB·중복/미지 키·필수 필드·enum 문자열·selector 형태를 검사한다. 요청의 최대 변경 scalar는
서버 검색 상한과 교집합을 취하며 query/replacement와 regex compiled/DFA의 더 낮은 서버 한도도 유지한다.
서버 query byte 초과는 원본 읽기 전에 거부한다. regex 문법/컴파일 한도는 권한 있는 원본 경로 안에서 검사한다.
style_filter/preview_only 등 미지원 옵션은 무시하지 않고 거부한다.

315는 시험 JSON 콜백 컴파일 실패/시험0과 불필요 import 경고를 보존했다. 시험의 콜백을 closure로
고치고 import를 제거했으며 두 축의 실제 출력 폰트 이름 검사를 강화했다. 제품 코드는315와 동일하다.
별도 독립 바이너리의316 신규24개는 모두pass·739fresh/final739·진단/경고없음·cleanupTrue다.
네 selector·부분 선택/공유 정의 보존·두 축의 실제 결과·borrowed/owned 동일성·JSON/요청 지문·
변경 수/regex/writer 한도·read-only/외부5scope·ACL 철회/재부여·격리·AEAD·prepare/verify/consumer
직전 head 경합·필드 캐시 거부·비노출/route 거부와 원본/head/ingest 불변을 확인했다.

전체107.782초·빌드 포함 명령12.969초/시험8.39초·Job CPU12.266초·private최고736.46MiB/2.3115%·
시스템CPU최고16.93%·가용RAM최저41.2961%다. Job active0/empty/handle closed와 원 한 코어·
BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 기존20/24와 공식249는 반복하지 않았다.
이 측정은 PC 프리즈 해결이나 실제 한글 성능을 증명하지 않는다.

다음은 실제 원본 편집 inventory와 공통 operation compiler/dispatcher 연결이다. 현재 경로는 독립
제품 준비 API이며 공통 실행 자격이 아니다. 풍부한 review/field/protection 조합·전체 옵션·cascade/
fallback·실제 저장/게시·유효 폰트/Native는 남는다. RouteUnqualified·P02 routing_allowed=false·
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

근거: [원 컴파일 실패](evidence/p09-361-stored-font-components315.v1.json),
[현재 저장과 제품24개](evidence/p09-361-stored-font-recovery316.v1.json),
[별도 폰트 제품 요청 계약](../../protocol/migrations/p09-stored-scoped-font-product-v1.md).
아래314까지는 현재 저장·제품 연결 전 이력이다.

## 폰트 이름과 선택 범위 치환

원본의 언어별 폰트 이름 query/replacement를 기존 네 selector 범위에 연결했다.
선택된 명시적 run/text 축에 필요한 charPr만 새 ID로 복제하고 부분 원문을 연결한다.
원래 공유 정의와 비선택 문단/글자, 모든 비폰트 서식·원문·제어·폰트 선언과 리소스는 보존한다.
출력 전체 typed catalog와 모든 원문 scalar/run/text 참조, 편집 밖 바이트와 compiled bytes를 재검증한다.

이름은 literal/유한 regex, case/whole-word와 명시적 언어 집합을 사용한다. 대상은 해당 언어의
정확하고 유일한 기존 선언이어야 하며 없거나 모호하면 거부한다. 명시된 축이 없거나 run 축에
text-style/해석되지 않은 ctrl 문맥이 있으면 우선순위·fallback을 추정하지 않는다.
별도 scoped-font/v11은 기존 v9/v10 어휘의 합집합이며 v1~v10과 기존 renderer/보호 알고리즘은 유지했다.
기존 코드 변경은 module 연결과 내부 재사용 가시성뿐이며 역변환으로 기존 본문 동일성을 확인했다.

310은 새 코드의 없는 오류 항목, 311은 PackagePath 직렬화 타입 오류로 컴파일 실패했다.
각각 기존 Selection 오류와 검증된 path 문자열로 고쳤다. 312는12pass/8fail이며 실패 원본을 보존했다.
fixture가 선택된 charPr의 실제 참조 대신 다른 font ID의 이름을 사용해 NoMatches가 난 것을 확인했다.
실제 서식의 폰트를 조회하고 두 원형 모두를 바꾸는 사례에는 명시적인 전체 이름 regex를 사용했다.
미일치 선택은 NoMatches로 유지하는 검사를 추가했고 writer 오류는 정확한 Writer 거부로 강화했다.
제품 코드는312와 동일하다. 313의 실패8+영향3=11pass와 무관 통과9개 보존으로 고유20개를 확인했다.
현재20개 전체 단일 실행이 아니며 기존24개·공식249는 반복하지 않았다.

313은731fresh/final731·진단없음·cleanupTrue·전체98.984초다. 빌드 포함 명령5.203초/시험3.71초·
Job CPU5.062초·private최고583.82MiB/1.8324%·시스템CPU최고21.80%·가용RAM최저43.9516%다.
Job active0/empty/handle closed와 원 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
PC 프리즈 해결이나 실제 한글 성능 향상 증거는 아니다.

다음은 현재 저장 권한/원본 경계와 엄격한 제품 입력에 연결하는 작업이다. 풍부한 review/field/protection
조합, style_filter/preview_only·전체 유효 cascade/fallback, operation compiler/실행/저장·게시,
실제 폰트와 Native match_set·semantic_diff·reopen은 남는다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.

근거: [원12pass/8fail](evidence/p09-361-scoped-font-path-recovery312.v1.json),
[실패8개와 영향3개](evidence/p09-361-scoped-font-fixture-recovery313.v1.json),
[이름·선택 범위 계약](../../protocol/migrations/p09-scoped-font-name-replacement-v1.md).
이하309까지는 이름·선택 범위 연결 전 이력이다.

## 바이너리 참조 결속과 보존

현재 원본 편집 기반은 신규10개와 영향받는 기존14개를 합한24개 시험을 통과했다.
이전 내장 폰트 실패는 원 shape/v6에서 미등록 참조 속성으로 거부되는 문제와 fixture에 실제
리소스가 없는 문제를 분리해 확인했다. 원 실패305는 그대로 보존하며 성공으로 재분류하지 않았다.

별도 `hwpml-2011-font-binary-static/v10`은 shape/v6에 header font/substFont의 binaryItemIDRef와
패키지 manifest item 연결만 추가한다. 기존 v1~v9 프로필·규칙·matching 본문은 역변환으로 동일성을 확인했다.
새 프로필은 text-style, chart, caption-owner 규칙이나 Native 자격을 추가하지 않는다.

현재 원본의 각 폰트·대체 폰트에 선언된 바이너리 참조는 실제 manifest/파트에 결속돼야 한다.
누락·빈 파트·XML 또는 text/* 미디어·spine/infrastructure 대상은 거부한다. 파트·수입 파트·manifest 색인은
각각 한 번 만들며 원본 그래프를 다시 수입하거나 참조마다 전체 파트를 순회하지 않는다.
출력은 기존 writer/readback을 거치고 모든 메타데이터와 바이너리 바이트를 보존한다.

원래 실패 양성 fixture에는 메모리 안에서 manifest item과 보존용 opaque 바이너리를 추가했다.
잘못된 선언만 있는 원 형태는 별도 거부 시험에서 유지한다. 해당 데이터는 유효한 실제 글꼴이 아니며,
설치·가용성·임베딩 활성화·라이선스·fallback/렌더를 검증하지 않았다. 공식 모델의 전체 substFont
속성을 지원한다는 증거도 아니며 원 typed reader의 허용 범위는 그대로다.

308은24pass·716fresh/final716·진단없음·cleanupTrue다. 전체123.906초, 빌드 포함 명령32.109초,
시험5.75초·Job CPU30.906초·private최고1807.71MiB/5.6738%다. 시스템CPU최고24.29%·
가용RAM최저41.9092%이며 Job active0/empty/handle closed를 확인했다.
기존 한 코어·BelowNormal·CPU cap6.25%·private hard8%/stop7%·RAM/commit95%를 유지했다.
검증 프로필이 바뀌어 기존14개를 영향 회귀로 실행했으며 공식249와 무관 시험은 반복하지 않았다.

다음은 폰트 이름 query/replacement와 선택 범위의 연결이다. 공유 글자 모양을 사용하는 비선택
영역을 바꾸지 않는 분리·재결속, fallback 정책, 현재 저장·엄격한 제품 요청과 실제 실행/저장,
match_set·semantic_diff·reopen/Native/Gate는 남는다. 공식158/249·잔여91·next165와
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.

근거: [현재24개 시험](evidence/p09-361-font-embedding-components308.v1.json),
[독립 ID 프로필과 리소스 계약](../../protocol/migrations/p09-font-binary-id-profile-v10.md).
이하307까지의 구현·검증 기록은 이전 상태다.

SEARCH-024 폰트 일괄 대체의 원본 편집 기반을 추가했다. 실제 원본의 언어별 폰트 선언 사이에서
글자 모양의 fontRef를 교체하고 결과를 재수입한다. 현재 고유 시험13개가 통과했고 내장 폰트
사례1개는 ID 검증에서 실패했다. 이름 검색, 선택 범위, 현재 저장 서비스와 전체 제품 연결은 남는다.

## 구현 범위

`ImportedDocumentFonts::lower_reference_replacement_candidate`는 같은 원본에 이미 선언된
같은 언어의 폰트 ID만 받는다. Hangul/Latin/Hanja/Japanese/Other/Symbol/User의 숫자 ID는
서로 다른 도메인이다. 매핑은 원본을 기준으로 동시에 적용하며 A→B와 B→C가 있어도 A를 C로 바꾸지 않는다.
중복·충돌 매핑, 자기 자신 치환, 없는 선언과 일치 없음은 구분해서 거부한다.

공유 글자 모양 정의를 바꾸므로 사용 중인 곳뿐 아니라 미사용 정의에도 적용한다. 이 경로는
SearchScopeSelector가 아니다. 선택 범위를 연결할 때는 선택 밖 사용에 영향을 주지 않도록
공유 정의의 복제와 선택된 참조 재결속이 필요하다.

변경 전 원본 전체 바이트를 불변 수입 객체의 원본과 비교한다. 기존 폼·필드·카탈로그 그래프를
다시 수입하지 않는다. 한 번의 기존 patch/writer와 출력 재수입으로 모든 언어의 참조 및 전체
글자 모양 카탈로그를 기대값과 비교한다. 원 폰트 정의와 편집한 속성 값 밖 바이트를 보존한다.

매핑은 최대128개, 변경 참조는 최대4096개이며 서버가 더 낮은 한도를 지정할 수 있다.
관측된 전역 보호 신호는 거부한다. 공유 정의가 잠긴 사용에도 영향을 줄 수 있어 관측된 로컬
잠금이 있는 경우도 이 전역 편집 경로에서는 거부한다. 신호 부재는 완전한 보호 해제 판정이 아니다.
현재 ACL/head·실행 자격·revision 저장 권한은 부여하지 않는다.

## 검증 결과

300은 문자열 참조 타입 오류로 컴파일 실패, 301은 fixture의 비공개 메서드 호출로 컴파일 실패했다.
제품의 참조 한 곳과 fixture의 공개 span 읽기만 각각 수정했다. 302에서는 fixture의 비연속 폰트 ID가
원 reader에 거부됐다. reader는 바꾸지 않고 선언 순서에 맞는 연속 ID와 실제 대상 조회로 fixture를 고쳤다.

303은12pass/2fail이다. 그중 한 실패는 매핑하지 않은 기존 참조도 바뀐다고 가정한 시험이었다.
304에서 원본의 각 참조에 매핑을 적용한 기대값과 보존값, 전체 변경 수를 대조하도록 고쳐 그1개만 통과했다.
고정 patch 오류 코드 전달 외에 제품 알고리즘은 같고, 다른13개 시험 본문은 보존했다.
고유13개 통과이며 현재14개 전체 단일 실행 PASS는 아니다. 통과12개와 공식249는 반복하지 않았다.

305는 남은 내장 폰트 사례1개만 진단 실행했고 `id_index_validation_failed`로 다시 실패했다.
실패를 통과나 지원 증거로 올리지 않았다. fixture의 binaryItemIDRef는 선언만 있고 실제 폰트 리소스가 없으며,
현재 shape/v6의 폰트 참조 규칙도 검토해야 한다. 유효한 내장 폰트와 대체 폰트 결속·보존은 미완료다.

304는710fresh/final710·진단없음·cleanupTrue, 전체117.859초·Job CPU26.094초·private최고1805.99MiB다.
시스템CPU최고26.33%·가용RAM최저39.9289%이며 Job active0/empty/handle closed를 확인했다.
305도 정상 정리됐고 Job CPU0.359초·private최고46.68MiB·시스템CPU최고12.77%다.
한 코어·BelowNormal·CPU cap6.25%·private hard8%/stop7%·RAM/commit95%를 유지했다.
PC 프리즈 원인이나 해결을 입증한 수치는 아니다.

## 다음 구현과 Gate

먼저 내장 폰트 사례의 ID 규칙과 실제 패키지 리소스 결속을 구분해서 조사한다. 유효한 원본과
실패 원본을 보존하고, 필요한 독립 프로필과 거부 시험을 검증한 뒤 실패 사례만 다시 확인한다.
이후 폰트 이름 query/replacement, fallback 정책, 선택 범위, 현재 저장·엄격한 제품 요청,
operation compiler/실행/저장 및 match_set·semantic_diff·reopen을 연결한다.

RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다. 한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다.

근거: [12pass와 원 실패](evidence/p09-361-font-reference-valid-ids303.v1.json),
[실패한 양성 사례1개 복구](evidence/p09-361-font-reference-followup304.v1.json),
[내장 폰트 실패 진단](evidence/p09-361-font-reference-followup305.v1.json).
