# 개인정보 형식 후보 탐지와 원본 선택

SEARCH-020의 읽기 전용 source 코어는 요청자가 명시한 형식 묶음을 실제 HWPX 원본에서 찾고,
원문을 노출하지 않는 위치·종류와 원본 선택 좌표를 반환한다. 현재 저장 서비스·엄격한 읽기 전용 제품
요청에도 연결했으며 한글 기본 개인정보 패턴이나 실제 개인정보 유효성을 판정한 결과는 아니다.

전체 카탈로그에서 실제 일치한 문자열을 가리는 source/저장 서비스는 별도 구현으로
[원본30·저장20 검증](P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md)을 완료했다. 이 결과는 탐지 결과 조회와
구분하며, 엄격한 변경 제품 요청·공통 변경 compiler·실제 저장/게시·Native 의미 검증은 남는다.

## 설치 개인정보 형식 카탈로그

별도 source reader는 실제 설치된 `PrivateInfo.ini`의 전체17020bytes·UTF16LE BOM과 SHA256
`fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434`를 결속한다.
총11section 중10종에64patterns가 있고 USERDEF는 비어 있다. 전화8·주민1·외국인1·이메일6·계좌35·
면허1·여권2·신용카드1·IP1·생일8을 원 순서/문자열 그대로 보존한다. ADDRESS를 임의로 추가하지 않는다.
선택한 종류의 모든 패턴을 한 결합 검색에 연결하며 기존 명시적 규칙 제품v1의16개/4096byte 상한은 바꾸지 않는다.
새 source 카탈로그는64KiB 입력·128패턴·개별4096byte·패턴합계64KiB·결합식128KiB와 기존 regex/DFA·
scalar/point/result 상한을 적용한다. 빈 USERDEF만 선택하면 가짜 빈 regex가 아닌 명시적 빈 결과를 반환한다.

382는 독립 parser가 빈 USERDEF를 찾아 빌드/시험 전 중단했다.383은 신규27+영향3이pass였으나
미사용 import 경고로 후속 review3 전 중단했다. 정확한 limit 오류 단언을 강화한384는 그1개와
미실행 review3만pass·이전29보존으로 고유33개를 확보했다.385는 Windows 설치 fixture4개를
`p09-installed-format-fixture` opt-in으로 분리하고, 기본 환경변수 없는1+실제 설치4만pass·이전28보존했다.
기본 시험은 설치 환경변수를 요구하지 않으며 명시적 fixture 모드에서 원본/환경변수가 없으면 실패한다.
시험을 ignore하거나 성공으로 건너뛰지 않는다.

[385](evidence/p09-361-personal-info-catalog-fixture-profile385.v1.json)는893fresh/final893·외부 config1final·
cleanupTrue·179.500초·시스템CPU최고48.76%·가용RAM최저34.1176%다. 신규 source27+영향6의 고유33개이며
33개 전체를 반복 실행한 결과가 아니다. 설치 파일과 private user INI는 변경하지 않았다.
원 IP 패턴의 unparenthesized alternation도 수정하지 않았으며 그 관측을 Native 동일성이나 실제 IP 유효성으로
표시하지 않는다. 전체 카탈로그의 현재 저장 provenance·엄격한 제품 선택과 실제 설치 파일 저장 통합 fixture는
아래 후속417에 연결했다. Native matching/target 검증은 남는다.
아래 현재 저장/제품v1은 명시적 사용자 규칙 경로이며 이 카탈로그 전체의 제품 연결 완료가 아니다.

## 전체 카탈로그의 현재 저장 연결

현재 저장 서비스는 전체 source 카탈로그와 선택한 종류의 모든 패턴을 원 sealed Result owner에 연결한다.
document.write·5종 provider scope·head/ACL/quarantine/AEAD·whole Form proof를 유지하고 한 review 인덱스와
결합 검색을 준비 시1회 사용한다. 전체 카탈로그 SHA/bytes/section/원본 순서와 선택·요청·결과 지문을
보관하며 기존 명시적16규칙 제품v1의 상한이나 의미는 바꾸지 않는다.

현재 카탈로그 source는 요청자가 지정하는 경로나 저장 영수증이 아니라 host dependency다. 고정 설치 경로의
readonly loader는64KiB를 초과해 읽지 않으며 private 사용자 INI를 읽지 않는다. 매 결과 조회·앞뒤 이동·
원본 선택에서 현재 문서와 전체 카탈로그 hash를 확인한다. JSON을 만든 뒤 카탈로그를 다시 읽고 consumer 직전
최종 head를 확인한다. verify/전달 시 regex 컴파일·review index·검색을 반복하지 않으며 원문/패턴을 출력하지 않는다.

[415](evidence/p09-361-personal-info-catalog-stored415.v1.json)는 신규 저장23+영향 탐지2 중24pass/1fail·
769fresh/final769·cleanupTrue다. 시험 helper의 ?가 거부될 원본 수입 오류를 단언 전에 전파한 실패를 보존했다.
해당 실패 시험만 오류 수집으로 고친 [416](evidence/p09-361-personal-info-catalog-stored-recovery416.v1.json)은
1pass·이전24보존의 현재 고유25개·771fresh/final771·진단/경고없음·cleanupTrue다. 제품 알고리즘과 통과한
24개 본문은 변경하지 않았으며 source33·공식249·이전 Native는 반복하지 않았다.

