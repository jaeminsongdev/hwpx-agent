# 원본 일치 대소문자 변환 제품 요청

`hwpx-agent.product-case-conversion-request/v1`은 현재 sealed 원본의 정확한 검색 일치를
대문자 또는 소문자 후보로 바꾸는 SEARCH-013 제품 준비 경로다. 기존 원본 compiler를
현재 저장 서비스와 엄격한 JSON 요청에 연결하며 실제 ingest/commit/CAS/실행은 열지 않는다.
제품 capability는 카탈로그의 `search.case_convert`다.

## 요청 계약

기존 unique JSON/object parser의16KiB 상한과 네 selector 검증을 공유한다. envelope는
schema_version·idempotency_key·project/document·base_revision·head generation·source SHA·
plan_id·selector·operation을 요구한다. selector는 document/section/node_set/selection 중 하나이며
revision·section 집합·정확한 원 NFC 좌표 창을 기존 규칙으로 검증한다.

operation은 kind=convert_case_matches·query·regex·case_sensitive·whole_word·max_matches·
mode·case_policy·review_policy를 모두 요구한다. query는 비어 있지 않은4096bytes 이내,
max_matches는1..10000, mode는 uppercase/lowercase,
case_policy는 unicode_default_each_matched_text_group이다. review_policy는 숨은 설명·메모
본문 포함 Boolean 두 개를 요구한다. 선택적 style_filter는 기존 선언/typed 정의 조건이며
생략과 null은 canonical 지문에서 같고 raw 지문에서는 구분한다.

미지·중복·escape 중복·잘못된 타입/값·불완전 조건은 원본 읽기 전에 거부한다. locale·titlecase·
자동 정규화·replacement·run_policy·direction을 무시하지 않고 거부한다. 기존 문자/정규식/
정규화 제품의 schema나 작업 의미는 넓히지 않으며 새 작업과 상호 거부한다. 범용 카탈로그의
전체 방향·서식 계약을 지원한다는 선언이 아니다.

## 저장 후보와 현재 권한

`hwpx-agent.stored-case-conversion-candidate/v1`은 현재 document.write·provider scope·head·
ACL·quarantine·AEAD와 전체 Form proof에서 한 원본 matcher/case compiler를 호출한다.
Borrowed/Owned owner를 기존 경계로 이동해 clone/reimport를 추가하지 않는다. 이후 verify/bytes는
질의·변환을 반복하지 않고 현재 접근/원본과 writer integrity를 확인한다. consumer 직전 최종
head 확인은 writer callback 안에 유지하며 최신 문서가 바뀌면 consumer를 호출하지 않는다.

원본/index/selector·검색/region/filter·Unicode17 mode/policy·raw/canonical/scoped·key/plan과
출력 지문을 결속한다. locale/titlecase/casefold/자동 정규화는 하지 않으며 한글 동등성도 부여하지
않는다. 원 text atom의 서식·제어·참조·변하지 않은 entity를 보존하는
[원본 정책](p09-source-case-conversion-v1.md)을 그대로 사용한다.

stored/product receipt와 key는 실행 권한이나 durable key claim이 아니다.
require_current_product_route는 현재 검증 뒤 RouteUnqualified를 반환한다. 실제 dispatcher·
저장 commit·원자적 CAS·멱등 실행·Native·게시는 별도 미완료 경계다.

## 제품 검증

components173은 신규제품22pass·676fresh/final676·진단/경고없음·cleanupTrue다. upper/lower·
확장·문맥 Sigma/선택 경계·네 범위·clipped regex·선언/정의·casefold 검색/whole-word와 제외우선상한·
review4정책/cache/metadata·제어/entity/참조/서식 보존·strict/중복/16KiB/null/legacy·지문·현재write/
다섯 외부scope·ACL철회/복구/격리/AEAD·준비/확인/전달 최종head 경합·borrowed/owned/JSON동등성·
잘못된 source/head/revision/doc/project/index·NoMatches/NoChange/빈일치/역상/보호/no-op·패턴/일치/
확장/응답/writer 상한·비노출·닫힌route·source/head/ingest 보존·128일치 공유map·2만 글자 단일patch를 확인했다.

원 두 root 모듈과 시험 parent는 선언 한 줄씩 제거로 전체 역변환했고 source compiler와 기존
제품·시험·fixture는 변경하지 않았다. source64·기존제품172·공식249는 반복하지 않았다.
기존 시험이 같은 binary에 컴파일된 것과 실제 실행된 것은 구분한다.

전체133.891초·명령47.687초/시험11.79초·Job CPU45.719초·private최고1716.68MiB/5.3880%·
시스템CPU최고40.82%·가용RAM최저24.6525%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초와 Job active0/empty/handle closed 및
전후 입력 확인을 유지했다. 다른 앱·OS·Defender 변경이나 프리즈 해결·benchmark 주장은 없다.
근거는 implementation/p09/evidence/p09-361-case-product-components173.v1.json이다.

## 남은 P09와 통합 계약

SEARCH-014의 전각·반각 원본 compiler는 [별도 프로필](p09-source-width-conversion-v1.md)로 검증했다.
그 변환의 현재 저장 서비스·엄격한 제품 JSON은 [폭 변환 제품 프로필](p09-width-product-request-v1.md)로 연결했다.
다음 접근허용 불필요 작업은 SEARCH-023 공백·탭·줄바꿈 정규화 정책과 원본 compiler다.
SEARCH-013의 전체 유효 서식·selector/filter/방향·보호·target match_set/semantic_diff/reopen,
dispatcher/DB/commit/CAS/멱등 실행/게시·Native는 미완료다. source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행과 기존 Native 재실행 금지도 유지한다.
