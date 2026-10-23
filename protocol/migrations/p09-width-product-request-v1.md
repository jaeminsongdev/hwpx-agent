# 원본 일치 전각 반각 변환 제품 요청

`hwpx-agent.product-width-conversion-request/v1`은 현재 sealed 원본의 정확한 검색 일치를
전각 또는 반각 후보로 바꾸는 SEARCH-014 제품 준비 경로다. 기존 원본 compiler를 현재 저장
서비스와 엄격한 JSON 요청에 연결하며 실제 ingest/commit/CAS/실행은 열지 않는다.
제품 capability는 카탈로그의 `search.full_half_width`다.

## 요청 계약

기존 unique JSON/object parser의16KiB 상한과 네 selector 검증을 공유한다. envelope는
schema_version·idempotency_key·project/document·base_revision·head generation·source SHA·
plan_id·selector·operation을 요구한다. selector는 document/section/node_set/selection 중 하나며
원 revision·section 집합·정확한 NFC 좌표 창을 기존 규칙으로 검증한다.

operation은 kind=convert_width_matches·query·regex·case_sensitive·whole_word·max_matches·
mode·width_policy·run_policy·review_policy를 모두 요구한다. query는 비어 있지 않은4096bytes 이내,
max_matches는1..10000, mode는 fullwidth/halfwidth,
width_policy는 unicode17_width_pairs_with_kana_pairs,
run_policy는 first_original_run_retain_all_runs다. review_policy는 숨은 설명·메모 본문 포함
Boolean 두 개를 요구한다. 선택적 style_filter는 기존 선언/typed 정의 조건이며 생략과 null은
canonical 지문에서 같고 raw 지문에서는 구분한다.

미지·중복·escape 중복·잘못된 타입/값·불완전 조건은 원본 읽기 전에 거부한다. locale·자동
정규화·replacement·direction·대소문자 정책을 무시하지 않고 거부한다. 기존 문자/정규식/
정규화/대소문자 제품의 schema나 작업 의미는 넓히지 않으며 새 작업과 상호 거부한다.
범용 카탈로그의 전체 방향·서식 계약을 지원한다는 선언은 아니다.

## 저장 후보와 현재 권한

`hwpx-agent.stored-width-conversion-candidate/v1`은 현재 document.write·provider scope·head·
ACL·quarantine·AEAD와 전체 Form proof에서 한 원본 matcher/width compiler를 호출한다.
Borrowed/Owned owner를 기존 경계로 이동해 clone/reimport를 추가하지 않는다. 이후 verify/bytes는
검색·변환을 반복하지 않고 현재 접근/원본과 writer integrity를 확인한다. consumer 직전 최종
head 확인은 writer callback 안에 유지하며 최신 문서가 바뀌면 consumer를 호출하지 않는다.

원본/index/selector·검색/region/filter·mode/width/run/review 정책·Unicode17 대응표 원본 SHA·
폭226쌍/가타카나28쌍·raw/canonical/scoped·key/plan과 출력 지문을 결속한다.
일반 NFKC나 표시 폭 판정으로 바꾸지 않으며 원 run/서식·제어·참조·비변경 entity를 보존하는
[원본 정책](p09-source-width-conversion-v1.md)을 그대로 사용한다.

stored/product receipt와 key는 실행 권한이나 durable key claim이 아니다.
require_current_product_route는 현재 검증 뒤 RouteUnqualified를 반환한다. 실제 dispatcher·
저장 commit·원자적 CAS·멱등 실행·Native·게시는 별도 미완료 경계다.

## 제품 검증

components177은 Rust enum에 이전 작업명이 남은 것을 사전 정적 대조가 거부한 기록이며
Cargo/제품시험0이다. enum을 ConvertWidthMatches로 고친 한 변경만 역변환해 대조하고
다른 production·시험·fixture·보호를 유지했다. 원 실패177은 보존한다.

components178 신규제품24pass·688fresh/final688·진단/경고없음·cleanupTrue다.
두 모드·원본 폭/가타카나/서식·일치별 문맥·네 범위/clipped regex·선언/정의·casefold 검색/
whole-word·제외우선상한·review4정책/cache/metadata·제어/entity/참조 보존·strict/중복/16KiB/
null/legacy·지문·현재write/다섯 외부scope·ACL철회/복구/격리/AEAD·준비/확인/전달 최종head 경합·
borrowed/owned/JSON동등성·잘못된 source/head/revision/doc/project/index·NoMatches/NoChange/빈일치/
역상/보호/no-op·패턴/일치/source work/응답/writer 상한·비노출/닫힌route/source/head/ingest 보존·
128일치 공유map·2만 글자 단일patch·대응표 원본 결속과 폭 변환 외 정규화 금지를 확인했다.

원 두 root 모듈과 시험 parent는 선언 한 줄씩 제거로 전체 역변환했고 원본 compiler/표와
기존 제품·시험·fixture는 변경하지 않았다. source24·기존제품194·공식249는 반복하지 않았다.
짧은 module prefix로 argv를 줄였지만 실제 실행24개의 전체 이름·개수·상태를 정확히 대조했다.
기존194개가 같은 binary에 컴파일된 것과 실제 실행된 것은 구분한다.

전체138.422초·명령50.219초/시험12.04초·Job CPU48.109초·private최고1720.37MiB/5.3996%·
시스템CPU최고40.52%·가용RAM최저25.3686%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초와 Job active0/empty/handle closed 및
전후 입력 확인을 유지했다. 다른 앱·OS·Defender 변경이나 프리즈 해결·benchmark 주장은 없다.
근거는 implementation/p09/evidence의 p09-361-width-product-components177.v1.json과
p09-361-width-product-components178.v1.json이다.

## 남은 P09와 통합 계약

SEARCH-023의 별도 [공백 제어 편집 기반](p09-whitespace-atom-patch-v1.md)을 검증했다.
다음 접근허용 불필요 작업은 원본 정책·검색/selector·보호 compiler와 제어 변경 후 readback이다.
SEARCH-014의 전체 유효 서식·selector/filter/방향·보호·target match_set/semantic_diff/reopen,
dispatcher/DB/commit/CAS/멱등 실행/게시·Native는 미완료다. source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행과 기존 Native 재실행 금지도 유지한다.