synthetic64패턴 전체의 provenance·source 동등성·현재/전달 직전 config 변경·읽기 실패/상한·write/5scope·
ACL 철회/복구·격리/AEAD·결과 이동/선택과 기존 마스킹 연결·빈 USERDEF·전체 응답 byte 경계·값 비노출·
원본/head/ingest 불변·준비/검증/metadata/이동/선택의5개 최종 head 경합을 확인했다. 설치 파일용 loader는
컴파일됐지만 이번 저장 시험은 실제 설치 파일이나 개인정보를 사용하지 않았다.

415 전체141.547초/명령43.766초·Job CPU41.828초/private1910.89MiB·시스템CPU최고18.22%·
가용RAM최저44.7540%다.416 전체102.063초/명령3.969초·Job CPU3.875초/private784.61MiB·
시스템CPU최고13.54%·가용RAM최저48.3289%다. 두 Job active0/empty/handle closed를 확인했다.
한 코어/BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%를 유지했고 프리즈 해결 판정은 아니다.

후속417은 전체 카탈로그의 엄격한 제품 요청/후속 요청 결속과 실제 설치 파일의 저장 통합 fixture를 확인했다.
Native matching/target·전체 옵션·실제 변경/저장/게시·신뢰 registry·P09 Gate는 남는다.
외부 CROSSREF 실행 입력은 수정하지 않았으며 사용자8종은 아직 NOT_RUN이다.

## 전체 카탈로그 제품 요청과 설치 source 통합 검증

별도 strict16KiB 요청은 전체 카탈로그 SHA와 중복 없는 형식 종류·원 revision/네 selector·명시적 review 정책을
받고 현재 저장 서비스로 연결한다. 경로/임의 패턴·승인·변경 필드는 받지 않는다. 별도 next/selection 요청을
raw/key/plan/provider·카탈로그/형식 선택·전체 결과 영수증에 결속하며 outer metadata 직렬화 뒤 current config와
최종 head를 검사한다. 기존 명시적16규칙 제품 경로와 저장 서비스의 기존 동작은 변경하지 않았다.

새 제품 코드와 합성33개·실제 설치 파일 opt-in1개·영향 저장2개 시험을 추가했다. 기본 fixture 환경변수 없는1개를
먼저 실행하고 명시적 feature에서 나머지32개/설치1개/영향2개만 실행해 모두 통과했다. 기본 시험은 설치 파일을
요구하지 않으며 opt-in에서 원본이 없거나 hash가 다르면 실패한다. 실제 설치 loader는 private 사용자 INI를 읽지 않는다.

[417](evidence/p09-361-personal-info-catalog-product417.v1.json)은36pass·775fresh/final775·설치 config1final·
진단/경고없음·cleanupTrue다. 실제17,020bytes 설치 파일의 전체64개와 전화8개 선택을 현재 저장/제품 경로에서
확인했다. 원본 SHA/bytes와 원 패턴 순서를 보존하며 Native/vendor authenticity는 false다.
이전416 결과를 새 제품 PASS로 올린 것이 아니라 새 제품 경로를 실행한 결과다. source33·저장25개 전체·
공식249·이전 Native는 반복하지 않았다. [검증기](../../tools/p09/run_personal_info_catalog_product.py)는 원 결과를 덮어쓰지 않는다.

전체141.984초·두 명령18.750/23.797초·Job CPU16.688/22.344초·private최고971.40MiB·
시스템CPU최고45.09%·가용RAM최저40.9500%와 두 Job active0/empty/handle closed를 확인했다.
한 코어/BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%를 유지했으며 프리즈 해결 판정은 아니다.
[전체 카탈로그 제품 계약](../../protocol/migrations/p09-personal-info-catalog-product-v1.md)을 따르며 Native/전체 옵션/Gate는 남는다.

## 현재 저장과 읽기 전용 제품 요청

현재 sealed Result·document.write·scope/head/ACL/quarantine/AEAD와 원본 whole Form proof를 유지한다.
원본 owner를 이동하고 review 인덱스·결합 형식 검색은 준비 시1회 사용한다. 보관 verify/metadata/결과 이동/
선택 전달은 현재 source 재구성·보관 결과 지문을 확인하되 regex/index/search를 반복하지 않는다.
전체 service/product 응답을 서버 byte 상한으로 제한하고 직렬화 뒤 consumer 직전 최종 head를 확인한다.

strict16KiB 탐지 요청은 rules/review_policy/max_results와 네 selector의 원본 revision을 요구한다.
변경/preview/승인/graph 필드는 원본 읽기 전에 거부하며 별도 next/selection 요청을 전체 product receipt에
결속한다. key/plan/raw/canonical/provider/정책/결과 지문이 다른 요청은 이전 cursor나 좌표 요청을 재사용하지 못한다.
선택 좌표는 현재 접근 후에만 전달하고 기존 마스킹에 넘겨도 source/보호 검사를 생략하지 않는다.

[378](evidence/p09-361-personal-info-detection-product378.v1.json)은 신규32+영향 기존 마스킹3=35pass·
881fresh/final881·진단/경고없음·cleanupTrue다. 직접 service/product 동등성·네 selector/review·범주/regex·
strict JSON/정확한16KiB/전체 응답 byte·규칙/서버 상한·값 비노출·현재 write/5scope/ACL 철회·복구/격리/AEAD·
결과 이동/선택 결속·원본/head/ingest 불변과 prepare/verify/metadata/next/selection 최종 head 경합5개를 확인했다.
이전 source23/제품 전체/공식249를 반복하지 않았다.

전체162.407초·명령45.020초·Job CPU42.891초·private최고1906.07MiB/5.98248%·시스템CPU최고41.07%·
가용RAM최저35.8555%와 Job active0/empty/handle closed를 확인했다. 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했고 프리즈 해결 증거는 아니다. 원 실패와 문서 감사375/376의
미완료 입력 확인은 [377 감사](evidence/p09-361-personal-info-detection-sync-final377.v1.json)에 보존돼 있으며 runtime 재실행으로 바꾸지 않는다.

제품 계약은 [읽기 전용 탐지 요청](../../protocol/migrations/p09-personal-info-detection-product-v1.md)을 따른다.
기본 형식 정책·전체 옵션·실제 변경/저장/게시·신뢰 registry·target/Native/Gate는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기를 유지한다. 아래377까지는 현재 저장/제품 연결 전 이력이다.

## 탐지와 선택 경계

기존 review/NFC 인덱스와 document/section/node/지문 결속 selection,hidden/MEMO 정책을 공유한다.
9종 의미 label과 custom 규칙은 literal/regex·case/whole_word를 명시한다. 규칙마다 원본을 다시 읽지 않고
결합 검색1회로 찾으며 겹침은 leftmost 후 규칙 순서로 결정한다. 보관 결과의 앞/뒤 이동·순환은 재검색하지 않는다.
부분 NFC 기여는 편집 선택을 만들지 못하고 정확한 선택도 기존 마스킹의 fresh source/보호/writer 검사를 생략하지 않는다.

metadata/Debug에는 원문·정규식·개인정보 값별 해시가 없다. 규칙16개·질의 합계/결합식4096byte ceiling과
기존 scalar/regex/일치/point/전체 응답 상한을 유지한다. 문서 전체 익명화나 실제 실행 권한은 없다.
공식 도움말과 exact target의 구분 및 정책은 [탐지 코어 계약](../../protocol/migrations/p09-source-personal-info-detection-v1.md)을 따른다.

## 실패 원본과 현재 결과

[373](evidence/p09-361-personal-info-detection373.v1.json)은 신규23+영향3 중25pass/1fail·873fresh/final873·cleanupTrue다.
실패는 필수 width/leader/type 없는 합성 tab가 Body 수입에서 거부된 것이며 탐지 결과 실패로 바꾸지 않았다.
원 수입 규칙과 탐지 알고리즘은 유지하고 tab fixture와 unused import만 수정했다.
[374](evidence/p09-361-personal-info-detection-recovery374.v1.json)는 실패1pass·이전25보존·875fresh/final875·진단/경고없음·cleanupTrue다.
현재 신규 탐지23+영향 기존3의 고유26개이며 단일26개 재실행이 아니다. 공식249와 이전 전체 mask/product는 반복하지 않았다.

범주는 synthetic marker로 검증했다. 실제 개인정보나 내장 패턴의 정확도 검증이 아니다. 원 run/entity/NFC 기여,
컨트롤/문단 경계,네 범위와 stale/foreign 거부,hidden/MEMO,규칙 순서와 flag/capture 격리,zero-width/상한,
값 비노출,결과 이동과 선택→기존 마스킹의 비선택 보존을 확인했다.

374 전체145.343초·명령28.550초·Job CPU26.812초·private최고1893.80MiB/5.94395%·시스템CPU최고74.76%·
가용RAM최저36.5547%다. Job active0/empty/handle closed와 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했다. 프리즈 원인 귀속이나 해결 증거는 아니다.
[이전 공통23 문서 감사372](evidence/p09-361-compiled-personal-info-mask-sync372.v1.json)는32fresh/final32·cleanupTrue이며 runtime을 반복하지 않았다.

## 원본 코어 당시의 다음 제품 연결

현재 sealed Result·document.write/scope/head/ACL/quarantine/AEAD와 최종 head 확인을 유지하는 저장 owner,
엄격한 읽기 전용 JSON 요청과 결과 이동·선택 전달이 다음이다. 기본 형식 정책·전체 옵션·실제 변경/저장/게시·
신뢰 registry·target/Native/Gate는 남는다. whole_package_personal_data_removed=false와
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3를 유지한다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기도 그대로다. 한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다.
