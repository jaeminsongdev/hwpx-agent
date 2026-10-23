# P09 원본 검색 인덱스 구현 현황

공통 definition matcher의 큰 조건 전달을 참조로 바꾸고, 한 작업 안에서 마지막 선택 정의 쌍만 재사용하도록 최적화했다.
추가한 캐시는 heap·전역·문서별 테이블 없이 같은 쌍의20,000회 호출에서 실제 비교2회였으며 다른 축·부재/ID0·NFC·새 요청/원본을 구분한다.
[502](evidence/p09-361-style-predicate502.v1.json)은500의 원19개 본문을 보존하고 새 review1·미실행 제품5를 확인했다.
현재25개·854fresh/final854·compiler dep-info2final·cleanupTrue다.500의 fixture 경고와501의 시험 helper E0603은 보존했다.
최종502의 CPU최고26.67%·가용RAM최저37.825%·보호 중단없음이며 실제 글꼴 선언 조건 연결·전체 유효서식·Gate는 남는다.

글자·문단이 실제 참조하는 테두리 정의의 선·굵기·색·대각선·채우기 조건을 기존 v3/v4/v7/v9 제품에 연결했다.
원 P05 판독 결과의 조밀한 ID를 직접 조회하고 검색 위치별 XML/ZIP 재판독은 하지 않는다.
[498](evidence/p09-361-border-definition498.v1.json)의 잘못된 중첩 요청 거부 실패를 보존하고 absent 변형을 수정했다.
[499](evidence/p09-361-border-definition499.v1.json)은 원본8·신규제품5·영향회귀4의17개,
824fresh/final824·compiler dep-info2final·cleanupTrue다. CPU최고38.02%·가용RAM최저35.323%·보호 중단없음이다.
상세 계약은 [참조된 테두리 정의 검색](../../protocol/migrations/p09-border-definition-search-v1.md)을 따른다.
공식158/249·Native/003·전체 유효 서식·P09 Gate를 완료한 결과는 아니다.

새 글자24/문단27 조건의 명시적 v3/v4·네 범위 v7 제품 연결도 마감했다.
공통 v1~v4 요청의 정규형16KiB 검사를 원본 접근 전으로 옮겼고, 한도와 기존 source/result 확인은 유지한다.
[496](evidence/p09-361-detail-axes496.v1.json)의10개 본문 통과 뒤 fixture 경고 중단을 보존했으며,
[497](evidence/p09-361-detail-axes-recovery497.v1.json)은 원9개를 반복하지 않고 독립 AEAD 보호를 보완한1개만 실행했다.
현재10개·809fresh/final809·compiler dep-info1final·cleanupTrue다.495의36개·공식249·Native는 반복하지 않았다.
상세 축·범위·거부 계약은 [명시적 세부 조건 제품](../../protocol/migrations/p09-detail-definition-product-v1.md)을 따른다.

문단 모양의 선택적 세부 조건27개도 기존 definition matcher와 strict v9 저장 제품에 연결했다.
들여쓰기/여백/줄 간격의 값·단위, 제목의 direct/meta_tag와 current/fallback 선언을 구분하고 표시 우선순위는 추정하지 않는다.
[495](evidence/p09-361-paragraph-detail495.v1.json)는 신규 core8·제품6+직접 영향22의36개,
798fresh/final798·실제 compiler dep-info2final·cleanupTrue다. 기존 통과 검사기 빌드·공식249·Native는 반복하지 않았다.
전체 유효 cascade/가시성·실제 실행/저장/Native/Gate는 미완료이며 공식158/249를 변경하지 않는다.
상세 조건은 [문단 모양 세부 조건](../../protocol/migrations/p09-paragraph-detail-search-v1.md)을 따른다.

글자 모양의 선택적 세부 조건24개를 기존 typed 원본 catalog와 strict v9 저장 제품에 연결했다.
밑줄/취소선/윤곽/그림자/강조/색/테두리/효과 및 언어별 font ID·장평·자간·상대 크기·위치를 비교한다.
기존 요청 bytes/해시와 요구 축 미해결 거부를 유지하며 실제 설치 글꼴/대체/유효 cascade는 해석하지 않는다.
[482](evidence/p09-361-character-detail-focused482.v1.json)의 신규 제품5+영향20·883fresh/final883·cleanupTrue로 수용한다.
481의 발행 실패와 core43개 미수용은 보존했다. 원 fixture/시험 본문을 유지한 전용 호스트에서 명령21.860초·private753.49MiB였다.
상세 계약은 [글자 모양 세부 조건](../../protocol/migrations/p09-character-detail-search-v1.md)을 따른다.

실제 HWPX에서 읽은 문단을 대상으로 NFC 검색 인덱스와 문자열·정규식 검색을 구현했다.
명시적 원본 범위와 인증된 저장 서비스의 엄격한 제품 요청도 연결했다.
원본에 명시된 서식 참조와 구조 컨트롤을 찾는 v2 제품 요청도 연결했다.
v3에서는 원래 typed header 정의에 참조를 결속하고 실제 정의값 조건으로 검색한다.
v4에서는 실제 숨은 설명·MEMO 본문의 포함/제외를 명시해 검색하고 검색 범위를 결과에 기록한다.
보관 결과에 결속한 다시 찾기 요청은 기존 질의를 반복하지 않고 앞/뒤 이동·순환을 처리한다.
네 selector 범위의 v5/v6 Find 결과도 같은 next 요청으로 이동하며 inventory는 이동 대상이 아니다.
네 범위와 review 정책의 서식 결합은 core와 현재 저장/엄격한 v7 제품 요청 및 cursor까지 연결했다.
컨트롤의 네 범위는 실제 원본 시작 위치를 사용하는 core와 현재 저장/엄격한 v8 제품 요청·region cursor까지 연결했다.
정규식 캡처·템플릿의 일치별 원 atom 치환은 현재 저장/엄격한 regex 제품 JSON까지 연결했다.
별도 source v2의 정확한 빈 일치 삽입도 현재 저장/필수 삽입 정책을 받는 엄격한 regex 제품 v2까지 연결했다.
원본 서식 검색을 사용하는 부분 run 글자 모양 치환은 core와 현재 저장/엄격한 제품 JSON까지 연결했다. 다른 서식 축은 남는다.
text-style 참조만 교체하고 원 run을 유지하는 별도 core와 현재 저장/엄격한 제품 JSON 연결도 통과했다.
문단 모양/이름 있는 문단 스타일의 두 원본 참조 축도 core와 현재 저장/엄격한 v1 제품 JSON 연결을 통과했다.
별도 직접 서식 해석 core/현재 저장/v9 제품과 next는 선택 범위의 요청 축이 미해결이면 검색 전에 오류로 반환한다. 전체 유효 cascade/숨김은 남는다.
상위 ctrl의 미해석 text-style 문맥도 segment 단위로 결속하며 styled MEMO의 기존 원본 admission 거부는 유지한다.
별도 SEARCH-022는 네 정규화 형태로 실제 원본 글자를 변환하며 변경 최소 성분만 편집한다. 현재 저장/엄격한 선택 범위 v1과 검색어·명시적 서식 일치 v2 제품까지 연결했으며 전체 통합/target 계약은 남는다.
검색과 원본 치환·변환의 위 경로들은 전체 제품 계약의 완료가 아니다.
최신 저장 연결은 review 본문을 포함하는 네 selector 범위의 검색과 문자열/정규식/부분 run 글자 모양/text-style/문단 참조 치환까지다.
최신 제품 연결은 review 범위 검색 v6·서식 v7·컨트롤 v8·직접 서식 해석 v9, selector 문자열 치환 v4와 별도 regex 치환 v1/v2 및 character-style/text-style/paragraph-style 치환 v1의 엄격한 JSON 요청이다.
선택 범위 Unicode 정규화 v1은 필수 형태/run/review 정책으로 현재 저장 원본에 연결하며 미지원 query/filter는 거부한다.
별도 Unicode v2는 literal/regex·선택적 선언/정의 서식 필터·일치 상한을 원본 일치 정규화와 현재 저장 경계에 결속한다.
SEARCH-013은 명시적 기본 대소문자 변환의 source core 고유64개와 현재 저장·엄격한 제품 JSON 신규22개를 확인했다. 전체 통합/target 계약은 남는다.
SEARCH-014는 Unicode17 폭 대응226쌍·가타카나28쌍, 원본 신규24개와 현재 저장·엄격한 제품 JSON 신규24개를 확인했다. 전체 통합/target 계약은 남는다.
SEARCH-023은 공백·구조적 탭/줄바꿈의 별도 typed patch 고유43개·원본 정규화24개·현재 저장/엄격한 제품24개를 확인했다. 전체 통합/target 계약은 남는다.
SEARCH-009는 Tab/LineBreak 치환의 typed patch18개·원본24+영향12개와 현재 저장/엄격한 제품24개를 확인했다. 다른 제어 종류·카탈로그 query/replacement·실제 실행/저장 계약은 남는다.
별도 AutoNumber/NewNumber source 경로는 실제 review 결속 입력/공유 출력 수입의67개와 현재 저장/엄격한 제품 JSON 신규26개를 확인했다. 실제 저장/전체 실행 계약은 남는다.
공식 시험은 158/249 수용, 잔여 91개, 다음 case165이고 P09/A12/A13은 OPEN이다.
기존 치환·변환16개 스키마는 아래 공통 후보준비 dispatcher에도 연결했다. 실제 저장 트랜잭션과 실행 자격은 별도다.

## 검색 범위와 원본 위치

`ImportedDocumentStructure::source_text_index`는 입력 전체를 원래 source 검증 경로로 확인한 뒤
이미 읽은 XML과 graph의 원본 문단 anchor를 사용한다. 일반 본문과 매핑된 표·그림·각주·미주
문단을 수집하며 별도 ZIP/XML 재수입을 검색 건수만큼 반복하지 않는다.

텍스트 run 사이는 연결하지만 문단, 필드 제어, 기타 컨트롤과 미해석 영역은 경계로 분리한다.
기본 인덱스와 구분되는 v4 보조 본문 범위는 아래 명시적 파일 본문 정책을 따른다.
매핑되지 않은 XML 문단은 제외하고 개수를 기록한다. 따라서 전체 문서의 숨김 상태·실제 쪽 순서나
전체 텍스트 검색을 보장하지 않는다. 정규식의 시작·끝은 각 검색 블록 기준이다.

NFC의 분해·결합·재정렬 후에도 원본 text anchor, atom, 디코딩된 Unicode scalar 위치를 보존한다.
이 위치는 원본 XML byte/UTF-8 offset이 아니다. 한 원본 scalar의 일부 정규화 결과만 선택하면
정확한 원본 선택으로 표시하지 않는다. 재정렬 때문에 선택 조각이 떨어져 있을 수도 있으므로
`source_scalar_selection_exact`는 연속 편집 범위나 쓰기 권한을 뜻하지 않는다.

문자열 검색어만 NFC로 정규화한다. 정규식 문법과 escape는 그대로 유지하고 NFC 본문에서 실행한다.
대소문자 무시는 regex의 Unicode simple case folding, whole word는 Unicode word boundary를 사용한다.
한글의 실제 찾기 동작과 동등하다고 간주하지 않는다. 결과는 왼쪽 우선 비중첩이며 빈 일치도
유한한 위치 결과로 반환하되 편집 가능한 원본 범위를 만들어내지 않는다.

## 자원 상한과 검증 결과

기본 상한은 원본 scalar 250,000개, 전체 분해 scalar 1,000,000개, 검색어 4,096 bytes,
일치 10,000개, 보고 원본 point 250,000개, 응답 4 MiB이다. 문단·블록·텍스트 요소와
정규식 컴파일·DFA 메모리에도 별도 상한이 있다. 초과 시 잘라낸 성공 결과 대신 오류를 반환한다.
정규화 결과는 라이브러리의 독립 streaming NFC 결과와 대조하고 실제 Unicode 버전을 receipt에 넣는다.
UTF-8 offset 표를 한 번 만들고 이진 탐색하므로 일치마다 앞부분을 다시 세지 않는다.
결과 크기 검사는 복사본 JSON을 만들지 않는 계수 writer를 사용한다.

`p09-361-source-search-components042.v1.json`에서 23개가 통과했다. 나머지 1개는 단일 문자
최적화 경로에도 컴파일 한도 오류를 기대한 시험이었다. 실제 컴파일 공간을 요구하는 문자 클래스·반복
패턴으로 바꾸고, production 및 다른 입력 일치와 시험 파일 전체 역변환을 확인했다.
`p09-361-source-search-recovery043.v1.json`에서 그 1개만 통과했고 기존 23개는 재실행하지 않았다.
복구 입력은 439 fresh/final439, diagnostics 없음, cleanup True이다. 앞선 040/041 컴파일 실패와
042의 실패 상태는 그대로 보존한다.

복구 전체 시간은 57.766초, 시험 본체는 0.01초였다. 시스템 CPU 최고 표본은 18.15%,
가용 RAM 최저는 21.8759%였고 한 코어·BelowNormal·Job CPU cap 6.25%·RAM/commit 95%를 유지했다.
이 수치는 성능 벤치마크나 PC 프리즈 해결 증거가 아니다.

## 명시적 범위와 인증된 제품 요청

`find_scoped`는 매핑된 원본 전체 또는 원본 paragraph handle 집합을 먼저 확인한다.
중복·빈 선택·외부/미매핑 handle은 일치가 없어도 거부한다. 선택 순서는 집합으로 정규화하되
전체 범위와 명시적 문단 집합은 서로 다른 scope digest로 결속한다. 결과는 선택한 문단/블록 수와
부분 coverage를 표시하며 기존 전역 block 위치를 유지한다. 범위 wrapper도 응답 byte 상한에 포함한다.

`StoredSourceSearchProductRequest::prepare_json`은 별도
`hwpx-agent.product-source-search-request/v1` 요청에서 sealed current Result만 읽는다.
원본 graph/파일 경로/승인 bits는 받지 않는다. 요청에는 project/document/revision/head/source SHA,
key/plan, 명시적 scope와 문자열·정규식 operation이 필요하다. 16 KiB 한도, 중복/미지 필드,
배열 envelope와 operation/scope, 부적합 값은 원본 읽기 전에 거부한다.
`include_hidden`/`style_filter`/`regex`는 이 제한된 요청 스키마에서 허용되지 않으며
정규식 여부는 operation kind로만 정한다. 전체 검색 계약을 지원하는 척하면서 옵션을 무시하지 않는다.

읽기 전용 검색에도 카탈로그의 document.write를 요구한다. 원래 scope/head/ACL/quarantine/AEAD와
전체 Form 재구성을 유지하고 동일 호출의 proof로 검색 인덱스를 만들어 두 번째 원본 재수입을 피한다.
보관한 결과의 verify/전달은 현재 접근과 원본/head를 다시 확인하지만 검색 질의 자체는 반복하지 않는다.
결과 JSON 전달 직전에 마지막 head를 확인하며, 무검사 match/bytes 접근자는 추가하지 않았다.
이 확인은 원자적 CAS나 반환 이후 권한 철회 시 이미 전달한 자료의 회수를 뜻하지 않는다.

`p09-361-scoped-search-product-components045.v1.json`에서 신규 범위 6개, 영향 기존 검색 24개,
신규 제품 9개, 총 39개가 통과했다. 기존 검색 시험 본문은 그대로이며 범위 분기 변경의 회귀만
검증했다. 무관한 저장 시험 286개와 공식 대기열은 실행하지 않았다. 제품 시험은 문자열/정규식과
문단 선택, 엄격한 JSON/정확한 16 KiB 경계, key/plan/query/scope 결속, 읽기 scope 거부,
타 provider 5개 scope, ACL 철회/복구·격리·AEAD 변조와 prepare/verify/최종 전달 head 경합을 확인했다.
전체 444 fresh/final444, diagnostics 없음, cleanup True다.

전체 158.250초 중 핵심 명령은 22.906초, 제품 명령은 78.375초였고 시험 본체는
0.14+0.05+0.51초였다. 시스템 CPU 최고 54.05%, 가용 RAM 최저 20.8380%였으며
모든 소유 Job은 active0/empty/handle closed다. 기존 자원 보호와 입력 확인을 유지했다.

## 명시된 서식 참조와 구조 컨트롤

`SourceInspectionIndex`는 기존 원본 인덱스의 anchor와 XML을 재사용한다. 서식 조건은
`paragraph_property`, `paragraph_style`, `run_character_property`, `text_character_style`의
명시된 u32 참조만 비교한다. 빠진 값은 0이나 기본 서식으로 만들지 않는다. NFC 일치에 기여한
모든 원본 scalar가 조건을 만족해야 하며, 원본 글자가 없는 빈 일치는 서식 일치로 표시하지 않는다.
조건 불일치 후보는 결과 수/보고 point 상한을 소모하지 않지만 실제 허용 결과 초과는 오류다.

컨트롤은 고정된 enum과 부모 위치로만 분류한다. 캐시의 공식 모델 `runType.cpp`·`ctrl.cpp`·`t.cpp`
태그 집합과 Run 28·Control 15·Text 14, 총 57개 부모/태그 조합을 대조했다.
원본에 직접 있는 알려진 text 조판 부호는 텍스트 reader가 해당 t를 opaque로 남겨도 찾을 수 있다.
미지/외부 wrapper 안이나 매핑되지 않은 문단에는 내려가지 않고, 다른 부모 위치의 같은 태그도 제외한다.
컨트롤의 원본 paragraph/control anchor를 반환하되 태그 존재가 매개변수·동작·ID 무결성 검증은 아니다.

새 요청 `hwpx-agent.product-source-search-request/v2`에 `find_declared_style`과 `find_control`을 추가했다.
앞의 작업은 비어 있지 않은 엄격한 `style_filter`를 요구한다. 뒤의 query는 닫힌 control-kind enum이며
raw QName/action은 거부하고 case_sensitive=true·whole_word=false만 허용한다. 기존 v1은 새 작업과
style_filter를 계속 거부한다. 배열/null filter·미지/중복 키·부적합/무관한 옵션도 읽기 전에 거부한다.
private 결과 enum으로 기존 저장 결과의 현재 ACL/source/head 검사와 최종 전달을 공유한다.

`p09-361-search-inspection-components048.v1.json`은 신규 core 9개+영향 core 30개+신규 제품 5개+
영향 v1 제품 9개, 총 53개 PASS, 449 fresh/final449, diagnostics 없음, cleanup True다.
기존 39개 시험 본문은 그대로이며 변경된 matcher/서비스/요청에 해당하는 회귀만 실행했다.
무관한 저장 286개와 공식 대기열은 실행하지 않았다. 047은 새 사례 앞 구분 빈 줄이 원본 역변환에
포함된 사전 대조 실패이며 Cargo/시험 실행은 0이었다. 048은 그 추가 구분 줄 하나만 분리해
기존 파일 prefix의 정확한 지문 일치를 확인했고 원 실패를 보존했다.

전체 114.985초, core 명령 24.828초/시험 0.18초, 제품 명령 31.937초/시험 0.41초다.
시스템 CPU 최고 58.33%, 가용 RAM 최저 21.0979%, 소유 Job private 최고 전체 RAM의 4.9645%였다.
기존 한 코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%와 입력 검증을 유지했고
모든 Job은 active0/empty/handle closed다. 메타데이터 digest는 별도 JSON 복제 없이 유한 writer에서
streaming으로 계산한다. 성능 벤치마크나 PC 프리즈 해결 증거로 삼지 않는다.

v2 자체는 서식 정의를 해석하지 않는다. 아래 v3는 존재하는 참조를 원본 정의에 결속하며,
캐스케이드·숨김/유효 서식과 제어 매개변수 의미는 여전히 unverified다.
v2 경계는 [v2 요청 프로필](../../protocol/migrations/p09-source-search-inspection-v2.md)에 있다.

## 원본 서식 정의와 조건 검색

`SourceStyleDefinitionIndex`는 기존 카탈로그의 private `read_header`와 글자·문단 reader를 재사용한다.
추가 bridge를 제거하면 기존 카탈로그 전체 코드와 같으며 matcher/inspection도 새 선언만 제거하면 같다.
named style의 charPr/paraPr/nextStyle 관계, dense ID·정의 수와 원래 참조 검사도 유지한다.
별도의 새 header parser나 매 글자당 XML 재파싱은 추가하지 않았다.

`find_definition_style`은 굵게·기울임·HWPUNIT 크기·RGB 색·문단 가로 정렬을 찾는다.
글자 조건은 run_property/text_style/named_style 중 하나, 문단 조건은 direct_property/named_style 중 하나를
명시해야 한다. 무관한 축이나 축 없는 값·빈 조건은 거부한다. text_style은 기존 typed 글자 reader의
참조 domain을 따르며, named_style과 자동으로 섞거나 nextStyle을 상속으로 해석하지 않는다.
존재하는 네 계열 참조는 전부 정의에 대조한다. 없는 참조는 missing 개수로 남기고 0·named style로
대체하지 않으며 해당 명시적 축 조건에 일치시키지 않는다. 손상·dangling·지원하지 않는 header는 거부한다.
정의 연결은 한 번 계산하고 원본 scalar의 조건 판정에는 미리 계산한 인덱스를 사용한다.

요청은 별도 `hwpx-agent.product-source-search-request/v3`이다. v1/v2는 새 작업과 definition_filter를
계속 거부한다. 엄격한 중복/미지 키·object/축/값 검사와16KiB 한도, 현재 document.write·scope/head·
ACL/quarantine/AEAD·전체 source 재구성·최종 consumer head 경계는 공유한다. pure 정의 receipt는
현재 source에 있는 참조의 해석 범위만 증명하며 접근·CAS·실행 권한이 아니다.

첫 components051은3pass/6fail이었다. 새 synthetic fixture가 기존 효과 뒤에 bold→italic을 붙여 원래
글자 reader의 italic→bold→underline 순서를 어겼다. 독립 진단052/053으로
character_style_unsupported_shape를 확인했다. 제품 코드/reader는 수정하지 않고, fixture에서 기존
효과 앞에 italic→bold를 삽입하도록 고쳤다. 원본 fixture·실패 결과는 삭제하거나 PASS로 바꾸지 않았다.
051의 두 header 의존 negative 결과는 수정 fixture에서 다시 확인했고, 독립 필터 검사1개만 보존했다.

`p09-361-search-definition-recovery054.v1.json`은 영향core8+독립 header 진단1=9개와 제품20개
(신규v3 6+영향v1/v2 14), 총29개를 실행해 통과했다. 독립 필터1개를 더해 정의 경로 고유30개를
확인했으며 이전 핵심39개는 원래 구현/시험 본문 대조로 보존하고 재실행하지 않았다.
449 fresh/final449·diagnostics 없음·cleanup True이고 무관한 저장286개·공식 대기열은 실행하지 않았다.

복구 전체110.406초, 핵심 명령10.438초/시험4.34초, 제품 명령41.016초/시험2.04초다.
시스템 CPU 최고55.09%, 가용 RAM 최저23.2508%, 소유 Job private 최고4.9804%였다.
원래 한 코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%를 유지했고
모든 Job은 active0/empty/handle closed다. 이는 PC 프리즈 해결이나 성능 벤치마크가 아니다.

정의값 일치는 실제 유효 서식이나 숨김/레이아웃 판정과 구분한다. 존재하는 참조의 결속 완료와
missing 개수를 함께 기록하며 암묵적 캐스케이드/숨김·전체 검색/Native/Gate 권위는 계속 false다.
[v3 정의 검색 프로필](../../protocol/migrations/p09-source-definition-style-search-v3.md)에 경계를 명시한다.

## 숨은 설명과 메모 본문 검색

`SourceReviewTextIndex`는 전체 원본 Form 재구성 proof와 기존 review-body mapper를 사용한다.
일반 본문·각주·미주에 더해 실제 hiddenComment/subList와 짝이 맞는 MEMO/subList의 매핑 문단을
수집한다. caller graph·본문·승인 bits를 받지 않으며 손상된 본문이나 짝 없는 필드를 조용히 건너뛰지 않는다.
원본 paragraph handle에만 scope를 결속하고 전체 수용 corpus에서 먼저 선택을 확인한다.

제품 요청 v4의 `find_review_literal`과 `find_review_regex`는 `review_policy`의
`include_hidden_explanations`와 `include_memo_bodies` 두 Boolean을 모두 명시한다.
일반 본문/각주/미주는 유지하며 두 보조 영역을 각각 포함하거나 제외한다. 제외는 검색 일치 수
상한을 소모하기 전에 적용한다. 제외한 문단만 선택한 경우는 외부 scope 오류가 아닌 검색0건이며,
검색 문단·블록 수와 제외 hidden/MEMO 문단 수를 함께 반환한다. 정책·질의·원본·범위는 digest로 결속한다.

검색 일치의 `match_regions`는 body_and_notes/hidden_explanation/memo_body를 구분한다.
수용한 블록은 spine과 각 블록의 첫 원본 text anchor 위치로 한 번 정렬한다. 문단/제어/opaque 경계를
넘겨 이어 붙이지 않으며 NFC의 원본 scalar provenance를 유지한다. 원본 순서는 실제 쪽/렌더링
순서가 아니고, 파일 본문 종류는 앱에서 현재 보이는 상태가 아니다. opaque 개수는 기본 graph 기준임을
명시하며 미매핑 영역과 전체 visibility/cascade 자격을 만들어내지 않는다.

기존 v1/v2/v3는 새 작업과 review_policy를 거부한다. v4도 누락/배열/null/미지·중복 키·잘못된 Boolean,
다른 작업에 붙인 정책과 style/definition 필터 혼용을 원본 읽기 전에 거부한다. generic include_hidden도
임의로 받아들이지 않는다. 기존 document.write·scope/head/ACL/quarantine/AEAD·전체 원본 proof와
최종 전달 head 경계를 공유한다. 같은 준비 호출에서 사용하지 않는 기본/서식 인덱스를 만들지 않고,
보관한 결과의 현재 접근 검사는 검색 질의나 과거 시험을 다시 실행하지 않는다.

`p09-361-search-review-text-components056.v1.json`은 신규core8+영향core4+신규제품6+영향제품20,
총38개 PASS·454 fresh/final454·diagnostics 없음·cleanup True다. 포함 정책4종·NFC와 원본 순서·
제외 우선 상한·선택/지문·손상 본문·유한 한도와 현재 write scope/ACL/격리/AEAD/최종 head 경합을
확인했다. 기존 matcher/추출 None 분기 역변환과 기존20개 제품 시험 본문을 확인했고 나머지 핵심
시험과 저장286개·공식 대기열은 재실행하지 않았다.

전체184.063초 중 핵심 명령29.579초/시험0.10초, 기존추출2.578초/시험0.19초,
제품명령93.140초/시험2.35초였다. 시스템 CPU 최고53.83%, 가용 RAM 최저20.0813%,
소유 Job private 최고4.9954%였으며 모든 Job은 terminal/empty/closed다. 기존 자원 보호를
유지했고 성능 벤치마크나 PC 프리즈 해결을 주장하지 않는다.

완료 범위는 수용한 파일 본문을 명시적 정책으로 검색하는 경로다. 실제 앱 표시/숨김·유효 서식
캐스케이드·완전한 SearchScopeSelector·Native/전체 검색/P09 Gate와 구분한다.
[v4 파일 본문 검색 프로필](../../protocol/migrations/p09-source-review-text-search-v4.md)에 계약을 기록했다.

## 보관된 결과에서 다시 찾기

`SourceSearchNavigationRequest`는 forward/backward와 wrap 여부를 명시한다. cursor가 없으면
앞/뒤 첫 항목을 선택하고, 있으면 해당 결과 번호 다음/이전을 선택한다. 끝에서 wrap=false이면
선택 없이 exhausted=true와 기존 cursor를 반환한다. 따라서 끝을 다시 호출해도 처음으로 리셋하지
않고 방향을 바꿀 수 있다. wrap=true일 때만 순환 사실을 표시하며 빈 결과는 cursor를 만들지 않는다.
빈 정규식 일치도 scalar를 억지로 이동시키지 않고 결과 번호로 진행한다.

cursor는 전체 원래 결과와 제품 문맥 digest, 결과 번호와 해당 occurrence 지문을 결속한다.
전체 결과에는 원본/질의/범위·서식/제어/본문 정책이 포함되고 제품 문맥에는 기존 key/plan/provider
scope/raw 요청 지문까지 포함한다. cursor는 서명된 권한이나 실행 receipt가 아닌 선택 좌표다.
문자열/정규식·명시적 서식/정의값·컨트롤·숨은 설명/MEMO 결과 모두 같은 이동 정책을 사용한다.
선택한 원본 match/pieces 또는 control anchor와 필요 시 본문 region을 그대로 반환한다.

별도 `hwpx-agent.product-source-search-next-request/v1`은 준비 receipt SHA와 엄격한 navigation
객체만 받으며16KiB·중복/미지 키·배열·잘못된 방향/Boolean/cursor를 원본 읽기 전에 거부한다.
기존 v1~v4 검색 준비 요청에는 새 필드를 넣지 않는다. 매 결과 노출은 기존 현재 source/권한/ACL/
quarantine/AEAD/응답 지문과 최종 head를 확인한다. 질의/인덱스를 재생성하지 않고 선택1개만
복제한다. 현재 보관 결과의 지문 검사는 유한 streaming hash이며 전체 이동 비용이 O(1)은 아니다.

components058의 core10개는9pass·1fail이었다. 새 시험이 선택 응답은 전체 검색 응답보다 커야 한다고
가정한 것이 원인이었다. 제품·상한 검사는 바꾸지 않고 정확한 원래 응답 상한에서 완전한 결과가
보존되고 상한을1byte 줄이면 원래 전체 결과가 거부되는지 확인하도록 수정했다. recovery059는
실패1개+미실행제품7개만8pass·461 fresh/final461·cleanup True다. 기존9개를 재실행하지 않아
고유17개를 확인했다. 제품7개에는 재사용 fixture package 함수 미사용 경고1종이 남는다.
원 실패와 경고를 숨기지 않으며 나머지 검색·저장312개·공식 대기열은 반복하지 않았다.

복구 전체94.578초, core명령1.422초/시험0.01초, 제품명령33.375초/시험1.77초였다.
시스템 CPU 최고20.64%, 가용 RAM 최저21.2149%, Job private 최고5.0134%였으며 모든 소유
Job은 terminal/empty/closed다. 기존 자원 보호를 유지했다. 근거는
`p09-361-search-navigation-recovery059.v1.json`과 [다시 찾기 프로필](../../protocol/migrations/p09-source-search-navigation-v1.md)이다.

이는 보관한 부분 검색 결과의 다음 위치 선택이다. 실제 앱 선택·쪽 이동·전체 검색 범위·필수 target
검증·전체 operation dispatcher/CAS/실행/게시·Native/전체 SEARCH-005 제품 지원과 구분한다.

## 실제 치환을 위한 원본 범위 편집

SEARCH-006을 기존 전체 leaf 교체에 바로 연결하면 바꾸지 않은 entity 표기나 literal CRLF까지
재작성할 수 있다. 새 `ReplaceLeafScalarRanges`는 원래 XmlElementSelector에 결속된 Unicode
scalar 범위만 바꾼다. LeafTextRangeReplacement는 start/end와 XML 1.0 의미 문자열을 검증하며
caller byte offset이나 XML fragment를 받지 않는다. 이 primitive 자체는 접근·보호·실행 권한이 아니다.

원본의 text/reference token을 한 번 스캔해 요청한 경계만 저장한다. literal CR/CRLF는 XML 의미상
LF 한 글자이고 character reference CR은 별도 한 scalar다. 선택 밖 원래 bytes는 보존하며 치환값의
CR은 `&#13;`으로 쓴다. 여러 disjoint/adjacent 범위는 모두 원래 좌표를 사용한다. 겹침·잘못된 순서·
중복 요소 요청과 stale/자식/주석/루트 선택을 거부한다. 동일 package collision key의 대소문자 별칭도
같은 요소 요청으로 취급한다. 전체 범위 수와 값/escape 후 byte 예산을 먼저 검사하며 이미 정렬된
endpoint는 다시 정렬하지 않는다. 기존 patch의 충돌·ID·보존·writer 검증을 재사용한다.

components061은 새 범위 타입의 Eq/PartialEq 선언 누락으로 컴파일 실패했고 시험은 실행되지 않았다.
선언을 보완한 recovery062는 신규8+영향5=13pass·466 fresh/final466이었다. alias063은 시스템
CPU96.35%로 보호 중단됐고 소유 Job은 CPU0.172초·private34.71MiB·active0/empty/closed였다.
당시 프로세스별 원인 증거는 없어 검증/Defender/다른 프로세스 중 원인을 확정하지 않는다.
자원 정책은 그대로 유지했고 한 요소 반복 스캔 방지와 endpoint 선형 수집을 보완했다.

linear064는 새 시험에서 비공개 collision_key를 호출해 컴파일 실패했다. production/API는 바꾸지 않고
ASCII fixture 경로 확인만 공개 값으로 고쳤다. linear065는 영향core9개 PASS·468 fresh/final468·
diagnostics 없음·cleanup True다. 기존 patch 회귀5개를 보존해 고유14개를 확인했다. 시험은 entity/
Unicode·CR/CRLF·삽입/삭제·다중 범위·원자적 거부·범위/출력 한도·경로 별칭과 결정성을 확인한다.
원 실패/중단은 보존하며 기존 검색·제품 시험이나 공식 대기열을 반복하지 않았다.

마지막 실행은 전체116.812초, 명령54.766초/시험0.31초, 시스템 CPU 최고18.62%, 가용 RAM
최저34.9148%, Job private 최고1.7572%였다. 한 코어·BelowNormal·CPU cap6.25%·private
cap8%/stop7%·RAM/commit95%를 유지했고 모든 소유 Job은 terminal/empty/closed다.
[원본 범위 편집 경계](../../protocol/migrations/p09-source-search-scalar-patch-prerequisite-v1.md)에 계약과 후속 작업을 기록했다.

이 기반 위에 아래 실제 치환 후보와 저장 경계를 연결했다. generic primitive만으로 검색이나
완전한 제품 계약이 완료된 것은 아니며 혼합 제어/필드·전체 scope·CAS/실행/게시는 남는다.

## 원본 문자열 치환 후보와 저장 경계

`lower_literal_search_candidate`는 실제 원본 Form과 operation-local proof만 받는다. 기존 NFC 검색과
명시적 문단 scope로 일치를 구하고 전체 원본 기여·연속성/겹침을 확인한다. 불완전한 Unicode
분해 일부나 canonical 재정렬의 비연속 선택은 거부한다. 여러 run의 일치는 명시적인
FirstOriginalRunRetainAllRuns 정책으로 첫 원본 text leaf에 치환값을 넣고 나머지 범위만 지운다.
모든 run/leaf 구조·선언 속성은 유지하며 실제 유효 서식/레이아웃을 추정하지 않는다.

원래 관측 보호 scanner를 part당 한 번 사용해 table/cell/size/ancestor 보호를 거부한다.
필드 범위는 원래 collector로 읽고 part별 interval을 정렬·합친 뒤 조회한다. 필드 cached text는
editable=true도 치환 허가로 해석하지 않는다. mixed atom leaf와 제어/opaque/문단 경계는
plain text로 평탄화하지 않는다. 무일치·무변경·불완전 선택·한도 초과는 구분해 거부한다.

선택된 여러 일치를 한 scalar-range transaction으로 처리한다. 입력 전체 Form 재구성은 호출당
한 번 공유하고 매 일치마다 ZIP/Form을 다시 읽지 않는다. 출력은 전체 Form/필드를 재수입해
기대 leaf 의미값을 확인하고 선택 leaf content 밖 XML과 다른 part를 대조한다. receipt는 원본/
index/scope/query/replacement/run 정책과 선택 수·변경 범위/leaf 지문을 기록하며 plaintext를 싣지 않는다.

`prepare_literal_search_candidate` 저장 경로는 기존 sealed current Result에서 document.write와
현재 scope/head/ACL/quarantine/AEAD를 확인한다. verify/byte 노출은 현재 원본·writer integrity와
최종 consumer head를 다시 확인하되 검색이나 후보 생성을 반복하지 않는다. 후보는 원본을
덮어쓰지 않고 ingest/commit/CAS/멱등 claim을 하지 않으며 실행/게시 route는 계속 거부한다.

components067은9pass·1fail이었다. 새 시험의 literal CRLF 원본을 기존 typed reader가 거부했다.
generic XML scalar 편집의 CR 지원은 HWPX plain text 허용과 다르다. reader/기존 정책 본문은
바꾸지 않고 원래 validate_text를 재사용해 제어 문자와 noncharacter 치환값을 일찍 거부한다.
해당 시험만 수용 가능한 다중 치환/삭제와 CR/LF/tab/noncharacter 거부로 수정했고 기존9개 본문은
그대로다. recovery068은 수정1개+저장6개만7pass·472 fresh/final472·cleanup True로 고유16개를
확인했다. 이전 fixture package 함수 미사용 경고1종과 원 실패를 보존한다. 나머지 검색/patch와
무관저장319개·공식 대기열은 반복하지 않았다.

복구 전체115.875초, core명령21.234초/시험0.43초, 저장명령33.672초/시험2.29초였다.
시스템 CPU 최고36.74%, 가용 RAM 최저30.8222%, Job private 최고5.0373%였고 모든 소유
Job은 terminal/empty/closed다. 기존 자원 보호를 유지했으며 PC 프리즈 해결을 주장하지 않는다.
[실제 치환 후보 프로필](../../protocol/migrations/p09-source-literal-replacement-output-v1.md)에 범위를 명시한다.

아래 제품 JSON 요청은 이 후보와 key/plan을 연결한다. 전체 SearchScopeSelector·숨은 설명/MEMO
치환·필드/혼합 제어/개행 치환·완전한 보호·target 검증·dispatcher/DB/CAS/실행/게시는 남는다.

## 문자열 치환의 엄격한 제품 준비 요청

`hwpx-agent.product-literal-replacement-request/v1`은 원본/project/document/revision/head/source SHA와
key/plan·scope를 명시한다. operation은 replace_literal/query/replacement/case_sensitive/whole_word/
max_replacements/run_policy를 모두 요구한다. 범위는 기존 mapped_document 또는 중복 없는 원본
paragraph handle 집합이고, run_policy는 first_original_run_retain_all_runs다. 빈 replacement는 삭제다.

16KiB·미지/중복/누락 키·배열·잘못된 값/enum/type은 원본 읽기 전에 거부한다. 기존 값 정책을
추출한 pure validator를 JSON과 lowering이 공유하며 새 정책이나 권한을 만들지 않는다. regex/
style_filter/include_hidden/preview_only·승인 bits·출력 경로는 지원하는 척 무시하지 않고 거부한다.
원본은 caller graph나 경로가 아닌 provider의 sealed current Result에서만 가져온다.

준비된 source를 private Borrowed/Owned enum으로 옮겨 source/artifact 복제나 추가 reimport를
하지 않는다. 기존 preparation/fresh/verify/bytes/head 검사 본문은 그대로다. raw/canonical/provider
scope request digest는 key/plan/query/replacement/scope를 결속하고 보관 후 document.write와
현재 원본/ACL/quarantine/AEAD/writer integrity·최종 consumer head를 유지한다. 후보 반환은
원본 변경·revision CAS·멱등 key claim·실행/게시가 아니며 full product route는 계속 거부한다.

components070은 신규제품9+영향기존저장6=15개 PASS·475 fresh/final475·cleanup True다.
기존 core10개는 원 정책/치환 본문 역변환과 시험 입력 일치를 확인하고 재실행하지 않았다.
strict JSON·16KiB 경계·원 값 정책·key/plan/query/replacement 지문·검색 응답에서 얻은 handle을
사용한 문단 선택/삭제·5개 외부 scope·ACL 철회/복구·격리/AEAD·최종 head 경합을 확인했다.
기존 fixture 미사용 경고1종을 기록하며 나머지 검색/patch/저장 시험과 공식 대기열은 반복하지 않았다.

전체176.000초, 신규제품명령107.625초/시험11.23초, 영향기존6명령6.750초/시험6.03초였다.
시스템 CPU 최고32.81%, 가용 RAM 최저28.5142%, Job private 최고5.0349%였고 두 Job은
terminal/empty/closed다. 기존 자원 보호와 입력 확인을 유지했으며 PC 프리즈 해결을 주장하지 않는다.
[치환 제품 요청 프로필](../../protocol/migrations/p09-literal-replacement-product-request-v1.md)에 경계를 기록했다.

## 제어를 보존하는 원본 텍스트 atom 편집 기반

새 `ReplaceTextAtomScalarRanges`는 원래 TextSpan의 atom 번호와 atom 안의 Unicode scalar 범위를 받는다.
`TextAtomRangeReplacement`의 치환값은 기존 본문 정책을 따르며 탭·줄바꿈·비문자를 거부한다.
기존 text-span reader를 내부 bridge로 재사용하므로 제어 속성·opaque·주석 처리 규칙을 복제하지 않는다.
탭·줄바꿈은 좌표 번호에 포함되지만 편집 대상은 Text atom뿐이다. 빈/제어 전용 요소에 새 atom을
추정해서 만들지 않으며, 기존 leaf 편집의 자식 거부와 generic XML CR/CRLF 지원도 유지한다.

원 reader가 한 번 수용한 요소에서 제어의 원본 token 범위를 건너뛰어 lexical text 범위를 만든다.
선택 atom의 요청 endpoint만 기존 scalar byte 경계 함수로 한 번 읽는다. 한 요소의 여러 일치를
하나의 intent로 묶으며 같은 atom을 일치마다 다시 읽지 않는다. 두 range-intent 계열의 중복 요소는
package collision key로 거부하고 전체 범위 수·값 크기·escape 후 출력 크기를 합산 제한한다.
기존 patch/ID/보존/writer 검사를 공유하며 이 기반 자체는 field/protection 권한을 부여하지 않는다.

`p09-361-text-atom-patch-components072.v1.json`은 신규10개 중8pass·2fail이었다.
성공 fixture의 charStyleIDRef는 원 ID 프로필이 수용하지 않아 거부됐고, 검색어 D는 보존용 문구에도
있어2건이었다. ID 거부를 negative로 유지하고 허용 namespace 선언 보존·고유 검색어로 그 두 시험만
수정했다. production은 미사용 import 하나만 제거했으며 원 reader/ID/값 정책은 바꾸지 않았다.
`p09-361-text-atom-patch-recovery073.v1.json`에서 수정2개+미실행 영향 scalar9개가 통과했다.
이전8개와 공통 fixture 본문을 정확히 보존해 고유19개를 확인했으며 원 실패와 기존 다른 시험은 유지한다.
실제 검색 API의 atom/scalar 위치로 후보를 만들고 원문 entity·제어 내부 공백·run 서식·다른 part 보존,
앞/연속/뒤 제어, 삽입·전체 atom 삭제, 잘못된 범위/중복/혼합 intent 예산·stale 거부를 확인했다.

복구 입력481 fresh/final481, diagnostics 없음, cleanup True다. 전체144.047초,
복구명령78.109초/시험0.50초, 영향 scalar명령1.672초/시험0.10초였다.
시스템 CPU 최고26.89%, 가용 RAM 최저26.6786%, Job private 최고5.0086%이며 두 Job은
terminal/empty/closed다. 원 한 코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%를
유지했고 PC 프리즈 해결이나 benchmark를 주장하지 않는다.

이는 편집 기반이며 기존 문자열 치환 compiler/저장/제품 v1의 혼합 leaf 거부는 유지한다.
별도 v2 후보 compiler와 저장 연결은 다음 절의 범위이며 기존 v1을 확장하지 않는다.
[원본 atom 편집 프로필](../../protocol/migrations/p09-source-text-atom-patch-v1.md)에 계약을 기록했다.

## 혼합 본문 문자열 치환 후보와 현재 저장 서비스

`lower_literal_text_atom_candidate`는 별도 candidate/v2에서 실제 원본 NFC 기여/연속성·겹침 검사와
FirstOriginalRunRetainAllRuns 정책을 사용한다. 필드 캐시와 관측된 보호는 기존과 같이 거부하며,
일치에 제어 atom이 하나라도 있으면 전체 후보를 거부한다. 각 요소의 원본 TextSpan을 읽고
선택 Text atom별 모든 범위를 함께 편집한다. 완전 삭제로 사라진 빈 Text atom만 기대 모델에서
제거하며 탭/줄바꿈과 run/leaf 태그는 지우지 않는다.

기존 v1의 NFC 선택 본문과 patch/ID/보존/writer prefix를 private helper로 추출해 공유했다.
출력 Form/필드를 한 번 재수입하고 TextSpan 전체 값·지문·텍스트 길이를 대조한다. 제어 사이의
slot은 Text atom 전체 삭제 뒤에도 유지되므로 원본/출력의 선택 atom 밖 XML과 제어 bytes를
정확히 대조할 수 있다. 선택 atom 내부의 미선택 scalar/entity 보존은 앞 절의 patch 근거이며
독립 readback의 바이트 비교 범위는 선택 atom 밖이다. receipt는 그 범위만 명시한다.

`prepare_literal_text_atom_candidate`는 원래 document.write·현재 scope/head/ACL/quarantine/AEAD,
whole-source Form proof·writer integrity와 최종 consumer head 경계를 유지한다. v2 preparation,
fresh 검증·verify/전달·route 거부 본문은 기존 v1과 typed 출력/원본 소유 형식 및 닫힌 v2 flag 외에
같음을 대조했다. 보관 후보 전달에서 query/lowering을 반복하지 않는다. borrowed Rust 서비스 API와
다음 절의 owned 제품 요청은 같은 접근 경계를 사용한다. 기존 v1 외부 계약과 plain-only 의미는 유지한다.

`p09-361-literal-text-atom-components075.v1.json`의 신규core12+영향v1 core10=22pass,
484 fresh/final484·diagnostics 없음·cleanup True다. 혼합 다중/삭제·run/NFC·범위·noop entity,
field/보호·제어 거부·한도·part당2N 보호 방문을 확인했다. 전체92.703초,
명령26.547초/시험3.51초+영향명령4.187초/시험2.77초, CPU최고25.71%·가용RAM최저27.6842%·
Job private최고5.0323%였다.

저장 components076은 새 시험의 ArtifactPermission 타입 범위 오류로 컴파일 실패·시험0이었다.
시험 한 곳을 artifact_service::ArtifactPermission으로 지정한 recovery077은 신규저장6pass,
489 fresh/final489·cleanup True다. 권한/foreign document·ACL 철회/복구·격리/AEAD·prepare/verify/
최종 consumer head 경합·선택 범위/digest·제어/필드/한도를 확인했다. 원 실패를 보존하고 기존
fixture package 미사용 경고1종을 기록한다. core22는 다시 실행하지 않았다. 전체186.281초,
명령121.234초/시험8.33초, CPU최고29.40%·가용RAM최저28.4297%·Job private최고3.0408%였다.

이번 core22+저장6=28개 시험이며 모든 Job은 terminal/empty/closed다. 원 한 코어·BelowNormal·
CPU cap6.25%·private cap8%/stop7%·RAM/commit95%와 입력 확인을 유지했다. 기존 scalar·다른 저장/
제품·공식 대기열은 반복하지 않았으며 전체 제품/Gate나 PC 프리즈 해결로 해석하지 않는다.
[혼합 본문 치환 v2 프로필](../../protocol/migrations/p09-source-literal-text-atom-output-v2.md)에 경계를 기록했다.

## 혼합 본문 치환의 엄격한 제품 준비 요청

`StoredLiteralTextAtomProductRequest::prepare_json`은 별도 product-literal-replacement-request/v2를
받아 원본/head/key/plan/scope와 실제 v2 후보를 결속한다. v1과 같은 필수 원본 identity와 operation을
요구하며 schema는 v2를 명시해야 한다. 기존 parser와 provider-scope 해시의 private schema 매개변수만
추출했고16KiB·중복/미지/누락/배열·값/범위·제어 문자 치환값 거부 본문은 공유한다. v1/v2는 서로의
schema를 원본 읽기 전에 거부한다. regex/style/hidden/제어 편집·승인/출력 경로 같은 미지원 입력도 거부한다.

v2 후보는 기존 private Borrowed/Owned enum으로 원본을 move한다. output/receipt/원본의 소유권만
넘기고 clone 또는 소유권 전달 때문에 추가하는 reimport는 없다. 초기 import와 fresh whole Form proof는
그대로다. 원 준비·현재 접근·writer/최종 head 본문은 wrapper 변경을 제거하면 기존과 정확히 같다.
raw/canonical/provider-scope 지문을 구분해 schema·key/plan·원본·질의/범위·값·정책·출력을 결속한다.
보관 후보의 verify/전달은 현재 접근을 확인하지만 query나 lowering을 반복하지 않는다. key/receipt는
권한이 아니며 durable claim·revision commit/CAS·dispatcher·실행/게시는 추가하지 않았다.

`p09-361-literal-text-atom-product-components079.v1.json`에서 신규제품10+영향 v1제품9/v2저장6=
25pass·492 fresh/final492·cleanup True다. 기존 두 시험 파일 본문은 그대로다. 실제 혼합 cross-run·
제어 보존·인증된 검색 handle의 범위 선택/삭제, 엄격한 JSON/정확한16KiB 경계, 요청/옵션/값 지문,
5개 foreign provider scope·ACL 철회/복구·격리/AEAD·3단계 head 경합·한도/field/control/noop·버전 거부를
확인했다. 기존 fixture package 미사용 경고1종을 기록하고 원 core/patch·무관 저장·공식 대기열은 반복하지 않았다.

전체215.344초, 신규제품명령140.359초/시험13.24초, 영향15명령10.797초/시험10.07초였다.
시스템 CPU 최고33.16%, 가용 RAM 최저27.2722%, Job private 최고3.0762%였고 두 Job은
terminal/empty/closed다. 한 코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%와
입력 검증을 유지했으며 PC 프리즈 해결이나 benchmark를 주장하지 않는다.
[v2 치환 제품 요청 프로필](../../protocol/migrations/p09-literal-replacement-product-request-v2.md)에 경계를 기록했다.

## 숨은 설명과 메모 본문의 문자열 치환

별도 candidate/v3의 lower_review_literal_candidate는 기존 review mapper와 검색 projection을
한 번 사용하며 hidden/MEMO 포함 정책을 각각 명시한다. 실제 MEMO 소유 fieldBegin의 직접 subList
본문만 그 필드의 보호 구간에서 분리하고 다른 필드 구간과 합친다. 따라서 상위 필드가 감싸는 본문,
hidden cache, bodyless MEMO와 editable 플래그는 필드 캐시 쓰기 권한을 만들지 않는다.
기존 NFC·연속성·겹침·run 정책·제어 거부·한도·part당 보호 순회는 그대로다.

출력 Form/field/review를 각각 한 번 읽고 기존 TextSpan 값·제어/선택 atom 밖 bytes를 대조한다.
wrapper·parameters·metaTag·cache는 원본대로 남는다. 정책·본문 영역·원본/출력 review 관측을
receipt에 결속하되 실제 앱의 author/visibility/resolution·완전한 보호·실행 권위는 부여하지 않는다.

prepare_review_literal_candidate는 현재 document.write/scope/head/ACL/quarantine/AEAD와
whole Form proof·writer integrity·최종 consumer head를 공유한다. 보관한 후보의 전달은 현재
접근을 확인하지만 질의·lowering·review projection을 반복하지 않는다. borrowed 저장 서비스이며
아래 별도 v3 제품 요청이 owned 원본을 연결한다. v1/v2 외부 계약은 그대로다.

components081은 신규core12+영향기존20=32pass·495fresh/final495·cleanupTrue다.
저장 components082는 명령300초로 중단됐으며 시험 결과 필드가 없어 실행 건수는 미확인이다.
focused083은 그 없는 필드를 읽은 KeyError,084는 잘못된 target 빈 줄 예상으로 Cargo 전에 실패했다.
실패 원본과 제품/시험 조건을 보존하고 실행기만 고쳤다.

focused085는 원래 저장6개를 review_literal_stored 전용 대상으로 분리해6pass·502fresh/final502다.
StoredFixture new/provider는 그대로 공유하며 원래 root/module 전체 역변환과 기존 시험 본문을
확인했다. 기존 큰 대상은 cargo check만 통과했고 시험은 실행하지 않았다. 핵심32개는 재실행하지
않았으며 신규 기능18개와 영향20개, 고유38개 구성요소를 확인했다. 공식249 대기열 수용은 별개다.

복구 전체160.188초·저장명령81.281초/시험0.32초·기존대상check12.578초다.
시스템CPU최고31.05%·가용RAM최저26.7908%·Job private최고5.0788%이고 두 Job은
active0/empty/handle closed다. 저장6 diagnostics는 없고 기존 check에는 fixture package 미사용
경고1종이 남는다. 한 코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%,
명령300초·guard600초를 유지했다. PC 프리즈 해결이나 성능 benchmark로 해석하지 않는다.

[명시적 review 치환 v3 프로필](../../protocol/migrations/p09-source-review-literal-output-v3.md)에
계약과 실패/복구 근거를 기록했다. 엄격한 JSON과 owned 원본 연결은 다음 절의 별도 제품 경로다.

## 숨은 설명과 메모 치환의 엄격한 제품 요청

StoredReviewLiteralProductRequest는 product-literal-replacement-request/v3에서 원래 필수
원본/project/document/revision/head/SHA·key/plan·scope·replace_literal 옵션과 함께
operation.review_policy의 include_hidden_explanations/include_memo_bodies 두 Boolean을
요구한다. 원 strict parser를 object/value 단계로 추출해 공유하며 v1/v2 본문·canonical/scope
해시와 접근 검사는 정확히 역변환 대조했다. 누락/null/배열/잘못된 Boolean·중복·미지 키·16KiB와
값/범위 한도는 읽기 전에 거부하고 기존 버전은 review 정책을 무시하지 않고 계속 거부한다.

into_review_literal_candidate는 원래 borrowed 준비의 output/receipt를 move하고 기존
Borrowed/Owned enum에 원본을 box한다. clone/소유권 전달용 reimport는 없고 필수 초기 import와
fresh whole Form 재구성은 유지한다. 현재 write/scope/head/ACL/quarantine/AEAD·writer integrity·
최종 consumer head는 원래 본문 그대로다. raw/canonical/provider-scope 요청과 두 정책·질의/범위·
값/원본/출력은 결속하지만 key claim·commit/CAS·dispatcher·실행/게시 권위는 추가하지 않았다.

components088은 신규제품10+영향 v1/v2제품19/v3저장6=35pass·508fresh/final508·cleanupTrue다.
전용 대상에 기존 공유 fixture와 기존 시험3개 module을 그대로 연결했다. 정책4종/정확한 출력·
요청 drop 후 owned 후보·엄격한 JSON/정확한16KiB·요청/정책/옵션/값 digest·인증된 review 검색
handle로 hidden/MEMO 선택 삭제·제외 우선 상한·5개 외부 scope·ACL 철회/복구·격리/AEAD·
prepare/verify/최종 head 경합·cache/control/noop/출력 한도·유효한 상위 field의 정확한 FieldContent
거부·세 버전 의미를 확인했다. 핵심32·다른 저장 시험·공식249 대기열은 재실행하지 않았다.

전체101.984초·명령36.234초/시험10.10초·시스템CPU최고46.88%·가용RAM최저28.9834%·
Job private최고2.1868%다. diagnostics 없음·Job active0/empty/handle closed이며 원 한코어·
BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%, 명령300초·guard600초를
유지했다. PC 프리즈 해결이나 성능 benchmark가 아니다.
[v3 제품 요청 프로필](../../protocol/migrations/p09-review-literal-product-request-v3.md)에
완료 경계를 기록했다. 다음은 mapped_document/paragraphs를 넘어 전체 SearchScopeSelector의
계약과 현재 범위 선택 사이 차이를 보완하는 것이다.
규범 selector의 document/section/selection/node_set과 revision_id·section_ids·range를
현재 mapped_document/paragraphs의 단순 별칭으로 처리하지 않는다.

## 원본 구역과 노드 및 선택 범위

위치별 source 범위 선택은 source-index-scope-selector/v1에서 별도 검증했다. Document는
수용된 인덱스 블록과 기존 미매핑 count를 유지하며 전체 검색으로 승격하지 않는다. Section은 실제
graph section ID와 section-root spine part, NodeSet은 실제 graph node ID와 원본 XML 구간을
사용한다. source 문단 handle을 node ID의 별칭으로 받지 않으며 표·셀 하위 문단과 겹친 선택을
정확히 처리한다. 구간은 part별 정렬·병합 후 이진 탐색하므로 대상×문단 전체 반복을 추가하지 않는다.

Selection은 index SHA·문단 handle·global block·NFC scalar 두 경계에 결속한다. 원본 한 scalar의
여러 NFC 기여를 자르는 경계·외부/오래된/역순/범위 초과 선택은 검색0건이어도 거부한다. 검색 뒤
필터가 아닌 실제 문자열 창을 먼저 잘라 regex ^/$·whole-word를 계산하고 결과 좌표는 원래 global
좌표로 돌려준다. 문단·제어·opaque 경계는 연결하지 않으며 이 순서는 실제 Native 문서 흐름이 아니다.

components090에서 신규12+영향 matcher24/문단범위6/review8=50pass·511fresh/final511·cleanupTrue다.
기존 matcher는 None 경로를 정확히 역변환 대조했고 기존38개 시험 본문은 그대로다. 새 시험의
PackageLimits 미사용 import 하나만 제거하고 해당 대상 cargo check만 수행하며50개는 반복하지 않는다.
전체91.625초·명령25.875초/시험0.11+0.09+0.03+0.17초·시스템CPU최고27.93%·가용RAM최저27.0931%·
Job private최고5.0637%이고 Job active0/empty/handle closed다. 한코어·BelowNormal·CPU cap6.25%·
private cap8%/stop7%·RAM/commit95%·명령300초·guard600초는 유지한다. PC 프리즈 해결이나 benchmark가 아니다.

이는 typed source 검색 범위의 구현이며 전체 제품 SearchScopeSelector 완료가 아니다.
아래 v5 경로가 selector 발견 API·현재 stored revision/head/source·엄격한 JSON을 연결한다.
review 정책과 치환의 선택 창 연결은 남는다. [source 범위 프로필](../../protocol/migrations/p09-source-index-scope-selector-v1.md)에
좌표·검증·남은 제품 경계를 기록했다.

## 검색 범위의 인증된 조회와 제품 요청

StoredSourceScopeProductRequest는 별도 product-source-search-request/v5에서 selector의
revision_id를 base_revision과 먼저 대조하고 현재 provider의 revision/head/원본 SHA에 결속한다.
scope_inventory는 document selector와 옵션 없는 operation을 요구하며 본문 없이 실제 section ID·
node ID/source handle 대응·문단 handle/global block/NFC 길이·index 지문만 반환한다. 같은 호출의
whole Form proof로 index를 한 번 만들고 보관 결과의 verify/전달은 inventory/query를 재실행하지 않는다.

find_literal/find_regex는 document/section/selection/node_set을 실제 원본에 적용한다.
클라이언트의 별도 Form/graph import 없이 조회 JSON으로 네 요청을 만들었다. 선택은 검색 전
창을 유지하며 v1~v4 문단 scope나 전체 본문으로 바꾸지 않는다. 원래 write/scope/ACL/quarantine/
AEAD·finish_search/fresh_json·최종 consumer head는 typed private result arm 밖 본문이 같다.
strict16KiB·중복/미지 키·revision/값/shape·부적합 range 거부와 버전 분리를 유지한다.
key/receipt는 실행 권한이 아니고 CAS/ingest/dispatcher·실행/게시는 추가하지 않았다.

components092는 inventory core4+신규제품10+영향검색26/이동7=47pass·522fresh/final522·cleanupTrue다.
현재 API JSON→4종 범위·원본 보존, 두 실제 구역·node/source ID 구분·선택 regex 좌표·strict 요청,
현재 write/5개 외부 scope·ACL 철회/복구·격리/AEAD·두 operation의 prepare/verify/최종 head 경합,
선택·집합·출력 상한과 v1~v4 검색/이동을 확인했다. 이전50개는 원본 본문/역변환 일치로 보존하고
재실행하지 않았다. 새 core diagnostics는 없고 기존 fixture package 미사용 경고1종이 남는다.

전체158.266초·core명령57.735초/시험0.03초·제품명령33.093초/시험4.28초다.
시스템CPU최고70.10%·가용RAM최저26.7706%·Job private최고5.0981%이며 두 Job은
active0/empty/handle closed다. 원 한코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·
RAM/commit95%·명령300초·guard600초와 입력 확인을 유지했다. 시스템 CPU 표본으로 원인 프로세스나
PC 프리즈 해결을 판정하지 않는다. [v5 범위 제품 프로필](../../protocol/migrations/p09-source-scope-product-request-v5.md)에
원본과 실제 저장 결속·엄격한 요청 범위를 기록했다.

이 v5 요청은 review 정책을 받지 않는다. 뒤의 review 선택 창과 저장 연결도 기존 v5 JSON을 넓히지 않는다.

## Review 본문의 선택 창과 저장 후보

source_review_scope_index는 원래 field/review admission으로 실제 숨은 설명과 MEMO 본문을 읽고,
그 graph의 실제 node ID/source anchor를 보조 catalog에 넣는다. 조회에는 본문 없는 원본 좌표와
block region을 반환한다. Document/Section/NodeSet/Selection을 전체 수용 index에서 먼저 해석한 뒤
명시적 정책으로 제외하며, 부분 선택을 문단 전체로 넓히지 않는다. 제외된 실제 node는 외부 node가
아니므로 검색 결과0과 제외 수를 반환한다. 정책은 request digest에, 선택 창은 scope digest에 결속한다.

lower_review_selector_literal_candidate는 같은 창의 실제 일치를 원래 v3 review compiler에 전달한다.
source-selector-literal-replacement-candidate/v1의 바깥 receipt에 selector를 넣고 기존 v3 body receipt를
유지한다. NFC 원본 기여·field cache/다른 상위 field·보호·control·writer/readback을 재사용하며
원본 같은 문단의 비선택 일치를 건드리지 않는다. 기존 v3 JSON 의미는 바꾸지 않는다.

094는 build 중 시스템CPU98.6% 보호 중단으로 시험 완료 건수가 미확인이다. 095는 새 시험의
u32/usize assertion 비교 때문에 컴파일 실패했고, 그 한 곳만 명시적 변환으로 수정했다.
recovery096은 같은52개 시험을 한 바이너리에 묶어 신규16+영향36=52pass·532fresh/final532·cleanupTrue다.
두 실패 원본과 시험/자원 조건은 보존한다. 바이너리6→1은 빌드 구성을 줄인 것이며 CPU 원인 규명이나
성능 benchmark가 아니다. 전체90.062초·명령20.219초/시험9.39초·CPU최고26.92%·가용RAM최저36.8802%·
Job private최고1.7867%이고 Job은 active0/empty/handle closed다.

into_review_source_scope는 원래 current source/whole proof로 한 review index를 만들고 private
ReviewScope 결과만 추가해 finish_search/fresh_json/verify·최종 head를 그대로 공유한다.
stored-source-search/v6의 Inventory와 Find를 구분하며 기존 v1~v5 결과/이동 의미를 보존한다.
prepare_review_selector_literal_candidate와 owned 전달은 원본/output을 move하며 clone/소유권 전달용
reimport를 하지 않는다. 검증·전달은 현재 write/scope/head/ACL/quarantine/AEAD와 writer integrity를
확인하되 inventory/query/lowering/review projection을 반복하지 않는다. 실행 route는 계속 거부한다.

components097은 신규12+영향49=61pass·536fresh/final536·cleanupTrue다. API 조회 JSON으로 네 범위를
구성하고 세 본문의 두 번째 일치만 byte exact 치환했다. 정책4종·상한·owned 전달·잘못된 선택·
write/5개 외부 scope·ACL 철회/복구·격리/AEAD·두 검색 operation/치환의 prepare/verify/최종 head 경합·
cache/상위 field/control/noop·한도를 확인했다. 기존52개 핵심과 공식249 대기열은 재실행하지 않았다.
기존 v5제품10/검색26/이동7/v3저장6 시험 본문은 그대로이며 fixture package 미사용 경고1종이 남는다.
전체269.953초·명령196.813초/시험25.18초·CPU최고26.70%·가용RAM최저35.6382%·Job private최고5.1055%다.

두 실행은 원 한코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%·명령300초·
guard600초와 전후 입력 검증을 유지했다. 모든 Job은 active0/empty/handle closed다.
근거는 evidence/p09-361-review-selector-recovery096.v1.json과
evidence/p09-361-stored-review-selector-components097.v1.json이다.
[저장 선택 범위 프로필](../../protocol/migrations/p09-stored-review-selector-candidates-v1.md)에 실제 경계를 기록했다.
이 stored 프로필을 사용하는 엄격한 제품 JSON은 다음 절의 별도 schema로 연결했다.

## Review 선택 범위의 엄격한 제품 요청

product-source-search-request/v6는 필수 selector.revision_id를 base_revision과 읽기 전에 대조한다.
scope_inventory는 document만, find_literal/find_regex는 네 범위와 명시적 review_policy를 받는다.
scope_inventory는 정책/query/options를 받지 않으며 검색은 두 Boolean을 모두 요구한다.
product-literal-replacement-request/v4는 기존 scope 대신 같은 selector와 replace_literal operation을
사용하고 기존 query/replacement/case/whole-word/max/run_policy와 두 review 정책을 필수로 받는다.

두 요청은 같은 selector shape/native 변환을 사용한다. v5 parse의 object/value 단계 추출과
selector 검사 공유 외 전체 v5 원본을 역변환 대조했고 원래 revision·값·한도·canonical/provider
scope/auth 의미를 유지했다. v1~v3 치환 파서는 새 module 외 본문 그대로다. strict16KiB·중복/미지 키·
배열/null·필수/형태/좌표·값·교체문자 검사를 읽기 전에 유지한다. 기존 schema는 새 필드를 거부한다.
유효하지만 정책으로 제외한 node는 검색0, 치환 NoMatches이며 부분 창을 문단 전체로 넓히지 않는다.

준비/verify/전달은 기존 current sealed source/write/scope/head/ACL/quarantine/AEAD·whole Form proof·
writer integrity와 최종 consumer head를 공유한다. 보관 결과의 inventory/query/lowering/review import는
반복하지 않는다. raw/canonical/provider scope 요청에 key/plan·선택·정책·원본·질의·출력을 결속하지만
idempotency claim·dispatcher·ingest·commit/CAS·실행·게시 권한은 추가하지 않았다.

components099는 신규제품16+기존v5범위10/v3치환10=36pass·542fresh/final542·diagnostics 없음·cleanupTrue다.
실제 조회 JSON으로 네 검색/치환 요청을 구성하고 세 본문의 두 번째 일치만 byte exact 치환했다.
선택 regex/상한·정책4종·strict/정확한16KiB·digest/집합 순서·write/5개 외부 scope·ACL 철회/복구·
격리/AEAD·세 operation의 prepare/verify/최종 head 경합·선택 오류·cache/상위 field/control/noop·한도와
원본/head 보존을 확인했다. 핵심52·저장61·공식249 대기열은 재실행하지 않았다.
전체311.547초·명령239.813초/시험6.50초·Job CPU12.531초·시스템CPU최고26.43%·가용RAM최저39.8378%·
Job private최고2.2072%다. 원 한코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%·
명령300초·guard600초와 입력 검증을 유지했고 Job은 active0/empty/handle closed다.
근거는 evidence/p09-361-review-selector-product-components099.v1.json이다.
[Review 범위 제품 요청](../../protocol/migrations/p09-review-selector-product-requests.md)에 schema와 남은 계약을 기록했다.
이 제품 요청의 선택 범위 결과 이동은 다음 절의 보관 결과 경로로 연결했다.

## 선택 범위 결과의 다시 찾기

SourceSelectorSearchResult와 SourceReviewSelectorResult는 보관한 실제 일치와 선택 창/정책을 원래
navigation 엔진에 전달한다. v5/v6 Find의 navigation_receipt_sha256/with_next_verified_json은 기존
product-source-search-next-request/v1을 사용하며 query/index를 다시 만들지 않는다. 앞/뒤 시작·
이동·명시적 순환·종료 후 cursor 유지와 방향 전환, 빈 결과/빈 일치의 ordinal 이동을 보존한다.
Review region과 NFC 원본 기여/전역 scalar 좌표도 그대로다. source 순서는 Native 쪽/배치 순서가 아니다.

cursor는 전체 불변 result와 제품 receipt context에 결속한다. 원본/revision/head·key/plan·raw 요청·
provider scope·query/options·selector/정책이 다르면 같은 위치라도 거부한다. strict next parser와 기존
v1~v4 이동·navigation 엔진은 본문 그대로이고, Scope/ReviewScope Find 분기만 연결했다.
inventory의 제품 이동은 Request로 읽기 전에 거부하며 stored fallback도 Cursor 오류를 유지한다.
현재 write/scope/head/ACL/quarantine/AEAD·fresh source/result와 최종 consumer head를 그대로 확인한다.
전체 결과의 유한 직렬화·해시 무결성 검사는 유지하므로 이동 총비용이 상수 시간이라는 주장은 아니다.

components101은 신규core6+기존core10=16pass와 신규제품10+기존이동7=17pass, 총33pass·548fresh/final548·cleanupTrue다.
네 범위·v5/v6·원본 일치/region·앞뒤순환/종료·선택 regex/빈 결과/빈 일치·NFC·cursor 위변조/문맥·
strict/정확한16KiB·write/5개 외부 scope·ACL 철회/복구·격리/AEAD·최종 head 경합·inventory 거부와
원본/head/ingest 보존을 확인했다. 기존 navigation core10/제품7 본문은 그대로다.
이전핵심52·저장61·제품36·공식249 대기열은 재실행하지 않았다. core diagnostics 없음·제품은
기존 fixture package 미사용 경고1종이다. 전체139.547초·core명령38.343초/시험0.25초·제품명령30.266초/시험2.66초·
CPU최고25.19%·가용RAM최저37.1637%·Job private최고5.1099%다. 두 Job은 active0/empty/handle closed이며
원 한코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%·명령300초·guard600초와 입력 확인을 유지했다.
근거는 evidence/p09-361-selector-navigation-components101.v1.json과
[선택 범위 이동 프로필](../../protocol/migrations/p09-selector-result-navigation-v1.md)이다.
Selector의 서식 core 결합은 다음 절에서 보완했다. 컨트롤 위치 결속과 전체 제품 계약은 남는다.

## 선택 범위와 Review 서식 조건

SourceReviewScopeIndex.find_style은 같은 네 selector 창과 명시적 body 정책에 Declared 또는 Definition
조건을 적용한다. Declared는 실제 p/run/t의 명시적 참조값, Definition은 실제 typed header의 명시한 축만
비교하며 빠진 참조를0/이름 스타일로 보충하지 않는다. 전체 NFC 원본 기여가 predicate를 만족해야 하고
빈 일치는 서식 기여가 없어 제외한다. 창/정책/서식 제외를 matcher 상한 전에 적용하며 regex는 잘린 창을 본다.

기존 inspection/definition의 원본 point predicate와 review 창/제외/결과 조립을 추출해 공유하고 전체
기존 파일 본문을 역변환 대조했다. inspection은 원래 XML을 재사용하고 typed 정의 lookup은 Definition
일 때 한 번만 만든다. source-review-selector-style-search/v1은 filter·inspection/선택적 정의 receipt·
index/scope/query/policy/결과를 결속하며 core cursor도 이 전체 결과에 묶인다. 원본/작성자 본문을 반환하지 않는다.

components103은 신규8+기존declared/control9·definition10·review selector8=35pass·552fresh/final552·cleanupTrue다.
두 predicate/4종 범위·실제 MEMO node·부분 regex·정책/조건 제외 우선 상한·혼합 NFC 기여·명시적/빠진 축·
미해결 참조/잘못된 header·cursor/filter/policy 결속·정확한 응답 한도/1byte 부족·원본/비노출을 확인했다.
이전이동33·다른 완료 suite·공식249 대기열은 재실행하지 않았다. 재사용 fixture의 package/with_body 미사용
경고2종은 남는다. 전체149.640초·명령77.047초/시험2.33초·Job CPU28.031초·CPU최고20.83%·가용RAM최저35.5548%·
Job private최고5.0859%이며 Job은 active0/empty/handle closed다. 원 한코어·BelowNormal·CPU cap6.25%·
private cap8%/stop7%·RAM/commit95%·명령300초·guard600초와 입력 확인을 유지했다.
근거는 evidence/p09-361-selector-styles-components103.v1.json과
[Review 선택 범위 서식 core](../../protocol/migrations/p09-review-selector-style-core-v1.md)다.

이 core의 저장/제품 연결은 다음 절에서 보완했다. 컨트롤은 텍스트 좌표가 없는 위치도 있어 선택 문단이라는
이유만으로 허용하지 않으며 actual control_anchor/경계를 결속해야 한다.

## Review 선택 범위 서식의 현재 저장과 제품 요청

product-source-search-request/v7은 필수 selector/revision·find_style/query/regex/case/whole-word/max·
tagged style_filter와 두 review 정책을 요구한다. 두 predicate 가족 모두 네 source 범위와 문자열/정규식
검색을 사용한다. strict16KiB·중복/미지 키·배열/null/필수·범위/좌표·명시적 축·값 검사를 읽기 전에 유지한다.
원 selector shape/native 변환과 unique JSON/object parser를 공유하고 기존 schema는 새 조합을 거부한다.
조회는 v6 scope_inventory JSON을 사용하며 caller가 Form/graph/typed catalog를 따로 import하지 않는다.

into_review_style_search는 현재 write/scope/head/ACL/quarantine/AEAD·whole Form proof와 한 review index를
사용한다. Private ReviewStyle result가 stored-source-search/v7과 원 finish_search/fresh_json/verify·최종
consumer head를 공유한다. 새 제품 receipt는 source/index/selector/policy/style과 raw/canonical/provider
scope 요청·key/plan을 결속한다. next/v1은 같은 전체 스타일 결과에 cursor를 결속하고 현재 원본/권한/
최종 head를 다시 확인한다. 전달에서 query/index/서식 정의 lookup은 반복하지 않되 전체 결과 무결성 검사는
유지한다. dispatcher/ingest/commit/CAS·멱등 claim·실행/게시 권한은 추가하지 않았다.

components105는 신규12+기존검색26/이동7=45pass·559fresh/final559·cleanupTrue다. 두 predicate/4종 범위·
부분 regex/빈 일치·정책/조건 제외 우선 상한·strict/정확한16KiB·digest/legacy 분리·write/5개 외부 scope·
원본/head·ACL 철회/복구·격리/AEAD·두 가족의 prepare/verify/출력/next 최종 head 경합·cursor 문맥·빠진 축/
dangling 참조/header·한도/비노출·원본/head/ingest 보존을 확인했다. 새 specimen 본문은 핵심 시험과 같다.
핵심35·다른 완료 suite·공식249 대기열은 재실행하지 않았다. 기존 fixture package 미사용 경고1종이 남는다.
전체112.203초·명령40.344초/시험10.71초·Job CPU38.250초·CPU최고18.01%·가용RAM최저33.8018%·Job private최고5.1125%다.
원 한코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%·명령300초·guard600초와 입력 검증을
유지했고 Job은 active0/empty/handle closed다. 근거는 evidence/p09-361-selector-style-product-components105.v1.json과
[서식 제품 v7](../../protocol/migrations/p09-review-selector-style-product-v7.md)이다.
실제 control_anchor와 선택 경계의 core 결속은 다음 절에서 보완했다. 전체 SearchScopeSelector·
cascade/visibility/Native flow·transaction·Native/Gate는 미완료다.

## 실제 컨트롤 위치와 선택 범위

SourceReviewScopeIndex.find_control은 기존 document/section/selection/node_set 해석에서 원본 구간도
함께 받아 실제 control_anchor 시작 위치가 반열린 구간 안인지 검사한다. 개체 자체를 선택했을 때 부모
문단 시작이 범위 밖이라는 이유로 누락하지 않고, 선택된 문단 안의 다른 컨트롤을 모두 포함하지 않는다.
기존 텍스트 창과 receipt 의미는 유지하며 selected_paragraphs는 텍스트 coverage이지 제어 포함 조건이 아니다.

부분 선택은 원 NFC origin의 prefix/suffix 순서와 원래 TextSpan reader를 사용한다. 양 끝의 최대2개
text 요소만 한 번씩 읽고 lexical atom/scalar edge로 제어 시작 전후를 구분한다. NFC 재정렬로 원본
연속 경계를 정할 수 없으면 Scope 오류다. 같은 좌표의 접힌 선택은0건이지만 서로 다른 블록 사이의
텍스트 없는 구간은 실제 중간 컨트롤을 포함할 수 있다. 첫 글자 전/마지막 글자 후의 제어를 문단 전체로
확장하지 않는다. Document/Section/실제 NodeSet은 텍스트가 없는 컨트롤도 선택할 수 있다.

hidden/MEMO 본문 정책은 일치 상한 전에 적용하고 제외 제어 수를 각각 기록한다. 원 inspection은 부모
문단을 먼저 방문하므로 결과만 spine/실제 control 시작으로 한 번 정렬하고 region을 결속한다.
기존 cursor 엔진의 새 ControlRegions 분기는 보관 결과·scope/policy/kind/상한·context를 결속하며
검색이나 XML 재수입을 반복하지 않는다. 기존 텍스트/문단 기반 v2 컨트롤 경로는 그대로다.

components107은58pass/1fail이었다. 새 시험의 원시 CR/LF·&#13;는 기존 reader의 금지 텍스트이므로
정상 투영을 기대한 fixture가 잘못됐다. 제품/reader와 성공58개 본문을 보존하고 그 시험에 정확한
text_flow_invalid_text 원 import 거부를 추가했다. recovery108은 실패한1개만1pass·566fresh/final566·cleanupTrue다.
따라서 신규12+영향기존47=고유59개를 확인했고 성공58·기존제품45·공식249 대기열은 재실행하지 않았다.
원 실패와 기존 fixture package/with_body 미사용 경고2종을 남긴다. 복구 전체74.719초·명령2.016초/
시험0.02초·Job CPU1.922초·CPU최고11.64%·가용RAM최저40.4980%·Job private최고1.7969%다.
Job active0/empty/handle closed와 원 한코어·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%·
명령300초·guard600초·입력 전후 확인을 유지했다. 이는 PC 프리즈 원인 해결이나 성능 benchmark가 아니다.
근거는 evidence/p09-361-selector-controls-components107.v1.json과
evidence/p09-361-selector-controls-recovery108.v1.json 및
[컨트롤 범위 core](../../protocol/migrations/p09-review-selector-control-core-v1.md)다.
이 core의 현재 저장/엄격한 제품 JSON과 next 연결은 다음 절에서 보완했다. Native/전체 계약 자격은 남는다.

## 컨트롤 범위의 현재 저장과 제품 요청

product-source-search-request/v8은 닫힌 control kind query와 find_control·regex=false·case_sensitive=true·
whole_word=false·max_results·두 review 정책·selector/revision을 모두 요구한다. 정규식·무관한 서식 옵션이나
미지/중복 키·누락·잘못된 scope/옵션/형식은 원본 읽기 전에 거부한다. 원16KiB unique JSON parser와
selector shape/native 변환을 재사용하며 v1~v7 요청을 넓히지 않는다. v6 발견 JSON만으로 MEMO 문단과
실제 table control의 node를 선택하고 별도 caller Form/catalog import를 하지 않는다.

into_review_control_search는 현재 write/scope/head/ACL/quarantine/AEAD·whole Form proof와 한 review index를
사용한다. private ReviewControl result는 stored-source-search/v8과 원 finish_search/fresh_json/verify·최종
consumer head를 공유한다. 준비 receipt는 원본/index/범위/정책/kind·raw/canonical/provider scope·key/plan을
결속하고 next/v1은 전체 결과와 원래 region cursor를 사용한다. 전달/이동에서 query/index를 반복하지 않지만
원본/전체 결과의 유한 무결성 검사와 최종 head는 유지한다. dispatcher/ingest/commit/CAS·멱등 claim·
실행/게시 권한은 추가하지 않았다.

components110은 신규13+영향기존검색26/이동7=46pass·571fresh/final571·cleanupTrue다. 네 범위·실제개체 node와
typed 저장 동등성·부분atom/gap·정책4종/제외우선상한·strict/정확한16KiB·legacy분리·write/5개외부scope·
ACL철회/복구·격리/AEAD·prepare/verify/출력/next 최종head경합·cursor 문맥/region·cross-run NFC/모호한재정렬/
외부좌표·한도/비노출·원본/head/ingest보존을 확인했다. 기존33개 시험 본문과 공통 권한/최종head 코드를
역변환 대조했다. 핵심59·기존v7제품45·공식249 대기열은 재실행하지 않았고 기존 fixture package 미사용
경고1종은 남는다. 전체177.953초·명령103.079초/시험5.19초·Job CPU36.844초·CPU최고23.83%·가용RAM최저36.9131%·
Job private최고5.1601%이며 Job active0/empty/handle closed다. 원 한코어·BelowNormal·CPU cap6.25%·
private cap8%/stop7%·RAM/commit95%·명령300초·guard600초와 입력 전후 검증을 유지했다.
근거는 evidence/p09-361-selector-control-product-components110.v1.json과
[컨트롤 제품 v8](../../protocol/migrations/p09-review-selector-control-product-v8.md)이다.
다음은 전체 검색 계약과 정규식/서식/컨트롤 치환·변환의 원본 편집/보호 경로다.

## 정규식 캡처와 일치별 원본 치환

lower_review_selector_regex_candidate는 원 field/review/index를 한 번 구성하고 기존 네 선택 창과 body 정책을
먼저 적용한다. compiled regex는 한 번 만들고 각 허용 창의 captures_iter에서 원래 일치/provenance와
확장을 함께 수집한다. 기존 검색의 None 경로는 find_iter를 유지하며 새 capture set을 만들지 않는다.
공통 matcher·review 창·literal compiler·MEMO context는 추가 wrapper/매개변수를 역변환하면 이전 전체
본문과 같다. 캡처를 얻으려고 매 일치에서 질의/원본 import를 다시 실행하지 않는다.

템플릿은 $0·번호·이름·${이름}·$$를 지원한다. optional group이 불참하면 빈 값이지만 미지 group이나
잘못된 문법은 오류다. 캡처는 NFC index 값이며 원래 문자열 표현을 그대로 복사한다고 주장하지 않는다.
일치마다 다른 값을 원 compiler의 첫 원본 run에 넣고 나머지 run/서식·제어와 선택 밖 bytes를 보존한다.
원본 연속성/겹침·필드 cache와 상위 field·보호·writer/readback 검사는 유지한다. 빈 일치는 조용히 건너뛰지
않고 전체 후보를 거부한다. regex의 인접 빈 일치 억제 규칙은 원 엔진을 따른다.

출력은 값당1MiB·전체 설정 result_bytes 이내이며, 빈 capture 반복도 별도 work counter를 소모한다.
template 참조 해석과 일치별 token 확장을 합산하고 상한은 설정 decomposed_scalars(기본1,000,000)다.
정확한512 work 통과와 다음 일치 거부를 확인했으며 결과가0byte라고 반복 비용을 무제한 허용하지 않는다.

components112는86pass/2fail이었다. styled-run 양성은 stub header 대신 실제 정의 fixture를 쓰고 원 stub
거부를 보존했다. 빈 일치 시험은 실제 검색 결과에서 빈 일치 존재를 확인한 뒤 거부를 검사하도록 고쳤다.
recovery113은 컴파일300초 제한으로 결과 미확인이며 원형 보존했다. CPU0 포화와 다른 maple-re의
affinity1·CPU delta를 관측했고 다른 앱을 변경하지 않았다. 동일17개 원문만 포함하는 전용 target을 만들고
우리 검증 프로세스만 CPU2(mask4) 한 코어로 제한했다. 기존 공통 guard/CPU cap/priority/RAM/시간 상한은 같다.

focused114는17pass·582fresh/final582·diagnostics없음·cleanupTrue다. 실패2+영향regex14+신규work1개를
실행했고 기존72개는 원 입력과 공통 코드 역변환으로 보존해 고유89개를 확인했다. 기존72·이전제품46·
공식249 대기열은 반복하지 않았다. 원 실패·중단·원 bundle의 unused fixture 경고2종은 그대로다.
전체100.703초·명령25.516초/시험1.44초·Job CPU23.875초·CPU최고29.49%·가용RAM최저36.2434%·
Job private최고5.1452%다. Job active0/empty/handle closed·affinity4 단일 bit·BelowNormal·CPU cap6.25%·
private cap8%/stop7%·RAM/commit95%·명령300초·guard600초와 입력 전후 검증을 유지했다.
근거는 evidence/p09-361-regex-replacement-components112.v1.json, evidence/p09-361-regex-replacement-recovery113.v1.json,
evidence/p09-361-regex-replacement-focused114.v1.json과
[정규식 원본 치환 core](../../protocol/migrations/p09-source-selector-regex-replacement-v1.md)다.
이 core의 현재 저장/엄격한 정규식 제품 JSON은 다음 절에서 보완했다. 빈 일치 삽입·전체 계약/Native는 남는다.

## 정규식 치환의 현재 저장과 제품 요청

product-regex-replacement-request/v1은 필수 replace_regex·regex=true·query/replacement·case/whole-word/max·
run_policy·두 body 정책과 selector/revision·source/head/key/plan을 받는다. 원 v4의16KiB unique JSON/object
parser를 추출해 공유하고 기존 파일 전체를 역변환 대조했다. 문법·값/형식은 읽기 전에 검사하며 group 존재와
pattern/좌표 의미는 원 core에서 검사한다. 기존 literal v1~v4는 Regex 조합을 받아들이지 않는다.

prepare/into_review_selector_regex_candidate는 현재 write/scope/head/ACL/quarantine/AEAD·전체 원본 proof와
한 capture compiler를 사용하고 원 LiteralSource Borrowed/Owned로 소유권만 옮긴다. private candidate의
매 verify/바이트 전달은 원 fresh_source·writer integrity·callback 직전 head를 확인한다. query/capture/lowering과
소유권 이동용 clone/reimport는 반복하지 않는다. template SHA/bytes와 ordered expansion SHA/bytes를 구분하며
원본/범위/policy/run/max/work·raw/canonical/provider scope/key/plan을 결속한다. 실행/commit/CAS/claim은 추가하지 않는다.

components116은 신규13+영향기존v4/v6제품16=29pass·586fresh/final586·diagnostics없음·cleanupTrue다.
발견 JSON→네 범위·부분 NFC/제어보존·일치별 값·정책4종/제외우선상한·strict/정확한16KiB·legacy분리·
template/expansion 지문 구분·write/5개외부scope·ACL철회/복구·격리/AEAD·prepare/verify/bytes 최종head경합·
pattern/ref/match/writer/output/work 상한·borrowed/owned/JSON 동등성과 원본/head/ingest보존을 확인했다.
이전core89·무관한suite·공식249 대기열은 반복하지 않았다. 전체109.250초·명령34.140초/시험2.46초·Job CPU32.062초·
CPU최고29.55%·가용RAM최저35.8753%·Job private최고5.1831%이며 active0/empty/handle closed다.
affinity4 한 bit·BelowNormal·CPU cap6.25%·private cap8%/stop7%·RAM/commit95%·명령300초·guard600초와
입력 전후 검증을 유지했다. 근거는 evidence/p09-361-regex-product-components116.v1.json과
[정규식 제품 요청](../../protocol/migrations/p09-regex-replacement-product-request-v1.md)이다.
이 v1 제품 경로는 실제 빈 일치·제어 atom·필드 cache 쓰기를 계속 거부한다.
별도 v2 source 삽입은 다음 절의 범위에 한정하며 전체 transaction/Native/Gate 자격으로 올리지 않는다.

## 정규식 빈 일치의 원본 삽입

별도 source candidate/v2는 RightOriginalPointElseLeftFirstEmptyText 정책으로 원본 NFC cut을 확인한다.
오른쪽 원본 point를 우선하고 block 끝에서는 왼쪽 끝, 빈 문단에서는 첫 admitted hp:t를 쓴다.
원 run/서식을 보존하며 탭·줄바꿈 바깥과 빈 paired/self-closing hp:t에 텍스트를 삽입한다.
자기 닫힘은 원래 /> shell만 확장하고 이름·속성·공백·닫는 이름과 선택 밖 bytes를 대조한다.
원본 text owner 없는 문단이나 NFC 분해/재정렬로 모호한 cut은 임의 보정하지 않고 거부한다.
기존 v1 API/제품 JSON의 빈 일치 거부, field cache/상위 field·보호 검사는 유지한다.

블록별 prefix/suffix, 타깃별 control edge를 한 번 계산한다. atom 배열의 반복 중간 삽입을
정렬된 경계와 원 atom의 단일 병합으로 바꿨으며 한 capture pass·원 preserving transaction을 공유한다.
components118은78pass/8fail이며 빈 질의였던8개 입력11곳만 (?:)로 고쳤다. production과78개 통과를
보존하고 빈 질의 거부1개를 추가한 recovery119는9pass+영향제품29pass·591fresh/final591이다.
전체 시험 파일을 역변환 대조했으며 신규19+기존core/patch68+제품29=고유116개다.
linear120은 병합 최적화 영향19개만19pass·592fresh/final592·diagnostics없음·cleanupTrue다.
원 compiler의 v2 병합 밖과 전체 projection을 역변환 대조했으며 기존97개·공식249 대기열은 반복하지 않았다.

linear120 전체102.328초·명령26.500초/시험1.77초·Job CPU24.891초·CPU최고29.31%·가용RAM최저35.9864%·
Job private최고5.1719%(1647.82MiB)이며 affinity4 한 bit·BelowNormal·CPU cap6.25%·private8%/stop7%·
RAM/commit95%·명령300초·guard600초를 유지했다. 소유 Job은 active0/empty/handle closed다.
이는 PC 프리즈 해결이나 통제된 benchmark 증거가 아니다. 근거는 evidence/p09-361-regex-insertion-components118.v1.json,
p09-361-regex-insertion-recovery119.v1.json, p09-361-regex-insertion-linear120.v1.json과
[빈 일치 원본 삽입 프로필](../../protocol/migrations/p09-source-selector-regex-insertion-v2.md)이다.
이 source v2의 현재 저장 서비스와 엄격한 제품 요청은 다음 절의 범위로 연결했다.

## 빈 일치 정규식의 현재 저장과 제품 연결

product-regex-replacement-request/v2는 기존 regex operation에 필수 insertion_policy를 추가한다.
right_original_point_else_left_first_empty_text만 허용하고 누락/null/배열/미지 값·decoded-name 중복을
읽기 전에 거부한다. 원16KiB unique object parser와 typed validator를 공유하며 schema·정책·전체 요청을
canonical/provider-scoped 지문에 결속한다. 기존 v1/literal은 새 필드를 받지 않는다.

원 fresh source/Form proof·한 capture compiler와 Borrowed/Owned를 사용하며 소유권 이동용 clone/reimport를
추가하지 않았다. 원 source receipt 검증 조건을 공유하고 v2 정책·정확한 경계·text-only 자격을 private
후보에 결속한다. 매 verify/bytes는 현재 source/access·원 writer integrity·callback 직전 head를 확인하며
검색/캡처/치환을 반복하지 않는다. 실행/commit/CAS/claim/게시 경로를 추가하지 않는다.

components123은32KiB 진단 출력 상한으로 중단돼 시험 완료 미확인/cleanupTrue다. 원 실패를 보존하고
child 선언만 원 매크로 뒤로 옮겨 짧은 compiler 진단을 사용했다. production·신규 시험 본문·fixture와
상한은 동일하다. recovery124는신규18+영향기존29=47pass·598fresh/final598·diagnostics없음·cleanupTrue다.
네 범위/빈 선택·원 run/NFC/제어/빈 요소·정책/제외우선상한·strict/16KiB/legacy분리·지문·권한/
ACL/격리/AEAD/최종head경합·borrowed/owned/JSON·보호/한도·privacy/source/head/ingest보존을 확인했다.
원 v1 저장/제품 전체 파일과 기존13개 시험 본문을 역변환 대조했고 source core·무관한suite·공식249는 반복하지 않았다.

전체85.266초·명령8.484초/시험3.79초·Job CPU7.312초·Job private최고2.1696%(691.26MiB)·시스템CPU최고75.2%·
가용RAM최저38.2103%다. 시스템 표본을 소유 Job 사용률이나 특정 외부 프로세스 원인으로 해석하지 않는다.
affinity4 한 bit·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했고
소유 Job은 active0/empty/handle closed다. PC 프리즈 해결이나 benchmark를 주장하지 않는다.
근거는 evidence/p09-361-regex-insertion-product-components123.v1.json,
p09-361-regex-insertion-product-recovery124.v1.json과
[빈 일치 정규식 제품 요청](../../protocol/migrations/p09-regex-insertion-product-request-v2.md)이다.
다음은 SEARCH-008 실제 서식 선택·치환·보존 경로다.

## 부분 run 글자 모양 원본 치환

source-selector-character-style-replacement/v1은 네 selector/review 정책과 declared/definition 필터로 찾은
원본 Text scalar에 원 typed catalog의 기존 character-property ID를 적용한다. 부분 run·cross-run NFC를
필요한 경계만 분할하고 entity/본문/제어 값을 복사하며 원 run을 서로 합치지 않는다. 원 QName/허용 속성과
in-scope namespace를 run shell에 유지하고 선택 밖 scalar의 서식을 보존한다. charTcId/미지원 run 속성·
control scalar·NFC 모호성·field cache/상위 field·관측 보호는 그대로 거부한다.

원 Form proof·field/review/index·한 matcher/definition import·preserving transaction·한 출력 import를 쓴다.
target anchor는 동일 typed catalog에서 이동해 별도 header 탐색을 없앴고 이미 파싱한 review를 재사용한다.
중첩 hidden/MEMO/table/note run 편집은 내부부터 합쳐 patch overlap을 없앤다. piece/namespace/fragment의
누적 bytes를 보관 전에 제한하며, 출력의 원 run 밖 gaps/tails·컴파일 bytes·모든 문자/제어 값과 각 scalar의
run/text 참조를 다시 읽어 확인한다. 선언된 참조 교체가 실제 유효 서식 변경/Native/권위라는 뜻은 아니다.

components126은신규18+영향기존40=58pass·603fresh/final603·cleanupTrue다. 변경 밖 원 공통 코드와 시험 본문을
역변환 대조했다. target127은 typed anchor와 독립 oracle 추가 후 영향19개만19pass·604fresh/final604·cleanupTrue다.
기존40개를 보존해 고유59개이며 기존 제품/무관한suite/공식249는 반복하지 않았다. 경고2개는 원본 fixture
review_scope_fixture.rs:5/6의 package/with_body dead_code이며 원본과 경고 기록을 유지한다.

target127 전체107.500초·명령30.359초/시험5.42초·Job CPU28.844초·private최고5.2083%(1659.40MiB)·CPU최고54.53%·
가용RAM최저35.5320%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·
guard600초를 유지했고 소유 Job은 active0/empty/handle closed다. PC 프리즈 해결/benchmark로 승격하지 않는다.
근거는 evidence/p09-361-style-replacement-components126.v1.json, p09-361-style-replacement-target127.v1.json과
[글자 모양 원본 치환 프로필](../../protocol/migrations/p09-source-character-style-replacement-v1.md)이다.
이 source core의 현재 저장 서비스와 엄격한 제품 요청 연결은 다음 절의 components129로 검증했다.

## 부분 글자 모양 치환의 현재 저장과 제품 요청

product-character-style-replacement-request/v1은 필수 replacement.axis=run_character_property·원본 declaration_id·
style_filter·review_policy를 네 selector와 결속한다. 원16KiB unique JSON/object parser를 재사용하며 누락/미지/중복
필드·잘못된 축/범위/값을 읽기 전에 거부한다. regex/case/whole-word/max·source/head·key/plan/provider scope는
typed 요청과 canonical/scoped 지문에 포함한다. 기존 literal/regex 스키마는 새 작업을 거부한다.

현재 write/scope/head/ACL/quarantine/AEAD·whole Form proof와 한 원본 style compiler로 후보를 준비한다.
Borrowed/Owned는 원 소유자를 이동하며 clone/reimport를 추가하지 않는다. 매 verify/bytes는 현재 원본/권한과
writer integrity·consumer 직전 head를 검사하고 검색/서식 lowering을 반복하지 않는다. receipt/key는 실행권위나
멱등 claim이 아니며 dispatcher/ingest/commit/CAS/게시를 추가하지 않았다.

components129는 신규제품18pass·608fresh/final608·diagnostics/경고없음·cleanupTrue다. 네 범위·부분 entity/한글
NFC·두 필터·regex/word·정책4종/제외우선상한·strict/정확한16KiB·legacy분리·지문·write/외부5scope·ACL철회/복구·
격리/AEAD·prepare/verify/bytes 최종head경합·borrowed/owned/JSON동등성·보호/한도·128일치·원본/head/ingest/비노출을
확인했다. 원 roots/기존시험 전체 역변환을 대조했고 기존제품47개와source59개·공식249·무관suite는 반복하지 않았다.

전체120.844초·명령42.610초/시험10.31초·Job CPU40.516초·private최고5.2374%(1668.69MiB)·시스템CPU최고28.12%·
가용RAM최저28.3665%다. 원 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·
guard600초와 active0/empty/handle closed를 확인했다. PC 프리즈 해결/benchmark로 승격하지 않는다.
근거: evidence/p09-361-style-product-components129.v1.json 및
[부분 글자 모양 제품 요청](../../protocol/migrations/p09-character-style-product-request-v1.md).
별도 text-style source core는 다음 절에서 검증했고 문단/이름 스타일과 전체 계약은 남는다.

## Text style 참조의 원본 치환

source-selector-text-style-replacement/v1은 동일 원본 proof·review matcher/typed target·네 selector/정책을 사용한다.
선택 Text scalar의 charStyleIDRef만 바꾸며 원 run/문단 shell과 참조는 그대로 둔다. text 경계만 분할하고
entity/제어 bytes와 모든 원본 scalar·선택 밖 text-style을 보존한다. field cache/상위 field·charTcId·관측 보호·
모호한 NFC/부분분해·지원하지 않는 text 속성·제어 scalar·noops·한도 초과는 전체 거부한다.

기존 shape/v6 ID 프로필은 charStyleIDRef를 허용하지 않으므로 별도 text-style-static/v9에서만 정확한 spine hp:t의
무namespace 속성과 header character domain을 결속한다. 기존 v1~v8은 바꾸지 않으며 미지/다른 위치/namespace·
dangling·잘못된 값·중복 참조 검사를 유지한다. 고정 공식 모델은 속성 존재만 뒷받침하고 Native 의미는 별도다.

131은 helper 컴파일 오류/시험0,132는5pass/11fail이며 실패 원본을 보존한다. 133/134는 실패1개의 닫힌 Patch
변형 진단으로 issue code/기능 PASS가 아니다. id-recovery135는실패11+writer한도1+신규ID5=17pass·616fresh/final616·
diagnostics/경고없음·cleanupTrue다. 출력 전의 음성4개를 보존해 고유21개이며 현재21개 전부 실행으로 합치지 않는다.
writer 한도 오류는 정확한 Writer 거부로 강화했고 기존 v1~v8 엔진/규칙·run 치환·원시험 본문을 역변환 대조했다.
이전 source59·제품47+18·공식249·무관suite는 반복하지 않았다.

전체108.485초·명령28.797초/시험4.79초·Job CPU27.219초·private최고5.2172%(1662.26MiB)·시스템CPU최고29.44%·
가용RAM최저29.5011%다. 기존 한코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·
guard600초와 active0/empty/handle closed를 유지했다. 프리즈 해결/benchmark로 승격하지 않는다.
근거: evidence/p09-361-text-style-id-recovery135.v1.json 및
[text-style 원본 치환](../../protocol/migrations/p09-source-text-style-replacement-v1.md).
이 text-style 후보의 현재 저장/엄격한 제품 요청 연결은 다음 절의 components138로 검증했다.

## Text style 치환의 현재 저장과 제품 요청

product-text-style-replacement-request/v1은 필수 kind=replace_text_character_style·replacement.axis=text_character_style·
원본 declaration_id·style_filter·review_policy와 네 selector를 결속한다. 원16KiB unique JSON/object parser를 공유하고
누락/미지/중복·잘못된 축/범위/값을 읽기 전에 거부한다. regex/case/whole-word/max·source/head/key/plan/provider scope는
typed 요청과 canonical/scoped 지문에 포함한다. 기존 run/literal/regex/search와 새 text 요청은 작업을 상호 혼용하지 않는다.

현재 write/scope/head/ACL/quarantine/AEAD·원 Form proof와 한 text compiler로 후보를 준비하고 원 Borrowed/Owned를
이동해 소유권 전달용 clone/reimport를 추가하지 않는다. verify/bytes는 현재 권한/원본·private receipt/candidate·
writer integrity·consumer 직전 head를 확인하며 검색/치환 lowering은 반복하지 않는다. receipt/key는 권한/멱등 claim이
아니며 dispatcher/ingest/commit/CAS/실행/게시를 추가하지 않았다.

components138은 신규제품18pass·619fresh/final619·diagnostics/경고없음·cleanupTrue다. 네 selector/발견 JSON·owned후보·
entity/한글NFC/상이한run참조·두필터·regex/word·정책4종/제외우선상한·strict/정확한16KiB·legacy상호거부·지문·
write/외부5scope·ACL철회/복구·격리/AEAD·prepare/verify/bytes 최종head경합·borrowed/owned/JSON동등성·보호/정확한
writer거부·128일치·원본/head/ingest/비노출을 확인했다. 원 root/기존시험 전체 역변환을 대조했고 기존제품65·
text-style source21·다른source/공식249·무관suite는 반복하지 않았다.

전체122.125초·명령42.844초/시험10.66초·Job CPU40.766초·private최고5.2508%(1672.95MiB)·시스템CPU최고63.18%·
가용RAM최저29.8710%다. 시스템 표본을 소유 Job 사용률/특정 외부 원인으로 해석하지 않는다. 기존 한코어 affinity4·
BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초와 active0/empty/handle closed를 유지했다.
프리즈 해결/benchmark로 승격하지 않는다. 근거: evidence/p09-361-text-style-product-components138.v1.json 및
[text-style 제품 요청](../../protocol/migrations/p09-text-style-product-request-v1.md).
문단/이름 스타일 축의 실제 원본 치환 core는 다음 절에서 검증했다.

## 문단 모양과 이름 있는 문단 스타일 참조의 원본 치환

source-selector-paragraph-style-replacement/v1은 ParagraphProperty/ParagraphStyle 두 축과 필수
WholeMatchedParagraphWithinScope를 받는다. 일치가 있는 문단의 모든 indexed block이 선택 창 안에 있어야 하며
부분 선택을 문단 밖으로 넓히지 않는다. paraPrIDRef/styleIDRef 중 한 축만 바꾸고 나머지 문단/run/text 참조와
entity/본문/제어 bytes를 보존한다. 원 typed catalog의 PARA 이름 스타일만 허용하고 CHAR/미지 종류는 거부한다.
styleIDRef 변경은 target의 charPrIDRef/paraPrIDRef를 복사하거나 실제 유효 서식을 적용했다는 증거가 아니다.

원 Form proof·field/review/index·한 typed catalog/스타일 검색·한 transaction/출력 import를 사용한다. exact windows는
재계산/clone 없이 이동하고 원 declaration anchor도 한 catalog 순회에서 인덱스로 이동한다. 반복 일치를 문단별
속성 편집 하나로 합치며 part별 보호2N+tracked/prefix1N으로 미검색 자손·상위 추적·필드/cache를 no-op 전에 검사한다.
출력은 속성 편집 밖 전체 bytes·모든 문단 참조·원 scalar/control/run/text 참조와 review를 다시 대조한다.

140은 Properties 조회 컴파일 오류/시험0,141은 기존 iter 조건으로 수정 후37pass/1fail이다. 실패는 새 fixture의
문단 lock 속성이 원 reader에서 Body 거부된 것이며 제품/나머지 시험은 그대로다. 해당 입력1줄만 수입 가능한 잠긴
표 자손으로 바꾼142는 실패1개만1pass·628fresh/final628·cleanupTrue다. 기존37을 보존해 신규20+영향기존18=고유38개다.
원 실패와 원 fixture의 package/with_body 미사용 경고2개를 유지하며 이전 제품83·공식249·무관suite는 반복하지 않았다.

142 전체85.218초·명령4.578초/시험0.12초·Job CPU2.125초·private최고1.8032%(574.51MiB)·시스템CPU최고47.16%·
가용RAM최저28.4418%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초와
active0/empty/handle closed를 유지했다. 프리즈 해결/benchmark로 승격하지 않는다. 근거:
evidence/p09-361-paragraph-style-fixture-recovery142.v1.json 및
[문단 서식 원본 치환](../../protocol/migrations/p09-source-paragraph-style-replacement-v1.md).
두 문단 축의 현재 저장/엄격한 제품 요청 연결은 다음 절에서 검증했다.

## 문단 스타일 치환의 현재 저장과 제품 요청

product-paragraph-style-replacement-request/v1은 replace_paragraph_style_reference 작업에 필수 target 축/원본 ID와
whole_matched_paragraph_within_scope extent·style_filter·review_policy를 받는다. 원16KiB unique JSON/object parser와
네 selector 검증을 공유하며 잘못된 값/누락/미지/중복은 원본 읽기 전에 거부한다. 기존 run/text/literal/regex/search
스키마와 상호 거부하며 query/regex/case/word/max·source/head/key/plan/provider scope를 canonical/scoped 지문에 결속한다.

현재 document.write/scope/head/ACL/quarantine/AEAD·한 Form proof/문단 compiler와 최종 head를 유지한다. borrowed 후보에서
원 소유자를 Owned로 이동하며 clone/재수입을 추가하지 않는다. verify/bytes는 현재 접근·원본·writer integrity와 consumer
직전 head를 확인하되 검색/문단 lowering은 반복하지 않는다. 원본 참조 교체는 유효 서식 적용이나 commit/CAS 권한이 아니다.

144는 시험21개를20개로 기대한 사전 검사 실패·Cargo/시험0이며145는 개수만 수정한 후 시험 helper의 미지원 quick_xml
참조 E0433으로 컴파일 실패·시험0이다. 두 실패를 보존하고 제품/의존성은 바꾸지 않은 채 독립 숫자 속성 판독기와 자체
검사를 수정한146에서 신규제품21pass·635fresh/final635·diagnostics/경고없음·cleanupTrue를 확인했다. 원 roots/기존 시험의
전체 역변환과 나머지 입력 일치를 확인했으며 기존제품83·문단source38·공식249·무관suite는 재실행하지 않았다.

두 축/네 범위/부분선택 거부·entity/cross-run 한글·필터/regex/word·정책4종/제외우선상한·strict/16KiB/legacy분리·지문·
write/5개 외부scope·ACL철회/복구/격리/AEAD·준비/확인/전달 최종head경합·borrowed/owned/JSON 동등성·보호/한도/NFC·
128일치/128문단·별칭/native field ID·원본/head/ingest/비노출을 검증했다. 전체103.156초·명령21.078초/시험13.91초·
Job CPU18.922초·private최고2.3510%(749.05MiB)·시스템CPU최고56.44%·가용RAM최저24.3988%다. 기존 자원 보호와
active0/empty/handle closed를 유지했고 프리즈 해결/benchmark로 승격하지 않는다. 근거:
evidence/p09-361-paragraph-style-product-compile-recovery146.v1.json 및
[문단 스타일 제품 요청](../../protocol/migrations/p09-paragraph-style-product-request-v1.md).
다음은 유효 cascade/숨김과 전체 selector/filter 계약이며 전체 transaction/Native는 미완료다.

## 선택 범위의 직접 서식 해석과 미해결 판정

source-resolved-direct-formatting/v1은 bold/italic/height/RGB/alignment의 비어 있지 않은 조건을 받고 기존 typed catalog의
직접 run/문단 값을 사용한다. 선택 창과 hidden/MEMO 제외를 먼저 적용하고 고유 원 text segment당 한 번 요청 축의
해석 범위를 확인한다. 직접 run 참조 누락 또는 미확정 text-style 우선순위는 글자 축 미해결, 직접 문단 참조 누락은
문단 축 미해결이다. 요청 축 미해결은 검색어가 없어도 Unresolved 오류이며 일치0이 아니다. 요청하지 않은 축의
미해결은 해당 predicate를 막지 않는다. 이름 스타일/ID0/nextStyle을 누락값의 fallback으로 추정하지 않는다.

네 범위 밖과 정책으로 제외된 본문의 미해결은 검색 coverage에 섞지 않지만 원 전체 참조/header admission은 유지한다.
선택 NFC unit의 모든 원 scalar 기여자를 포함하고 빈 창은 고유segment0/서식일치0이다. matcher는 기존 direct 정의
predicate를 재사용하며 별도 source/index/header·범위·정책·query/filter/coverage 지문과 retained navigation을 결속한다.
기존 명시적 검색/치환 계약과 receipt는 바꾸지 않았고 원 두 root는 모듈 선언2개 제거로 전체 역변환된다.

148에서 신규18pass·635fresh/final635·diagnostics/경고없음·cleanupTrue다. 원 typed reader 직접값/복합false조건·
미해결/질의없음/text-style0/1·요청축분리·네 범위/선택밖·숨김/메모 제외우선·NFC·regex/빈일치·원 admission·필터/
범위/원본·커서·정확한 출력/실행한도·128segment/128일치·원본/비노출을 검증했다. 기존 시험·공식249는 반복하지 않았다.
전체108.484초·명령27.094초/시험2.19초·Job CPU25.422초·private최고5.2864%(1684.28MiB)·시스템CPU최고69.14%·
가용RAM최저23.8824%이며 원 자원 보호와 active0/empty/handle closed를 유지했다. 프리즈 해결/benchmark 주장은 아니다.
근거: evidence/p09-361-resolved-style-components148.v1.json 및
[직접 서식 해석 프로필](../../protocol/migrations/p09-source-resolved-formatting-v1.md).
현재 저장/제품 연결은 다음 절에서 검증했다. text-style 우선순위·누락축·Native visibility는 아직 미해결이다.

## 직접 서식 해석의 현재 저장과 v9 제품 요청

product-source-search-request/v9는 find_resolved_style 작업에 필수 query/regex/case/word/max_results·비어 있지 않은
서식 filter·review_policy와 네 selector를 받는다. 원16KiB unique JSON/object parser를 공유하고 누락/미지/중복·
잘못된 값은 원본 읽기 전에 거부한다. 기존 v1~v8 스키마와 상호 거부하며 미해결 요청 축은 typed Resolution/Unresolved
오류를 그대로 전달한다. 원본 해석의 미확정 우선순위/누락을 성공한 일치0 검색으로 바꾸지 않는다.

저장 v9는 기존 write/scope/head/ACL/quarantine/AEAD·원 Form proof·한 해석/index와 원 finish/fresh_json/verify/JSON
경계를 공유한다. 확인/전달은 현재 원본/결과 무결성과 consumer 직전 head를 재검사하고 질의/해석은 반복하지 않는다.
원 next parser·전체 제품 receipt 문맥·결과 커서를 재사용해 앞/뒤/순환/소진을 제공하며 next의 최종 head도 유지한다.
원8종 body/receipt/navigation/parser/기존 시험은 추가 variant/arm/모듈 제거로 전체 역변환된다.

150 신규제품20pass·639fresh/final639·diagnostics/경고없음·cleanupTrue다. 네 범위/owned request drop·direct/복합false·
미해결/질의없음·요청축/선택밖·정책4종/제외우선·strict/16KiB/legacy분리·지문·write/5개 외부scope·ACL/격리/AEAD·
네 단계 최종head경합·저장/JSON 동등성·next 방향/순환/소진/strict/receipt/커서·stale입력·정확한 출력/실행한도·NFC·
128segment/일치·원본/head/ingest/비노출/닫힌route·빈선택을 확인했다. 기존제품104·해석source18·공식249는 반복하지 않았다.
전체121.843초·명령39.422초/시험6.42초·Job CPU37.875초·private최고5.3195%(1694.85MiB)·시스템CPU최고41.02%·
가용RAM최저23.9416%이며 기존 자원 보호와 active0/empty/handle closed를 유지했다. 프리즈 해결/benchmark 주장은 아니다.
근거: evidence/p09-361-resolved-style-product-components150.v1.json 및
[직접 서식 해석 v9 제품](../../protocol/migrations/p09-resolved-style-product-v9.md).
다음은 text-style 우선순위·누락축·Native 숨김 의미와 전체 selector/filter 계약이며 전체 실행/게시/Native는 미완료다.

## 제어 내부 서식 문맥과 기존 원본 거부

공식 ctrl/t의 charStyleIDRef 저장 지점을 확인하고 상위 hp:ctrl의 미해석 문맥이 있는 원 segment를 글자 축 Unresolved로
유지했다. 선택 part당 한 parent map과 정렬된 선택 cursor를 공유하며 일치마다 재파싱/조상 탐색을 하지 않는다. 형제·
선택밖·정책제외·빈 창에 문맥을 넓히지 않고 t+ctrl 중복은 segment당 한 번 센다. 별칭 namespace와 외부 속성을 구분한다.
원 filter/coverage shape/직접 predicate/v7 의미와 저장/권한/최종head는 바꾸지 않았다.

읽기 전용153은 준비fixture3+과거저장/재열기경로7의 XML20·p35·run59·t52에서 text/control-style 참조0·숨은설명0을
관측했다. 해당 조건 없는 표본을 Native 우선순위/숨김 근거로 승격하지 않는다. 152 모델pin 조회 KeyError와 원본은 보존했다.
154는24pass/2fail/제품0이며 새 MEMO ctrl-style 입력이 원 Form Body에서 거부돼 기대한 해석에 도달하지 못했다.
원 reader/production은 유지하고2개 source와 미실행제품1개의 기대를 원 Body 거부와 admitted hidden Unresolved로 분리했다.
155는 수정source2+제품26=현재28pass·645fresh/final645·diagnostics/경고없음·cleanupTrue다. 원24를 보존해 고유52개
(신규8source/6product+영향18source/20product)이며 단일 현재52개가 아니다. 통과24·무관제품104·공식249는 반복하지 않았다.
전체127.250초·명령2.984/41.266초·시험0.29/7.64초·Job CPU1.750/39.578초·private최고5.3198%(1694.93MiB)·
시스템CPU최고44.85%·가용RAM최저24.3244%이며 기존 보호와 두 Job active0/empty/closed를 유지했다. 프리즈 해결 주장은 아니다.
근거: evidence/p09-361-control-style-context-recovery155.v1.json 및
[제어 스타일 문맥](../../protocol/migrations/p09-control-style-context-v1.md).
실물 의미/원 MEMO admission은 미해결이며 다음 접근허용 불필요 작업은 SEARCH-022 실제 원본 Unicode 정규화다.

## 실제 원본 Unicode 정규화

명시적 NFC/NFD/NFKC/NFKD와 FirstOriginalRunRetainAllRuns 정책으로 네 selector의 원본을
변환한다. 검색용 NFC를 원본 수정으로 가장하지 않는다. 원래 review 정책과 exact 창을 이동해
사용하고 불완전·불연속 원본 역상은 거부한다. run/t 사이 결합은 지원하지만 탭·줄바꿈·기존
block 경계는 넘지 않는다. 변하지 않은 scalar는 원래 위치와 서식을 유지하고 변경된 최소 성분만
첫 원본 기여자 위치에 출력한다. 원 shell/참조·선택 밖 entity와 제어를 보존한다.

한 원본 proof·field/review/index·writer·output import를 사용한다. part별 보호3N과 segment별
한 TextSpan/atom 위치 표를 공유하고 no-op 전에 관측 잠금·상위 추적·field cache를 검사한다.
MEMO는 원 소유 payload만 허용하며 전체 선택에 cache가 들어 있으면 조용히 건너뛰지 않고 거부한다.
실제 테이블 Unicode17.0.0과 요청 형태/정책/범위는 receipt에 결속하며 라이브러리의 독립 결과와
모든 변환 그룹을 대조한다. 공통 atom readback은 전체 역변환으로 원 본문을 보존한 채 공유했다.

157은 시험 모듈 import 누락으로 컴파일 실패/시험0, 158은78pass/3fail이다. 제품 변경 없이
잘못된 추적 속성·NFD 변경 개수·원 selector Scope 오류의 세 시험을 바로잡고 실제 호환 분해
확장 상한 검사도 추가했다. 159는 수정3pass·654fresh/final654·진단/경고없음·cleanupTrue다.
통과78개를 반복하지 않아 신규24+영향기존57=고유81개이며 현재81개 단일 실행으로 합치지 않는다.
159 전체87.469초·명령3.437초/시험0.42초·Job CPU2.578초·private최고580.07MiB/1.8206%·
시스템CPU최고33.2%·가용RAM최저27.0673%이고 Job active0/empty/handle closed다.

이 source core의 현재 저장 서비스·엄격한 선택 범위 제품 요청은 아래에서 별도로 검증했다.
전체 요청의 query/filter·보호·실행/commit/CAS/멱등/게시·Native/SEARCH-022 완료는 아직 아니다.
[원본 정규화 프로필](../../protocol/migrations/p09-source-unicode-normalization-v1.md)에 정책과
원 실패157/158 및 성공159의 경계를 기록했다. 공식158/249·잔여91·next165는 변하지 않았다.

## 선택 범위 Unicode 정규화 저장과 제품 요청

product-unicode-normalization-request/v1은 필수 kind=normalize_unicode_scope·form=nfc/nfd/nfkc/nfkd·
run_policy·review_policy와 네 selector를 현재 sealed 원본에 연결한다. 원16KiB unique JSON/object
parser와 selector 검증을 공유하며 누락/미지/중복·잘못된 값과 미지원 query/filter를 원본 읽기 전에
거부한다. 기존 문자열/정규식/서식/검색 요청 의미는 바꾸지 않는다.

current write/scope/head/ACL/quarantine/AEAD·원본 Form proof와 한 compiler를 사용한다.
기존 Borrowed/Owned 소유자 이동으로 clone/reimport를 추가하지 않으며 verify/bytes는 정규화를
반복하지 않고 현재 접근·원본·writer integrity·최종 consumer head를 확인한다. 지문/key는
권한이나 key claim이 아니고 실제 ingest/commit/CAS/실행/게시는 열지 않는다.

components161 신규제품20pass·657fresh/final657·진단/경고없음·cleanupTrue다. 네 형태/범위·
discovery·요청 drop·cross-run/entity/상이한 참조·제어·재정렬 서식 유지·review/cache·strict/
중복/16KiB/legacy·지문·현재 권한/다섯 외부 scope·ACL/격리/AEAD·세 단계 최종 head 경합·
borrowed/owned/JSON 동등성·잘못된 source/head/doc/project/revision·보호/no-op/한도·128성분·
비노출/닫힌 route/원본/head/ingest 보존을 확인했다. source81·기존제품130·공식249는 반복하지 않았다.
기존 root와 시험 parent의 본문은 각 module 선언 한 줄 제거로 전체 역변환된다.

전체127.188초·명령43.297초/시험8.20초·Job CPU41.344초·private최고1705.17MiB/5.3519%·
시스템CPU최고31.84%·가용RAM최저23.4919%이며 Job active0/empty/handle closed다.
검색어·서식 필터 결합의 별도 source core는 아래에서 검증했다. 그 match 후보의 저장/제품·transaction/Native/Gate는 미완료이며
공식158/249·잔여91·next165와 P10 미시작은 그대로다.
[제품 요청 프로필](../../protocol/migrations/p09-unicode-product-request-v1.md)에 요청/검증 경계를 기록했다.

## 검색 일치 원본 Unicode 정규화

source-match-unicode-normalization/v1은 기존 literal/regex와 명시적 선언/typed 정의 서식
matcher 중 한 branch를 사용해 원본 일치의 정확한 scalar 집합을 정규화한다. 기존 선택 창과
review 제외를 먼저 적용하고 모든 NFC 기여자가 서식 조건을 만족해야 한다. 검색용 NFC
문자열로 원본을 덮어쓰거나 인접 일치를 합치지 않는다. partial/noncontiguous 원본 역상과
빈 일치는 거부하며 NoMatches/NoChange를 구분한다. regex는 NFC corpus 위의 문법을 유지한다.

source v1 scope compiler의 보호·정규화·patch·한도 본문을 공통 함수로 추출하고 전체 역변환해
대조했다. 한 Form proof·field/review/index·matcher·writer·output import와 part/segment별
map을 공유한다. receipt는 실제 검색 일치와 query/filter/form/정책을 결속하며 출력 profile은
v2로 구분한다. 기존 source/저장제품 v1 의미·권한/head 경계는 바꾸지 않았다.

components163은41pass/1fail이며 실패는 분해형 regex가 NFC corpus에도 일치한다는 새 시험의
NoMatches 기대 오류다. 제품과 통과41개를 보존하고 원 패턴의 정확한 거부 및 NFC 패턴의 탭
보존 검사를 같은 실패 시험에 넣었다. recovery164는 수정1pass·663fresh/final663·진단/경고없음·
cleanupTrue다. 신규18+영향기존24=고유42개이며 현재42개 단일 실행으로 합치지 않는다.
통과41개·무관source57·기존제품150·공식249는 반복하지 않았다.

163 시스템CPU최고65.23%·private최고1694.05MiB/5.3170%이며 164는 전체86.672초·명령1.875초/
시험0.19초·Job CPU1.781초·private최고575.61MiB/1.8066%·시스템CPU최고24.62%·가용RAM최저26.8442%다.
두 Job active0/empty/handle closed와 원 자원 보호를 유지했다. 시스템 표본을 검증 단독 CPU나
프리즈 원인으로 해석하지 않는다. 이 match 후보의 현재 저장/엄격한 제품 요청은 아래 별도 v2에서 검증했다.
[검색 일치 정규화 프로필](../../protocol/migrations/p09-source-unicode-match-normalization-v1.md)에
정확한 정책과 실패163/복구164의 경계를 기록했다.

## 검색 일치 Unicode 정규화 저장과 제품 v2

product-unicode-normalization-request/v2는 필수 normalize_unicode_matches·query/regex/case/
whole-word/max_matches·form/run/review 정책과 선택적 선언/typed 정의 style_filter를 받는다.
원16KiB unique JSON/object parser와 네 selector 검증을 공유하고 누락/미지/중복·잘못된
조건을 읽기 전에 거부한다. filter 생략/null은 canonical 결속하며 raw 지문은 구분한다.
기존 v1은 선택 범위 전체 의미를 유지하고 두 버전과 legacy 작업은 상호 거부한다.

현재 write/scope/head/ACL/quarantine/AEAD·원본 Form proof와 한 match compiler를 사용한다.
Borrowed/Owned 소유자를 이동하고 verify/bytes 때 matcher/정규화를 반복하지 않는다.
현재 접근/원본·writer integrity와 consumer 직전 최종 head를 확인하며 source/index/scope/
검색 일치/region/filter/form/정책·raw/canonical/scoped/key/plan을 결속한다. 실제 ingest/
commit/CAS/멱등 key claim/dispatcher/Native/게시는 열지 않는다.

components166 신규제품22pass·666fresh/final666·진단/경고없음·cleanupTrue다. 네 형태/범위와
검색/서식/원본 기여자·review/cache·보존·strict/중복/16KiB/null/v1/legacy·지문·현재권한/
다섯 외부scope·ACL/격리/AEAD·세 단계 최종head경합·borrowed/owned/JSON동등성·잘못된 source/
head/revision/doc/project/index·NoMatches/NoChange/빈일치/역상/보호/no-op·한도·비노출/닫힌route/
source/head/ingest 보존·128일치 공유map을 확인했다. source42·기존제품150·공식249는 반복하지 않았다.
원 v1 모듈/시험 parent는 module 선언 한 줄 제거로 전체 역변환되고 원본 compiler는 그대로다.

전체129.718초·명령44.547초/시험10.91초·Job CPU42.594초·private최고1703.56MiB/5.3469%·
시스템CPU최고32.33%·가용RAM최저23.3025%이며 Job active0/empty/handle closed와 원 자원 보호를
유지했다. [제품 v2 프로필](../../protocol/migrations/p09-unicode-match-product-request-v2.md)에
명시적 요청과 아직 남은 방향/유효 서식·통합/target 경계를 기록했다.
SEARCH-013의 명시적 변환 정책과 원본 compiler는 다음 절에서 검증했다. Unicode의
전체 계약/transaction/Native/Gate는 미완료이며 공식158/249·잔여91·next165는 유지한다.

## 원본 검색 일치 대소문자 변환

source-match-case-conversion/v1은 명시적 Uppercase/Lowercase와 UnicodeDefaultEachMatchedTextGroup으로
정확한 원본 글자를 변환한다. 네 selector/review·literal/regex·명시적 선언/typed 정의 필터를 사용하고
원 NFC 기여자 역상을 확인한다. 기존 검색용 NFC를 원본으로 쓰거나 옆 일치를 합치지 않는다.
한 TEXT 그룹의 run/text 경계는 문맥을 유지하고 제어/block/선택밖/다른 일치는 문맥 경계다.

Rust std Unicode17 문자열 변환을 한 번 수행하고 글자별 확장 길이로 원본에 배분·대조한다.
FinalSigma 문맥과 확장 글자를 처리하되 locale/titlecase/casefold/자동 정규화는 하지 않는다.
할당 전 scalar/byte 상한을 확인하며 같은 원 atom의 연속 변경만 합쳐2만 글자는 한 patch다.
원 서식·entity·제어·참조를 보존하고 기존 정규화 보호/patch/한도는 공유 추출 후 전체 역변환했다.
한 원본 proof·field/review/index·matcher·writer/readback과 part/segment map을 공유한다.

components168은 Point import 누락 E0425로 시험0이다. import만 고친169는63pass/1fail이며
실패는 새 시험이 본문이 아니라 XML 전체의 k를 센 기대 오류다. 제품을 유지하고 이 한 시험을
review4정책의 전체 section 및 다른 ZIP entry 보존 비교로 강화했다. recovery170은 수정1pass·
673fresh/final673·stdlib참고3/final3·진단/경고없음·cleanupTrue다. 신규22+영향기존42=고유64개이며
단일 현재64개 실행으로 합치지 않는다. 통과63개·무관source57·제품172·공식249는 반복하지 않았다.
원 실패168/169는 보존했고 기존 Unicode 의미와 현재 저장/제품 권한 경계는 그대로다.

169 시스템CPU최고62.31%·private최고1706.36MiB/5.3557%이며170 전체91.188초·명령4.250초/
시험0.84초·Job CPU2.922초·private최고577.45MiB/1.8124%·시스템CPU최고75.59%·가용RAM최저29.4735%다.
두 Job active0/empty/handle closed와 원 자원 보호를 유지했다. 시스템 표본을 검증 단독 CPU나
프리즈 원인으로 해석하지 않는다. [대소문자 원본 프로필](../../protocol/migrations/p09-source-case-conversion-v1.md)에
정확한 정책과 검증 범위를 기록했다. 현재 저장 서비스·엄격한 제품 JSON은 다음 절에서 검증했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작과 미완료 Native/전체 계약은 그대로다.

## 대소문자 변환 저장과 제품 요청

product-case-conversion-request/v1은 필수 convert_case_matches·query/regex/case/whole-word/max_matches·
upper/lower·명시적 문맥/review 정책과 선택적 선언/typed 정의 필터를 현재 sealed 원본에 연결한다.
원16KiB unique JSON/object parser와 네 selector 검증을 공유하고 누락/미지/중복·잘못된 조건을
읽기 전에 거부한다. filter 생략/null은 canonical 결속하며 raw 지문은 구분한다. locale/titlecase/
자동 정규화/replacement/방향을 무시하지 않고 거부하며 기존 제품 요청의 의미는 넓히지 않는다.

현재 write/scope/head/ACL/quarantine/AEAD·원본 Form proof와 한 case compiler를 사용한다.
Borrowed/Owned owner 이동으로 clone/reimport를 추가하지 않고 verify/bytes 때 matcher/변환을
반복하지 않는다. 현재 접근/원본·writer integrity·consumer 직전 최종 head와 source/index/
검색/region/filter/mode/policy·raw/canonical/scoped/key/plan을 결속한다. 실제 ingest/commit/
CAS/멱등 key claim/dispatcher/Native/게시는 열지 않는다.

components173 신규제품22pass·676fresh/final676·진단/경고없음·cleanupTrue다. 두 모드/확장/
문맥·네 범위/clipped regex·명시적 서식/whole-word·review/cache·제어/entity/참조 보존·strict/중복/
16KiB/null/legacy·지문·현재권한/다섯 외부scope·ACL/격리/AEAD·세 단계 최종head 경합·borrowed/
owned/JSON동등성·잘못된 source/head/revision/doc/project/index·NoMatches/NoChange/빈일치/역상/
보호/no-op·한도·비노출/닫힌route/source/head/ingest 보존·128일치 공유map·2만 글자 단일patch를 확인했다.
source64·기존제품172·공식249는 반복하지 않았다. 원 두 root 모듈/시험 parent는 선언 한 줄씩
제거로 전체 역변환되고 source compiler와 기존 제품/시험/fixture는 그대로다.

전체133.891초·명령47.687초/시험11.79초·Job CPU45.719초·private최고1716.68MiB/5.3880%·
시스템CPU최고40.82%·가용RAM최저24.6525%이며 Job active0/empty/handle closed와 원 자원 보호를
유지했다. [제품 요청 프로필](../../protocol/migrations/p09-case-product-request-v1.md)에 정책과 경계를 기록했다.
SEARCH-014 전각·반각 변환의 명시적 정책과 원본 compiler는 다음 절에서 검증했다.
대소문자의 전체 통합/transaction/Native/Gate는 미완료이며 공식158/249·잔여91·next165는 유지한다.

## 원본 검색 일치 전각 반각 변환

source-match-width-conversion/v1은 필수 Fullwidth/Halfwidth·Unicode17WidthPairsWithKanaPairs·
FirstOriginalRunRetainAllRuns로 정확한 원본 일치를 변환한다. Unicode17 wide104+narrow122=226쌍과
표현 가능한 가타카나28쌍을 사용하며 runtime 표/이진 탐색 index 전체를 추출 fixture와 대조했다.
일반 NFKC·표시 폭·한글/ICU 동등성이 아니며 음절 분해나 다른 호환문자 정규화를 하지 않는다.
한글 호환 자모 폭쌍을 유지하고 반각 기본자가 없는 가타카나는 근사 치환하지 않는다.

네 selector/review·literal/regex·선언/typed 정의 필터와 정확한 원본 역상을 사용한다. 같은 TEXT
그룹의 실제 폭 변경이 있는 가타카나 쌍만 결합하며 제어/block/다른 일치/선택밖은 경계다.
결합 결과는 첫 기여자에 두고 원 run shell/서식·제어·참조·비변경 entity를 보존한다. 같은 원 atom의
연속 변경만 합쳐2만 글자·4096쌍은 한 patch다. 한도 사전확인·단일 pending unit·이진 탐색과
한 원본 proof/field/review/index/matcher/writer/readback 및 공유 part/segment map을 사용한다.

components175 신규원본24pass·683fresh/final683·진단/경고없음·cleanupTrue다. 폭226쌍/가타카나28쌍
양방향 전수·범위/서식/문맥·review/cache·보존·proof/source·무일치/무변경/빈일치/역상/보호/no-op·
한도·후보 idempotence·비노출·장문을 확인했다. 원 atoms root는 module 선언 한 줄 제거로 전체
역변환되며 공통 plan/보호/writer와 기존 제품/시험/fixture는 그대로다. 기존제품194·원본64·공식249는 반복하지 않았다.

전체120.656초·명령33.172초/시험7.69초·Job CPU31.547초·private최고1710.41MiB/5.3684%·
시스템CPU최고54.09%·가용RAM최저26.5859%이며 Job active0/empty/handle closed와 원 자원 보호를
유지했다. [전각 반각 원본 프로필](../../protocol/migrations/p09-source-width-conversion-v1.md)에
원 UCD17·추출 fixture·license와 정책/검증 경계를 기록했다. 현재 저장 서비스·엄격한 제품 JSON은 다음 절에서 검증했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작과 미완료 Native/전체 계약은 그대로다.

## 전각 반각 변환 저장과 제품 요청

product-width-conversion-request/v1은 필수 convert_width_matches·query/regex/case/whole-word/max_matches·
fullwidth/halfwidth·width/run/review 정책과 선택적 선언/typed 정의 필터를 현재 sealed 원본에 연결한다.
원16KiB unique JSON/object parser와 네 selector 검증을 공유하고 누락/미지/중복·잘못된 조건을
읽기 전에 거부한다. filter 생략/null은 canonical 결속하며 raw 지문은 구분한다. 미지원 정규화/
locale/replacement/방향을 무시하지 않고 거부하며 기존 제품 요청의 의미는 넓히지 않는다.

현재 write/scope/head/ACL/quarantine/AEAD·원본 Form proof와 한 width compiler를 사용한다.
Borrowed/Owned owner 이동으로 clone/reimport를 추가하지 않고 verify/bytes 때 matcher/변환을
반복하지 않는다. 현재 접근/원본·writer integrity·consumer 직전 최종 head와 source/index/
검색/region/filter/mode/policy·Unicode17 대응표 원본 SHA·폭226/가타카나28·raw/canonical/scoped/
key/plan을 결속한다. 실제 ingest/commit/CAS/멱등 key claim/dispatcher/Native/게시는 열지 않는다.

components177은 이전 작업명 enum의 사전 정적 대조 거부로 Cargo/제품시험0이다. enum 한 곳만
ConvertWidthMatches로 수정하고 다른 입력을 대조해 유지했다. components178 신규제품24pass·
688fresh/final688·진단/경고없음·cleanupTrue다. 두 모드/가타카나/폭 의미·네 범위/서식/문맥·review/
cache·제어/entity/참조 보존·strict/중복/16KiB/null/legacy·지문·현재권한/다섯 외부scope·ACL/격리/
AEAD·세 단계 최종head 경합·borrowed/owned/JSON동등성·잘못된 source/head/revision/doc/project/index·
NoMatches/NoChange/빈일치/역상/보호/no-op·한도·비노출/닫힌route/source/head/ingest 보존·128일치 공유map·
2만 글자 단일patch를 확인했다. source24·기존제품194·공식249는 반복하지 않았다. 원 두 root 모듈/
시험 parent는 선언 한 줄씩 제거로 전체 역변환되며 원본 compiler/표는 그대로다. 짧은 prefix와
실제24개 전체 identity 대조를 함께 사용했고 원 사전 실패177은 보존했다.

전체138.422초·명령50.219초/시험12.04초·Job CPU48.109초·private최고1720.37MiB/5.3996%·
시스템CPU최고40.52%·가용RAM최저25.3686%이며 Job active0/empty/handle closed와 원 자원 보호를
유지했다. [제품 요청 프로필](../../protocol/migrations/p09-width-product-request-v1.md)에 정책과 경계를 기록했다.
다음 접근허용 불필요 작업은 SEARCH-023 공백·탭·줄바꿈 정규화의 명시적 정책과 원본 compiler다.
폭 변환의 전체 통합/transaction/Native/Gate는 미완료이며 공식158/249·잔여91·next165는 유지한다.

## 공백과 구조적 탭 줄바꿈의 타입 지정 편집 기반

ReplaceWhitespaceAtomRanges는 원본 Text의 공백 범위·기대 종류가 맞는 Tab/LineBreak·명시적
empty TextSpan만 받는다. 출력은19개 model-admitted Unicode17 공백 문자와 typed Tab/LineBreak다.
일반 글자 삭제·임의 XML을 거부하며 기존 raw 제어 문자와 일반 TextAtom 경로의 제어 변경 거부는
유지한다. 이 저수준 기반의 상위 원본 연결은 아래 별도 정규화 절에 기록하며 저장/제품은 미완료다.

원 reader/scalar scanner와 atom별 단일 cursor를 사용하며 namespace는 원 QName에서 구한다.
원 태그·서식·비선택 entity/바이트·다른 ZIP entry를 보존하고 empty self-closing t는 닫힘만 확장한다.
새/기존 두 range 계열의 공동 건수·escaped 출력 예산과 output atom/value/fragment/shell 한도를
적용한다. byte-disjoint라도 다른 계열이 같은 target을 공유하면 거부한다. 원 patch engine/ID profile/
validation·old atom reader/scanner 본문은 전체 역변환으로 대조했다.

components180은 XmlByteSpan→Range 타입 변환 누락 E0308로 시험0이며 원 실패를 보존했다.
그 타입 변환만 고친181은 신규24+영향atom10/leaf9=43pass·692fresh/final692다. 제품을 유지하고
혼합 range cap과 비겹침 shared target 시험 두 개만 강화했다. strengthening182는 수정2pass·
693fresh/final693·진단/경고없음·cleanupTrue다. 변경 없는41개를 보존해 고유43개이며 단일 현재43개
실행으로 합치지 않는다. 변경 없는41개·기존제품218·공식249는 반복하지 않았다.

181 시스템CPU최고43.18%·private최고1713.75MiB/5.3788%이며182 전체92.063초·명령3.188초/
시험0.14초·Job CPU2.141초·private최고575.36MiB/1.8059%·시스템CPU최고37.70%·가용RAM최저28.9681%다.
두 Job active0/empty/handle closed와 원 자원 보호를 유지했다. [공백 제어 편집 프로필](../../protocol/migrations/p09-whitespace-atom-patch-v1.md)에
정확한 경계와 검증 근거를 기록했다. 원본 정책·검색/selector·보호 compiler와 제어 변경 후 readback은 아래 별도 검증했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작과 미완료 Native/전체 계약은 그대로다.

## 원본 검색 일치 공백 탭 줄바꿈 정규화

source-match-whitespace-normalization/v1은 정확한 원본 검색 일치·네 selector·review 정책·선언/
typed 정의 서식 필터를 whitespace/control patch에 연결한다. Text 입력 정책은 None/ASCII space/
Unicode17 breaking16/all model-admitted19로 구분하며 NBSP·figure space·narrow NBSP는 all에서만
포함한다. 구조적 Tab/LineBreak 포함 여부와 연속 축약/개별 scalar, 고정1~1024칸/typed Tab/
LineBreak/삭제를 명시한다. 첫 원본 기여자에 출력을 두고 일반 글자·문단/run shell·선택 밖 제어/
entity·참조는 보존한다. 서로 다른 일치·문단과 미선택 whitespace/control은 축약 문맥을 잇지 않는다.

한 원본 proof·field/review/index·matcher·writer와 part별 보호3N·segment별 TextSpan/offset map을
공유한다. no-op을 버리기 전에 잠금·상위 추적·field cache를 거부하고 정확한 MEMO payload 허용
경계를 유지한다. 원 guard는 가시성만 넓혔으며 본문은 전체 역변환으로 대조했다. 기존 요소/slot
불변 readback은 변경하지 않았다. 별도 sparse 원본 byte edit/독립 canonical 출력 전수 대조와
안정적인 t 순서/출력 TextSpan 검증으로 제어 변경과 뒤 element index 이동을 확인한다. 실제
namespace·숫자 길이의 공동 출력 byte 예산을 할당 전에 검사한다.

components184는 fixture assembly import 누락 E0432로 시험0이며 원 실패를 보존했다. import와
출력 할당 전 예산·nested output strictness를 보강한 recovery185는 신규 원본24pass·700fresh/
final700·진단/경고없음·cleanupTrue다. 네 selector/서식·review/cache·typed 제어 생성/삭제·출력 index
이동·보호/no-op·NFC 역상·한도·비노출·독립 byte tamper oracle·2만 공백 단일 patch를 확인했다.
기존 patch43·제품218·공식249는 반복하지 않았다.

185 전체122.266초·명령32.688초/시험6.15초·Job CPU31초·private최고1728.36MiB/5.4247%·
시스템CPU최고40.62%·가용RAM최저27.1205%다. Job active0/empty/handle closed와 원 자원 보호를
유지했다. [원본 공백 정규화 프로필](../../protocol/migrations/p09-source-whitespace-normalization-v1.md)에
정확한 정책과 보존 경계를 기록했다. 현재 저장 서비스·엄격한 제품 JSON 연결은 아래 별도 검증했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작과 미완료 Native/전체 계약은 그대로다.

## 공백 탭 줄바꿈 정규화 저장과 제품 요청

product-whitespace-normalization-request/v1은 필수 normalize_whitespace_matches·query/regex/case/
whole-word/max_matches·전체 whitespace/run/review 정책과 선택적 선언/typed 정의 서식 필터 및
네 selector를 현재 sealed 원본에 연결한다. 원16KiB unique JSON/object parser와 selector 검증을
공유하며 누락/미지/중복·잘못된 정책/조건은 원본 읽기 전에 거부한다. 필수 text/tabs/line_breaks/
sequence/output과 typed 출력 내부 속성까지 검증한다. filter 생략/null은 canonical 결속하고 raw
지문은 구분한다. 미지원 direction/locale/normalization/replacement를 무시하지 않고 거부하며
기존 요청 의미는 넓히지 않는다.

현재 write/scope/head/ACL/quarantine/AEAD·원본 Form proof와 한 whitespace compiler를 사용한다.
Borrowed/Owned 소유자 이동으로 clone/reimport를 추가하지 않고 후보 verify/bytes는 matcher/
정규화를 반복하지 않는다. 현재 접근/원본·writer integrity·consumer 직전 최종 head와 source/
index/검색/region/filter/정책·raw/canonical/scoped/key/plan을 결속한다. key/receipt는 권한·key
claim이 아니며 실제 ingest/commit/CAS/영속 멱등 실행/dispatcher/Native/게시는 열지 않는다.

components187 신규 제품24pass·703fresh/final703·진단/경고없음·cleanupTrue다. 축약/개별/삭제·
typed Tab/LineBreak/고정 칸·명시적 NBSP·네 범위/서식/문맥·review/cache·cross-run/alias/default
namespace/entity/참조·strict/nested/중복/16KiB/null/legacy·지문·현재write/다섯 외부scope·ACL/
격리/AEAD·세 단계 최종head 경합·borrowed/owned/JSON동등성·stale source/head/revision/doc/
project/index·보호/no-op/역상·한도·비노출/닫힌route/source/head/ingest 보존·128일치와2만 공백을
확인했다. 원 두 root 모듈과 시험 parent는 선언 한 줄씩 제거로 전체 역변환되며 원본 compiler/
보호/readback과 기존 제품 본문은 그대로다. 원본24·기존제품218·공식249는 반복하지 않았다.

187 전체141.219초·명령51.328초/시험12.42초·Job CPU48.828초·private최고1738.89MiB/5.4578%·
시스템CPU최고52.84%·가용RAM최저26.2659%다. Job active0/empty/handle closed와 원 자원 보호를
유지했다. [공백 정규화 제품 요청](../../protocol/migrations/p09-whitespace-product-request-v1.md)에
정확한 준비 계약과 미완료 통합 경계를 기록했다. 다음 접근허용 불필요 구현은 SEARCH-009
지원 제어별 원본 치환과 참조/ID 보존이다. SEARCH-023 전체 통합/target/transaction/Native/Gate는
미완료이며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작은 그대로다.

## 탭 줄바꿈에서 일반 텍스트로의 타입 지정 치환 기반

ReplaceTextControlAtoms는 원본 qualified TextSpan의 실제 Tab/LineBreak atom과 기대 종류만 받는다.
기존 reader가 허용하는 일반 Text·typed Tab/LineBreak 출력과 명시적 삭제를 지원하되 원래 Text를
삭제하거나 가상의 atom을 만들지 않는다. XML처럼 보이는 텍스트도 escape하며 raw 제어 문자·
미지/opaque shape·stale/역순/중복/다른 종류는 거부한다. 표·필드·각주·개체의 일반 치환이나
검색/선택·관측 source 보호 연결은 아래 별도 원본 compiler에 기록하며 현재 저장/제품과 전체 SEARCH-009는 미완료다.

한 부모의 original control cursor와 원 QName의 namespace를 사용한다. escaped Text를 제한
아래 직접 출력해5배 임시 문자열을 만들지 않는다. 새 control·기존 whitespace/TextAtom/LeafScalar
네 계열의 내부 범위/typed 출력 atom 개수·escaped 실제 출력 byte 예산을 공유하고 byte-disjoint라도
같은 target을 공유하면 거부한다. 새 intent가 없으면 새 preflight는0이며 기존 예산과 거부 조건은
같다. 원 patch engine/ID profile/dispatch·whitespace reader/renderer 본문은 전체 역변환했다.

components189는 시험 helper의 PackageGraph API명 오류 E0599로 시험0이며 원 실패를 보존했다.
제품을 유지하고 build API 호출 한 줄만 고친 recovery190은 신규18pass·708fresh/final708·진단/
경고없음·cleanupTrue다. Unicode/escape·mixed typed 출력/삭제·원 atom/namespace/selector·
네 계열 혼합 한도와 동일 target 거부·2천 control 단일 cursor·20만 ampersand의 작은 예산 거부·
기존 텍스트/공백 경로의 거부 유지를 확인했다. 기존 patch/원본/제품242·공식249는 반복하지 않았다.

190 전체94.453초·명령3.657초/시험2.07초·Job CPU3.438초·private최고574.8MiB/1.8041%·
시스템CPU최고38.49%·가용RAM최저30.3866%다. 소유 Job active0/empty/handle closed와 원 자원
보호를 유지했다. [텍스트 제어 편집 프로필](../../protocol/migrations/p09-text-control-atom-patch-v1.md)에
경계와 근거를 기록했다. 실제 control_anchor의 검색/선택·보호 compiler와 변환 후 readback은 아래 별도 검증했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작과 미완료 Native/전체 계약은 그대로다.

## 실제 원본 control anchor의 탭 줄바꿈 치환

source-selector-text-control-replacement/v1은 실제 Tab/LineBreak control_anchor를 네 selector와
review 정책으로 검색해 일반 Text·typed 제어·명시적 삭제 후보를 만든다. 같은 selector에서 온
완전한 원본 단일 control unit/atom 대응을 추가 확인하며 anchor start 발견만을 편집 권한으로
올리지 않는다. 일반 글자·선택 밖 제어/entity·run/t 서식·참조를 보존한다. 표·필드·각주·개체 등
다른 관측 종류는 UnsupportedKind이며 raw XML/implicit fallback은 없다.

한 원본 proof·field/review/index·control matcher와 한 scope 해석의 원 windows를 공유한다.
no-op 제거 전에 관측 잠금·상위 추적·field cache를 검사하며 기존 정확한 MEMO 본문 예외만
사용한다. 선택된 부모/종류의 unit만 보관하고 부모별 TextSpan/control map·part별 보호3N·namespace별
독립 출력 인코딩을 공유한다. 출력 validation/hash는 호출당 한 번이며 각 control 복제 전에 실제
escaped byte·누적/atom/원 reader 상한을 검사한다. 원 control 검색 본문은 windows 반환으로
기계적 추출·역변환했고 sparse byte/안정적인 t 순서/readback 본문은 가시성만 넓혀 공유했다.

components192 신규 원본24+영향 선택 범위12=36pass·712fresh/final712·진단/경고없음·cleanupTrue다.
네 범위/완전한 atomic 선택·NFC 경계·review/MEMO/cache·잠금/추적/no-op·opaque 거부·일반
Unicode/typed 출력·namespace/entity/서식/참조·충돌 local ID의2개 part·stale proof/scope·한도/
복제 전 큰 출력 거부·2천 control/한 부모 map·비노출/지문을 확인했다. 변경 없는 patch18·
whitespace 원본24·제품242·공식249는 반복하지 않았다.

192 전체124.156초·명령33초/시험6.34초·Job CPU31.578초·private최고1765.96MiB/5.5427%·
시스템CPU최고53.32%·가용RAM최저28.6169%다. 소유 Job active0/empty/handle closed와 원 자원
보호를 유지했다. [원본 텍스트 제어 치환 프로필](../../protocol/migrations/p09-source-text-control-replacement-v1.md)에
정확한 선택/보호/출력 경계를 기록했다. 현재 저장 서비스·엄격한 제품 JSON 연결은 다음 절에서 검증했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작과 미완료 Native/전체 계약은 그대로다.

## 탭 줄바꿈 치환의 현재 저장과 제품 요청

product-text-control-replacement-request/v1은 필수 replace_text_controls·Tab/LineBreak·
max_replacements1~4096·typed output·review 정책과 네 selector를 현재 sealed 원본에 연결한다.
원16KiB unique JSON/object parser와 selector 검증을 공유하며 nested atom을 포함한 미지/중복/
누락·잘못된 값과 다른 제어 종류를 원본 읽기 전에 거부한다. 빈 output 배열은 삭제이고 빈 Text와
raw 제어 문자는 거부한다. query/replacement/regex/style_filter/preview_only 등 미지원 필드를
무시하지 않으며 기존 제품 스키마나 SEARCH-009 카탈로그 계약의 의미를 넓히지 않는다.

한 불변 ValidatedTextControlOutput이 빌린 payload·kind·limits·semantic SHA를 묶는다. 원본 증명이나
권한이 아니며 lower는 해당 모델의 fresh proof를 요구한다. JSON String 이동·빌린 atom 직렬화와
Borrowed/Owned 원본 이동을 사용하고 한 proof/compiler 이후 검증/전달 때 검색·치환을 반복하지
않는다. 변경 anchor의 ordered subset은 한 forward iterator로 대조한다. 현재 write/scope/head/
ACL/quarantine/AEAD·writer integrity·consumer 직전 head를 유지하며 key/receipt를 실제 ingest/
commit/CAS/영속 멱등 실행/dispatcher/Native/게시 권한으로 쓰지 않는다.

components194 신규 제품24pass·716fresh/final716·진단/경고없음·cleanupTrue다. 네 범위·일반/혼합
typed 출력·삭제/no-op subset·review/cache·namespace/entity/서식/참조·strict/nested/중복/16KiB/
legacy·지문·현재권한/외부5scope·ACL/격리/AEAD·세 단계 최종head 경합·borrowed/owned/JSON동등성·
stale source/head/index·보호/역상/한도·비노출/닫힌route·2천 control과 불변 입력의 proof/limits
오용 거부를 확인했다. 원 source compiler/공개 API와 기존 제품·시험 본문을 추가분 제거로 전체
역변환했다. 원본36·이전 제품242·공식249는 반복하지 않았다. 제품 고유266개이지 현재266개 단일
실행이나 공식 수용 증가가 아니다.

194 전체139.547초·명령48.234초/시험10.12초·Job CPU46.156초·private최고1776.22MiB/5.5749%·
시스템CPU최고33.14%·가용RAM최저29.1281%다. 소유 Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. 다른 앱/OS/Defender 변경없음·프리즈 해결/benchmark 미주장이다. 근거는
evidence/p09-361-control-product-components194.v1.json이며 계약은
[제품 준비 프로필](../../protocol/migrations/p09-text-control-product-request-v1.md)에 기록했다.
다음은 다른 제어 종류의 지원 조건과 참조/ID 보존이며 전체 실행/Native/Gate는 미완료다.

## 자동번호 재시작 제어의 원본 선택 치환

source-selector-number-control-replacement/v1은 네 selector/review 검색의 AutoNumber/NewNumber를
기존 complete number-stream compiler에 연결한다. 원본 outer range 전체의 선택과 원 source proof를
요구하며 저장 i32 번호·명시적 typed 서식만 교체한다. category/ID·문서 시작값·선택 밖 제어와 참조를
유지한다. 원 matcher의 geometry를 공유하고 part별 guard/prefix4N으로 의미상 no-op도 잠금/추적/
field-cache 교차를 먼저 확인한다. 기존 stream compiler·ID profile·독립 byte/번호 readback은 그대로다.

components197 신규20+영향기존36=56개는54pass/2fail이다. 원 실패를 보존하고 구조 제어가 나눈
검색 block을 한 좌표로 가정한 시험1개만 실제 inventory 경계로 수정했다. selection-recovery198은
수정1+원인 분리 진단1=2pass·721fresh/final721·진단/경고없음·cleanupTrue다. 변경 없는54개를
보존해 신규 기능 고유19개+영향기존36개+별도 진단1개다. 현재56개 단일 실행이나 신규20개 전체
통과로 합치지 않으며 기존 제품266·공식249는 반복하지 않았다. 판정은 MIXED다.

원 필수 review 제외/상한 성공 사례1개는 실패 상태로 유지했다. 진단에서 검색기는 숨김 제어를
제외한 뒤 max1로 본문 제어1개를 정확히 선택했다. 기존 번호 수입기는 main/note/caption에 표현되지
않은 review 문단의 번호 제어를 Coverage로 거부하며, 해당 숨김 번호가 없는 기준 원본은 통과한다.
입력/출력의 review-bound complete stream admission이 실제 잔여이며 원 시험을 삭제·완화·ignore하지
않았다. 추가 출력 Form/field/review 수입의 공유도 이 연결과 함께 검토한다.

197 전체82.844초·명령36.297초/시험10.29초·Job CPU34.578초·private최고1773.26MiB/5.5656%·
시스템CPU최고34.86%·가용RAM최저29.3168%다. 198 전체96.688초·명령4.422초/시험1.04초·Job CPU3초·
private최고581.33MiB/1.8246%·시스템CPU최고42.38%·가용RAM최저31.0251%다. 두 Job active0/empty/
handle closed와 기존 한 코어/낮은 우선순위/CPU·RAM 보호를 유지했다. OS/외부 앱 변경이나 프리즈
해결·benchmark 주장은 없다. 근거는 evidence/p09-361-number-control-source-components197.v1.json과
evidence/p09-361-number-control-source-selection-recovery198.v1.json이며 범위는
[번호 제어 source 프로필](../../protocol/migrations/p09-source-number-control-replacement-v1.md)에 기록했다.
저장/제품·다른 제어·전체 계약/Native/Gate는 미완료다.

## Review 결속 번호 수입과 공유 출력 검증

source-selector-number-control-replacement/v1의 원 필수 review 성공 사례를 입력/출력의 실제 모델
연결로 통과했다. import_review_bound는 같은 원본 Form/review의 pointer identity·SHA를 요구하며
실제 관측 Flow에서만 추가 문단을 수집한다. 기존 문단 set은 빌리고 추가 review 문단만 상한 아래
소유한다. 새 source-review-observations-v2 receipt는 review inventory SHA를 결속한다. 기존 strict
import·header/nonspine/미표현 제어 거부와 None 필드가 생략되는 v1 JSON은 유지한다.

stream compiler는 review-bound 입력일 때만 출력 Form/field/review/번호 수입을 공유하고 실제
output_review_import를 보관한다. 기존 strict 입력은 이전 Body 수입 분기를 사용한다. 번호 selector는
공유 receipt를 ReviewWriteContext에 대조하므로 추가 출력 ZIP/XML/Form/field/review 재수입이 없다.
원 보호/scope/no-op·번호 순서/값·frame/참조/선택 밖 byte readback은 그대로며 Native 계산이나
서비스 접근/저장/실행 권한은 아니다.

components200 원 번호 기능20+새 review 연결10+기존 strict 진단1+영향 컨트롤36=67pass·
723fresh/final723·진단/경고없음·cleanupTrue다. 원 성공 시험·네 정책과 제외 후 상한·MEMO payload/
cache·잠긴 no-op/제외 값·foreign model·header Coverage·한도·strict wire/출력 분기·공유 review SHA를
확인했다. 다른 원 importer·번호 compiler/보호/readback과 시험 본문은 명시적 추가·수입 선택·receipt
전달만 역변환하면 복원된다. 원197 실패/198 MIXED를 보존하며 기존 제품266·공식249는 반복하지 않았다.

200 전체133.125초·명령40.422초/시험12.88초·Job CPU38.531초·private최고1771.43MiB/5.5599%·
시스템CPU최고49.02%·가용RAM최저28.2862%다. 소유 Job active0/empty/handle closed와 기존 한 코어/
낮은 우선순위/CPU·RAM·commit·시간 보호를 유지했다. OS/외부 앱 변경이나 프리즈 해결/benchmark
주장은 없다. 근거는 evidence/p09-361-number-control-review-components200.v1.json이다.
AutoNumber/NewNumber 현재 저장 서비스·엄격한 제품 JSON은 다음 절에서 검증했다. 다른 제어·전체 계약·Native/Gate는 남는다.

## 자동번호 재시작 치환의 현재 저장과 제품 요청

product-number-control-replacement-request/v1은 필수 replace_number_controls·AutoNumber/NewNumber·
max_replacements1~4096·저장 i32 번호·22종 typed 서식 또는 명시적 Preserve·review 정책과 네 selector를
현재 sealed 원본에 연결한다. 원16KiB unique JSON/object parser와 selector 검증을 공유하며 nested
서식을 포함한 미지/중복/누락·잘못된 값과 다른 제어 종류를 원본 읽기 전에 거부한다. category/query/
replacement/regex/style_filter/preview_only 등을 무시하지 않으며 기존 제품 스키마의 의미를 넓히지 않는다.

불변 ValidatedNumberControlValues는 빌린 서식·값·두 limit set·한 서식/값 지문을 묶는다. 원본/접근/
실행 권한이 아니며 실제 lower는 fresh source proof와 원 보호/readback을 요구한다. 한 compiler와
Borrowed/Owned 원본 이동을 사용하고 검증/전달 때 검색·치환을 반복하지 않는다. anchor는 한 forward
ordered subset, 번호 노드는 한 순회 집계로 확인하며 canonical payload는 check당 한 번 직렬화해
scoped 지문에 재사용한다. 현재 write/scope/head/ACL/quarantine/AEAD·writer integrity·consumer 직전
head를 유지하며 ingest/commit/CAS/영속 멱등 실행/dispatcher/Native/게시는 열지 않는다.

components203 신규 제품26pass·727fresh/final727·진단/경고없음·cleanupTrue다. 두 종류/i32/22종
서식·네 범위/block 좌표·review/제외 상한/MEMO/cache·no-op subset·strict/nested/중복/16KiB/legacy·
지문·현재권한/외부5scope·ACL/격리/AEAD·세 단계 최종head 경합·borrowed/owned/JSON 동등성·stale
source/head/index·보호/한도/서식 미추정·비노출/닫힌route·256control·불변 입력의 proof/limits 오용과
추가 control0개인 review 문단 상한을 확인했다. 원 source compiler/공개 API와 matcher·기존 제품/
시험 본문은 추가 wrapper/getter/선언 제거로 전체 역변환했다. 원본67·이전 제품266·공식249는 반복하지
않았다. 제품 고유292개이지 현재292개 단일 실행이나 공식 수용 증가가 아니다.

203 전체148.453초·명령55.484초/시험15.73초·Job CPU53.156초·private최고1784.36MiB/5.6005%·
시스템CPU최고34.96%·가용RAM최저27.7413%다. 소유 Job active0/empty/handle closed와 기존 한 코어/
낮은 우선순위/CPU·RAM·commit·시간 보호를 유지했다. OS/외부 앱 변경이나 프리즈 해결/benchmark
주장은 없다. 근거는 evidence/p09-361-number-control-product-components203.v1.json이며 범위는
[번호 제품 준비 계약](../../protocol/migrations/p09-number-control-product-request-v1.md)에 기록했다.
다른 제어·전체 계약·실제 저장/실행·Native/Gate는 미완료다.

## 등록 영수증 기반 읽기 전용 복구

reconcile_registered_stored_commit는 별도 ServiceRequest 파일 없이 DB 조회 키/등록 행과 현재 ACL/AEAD가 확인된
intent/precommit 및 서버 manifest로 복구한다. RegistrationNotObserved·Registered(NotObserved)·Registered(Committed)를
구분하며 missing은 no_effect/재시도 허가가 아니다. 실행/lease/ingest/등록/CAS/작업·시도 변경을 하지 않는다.

신규10+영향 기존12=22pass·297은674fresh/final674·진단없음·cleanupTrue다.
새 전용 DB의298은681fresh/final681·실제3개 검사·진단없음·cleanupTrue다.
요청 fixture를 별도 이름으로 보존해 원 경로가 없는 재시작 후 커밋/결과 관측·등록 부재 구분·다른 manifest 거부를 확인했다.
전후 도메인 상태와 암호화 객체6개 SHA는 같고 재실행하지 않았다. 전체116.672초·시스템CPU최고20.90%·
가용RAM최저43.0679%·postmaster2회 정상 종료·두 Job active0/empty/handle closed다.
CPU cap6.25%·private8%/stop7%·RAM/commit95%는 유지했고 프리즈 해결을 주장하지 않는다.

cas_after의 attempt unknown_outcome 보존은 기존 P14 계약에 부합하며 이력/SQL migration은 바꾸지 않았다.
입력/route/scanner/validator는 합성이고 전체 제품/Native와 남은 거부 경계는 미완료다. 검색19개 기능의 완료 판정은 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[구현·검증·상태 해석과 남은 경계](P09_REGISTERED_RECOVERY_PROGRESS.md)를 따른다.
아래296까지는 이 읽기 전용 복구 진입점 전 이력이다.

## SQL23 응답 유실과 복구

호출자 경계의 합성 응답 유실4개를 실제 SQL/디스크 AEAD에 연결했다. register_after/cas_before는
커밋 미관측과 SQLSTATE55000 거부 뒤 unknown을 유지한다. cas_after는 근거로 성공 복구하고
complete_after는 기존 성공 상태만 읽는다. 이전1개 재사용+이번3개이며 모두 attempt1/fence1,
no_effect 추론·실행 재시도 없음이다. 실제 네트워크 장애 증거는 아니다.

292 보호 중단과293 slug 오류는 보존했다. 단일 cluster/schema·tenant 분리·즉시 사례 checkpoint로 바꿨다.
294 첫 사례의 입력 마무리684fresh/final684 뒤295는685fresh/final685·진단없음·cleanupTrue다.
initdb1회/schema23 적용1회·새 checkpoint3개·postmaster7회 정상 종료·전체123.438초·
시스템CPU최고21.63%·가용RAM최저41.8705%·두 Job active0/empty/handle closed다.
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했으며 프리즈 원인/Defender 인과는 미확정이다.

입력/route/scanner/validator와 주입은 합성이다. 네트워크/crash/키 유실 복구·실제 제품/Native는 미완료다.
cas_after 성공 뒤 attempt_state=unknown_outcome 이력 정합성도 후속 검토한다. 검색19개 기능의 완료 판정은 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[사례·자원·증거와 남은 경계](P09_SQL23_ACK_RECOVERY_PROGRESS.md)를 따른다.
아래291까지는 이 응답 유실 검증 전 이력이다.

## 디스크 AEAD와 SQL23 등록 CAS 완료

sql23_storage는 새 전용 D:/devdata/hwpx-agent-p09-pg18-storage-288에서 실제
ArtifactService/LocalEncryptedBlobStore/PostgreSQL23/PreparedStoredJob를 연결한다.
합성 artifact 행은0개로 시작해 서비스가 실제 AES-GCM 객체와 메타데이터를 만든다.
Source용 실제 lease/CAS/성공 완료로 초기 Result를 만든 뒤 SQL23 job이 실제 의도 등록/조회·
결과 CAS·precommit 영수증을 쓰는 성공 완료를 수행했다. 기존 서비스/엔진/migration과 기존 시험 본문은 바꾸지 않았다.

288은 실행기 observer 연결 AttributeError로 Cargo/DB0,289는 새 probe와 공용 helper의
Result 별칭 충돌 E0107/미사용 import로 DB0이었다. 원 실패를 보존하고 실행기 연결 및 새 probe의 두 선언만 수정했다.
290은675fresh/final675·빌드 진단없음·cleanupTrue다. fixture/초기 저장/SQL23 실행/잘못된 키/재시작 관찰의5회 probe이며
SQL23 작업 실행은1회다. 실제 암호화 객체6개를 DB의 ciphertext SHA/평문 크기+16과 대조했고 잘못된 AES 키는 CryptoFailure로 거부했다.

DB와 Rust 프로세스 재시작 뒤 실제 결과/원본/영수증 복호화·등록 행과 요청 결속·read-only 커밋 복구·
terminal_success replay를 확인했다. 전후 artifact6/available6·job2/성공2·attempt2·authorization0·intent1·
revision2/seal2·head2와 암호화 파일6개 SHA가 같다. 초기 작업과 SQL23 작업 모두 시도1이며 재실행하지 않았다.
키는 부모가 메모리에 보관한 임시 시험 키이므로 운영 KMS/키 복구 자격이 아니다.

290 전체114.422초·빌드2.422초/Job CPU1.922초/private최고704.79MiB·
실제 DB 명령5.938초/Job CPU3.609초/private최고73.33MiB다. 시스템CPU최고27.81%·가용RAM최저43.2051%이며
postmaster2회 정상 종료와 두 Job active0/empty/handle closed를 확인했다. 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했고 원 runtime/DB/실패를 보존했다. 시스템 표본은 PC 프리즈 해결 증거가 아니다.

입력 bytes/route/scanner/validator는 합성이다. 실제 HWPX 의미 검증·scanner/issuer·확인 유실/unknown 복구·
전체 거부 경계·자격 있는 P09 dispatcher/제품 실행/Native/Gate는 미완료다. 다음은 확인 유실 복구와 거부 경계 및 실제 제품 경로 연결이다.
한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다. 검색19개 기능의 완료 판정은 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
근거: evidence/p09-361-sql23-real-storage-compile290.v1.json; ../../target/p09-sql23-storage-observations-288.json.
아래287까지는 실제 디스크 AEAD와 SQL23 등록/CAS/성공 완료 검증 전 이력이다.

## SQL23 작업의 실제 claim과 lease

p09_sql23_jobs는 새 전용 D:/devdata/hwpx-agent-p09-pg18-job-286에서 실제 서비스 계정과
StoredJobLifecycleRepository를 사용한다. 합성 SQL 메타데이터를 초기화하고 기존 Source용 함수의
실제 worker 등록/claim/lease/단계 전환/CAS로 첫 Result revision을 만든다. revision/seal 직접 삽입·
guard 비활성화·애플리케이션에 legacy 실행 권한 부여는 하지 않았다. 이 초기 CAS는 합성 fixture 준비이며
암호화 blob이나 실제 HWPX 제품 검증이 아니다.

새 SQL23의 claim/replay·변경된 요청/비봉인 Source 거부·미등록/잘못된 profile/capability/draining worker 거부·
실제 lease/authorization·중복 lease/다른 execution/단계 생략 거부·순서대로3단계 전환·미커밋 결과의 완료 거부·
최종 replay의15개 검사를 통과했다. 거부10개는 adapter 오류뿐 아니라 같은 요청의 실제 SQLSTATE도 독립 확인한다.
정상 종료/재시작 후 새 Rust 프로세스에서 replay를 확인했고 전후 실제 SQL 상태는 validating/in_progress·
시도1/fence1·attempt행1·authorization행1·intent0·revision1·job2로 같다. 재실행/시도 증가/허위 완료는 없다.

286은228fresh/final228·빌드 진단없음·cleanupTrue다. 전체48.547초·시스템CPU최고20.08%·
가용RAM최저44.8425%이며 postmaster2회 정상 종료와 두 소유 Job active0/empty/handle closed를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했고 원 runtime/DB/실패를 보존했다.
시스템 표본은 PC 프리즈 해결 증거가 아니다.

실제 blob/AEAD/scanner/issuer·SQL23 intent 등록/결과 CAS/성공 완료/확인 유실 복구와
제품 dispatcher/실행 자격은 미완료다. 다음은 실제 파일 저장과 이 등록/CAS 경로다.
한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다. 검색19개 기능의 완료 판정은 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
근거: evidence/p09-361-sql23-job-lifecycle286.v1.json; ../../target/p09-sql23-job-observations-286.json.
아래285까지는 실제 SQL23 job 경로 검증 전 이력이다.

## SQL23 서비스 계정의 실제 접속과 거부

p09_sql23_admission은 별도 ASCII 전용 DB에 고정된 migration1..23/최소 권한 fixture/
두 tenant의 합성 SQL 메타데이터를 적재하고 실제
LocalPostgresMetadataRepository::connect_schema23_diagnosed와
LocalPostgresStoredRevisionJobsRepository::connect를 호출한다. Rust 프로토콜로 원 SQL 바이트를
전달해 prosrc 해시를 유지한다. 기존 migration·서비스 구현과 공식 시험은 바꾸지 않았다.
D:/devdata/hwpx-agent-p09-pg18-role-284만 새로 만들었으며 원 runtime/실패/이전 DB는 보존했다.

한 번 컴파일한 probe를35회 호출했다. fixture 적재/본문 주입·복구3회를 뺀 실제 접속 판정은32회다.
정상 두 계정 접속과 Artifact own/foreign tenant 조회·실제 artifacts 행 RLS·Revision 현재 head와
고정 tenant/subject의6개 검사를 확인했다. 과도한 job 표/column/함수 권한과 replication,
revision column write/직접 intent 조회/필수 claim 누락/legacy claim/기존 control search_path/
새 trigger/RLS/함수 본문 SHA, schema 이름/SHA/미래24의15개 변조를 거부하고 각각 정상 상태
복구를 확인했다. 원284의 actual_profile_probe_calls=35는 전체 호출수이며 접속 판정32회와 구분한다.

284는224fresh/final224·진단/경고없음·cleanupTrue다. 전체55.313초·빌드1.813초/
Job CPU0.984초/private최고311.95MiB, 실제 DB 명령11.406초/Job CPU8.906초/
private최고62.76MiB다. 시스템CPU최고25.05%·가용RAM최저46.1495%이며 postmaster 정상 종료와
두 Job active0/empty/handle closed를 확인했다. 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%를 유지했다. DB는 동기 I/O·병렬 worker0·
fsync/synchronous_commit/full_page_writes on이며 시스템 표본을 PC 프리즈 해결 증거로 해석하지 않는다.

메타데이터는 합성이고 실제 blob/AEAD/scanner/issuer·worker 등록/lease·job 함수/trigger의
실제 실행·등록/CAS·완료/확인 유실/재시작 복구와 P09 제품 실행 자격은 미완료다.
다음은 이 실제 worker와 저장 job 경로다. schema 접속과 변조 거부를 제품 실행 수용으로 올리지 않는다.
비밀번호 원문/전체 로그는 보관하지 않았고 시스템/Defender/WSL 설정·운영 DB·한글/접근 허용 창은 건드리지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다. 검색19개 기능의 완료 판정은 바꾸지 않았다.
근거: evidence/p09-361-sql23-service-admission284.v1.json; ../../target/p09-sql23-role-observations-284.json.
아래283까지는 서비스 계정의 실제 접속/거부 검증 전 이력이다.

## 네이티브 PostgreSQL의 SQL 적용과 재시작

PostgreSQL18.6-5 전용 ZIP에서 bin/lib/share의1583개·147885345bytes를 수입하고
postgres/initdb/psql의18.6 --version을 확인했다. ZIP384620317bytes의 관측 SHA는
e2246ba91d22345bc3d017586c09ede52d9df180b1eeb480f050445f1cad84e2다.
HTTPS 배포 원본과 로컬 해시를 고정한 것이며 vendor 서명/checksum 자격은 아니다.
278은 raw ZIP 이름/파일 부모 충돌의 모델2fail 뒤 네트워크 없이 종료했다.
실패를 보존한279는 두 경계를 수정해 모델12pass·버전3·156fresh/final156을 확인했다.

280의 새 cluster 명령/인증 모델10pass 뒤 한글 경로 initdb가 실패했고 SQL migration과
listener는 시작하지 않았다.281의 새 초기화 전용 진단은 UTF8 invalid byte sequence/0xb0를
확인했다.282는 원 ZIP·runtime·실패 data를 보존하고 동일1583개 SHA와 HBA를
D:/devdata/hwpx-agent-p09-pg18-ascii-282에 복사했다. ASCII 경로에서 initdb 성공·SCRAM
loopback 인증·원 migration1..23 실제 적용·전후 버전/SHA23개·정상 종료/재시작 뒤 표식 보존을
확인했다. 실제 함수 내부 SQL/권한/제품 실행의 완료 판정은 아니다. SQL23을 포함한 migration
파일은 변경하지 않았다. 기존 모델10·Rust·공식249는282에서 재실행하지 않았다.

279 전체97.171초·수입/버전 명령48.922초·Job CPU3.734초·private최고51.21MiB다.
282 전체32.625초·실제 DB 명령8.500초·Job CPU5.953초·private최고54.45MiB·
시스템CPU최고14.07%·가용RAM최저45.7678%·181fresh/final181이다.
두 postmaster 정상 종료와 모든 소유 Job active0/empty/handle closed를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
시험 DB만 shared_buffers16MB·work_mem1MB·연결12개·동기 I/O/병렬 worker0·
fsync/synchronous_commit/full_page_writes on으로 실행했다. Windows/Defender/언어·locale/
서비스/WSL 설정은 바꾸지 않았으며 PC 프리즈 해결을 주장하지 않는다.

SQL23은 이 전용 시험 DB에 실제 생성됐지만 ArtifactService/RevisionService 계정 admission·
실제 RLS/권한 거부·worker·job 함수/trigger·등록/CAS·완료/확인 유실 복구 검증은 미완료다.
다음은 검증된 ASCII 경로의 실제 서비스 계정과 저장 job 실행이다. 비밀번호 원문/전체 로그는
보관하지 않았고 원본·실패 폴더와 정상 종료한 전용 DB는 보존한다. Docker/WSL/시스템 서비스/
한글/접근 허용 창·기존 운영 DB는 시작하거나 접근하지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다. 검색19개 기능의 완료 판정은 바꾸지 않았다.
근거: evidence/p09-361-native-postgres-runtime-boundary-recovery279.v1.json;
evidence/p09-361-native-postgres-init-diagnostic281.v1.json;
evidence/p09-361-native-postgres-ascii-campaign282.v1.json.
아래277까지는 실제 SQL 생성/재시작 전 이력이다.

## SQL23 작업 처리와 1회성 coordinator

ArtifactService SQL23 profile과 예상 precommit 준비는270의 모델6+신규9+영향26=41pass다.
예상값은 실제 봉인된 CAS 요청으로 변환할 수 없다. StoredJobLifecycleRepository는
claim/lease/단계 전환/완료/결과 불명/committed 복구를 기존 SQL23·P14 함수에 연결한다.
기존 migration23개와 저장·등록·CAS 본문은 유지했다. Source 판정이 없는 P14 control2개의
권한·본문 SHA·definer·search_path·PUBLIC·owner 검사를 기존 접속 검사 뒤에 추가했다.

PreparedStoredJob는 manifest와 보관된 후보에서 source/plan/target/예상 효과·precommit을 결속하고
run_once에서 소비된다. 기존 scope 검사를 claim보다 먼저 수행하며 replay는 lease·workspace 생성 없이
반환한다. 새 작업은 실제 받은 lease를 같은 repository의 CAS에 결속한다. 원 엔진/validator 뒤에만
validating을 확인하고 기존 수입·등록·CAS·완료로 이어진다. 완료에 쓰는 Receipt는 intent envelope가 아닌
precommit이다. 단계/CAS/완료 확인 유실은 원 실패·산출물·요청·receipt를 보존하며 자동 재실행하지 않는다.
이 서버 저장 primitive는 P09 제품 route나 Native 실행 허가가 아니다.

271은 음성 SQL 문자열을 실행 코드로 오인한 checker 오류로 Cargo/시험0,272는 decoder 경로 누락
E0425로 시험0이었다.273은 경로만 명시해 신규 lifecycle15pass·914fresh/final914다.
274는 prepare receiver를 잘못 적은 checker 오류로 Cargo/시험0이고275는 제품/시험 변경 없이
checker를 수정해 신규 coordinator9pass·919fresh/final919다. 신규 고유24개이며 기존 lifecycle15와
저장38·engine35·공식249는275에서 반복하지 않았다. 원 실패271/272/274를 보존했다.

273/275 전체119.406/132.782초·명령1.828/14.328초·Job CPU1.641/12.328초·
private최고375.15/876.22MiB·시스템CPU최고24.95/26.56%·가용RAM최저45.1297/44.6472%다.
두 Job active0/empty/handle closed와 scratch 하위 정리를 확인했다. 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 시스템 표본은 검증 단독 부하나
PC 프리즈 해결 증거가 아니다.

실제 서비스 암호화·수입·CAS 코드를 사용했지만 저장소/worker/manifest/scanner/validator는 모델·합성이다.
SQL23 구문·실제 catalog/권한·worker·함수·trigger·DB/프로세스 재시작과 자격 있는 제품 dispatcher
연결은 미완료다. 다음은 이 실제 DB 검증과 실행 자격 결속이다. Docker/DB/한글과 접근 허용 창은
시작하지 않았다. RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
근거: evidence/p09-361-stored-job-lifecycle-compile-recovery273.v1.json;
evidence/p09-361-stored-job-coordinator-checker-recovery275.v1.json.
아래269까지는 coordinator 구현 전 이력이다. 검색19개 기능의 완료 판정은 바꾸지 않았다.

## SQL23 접속 검사와 CAS 전 등록

LocalPostgresStoredRevisionJobsRepository는 별도 loopback 접속에서 schema1..23의 이름/SHA·안전한 role·
기존 guards·강제 RLS/불변 trigger·직접 표/column 권한·11개 새 함수의 본문 SHA/definer/search_path/
PUBLIC 권한을 검사하도록 구현했다. 기존 SQL19~22 접속 함수는 바꾸지 않았다.
받은 lease는 구문만 검사하며 실제 권한은 SQL이 판정한다. 등록/조회와 동적 요청별 lease 결속을
컴파일했지만 SQL23은 여전히 미적용·실제 catalog/권한/함수 실행 미검증이다.

bind_registered는 CAS와 정확히 같은 repository를 registrar로 사용한다. 이미 readback한
result/intent/precommit과 받은 lease·정확한 요청을 등록하고 반환 행을 대조한 뒤 현재 원본/head/결과를
재확인한다. 등록 실패·확인 유실·잘못된 행은 CAS를 호출하지 않는다.
확인 유실은 revision 실행 증거가 아니며 자동 재시도하지 않는다.
registration_response는 거부 응답도 진단용으로 보존하고 registered_job_intent는 검증 뒤에만 채운다.
기존 plain bind는 여전히 실행 자격 없는 저장 primitive다.

components265는 READ_TABLES import 부재 E0425로 시험0, recovery266은 이전 빈 scratch 충돌로
Cargo/시험0이었다. fresh-temp267은 수정된 import와 새 전용 scratch로
모델5+등록9+영향29=43pass·903fresh/final903이었다.
기존 컴파일 migration21개를 새 입력으로 등록해 전체23개를 전후 확인했다.
confirmed268은 진단/확인 결과 분리를 보강하고 단일 음성 assertion을 강화한 뒤
등록9pass·901fresh/final901·진단/경고없음·cleanupTrue다. 모델5/기존29=34개는 재실행하지 않았다.
268 전체128.313초·명령12.000초·시험0.06초·Job CPU10.312초·private최고877.45MiB/2.75400%·
시스템CPU최고26.95%·가용RAM최저46.5261%다. Job active0/empty/handle closed와
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.

접속5는 순수 모델이고 등록 repository/manifest/scanner/validator는 합성·in-memory다.
실제 SQL23 catalog/권한/등록/CAS/DB 재시작 증거가 아니다.
ArtifactService SQL23 profile·typed claim/lease/complete coordinator·실제 DB 검증은 미완료다.
Docker/DB/한글을 시작하거나 시스템 설정을 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[접속과 등록 계약](../../protocol/migrations/p09-stored-revision-jobs-v1.md)을 따른다.

## Precommit receipt와 저장 job 경계

기존 v2 job은 Source만 허용하지만 P09 현재 원본은 sealed revision의 Result다.
별도 미적용 SQL23은 sealed Result를 head/ACL/크기/SHA에 결속하고 기존 v2 claim/lease/retry/complete/
reconcile와 효과 검사의6개 절차를 소스 판정만 바꿔 파생한다. 기존 v2 함수와 전역 Source 판정은 바꾸지
않았다. 의도 ID/SHA와 별도 precommit ID를 job/attempt/fence/authorization·정확한 commit 요청에 묶는
불변 표·등록/조회·커밋 trigger를 작성했다. SQL23은 구문/실행 미검증·미적용이며
Rust schema23 connector/등록 callback도 미연결이다.

v2 완료 판정이 요구하는 transaction SHA는 큰 intent envelope의 SHA가 아니라 엔진 precommit JSON의
SHA다. RevisionCommitRequest::canonical_json과 별도 workspace-precommit.json Receipt 저장·AEAD
readback을 추가했다. intent/두 receipt SHA·UUID는 구분하며 precommit 미확인/손상은 intent/CAS 전에
거부한다. 기존25개 시험 본문은 유지했고 intent 음성 scanner만 해당 파일명에 한정했다.
별도 신규 시험은 precommit 음성을 검사한다.

components261은 새 범위 P14 SQL의 이전 pin 부재, recovery262는 역변환 checker의 줄바꿈 경계 오류로
Cargo/시험0이었다. 원 P14 SQL은 단일 읽기 전용 Git HEAD blob과 일치했다. checker-recovery263은
제품 입력을 바꾸지 않고 checker만 수정하고 저렴한 delta 검사를 전체 source walk 앞으로 옮겼다.
Rust 신규4+영향25=29pass·872fresh/final872·진단/경고없음·cleanupTrue다.
SQL 정적 소스 계약13개(6개 역변환 포함)는 SQL parsing/runtime 증거가 아니다.
전체125.531초·명령12.469초·시험0.19초·Job CPU10.656초·private최고875.66MiB/2.74838%·
시스템CPU최고22.99%·가용RAM최저45.7716%다. Job active0/empty/handle closed와
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.

Rust 저장소는 in-memory이고 manifest/bytes/scanner/validator는 합성이다.
영속 job 등록·실제 DB/프로세스 재시작·P09 실행/Native/Gate는 미완료이며
Docker/DB를 시작하거나 시스템 설정을 바꾸지 않았다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[Precommit와 저장 job 계약](../../protocol/migrations/p09-stored-revision-jobs-v1.md)을 따른다.

## 커밋 의도와 읽기 전용 복구

StoredResultRevisionCas는 실제 CAS 전에 정확한 요청·tenant/subject·manifest/source/result SHA와 크기를
hwpx-agent.stored-revision-commit-intent/v1 Receipt로 ArtifactService에 저장하고 복호화 readback한다.
그 뒤 현재 원본/head/결과 상태를 다시 확인한다. 기존 저장·CAS/Unknown·공유 산출물 보존 절차는
유지하며 의도가 미확인/격리되면 CAS를 호출하지 않는다.

RevisionService::observe_commit는 기존 sealed node reader와 전체 원 요청을 대조한다.
현재 head가 더 진행돼도 원 커밋 receipt를 복원하고, NotObserved를 무효과나 재실행 허가로 해석하지 않는다.
reconcile_stored_commit는 서버가 보관한 기대 식별 정보와 64KiB 이하 의도·현재 ACL/AEAD를 확인한 뒤
읽기만 수행한다. 커밋은 확인됐지만 결과가 격리/읽기 불가이면 Committed/Unavailable로 구분한다.
영속 job의 intent ID/SHA 등록과 기존 v2 멱등 권한 연결은 미완료이며
실제 DB/프로세스 재시작 검증도 NOT_RUN이다.

components259 신규12+영향 기존13=25pass·860fresh/final860·진단/경고없음·cleanupTrue다.
기존13개 시험 본문은 유지하고 영향 검증으로 다시 실행했다. engine26·공식249는 재실행하지 않았다.
전체123.375초·명령12.641초·시험0.16초·Job CPU10.812초·private최고875.72MiB/2.74857%·
시스템CPU최고64.31%·가용RAM최저46.8754%다. Job active0/empty/handle closed와
CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
시스템 전체 CPU를 검증 자체 CPU나 프리즈 해결 증거로 해석하지 않는다.

서비스 코드는 실제 구현이지만 저장소는 in-memory이고 manifest/bytes/scanner/validator는 합성 시험이다.
PostgreSQL의 기존 검증된 sealed reader는 재사용하며 SQL/schema·보안 권한을 변경하지 않았다.
실제 P09 제품 실행/영속 멱등/Native/Gate는 미완료다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[커밋 의도와 복구 계약](../../protocol/migrations/p09-stored-commit-intent-v1.md)을 따른다.

## 저장 서비스와 revision CAS 연결

StoredResultRevisionCas는 서버가 보관한 manifest·출력·validation summary를 엔진의 봉인된 요청에 대조한다.
같은 tenant/subject와 document.read/write, 현재 sealed revision의 source·head·ACL·격리·AEAD를 확인하고
실제 ArtifactService 수입·출력 복호화 readback·마지막 원본/head/결과 상태 확인 뒤 실제 RevisionService
CAS를 호출한다. 이 서버 저장 primitive에는 CLI/MCP/JSON 실행 경로나 P09 자격 발급이 없다.

RevisionCasOutcome::Unknown을 추가했다. 서비스 CommitOutcomeUnknown 또는 요청과 다른 성공 receipt는
RevisionOutcomeUnknown 및 Incomplete/CommittedOutcomeUncertain으로 보존하며 자동 rollback·격리·
재실행하지 않는다. 알려진 충돌/실패의 엔진 로컬 복구는 유지한다. 서비스 산출물은 dedup으로 공유됐을
수 있어 삭제/격리하지 않으며, 반환된 descriptor·서비스 요청/receipt·출력 SHA를 보존한다. 수입 오류에도
저장 부수효과가 있을 수 있으므로 SHA를 통한 조사가 필요하다. 현재 복구 정보는 메모리뿐이고 영속 멱등이나
파일/저장소/DB 분산 원자성이 아니다.

components255는 엔진 신규3+기존23=26pass 뒤 새 서비스 시험의 match arm 반환형 E0308로 컴파일 실패·
서비스 시험0이었다. recovery256은 그 시험 arm만 고쳤고 엔진/서비스 구현과 기존 시험의 해시를 유지했다.
서비스13pass·852fresh/final852·진단/경고없음·cleanupTrue이며 엔진26과 공식249는 반복하지 않았다.
증거 합집합39개 중 신규16개다. 256 전체112.828초·명령3.422초·시험0.08초·Job CPU3.0초·
private최고727.44MiB/2.28318%·시스템CPU최고15.79%·가용RAM최저46.9934%다.
Job active0/empty/handle closed, CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.

서비스 암호화/수입/CAS 코드는 실제 구현이지만 저장소는 in-memory,
manifest/graph/bytes/scanner/validator/validation summary는 합성 시험이다.
실제 HWPX 의미 검증·영속 DB/멱등·현재 P09 제품 실행 연결/자격·Native/Gate는 미완료다.
RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[저장 서비스 CAS 계약](../../protocol/migrations/p09-stored-revision-cas-v1.md)을 따른다.

## bytes 원본 트랜잭션과 게시 무결성

WorkspaceTransaction::execute_bytes는 파일 경로 대신 불변 bytes 원본을 manifest의 크기/SHA에 대조하고
기존 staging·검증·게시·CAS·복구 상태 절차를 공유한다. bytes는 Cow::Borrowed로 사용하며 외부 원본 평문
파일을 요구하지 않는다. 원 파일 입력의 링크/포함 범위/읽기/변경 감지 메서드는 유지한다.
이 엔진 입력 primitive 자체는 P09 제품 실행 허가가 아니다.

probe251은 기존 P04 시험 파일의 원장 누락 KeyError로 Cargo/시험0이다. 원 Git HEAD blob의9개 시험 본문에
새 child만 추가했음을 확인한 probe-recovery252는 staging 변조 뒤 성공이 반환되는 음성 시험 실패1개를
재현했다. 이는 수용0의 결함 증거다. components253은 validator 뒤·게시 뒤·CAS 뒤에 크기/SHA를 스트리밍
재확인하며 CAS 뒤 손상은 Incomplete/CommittedOutcomeUncertain으로 남긴다.
추가 재검사만64KiB 버퍼이며 기존 validator readback 전체 버퍼는 유지한다.

253 신규14+영향 파일9=23pass·844fresh/final844·진단/경고없음·cleanupTrue다.
원 파일9개 시험 본문과 probe의 원 음성 사례를 바꾸지 않았다. 전체111.766초·명령3.344초·시험0.23초·
Job CPU2.062초·private최고440.98MiB/1.38409%·시스템CPU최고19.07%·가용RAM최저56.9722%다.
Job active0/empty/handle closed와 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·
기존 시간 보호를 유지했다. 자식 TEMP/TMP만 target/p09-transaction-byte-scratch-253으로 고정했고
시험 하위 폴더가 비었음을 확인했다. 시스템 설정이나 PC 프리즈 해결을 주장하지 않는다.

실제 filesystem 동작은 자기 소유 시험 scratch이고 manifest/validator/CAS는 합성이다.
실제 ArtifactService 수입·RevisionService CAS·영속 멱등·현재 실행 자격·Native/Gate는 미완료다.
CAS 후 검사도 동시 쓰기를 막는 파일 잠금이나 분산 원자성 보장이 아니다.
원 RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다. [bytes 원본 트랜잭션 계약](../../protocol/migrations/p09-transaction-byte-source-v1.md)을 따른다.

## 다중 그룹 정렬의 공통 계획 연결

다중 part의 실제 이동 목적 slot만 hwpx-agent.source-paragraph-sort-group-splices/v1로 결속한다.
고정 slot·singleton·무변경 그룹은 편집에서 제외하지만 원 receipt에는 남긴다. 전역 대상/복사 byte 상한·
원본 part 순서·목적 anchor/범위·치환 SHA/크기와 원 receipt SHA를 확인한다. XML 조각을 다시 복사하거나
receipt JSON을 바꾸지 않는다. 기존17개 schema를 유지하고 다중 그룹을18번째로 추가했다.
원 final_permutation_splices projection·OperationPlanCompiler·실제 소유자·12개 잠금 argument·manifest 본문을 재사용한다.

components248은 마지막 WORKSPACE_BOUNDED_RECEIPT 저장 상한 실패로 완전한 결과를 복구하지 못했다.
관측된 실패를 별도 보존하고 수용0으로 남겼다. compact249는 값·순서·누락/null/false와 전체 trace/source pin을
유지하는 무압축 compact JSON으로 같은262144byte 상한에 기록한다. 형식4계약 뒤 이번 범위만 재실행하여
원본6+신규 compiler/manifest14+영향기존5=25pass·836fresh/final836·진단/경고없음·cleanupTrue다.
저장된 전체 결과191499bytes는 compact_receipt_json.unpack으로 원래 row를 복원한다.
기존 다중 원본16/제품20·공식249는 반복하지 않았다.

249는 warm 재실행이며 전체121.188초·명령0.875/10.375초·시험0.65/10.14초·Job CPU0.828/10.156초·
private최고53.91MiB/0.16919%·시스템CPU최고23.24%·가용RAM최저48.8148%다.
두 Job active0/empty/handle closed와 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·
기존 시간 보호를 유지했다. 이 수치로 첫248 빌드의 최고 부하나 PC 프리즈 해결을 주장하지 않는다.

실제 P02 routing_allowed=false를 새18번째 schema에서도 원본 읽기 전에 거부했다.
manifest 라우팅 시험은 합성 fixture이며 실제 target/registry·Native 보호·실행/ingest/commit/CAS·영속 멱등/게시
자격이 아니다. 원 RouteUnqualified와 중첩 하위 트리·구조적 키·locale의 미완료를 유지한다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행이다.
[다중 그룹 공통 계획 계약](../../protocol/migrations/p09-sort-groups-operation-compiler-v1.md)을 따른다.

## 다중 그룹 정렬의 현재 저장과 제품 요청

StoredParagraphSortGroupsProductRequest::prepare_json은 별도 hwpx-agent.product-paragraph-sort-groups-request/v1·
sort_paragraph_groups를 현재 저장 원본의 다중 그룹 정렬에 연결한다. 중복 없는16KiB JSON·네 selector·명시적
spec/review 정책을 먼저 확인한다. 원 document.write·scope/head/ACL/quarantine/AEAD·전체 Form proof와
최종 head를 유지한다. 그룹별 순열/anchor 유일성·전역 대상/비교량·이동/변경 그룹/part 수를 대조한다.
Borrowed/Owned는 같은 원본 소유자를 재사용하고 보관한 후보의 verify/전달에서 정렬이나 원본 수입을 반복하지 않는다.

components246 신규 제품20pass·824fresh/final824·진단/경고없음·cleanupTrue다. 두 구역·지역 ID·NFC 양방향
안정성·singleton/무변경 그룹·네 selector와 부분/오래된 범위 거부·닫힌/중복 JSON·정확한16KiB·key/plan/spec/policy
결속·현재 write/외부5scope·ACL 철회/재부여·격리/AEAD·prepare/verify/전달의 최종 head 경합·전역 비교 예산/한도·
hidden/MEMO 두 그룹과 cache 보존·비노출/미게시·128문단을 확인했다. 기존 다중 원본16·단일 source19/제품20/
공통연결21·공식249는 반복하지 않았다. 원 source/정렬/reader/보호/기존 제품/시험 본문은 그대로이며 두 root child와
새 시험 child만 추가했다.

246 전체159.687초·명령52.782초·시험8.14초·Job CPU50.344초·private최고1809.18MiB/5.67837%·
시스템CPU최고59.72%·가용RAM최저46.6415%다. Job active0/empty/handle closed와 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%·기존 시간 보호를 유지했다. 시스템 전체 CPU를 검증 자체 CPU나
프리즈 해결 증거로 삼지 않는다.

새 다중 그룹의 실제 이동 목록·공통 dispatcher/compiler/manifest 연결, 선택된 중첩 하위 트리 합성·구조적 키·locale·
실제 실행/ingest/commit/CAS·영속 멱등/게시는 남는다. 원 RouteUnqualified와 P02 routing_allowed=false는 유지하며
단일 그룹의 공통 계획 증거를 새 API로 승격하지 않는다. source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다. [다중 그룹 제품 요청 계약](../../protocol/migrations/p09-paragraph-sort-groups-product-request-v1.md)을 따른다.

## 다중 부모와 다중 part 문단 정렬

lower_selector_paragraph_sort_groups_candidate는 명시한 selector의 완전한 원본 문단을 part·직접 부모별로
나눠 하나의 원본 기준 순열 트랜잭션으로 정렬한다. 그룹마다 package를 생성하거나 다시 수입하지 않는다.
원 NFC 안정 병합 정렬과 전체 누적 비교 예산·4096 대상·원 보호/field/review 검사를 유지한다.
singleton/무변경 그룹도 검사와 receipt에 남기고 비선택 slot·gap/tail은 제자리에 보존한다.
전체 출력 package/Form 수입과 독립 원문 대조는 한 번이다.

components242와 recovery243은 PackagePath의 Serialize 부재 E0277로 컴파일 실패/시험0이다.
첫 원인 설명의 Debug 미구현 추정은 틀렸으며 PackagePath에는 Debug가 있다. 새 그룹의 비노출 Debug를
유지하고 검증된 PackagePath 타입에 상대 경로 문자열 serializer만 추가했다. serialization-recovery244는
신규16pass·818fresh/final818·진단/경고없음·cleanupTrue다. 원 단일 그룹 API/receipt/비교/보호/patch/writer/
readback/제품 본문은 불변이며 기존 source19/제품20/공통연결21·공식249를 반복하지 않았다.
실패 원본242/243을 보존했다.

244 전체138.531초·명령32.970초·시험2.86초·Job CPU31.859초·private최고1798.73MiB/5.64557%·
시스템CPU최고62.52%·가용RAM최저44.7120%다. Job active0/empty/handle closed와 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%·기존 시간 보호를 유지했다. 시스템 전체 CPU는 검증
자체 CPU가 아니며 프리즈 해결 주장은 없다.

새 다중 그룹 API의 현재 저장/엄격한 제품 요청·실제 splice/common compiler 연결, 선택된 중첩 하위 트리
합성·구조적 키·locale·실제 실행/ingest/commit/CAS·영속 멱등/게시는 남는다. 기존 단일 그룹의 제품/공통
계획 자격을 새 다중 API로 승격하지 않는다. source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다. [다중 그룹 정렬 계약](../../protocol/migrations/p09-paragraph-sort-groups-v1.md)을 따른다.

## 문단 정렬의 실제 이동 목록과 공통 계획

SEARCH-021의 SourceParagraphSortSpliceInventory는 원본 정렬 후보의 실제 이동 목적 slot만 원본 anchor·
원 part byte 범위·치환 SHA/크기에 결속한다. 고정 slot은 편집으로 세지 않으며 기존 SourceParagraphSortReceipt
JSON은 바꾸지 않는다. 공통 dispatcher는 기존16개를 유지하고 정렬을17번째 schema로 추가한다.
공통 projection은 final_permutation_splices를 기존 SelectorSnapshot·OperationPlanCompiler의 실제 구조
소유 node와12개 잠금 argument에 결속한다. 가상 document/임의 첫 문단을 만들거나 정렬을 재실행하지 않는다.

components237은 원본6pass 후 시험 helper 부모의 타입 import 누락 E0432로 제품 시험0이다. 실패 원본을
보존하고 시험 import 한 줄만 추가했다. recovery238은 신규 compiler/manifest12+영향기존3=15pass·
810fresh/final810·진단/경고없음·cleanupTrue다. 원본6+신규제품12+영향기존3=고유21개 통과이며
현재21개 단일 실행이 아니다. 통과 원본6·이전 source 정렬19/제품20·공식249는 반복하지 않았다.
기존 비교/보호/patch/readback/receipt·원16계열 처리와 compiler/owner/router/manifest 본문은 보존했다.

시험은 실제 원본/출력 span·치환 SHA와 크기·고정 slot 제외·legacy receipt/목록 지문·NFC 안정성·128문단,
공통/개별 제품 byte 일치·실제 owner/12개 argument·scope/key/plan/policy 결속·불완전 요청 거부·현재 write/
ACL·compile/verify/전달의 마지막 head 경합·실제 P02 정책 거부를 확인했다. manifest는 합성 라우팅 fixture로만
원 plan/source/route 일치·현재 support/policy/protection/health·실제 문서 보호 신호·마지막 head 거부를 확인했다.

237/238 전체113.844/125.110초·명령26.110/34.656/20.063초·시험0.37/7.16초다. 시스템CPU 최고34.09%·
private 최고1804.04MiB/5.66222%·가용RAM 최저33.8663%이며 세 Job active0/empty/handle closed다.
기존 한 코어·낮은 우선순위·CPU/RAM/commit/메모리·시간 보호를 유지했다. OS 변경이나 프리즈 해결 주장은 없다.

합성 라우팅 증거를 현재 registry/target/Native 자격으로 승격하지 않는다. routing_allowed=false와
RouteUnqualified를 유지하며 실제 실행/ingest/commit/CAS·영속 멱등/게시·다중/중첩 그룹·구조적 키·
locale/target/Native/Gate는 남는다. [정렬 공통 계획 계약](../../protocol/migrations/p09-sort-operation-compiler-v1.md)을 따른다.

## 문단 정렬의 현재 저장과 제품 요청

SEARCH-021의 StoredParagraphSortProductRequest::prepare_json은 hwpx-agent.product-paragraph-sort-request/v1의
닫힌 JSON·네 selector·명시적 정렬/review 정책을 원본 읽기 전에 검사한다. 기존 현재 scope/head/ACL/quarantine/
AEAD·전체 Form proof에 원본 단일 형제 그룹 정렬을 연결한다. Borrowed/Owned는 같은 원본 소유자를 재사용하며
후보 verify/byte 전달은 현재 document.write·원본 접근과 consumer 직전 마지막 head를 확인한다. 정렬은 다시 실행하지 않는다.

components235 신규 제품20pass·802fresh/final802·진단/경고없음·cleanupTrue다. 실제 정렬/원문 보존·borrowed/
owned/JSON 일치·NFC 양방향 안정성·네 selector·부분/오래된 선택 거부·닫힌/중복/escaped JSON·정확한16KiB·
key/plan/spec/policy 결속·현재 write/외부5scope·ACL 회수/재부여·격리/AEAD·prepare/verify/전달의 마지막 head 경합·
보호/필드·한도·무변경·비노출/미게시·128문단·숨김 정책을 확인했다. 원 source 정렬19·patch18·공식249는 반복하지 않았다.
기존 제품/시험 본문은 root별 module child와 시험 child를 제거하면 전체 역변환된다.

235 전체152.296초·명령49.090초·시험6.90초·Job CPU46.734초다. 시스템CPU 최고25.00%·private 최고1801.05MiB/5.65285%·
가용RAM 최저26.7660%이며 Job active0/empty/handle closed다. 기존 한 코어·낮은 우선순위·CPU/RAM/
commit/메모리·시간 보호를 유지했다. OS 변경이나 PC 프리즈 해결 주장은 없다.

기존 RouteUnqualified를 유지한다. 공통 dispatcher/compiler·실제 실행/ingest/commit/CAS·영속 멱등/게시와
다중/중첩 그룹·구조적 키·locale/target/Native/Gate는 미완료다.
[문단 정렬 제품 요청 계약](../../protocol/migrations/p09-paragraph-sort-product-request-v1.md)을 따른다.

## 선택한 원본 형제 문단 정렬

SEARCH-021의 lower_selector_paragraph_sort_candidate는 명시적 NFC Unicode 순서·오름/내림차순으로 같은 부모의
완전히 선택된 원본 문단을 안정 정렬한다. Document/Section/NodeSet/Selection의 기존 원본 창과
review 정책을 재사용하며 부분 문단을 전체로 넓히지 않는다. 다른 부모 그룹·구조적 키를 일부만 처리하지 않고 거부한다.
전체 Form proof·원본 보호/추적 변경·필드 구간을 확인한 뒤 원 순열 intent·기존 writer를 통과한다.
한 번의 출력 Form/field/review 수입에서 모든 원본 하위 요소와 slot 사이의 바이트를 독립 대조한다.

NFC 동등 키의 원본 순서를 오름/내림 양쪽에서 유지한다. 명시적 비교 byte 예산의 fallible 병합 정렬로
긴 공통 prefix의 반복 비교 비용도 제한하고 초과 시 부분 결과 없이 거부한다. 원본 run·entity·탭·줄바꿈은
다시 쓰지 않는다. receipt에는 키의 SHA만 있고 원문·locale/Native/현재 서비스 실행 자격은 없다.

components230은17pass/2fail이다. 새 표 문단 ID1이 원 바깥 문단과 충돌했고 자기 닫힘 빈 문단은 원 reader
비허용 형태였다. diagnosis231은 id_index_validation_failed를 관측했으나 추가 allowlist 검사에서 실패했다.
두 fixture만 고유 ID901/허용된 빈 Text 문단으로 고치고 원 UnsupportedShape 거부도 음성 검사로 확인했다.
제품·reader·ID 검사는 변경하지 않았고 원 실패/진단을 보존했다. recovery232는 그2개만pass·796fresh/final796·
진단/경고없음·cleanupTrue다. 신규 고유19개 통과이며 현재19개 단일 실행이 아니다. 통과17개·이전 patch18·공식249는 재실행하지 않았다.

19개는 네 selector·부분/외부/중복/오래된 범위 거부, stable NFC 키·비연속 slot·빈 Text·run/탭/줄바꿈,
proof 재사용/외부 원본 거부·무변경·비교 작업량/입출력 상한·비노출·추적 변경/필드 거부·부모 분리,
숨김/MEMO 정책·동일 표 셀 정렬/상속 잠금·128문단의 결정적 출력을 확인했다.
230/232 전체79.906/107.500초·명령26.985/3.360초·시험0.96/0.39초다. 231 진단까지 시스템CPU 최고29.10%·
private 최고1791.06MiB/5.62150%·가용RAM 최저26.6083%이며 세 Job active0/empty/handle closed다.
기존 한 코어·낮은 우선순위·CPU/RAM/commit/메모리·시간 보호를 유지했다. OS 변경이나 프리즈 해결 주장은 없다.

다중 부모/중첩 합성·구조적 키·현재 저장 서비스/엄격한 제품 요청·공통 compiler·실제 실행/저장·target/Native/Gate는 남는다.
[원본 문단 정렬 계약](../../protocol/migrations/p09-source-paragraph-sort-v1.md)을 따른다.

## 원본 형제 요소 순서 변경

PatchIntent::PermuteSiblingElements는 같은 불변 part·부모의 원본 하위 요소 바이트만 명시한 순열로
교환한다. XML을 재작성하거나 namespace를 추가하지 않는다. slot 사이의 주석·텍스트·선택 밖 요소는
제자리에 남고, 각 하위 요소의 지역 namespace와 상속 문맥은 같은 부모에서 유지된다. 전체 대상 수와
실제 이동 복사 바이트를 transaction 누적으로 제한하며 기존 selector·ID/참조·겹침·보존·writer 검증을 유지한다.

components227은 신규11+기존6=17pass/1fail이다. 잘못된 양성 fixture의 PI가 원 SafeXml의
ProcessingInstructionForbidden에 걸렸다. 허용된 주석으로 바꾸고 정확한 PI 거부 음성 검사를 추가했으며
제품·보안 파서는 변경하지 않았다. 원 실패를 보존한 recovery228은 그1개만pass·786fresh/final786·
진단/경고없음·cleanupTrue다. 신규12+영향기존6=고유18개 통과이며 현재18개 단일 실행이 아니다.
통과17개·원 crypto/보호/compiler·공식249는 재실행하지 않았다.

시험은 서로 다른 길이·Unicode·entity·지역/상속 namespace, 비선택 요소/주석/간격, 고정 slot의 비복사,
잘못된 크기/순열/역순/중복/부모/중첩/root/외부 원본·part, 겹치는 삭제/속성/순열, 누적 대상/byte 한도와
정확한 경계, ID/참조 보존·dangling 거부 및1000개 형제 요소의 결정적 출력과 writer 재열기를 확인했다.
227/228 전체77.312/104.297초·명령26.312/3.000초·시험1.32/0.01초다. 두 실행의 시스템CPU 최고18.89%·
private 최고1784.83MiB/5.60195%·가용RAM 최저26.1195%이며 두 Job active0/empty/handle closed다.
기존 한 코어·낮은 우선순위·CPU/RAM/commit/메모리·시간 보호를 유지했다. OS 변경이나 프리즈 해결 주장은 없다.

이 기반은 SEARCH-021 전체 정렬이 아니다. 명시적 comparator·선택 범위·문단 소유/보호·정렬 후보와
제품 요청·실제 실행/저장·target/Native/Gate는 남는다. [원본 순열 계약](../../protocol/migrations/p09-sibling-permutation-v1.md)을 따른다.

## 보존된 P02 registry의 실제 서명 검증

p09-pinned-p02-registry-evidence/v1은 기존 P02-09의 정확한963624byte envelope·공개 trust policy/
공개키 pin과 실제 ring Ed25519·canonical payload/내장 registry SHA·target/policy/sequence·전체536개
binding projection/coverage를 확인한다. 개인 서명키는 읽지 않고 P02 원본/정책·과거 probe를 변경/재실행하지 않는다.

PinnedP02RegistryEvidence는 역사적 SignedSupportClaim을 한 번 색인한다. candidate32/unavailable504·
서명된 verified2/failed1/blocked17/not_run12이며 실행 경로0이다. routing_enabled/execution_authority와
runtime_probe_reexecuted/current_installed_target_observed는 false다. 원문/base64/raw binding은 공개하지 않는다.
prepare_compiled_search_json_with_pinned_registry는 닫힌 schema 분류 뒤 원본 읽기/후보 준비 전에
routing_allowed=false로 거부하며 caller approved/support/target/registry_trust나 복제 receipt로 우회하지 않는다.
서명 유효함은 현재 PC/Native 동작이나 P09 실행 자격이 아니다. 원 RouteUnqualified는 유지한다.

components225 신규 crypto12+제품6=18pass·780fresh/final780·진단/경고없음·cleanupTrue다.
실제 서명·변조/공개 trust pin·Base64 padding/한도·중복/escaped/nested JSON·claim 색인/비노출과
모든16개 검색 스키마의 원본 접근 전 정책 거부를 확인했다. 원본/보호44·compiler36·공식249는 반복하지 않았다.
원 compiler와 기존 제품/시험 본문은 module/시험 child 한 줄씩 제거하면 역변환된다.

225 전체125.281초·두 명령6.641/18.468초·시험0.36/1.29초·Job CPU합23.000초·private최고996.93MiB/3.1290%·
시스템CPU최고52.34%·가용RAM최저28.0415%다. 두 Job active0/empty/handle closed와 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%·시간 상한을 유지했다. 현재 P09 target/registry·Native 보호·
실행/저장 트랜잭션·Native/Gate는 미완료다. [고정 P02 서명 소비 계약](../../protocol/migrations/p09-pinned-p02-registry-evidence-v1.md)을 따른다.

## 원본 전체 보호 신호와 manifest 결속

source-protection-signals/partial-v1은 같은 실제 원본의 모든 admitted part/XML에서 기존 sensitive
이름 판정과 HP lock/TC/SZ guard를 재사용한다. META-INF signatures/encryption/rights 및 header/settings의
보수적 문서 신호는 caller Unprotected context로 우회할 수 없다. 로컬 잠금은 원 선택 guard를 유지하며
선택 밖 잠금을 전역 잠금으로 확대하지 않는다. 신호 부재는 보호 없음이 아니다.

SourceProtectionObservation은 document·source SHA/provenance·전체 part/XML/element 수에 결속된다.
native_protection_verified/cryptographic_signature_verified/execution_authority는 false다.
prepare_execution_manifest의 원 현재 byte 검증 안에서 한 번 관측하고 보관하며 verify/전달에서 다시
관측하거나 추가 ZIP/원본 수입을 하지 않는다. 원 현재 권한·routing/최종 head와 RouteUnqualified는 유지한다.

components222 원본10pass·제품33pass/1fail을 보존했다. 임의 문단 lock의 양성 fixture가 기존 Body
수입에서 거부됐으며 같은 형태의 음성 시험도 강화했다. 제품 코드 변경 없이 기존 수입 검증된 잠긴 표로
두 fixture만 고친 recovery223은 선택 밖 보존 양성·선택 안 정확한 Compile::Protection 거부를2pass·
764fresh/final764·진단/경고없음·cleanupTrue로 확인했다. 원본10+신규제품8+영향manifest26=고유44개이며
현재44개 단일 실행이 아니다. 통과42개·무관 compiler36·공식249는223에서 반복하지 않았다.

223 전체108.390초·명령10.450초/시험0.59초·Job CPU9.047초·private최고988.14MiB/3.1014%·
시스템CPU최고18.85%·가용RAM최저28.0594%다. 222 시스템CPU최고58.59%·Job private최고1859.44MiB/5.8361%다.
두 Job active0/empty/handle closed와 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·
시간 상한을 유지했다. 원 native scanner/local guard·기존 compiler/route와 다른 시험 본문은 보존했다.
전체 Native 보호·서명·신뢰 registry/target·실행/저장 트랜잭션·Native/Gate는 미완료다.
[원본 보호 신호 계약](../../protocol/migrations/p09-source-protection-signals-v1.md)을 따른다.

## 실제 원본 계획의 실행 manifest 연결

기존16개 치환·변환의 prepare_execution_manifest는 실제 provider 소유 원본 후보·compiled plan을
원 CapabilityRouter와 ExecutionManifest::from_receipts에 직접 연결한다. source artifact/SHA/크기·
revision·plan을 후보에서만 가져오며 caller source/plan/route receipt는 받지 않는다. 원 후보를 이동하고
현재 접근·byte 전달과 routing 뒤 최종 head를 유지한다. route_plan은 같은 불변 context/catalog 안에서
capability별 판정을 공유하고 operation ID를 따로 결속한다. 호출 밖 cache나 health lease는 없다.

milliseconds clock과 service seconds의 checked_mul(1000) 일치·정확한 target profile SHA·현재 route/
manifest 지문을 확인한다. DirectHwpx 후보는 Hybrid/Automation을 거부한다. 보관 후 verify/전달에서
현재 routing만 다시 판정하고 source import/검색/compiler는 반복하지 않는다. 원 RouteUnqualified는 그대로다.

components218은 Deserialize 부재 설명 주석의 정적 오인으로 Cargo0·시험0 실패이며 보존했다.
제품 주석과 시험 match 분기의 버려지는 반환값만 수정한 recovery219는 신규26pass·756fresh/final756·
진단/경고없음·cleanupTrue다. 모든16계열,128편집과20개 혼합 capability의 원 개별 route 동등성,
부분 결과 거부·원 거부 조건·clock/overflow·target/registry/health/backend drift·현재write/외부5scope·
ACL/격리/AEAD·routing 뒤 마지막 head 경합·transaction/key 결속·비노출을 확인했다. 기존36개·공식249는
반복하지 않았다. 원 개별 router/보안·기존 compiler/제품/시험 본문은 역변환·불변 입력으로 보존했다.

219 전체176.375초·명령79.734초/시험15.56초·Job CPU77.125초·private최고1870.93MiB/5.8722%·
시스템CPU최고26.17%·가용RAM최저23.6163%다. Job active0/empty/handle closed와 원 한 코어·BelowNormal·
CPU cap6.25%·private8%/stop7%·RAM/commit95%·시간 상한을 유지했다. 시험 경로 증거는 합성 fixture이며
실제 registry 신뢰·source protection·실행 dispatcher/ingest/commit/CAS/영속 멱등/Native/Gate는 미완료다.
[원본 실행 manifest 계약](../../protocol/migrations/p09-source-search-execution-manifest-v1.md)을 따른다.

## 실제 원본에 결속한 공통 operation compiler

product-source-search-operation-compiler/v1은 기존16개 치환·변환 스키마의 typed receipt와 실제
편집 anchor를 원 source graph·SelectorSnapshot·OperationPlanCompiler에 연결한다. 가장 가까운
실제 구조 소유 node는 문맥이며 편집 범위 확대가 아니다. 정확한 anchor/domain/index·원본/출력·
receipt/편집목록·raw/canonical/scoped 요청 지문을12개 필수 잠금 argument에 결속한다.
부분 run/text-style은 실제 최종 splice를 사용하며 임의 첫 문단이나 가상 document node를 만들지 않는다.

원 후보를 이동하고 source graph를 빌린다. 원 현재 권한·byte 전달과 consumer 직전 최종 head에
compiler 직후 head 확인을 더한다. 최대4096개·argument별2048byte·총 argument8MiB·plan16MiB와
bounded streaming hash를 쓰며 verify/전달에서 원본 수입·검색·compiler를 재실행하지 않는다.
CompiledOperationPlan은 실행 권한이 아니며 원 RouteUnqualified와 비공개 byte 경계는 유지한다.

components213 owner5pass/1fail·recovery214 실패·owner-admission215 owner1pass/제품29pass/1fail을
보존했다. 원 graph admission의 DuplicateIdentifier와 실제 anchor 포함 관계를 검사하도록 시험만
고쳤다. 마지막 review 사례는 field cache를 포함한 본문 문단의 FieldContent 거부를 명시적으로
확인하고 hidden/MEMO 문단의 양성 치환을 분리했다. recovery216은 그1개만pass·750fresh/final750·
진단/경고없음·cleanupTrue다. 제품30+실제 owner6=고유36개이며 현재36개 단일 실행이 아니다.
통과35개·이전50개·공식249는216에서 반복하지 않았다. 원16개 파서·접근·전달·route 본문은 역변환으로 보존했다.

216 전체109.578초·명령11.329초·시스템CPU최고21.48%·가용RAM최저27.3701%다. Job active0/empty/
handle closed와 기존 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·시간 상한을
유지했다. 실제 registry/route manifest·실행 dispatcher·ingest/commit/CAS·영속 멱등 실행·transport/
게시·전체 검색/참조·target/Native/Gate는 남는다. [공통 compiler 계약](../../protocol/migrations/p09-source-search-operation-compiler-v1.md)을 따른다.

## 서식 후보의 실제 최종 splice 목록

부분 run 글자 모양과 text-style 후보는 실제 PatchIntent로 전달하는 최종 Subtree splice를
source-style-splice-inventory/v1로 보관한다. 원본 anchor와 part 내부 바이트 범위·치환 SHA/크기·
fragment 수, source/output package SHA와 기존 receipt의 SHA를 결속한다. 중첩 overlay 병합 뒤
최종 목록이므로 검색 일치 수·원 변경 run 수와 구분한다. 목록은 편집 허가나 CompiledOperationPlan이 아니다.

원 receipt JSON과 요청 스키마는 변경하지 않았다. 최대4096개/목록8MiB와 bounded streaming hash를
사용하며 fragment XML이나 또 다른 직렬화 버퍼를 보관하지 않는다. 저장·제품의
with_verified_splice_inventory는 기존 with_verified_bytes와 product binding·현재 write/scope/
head/ACL/quarantine/AEAD·consumer 직전 최종 head를 재사용한다. 검색·치환·원본 수입을 추가하지 않는다.

components209는 시험 helper E0624/E0308로 컴파일 실패/시험0이다. 공개 bounded ZIP reader와
generic repository로 helper만 고친 recovery210은 신규12+영향 기존36+영향 공통2=50pass·
737fresh/final737·진단/경고없음·cleanupTrue다. 실제 output byte와 splice/지문을 독립 대조했고
부분·불연속·중첩/최종 병합·no-op·review 정책/선택·128개 target·현재권한/외부5scope·ACL/격리/AEAD·
최종head 경합·비노출/미게시를 확인했다. 무관 공통24·공식249는 반복하지 않았다. 원209 실패와
기존 matcher/compiler/보호/렌더/patch/writer/readback/receipt·저장·제품 본문을 보존했다.

210 Job private최고934.70MiB/2.9337%·시스템CPU최고50.80%이며 Job active0/empty/handle closed다.
기존 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%와 시간 상한을 유지했다.
다음은 실제 source anchor에서 원 IR target으로의 operation compiler 연결이다. 임의 첫 문단이나
가상 document node를 만들지 않으며 실제 route/저장/commit/CAS/영속 멱등/Native/Gate는 남는다.
[최종 splice 계약](../../protocol/migrations/p09-style-splice-inventory-v1.md)을 따른다.

## 공통 후보준비 dispatcher 연결

기존 StoredProductRequest의 Form/TableFormulas 분기에 SearchMutation을 추가해 기존16개 치환·변환
스키마를 같은 진입점으로 받는다. 단일 닫힌 표가 스키마와 원 typed 오류·receipt·prepared 객체를
결속하며 기능별 원 엄격한 파서와 compiler를 재사용한다. legacy Form bindings는 검색 요청의 준비·
전달·route 검사에서 읽기 전에 거부한다. 서버의 검증된 검색/번호/출력 한도를 그대로 전달한다.

원 prepared 객체를 이동하고 receipt는 빌린다. 공통 dispatcher는 원본 clone/reimport나 matcher
재실행을 추가하지 않는다. 현재 source/write/scope/head/ACL/quarantine/AEAD와 consumer 직전
최종 head를 유지하며 원 require_current_product_route의 RouteUnqualified도 그대로다.

components205는16pass/10fail·경고1이다. 공용 fixture의 기존 계열 미지원 t.charStyleIDRef를 해당
0~6 입력에서만 제거하고 borrowed receipt의 Debug를 비노출로 구현했다. recovery206은 실패10pass·
732fresh/final732·진단/경고없음·cleanupTrue다. 수정 영향을 받는 한도 시험1개는 정상 한도 성공/전달
대조를 추가해 budget207에서1pass·733fresh/final733·진단/경고없음·cleanupTrue다. 고유 연결26개이며
현재26개 단일 실행이 아니다. 207은 다른25개·기존 제품292·공식249를 반복하지 않았다. 원 Form/Formula
분기와 기존 제품/시험 본문은 역변환·불변 입력으로 보존했다. 원205 실패는 그대로다.

두 성공 실행은 Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·private8%/
stop7%·RAM/commit95%·명령300초·guard600초를 유지했다. 207 Job private최고929.96MiB/2.9188%·
시스템CPU최고74.91%이며 시스템 표본은 검증 단독 CPU나 프리즈 해결 증거가 아니다.
실제 ingest/commit/CAS·영속 멱등 실행·실행 dispatcher/transport/게시·Native/Gate는 남는다.
[공통 준비 계약](../../protocol/migrations/p09-common-search-mutation-dispatch.md)에16종과 경계를 기록했다.

## 개인정보 탐지의 현재 저장과 읽기 전용 제품

SEARCH-020의 명시적 형식 탐지 결과를 현재 sealed Result·document.write/scope/head/ACL/quarantine/AEAD와
별도 strict16KiB JSON 요청에 연결했다. 원본 owner를 이동하고1회 준비한 결과를 보관한다. verify/metadata/
next/selection 전달은 현재 source와 전체 지문을 확인하되 규칙/regex/인덱스/검색을 반복하지 않는다.
key/plan/raw/canonical/provider/보관 결과 receipt가 next/selection 요청과 cursor를 결속한다. 최종 JSON
전체를 서버 응답 상한으로 제한한 뒤 consumer 직전 head를 확인한다. 파일/preview/compiler/실행 API는 없다.

378 신규32+영향 기존 마스킹3=35pass·881fresh/final881·진단/경고없음·cleanupTrue다. 권한 철회/복구·5scope·
격리/AEAD·네 selector/review·엄격한 스키마/상한·비노출·원본/ingest/head 불변과5개 최종 head 경합을 확인했다.
이전 source23/제품 전체·공식249는 반복하지 않았다. 전체162.407초·명령45.020초·Job CPU42.891초·
private최고1906.07MiB/5.98248%·시스템CPU최고41.07%·가용RAM최저35.8555%와 원 자원 보호/Job 정리를 확인했다.
PC 프리즈 해결 증거는 아니다. 실제 기본 형식 정책·전체 옵션·실제 변경/저장·target/Native/Gate는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기를 유지한다. [상세](P09_PERSONAL_INFO_DETECTION_PROGRESS.md),
[읽기 전용 제품 계약](../../protocol/migrations/p09-personal-info-detection-product-v1.md). 아래377까지는 저장/제품 연결 전 이력이다.

## 개인정보 형식 탐지와 원본 선택

SEARCH-020의 읽기 전용 source 기반은 명시적 형식 묶음을 한 review/NFC 인덱스와 결합 검색에 연결한다.
전화번호/주민등록/외국인등록/전자우편/계좌/카드/IP/생년월일/주소와 custom은 요청자가 지정한 규칙의
종류이며 한글 내장 정규식이나 실명/번호 유효성 판정이 아니다. 원문/정규식/개인정보 값별 해시 없이
실제 원본 위치와 규칙 label만 반환한다. 문서/구역/node/지문 결속 선택과 hidden/MEMO 정책을 유지한다.
보관 결과의 앞/뒤 이동은 재검색하지 않으며 정확한 원본 기여만 선택할 수 있다. 기존 마스킹에 선택을
넘겨도 source/보호/writer 검증을 그대로 수행한다. 실제 제품 변경·저장 권한은 주지 않는다.

373은 신규23+영향3 중25pass/1fail·873fresh/final873·cleanupTrue다. 필수 width/leader/type 없는 합성 tab의
Body 수입 실패와 미사용 import 경고1을 보존했다. 기존 수입 규칙/탐지 알고리즘을 바꾸지 않고 tab fixture와
import만 고친374는 실패1pass·이전25보존·875fresh/final875·진단/경고없음·cleanupTrue다. 현재 고유26개이며
공식249/무관 통과 시험을 반복하지 않았다.374 전체145.343초·명령28.550초·Job CPU26.812초·private최고
1893.80MiB/5.94395%·시스템CPU최고74.76%·가용RAM최저36.5547%와 원 자원 보호/Job 정리를 확인했다.
PC 프리즈 원인 귀속이나 해결 증거는 아니다.372의 이전 공통23 문서 감사32fresh/final32도 보존한다.

현재 저장/엄격한 제품·기본 형식 정책·전체 옵션·실제 실행/저장·target/Native/Gate는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기를 유지한다. [상세](P09_PERSONAL_INFO_DETECTION_PROGRESS.md),
[형식 탐지 계약](../../protocol/migrations/p09-source-personal-info-detection-v1.md).

## 개인정보 마스킹의 공통 변경 계획

SEARCH-019의 opaque 변경 owner를23번째 family에 추가했다. 기존22개 순서·오류/권한·Form/Formula와
기존 preview는 그대로다. 별도 PersonalInfoMaskPreview는 원본 읽기 전 mutation/compiler 진입을 거부하고
JSON만 전달한다. 실제 변경된 hp:t anchor inventory와 전체 source/output/receipt를 실제 구조 owner·12개
잠금 인자에 결속한다. scalar/마스킹 성분 수를 operation 수로 대신하지 않으며 원문/값별 해시는 없다.

367 빌드 CPU99.13% 보호 중단/시험 시작 미관측/최종 입력 확인 미완료와368 중단 후 관측을 보존했다.
peak 원인·Defender 제외 적용은 미확정이며 설정을 바꾸지 않았다.369 metadata KeyError/시험0·864fresh/final864도
보존했다.370 신규19+영향13=32pass·866fresh/final866의 미사용 import 경고2는 원본으로 남겼다.
독립 receipt SHA 단언을 더한371은 영향1pass·이전31보존·868fresh/final868·진단/경고없음·cleanupTrue다.
현재 고유32개이고 source25/제품33 전체·공식249를 반복하지 않았다.370 시스템CPU최고35.67%·private최고
1896.81MiB/5.9534%·가용RAM최저37.6257%와 원 자원 보호/Job 정리를 확인했다. 프리즈 해결 증거는 아니다.

실제 실행/저장/게시·전체 개인정보 정책/target·SEARCH-020 탐지/읽기 전용 선택·신뢰 registry/Native/Gate는 남는다.
whole_package_personal_data_removed=false·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
CROSSREF8종 NOT_RUN·Native011 미승인/미실행·문자 스타일6종 선택 대기를 유지한다.
[상세와 원 실패](P09_PERSONAL_INFO_MASK_PROGRESS.md),
[공통 계획 계약](../../protocol/migrations/p09-compiled-personal-info-mask-v1.md).

## 개인정보 마스킹의 현재 저장과 제품 요청

SEARCH-019의 명시적 선택/두 마스킹 정책을 현재 sealed Result·document.write/scope/head/ACL/quarantine/AEAD와
별도 strict16KiB 제품 JSON에 연결했다. borrowed/owned는 준비 본문·원래 owner를 공유/이동하며 기존 proof/
index/masking/writer를 한 번 사용한다. verify/전달은 현재 source 재구성·권한·receipt/writer·consumer 최종 head를
확인한다. 필수 preview_only의 미리보기는 artifact를 폐기하고 metadata만 남기며 byte consumer를 호출하지 않는다.
전체 service/product envelope에 서버 byte 상한을 적용한다. generic query/regex/filter/승인·raw graph는 거부한다.

365 신규33+영향 기존3=36pass·856fresh/final856·진단/경고없음·cleanupTrue다. 기존 source25/전체 제품/공식249는
반복하지 않았다. 시스템CPU최고33.97%·private최고1896.59MiB/5.9527%·가용RAM최저37.0531%와 원 자원 보호·
두 Job 정리를 확인했다. PC 프리즈 해결 증거는 아니다. preview도 SEARCH-019의 준비이며 SEARCH-020 탐지/읽기 전용
선택의 완료가 아니다. whole_package_personal_data_removed=false이고 원문/개인정보 값별 해시는 metadata에 없다.

공통 변경 전용 owner/실행/저장·전체 개인정보 정책/target·Native/Gate는 남는다. 기존 공통22계열은 그대로다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기를 유지한다.
[상세와 원본 이력](P09_PERSONAL_INFO_MASK_PROGRESS.md),
[제품 마스킹 계약](../../protocol/migrations/p09-personal-info-mask-product-v1.md).

## 선택한 원본 본문의 개인정보 마스킹

SEARCH-019의 별도 source core는 document/section/node/정확한 selection과 hidden/MEMO 정책으로
선택한 원본 글자를 별표로 바꾼다. 원 scalar별 원래 슬롯 유지와 연속 텍스트 그룹별 별표3개/첫 기여 위치
정책을 구분하며 Native 길이/저장 동등성을 주장하지 않는다. 한 proof/whole protection/field/review/index와
기존 보호된 typed planner/writer/readback을 사용하고 컨트롤·비선택 XML·원본 run/style/reference shell을 보존한다.
원문·선택 조각·개인정보 값별 해시는 receipt/Debug에 포함하지 않는다. header/메모 저자/미리보기까지 제거하는
문서 전체 익명화가 아니며 whole_package_personal_data_removed=false다.

362 fixture assembly 선언 누락 E0432·시험0·848fresh/final848을 보존했다. 선언1개와 실행별 임시 경로 인자만
보완한363은 신규25+공유 보호/컨트롤/원본 선택 경계3=28pass·850fresh/final850·진단/경고없음·cleanupTrue다.
363 시스템CPU최고24.25%·private최고588.29MiB/1.8464%·가용RAM최저39.4991%와 원 자원 보호/두 Job 정리를
확인했다. 전체 제품·공식249는 반복하지 않았다. PC 프리즈 해결 증거는 아니다.

현재 저장·엄격한 제품·공통 실행/저장과 SEARCH-020 탐지/읽기 전용 선택·전체 개인정보 정책·target는 남는다.
카탈로그의 generic query/replacement와 공식 도움말의 선택 마스킹 차이는 계약에 명시하고 원 계약을 조용히
재정의하지 않았다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행과 문자 스타일6종 선택 대기를 유지한다.
[상세와 실패 원본](P09_PERSONAL_INFO_MASK_PROGRESS.md),
[선택 마스킹 계약](../../protocol/migrations/p09-source-personal-info-selection-mask-v1.md).

## 스타일 선언의 현재 저장과 제품 요청

SEARCH-025의 별도 읽기 전용 선언 resolver를 sealed Result·현재 document.write/scope/head/ACL/
quarantine/AEAD와 엄격한16KiB 제품 요청에 연결했다. 준비 시 한 catalog/이름 matcher를 사용하고,
보관 verify/전달은 원본 전체 재구성·현재 권한·지문과 consumer 최종 head를 유지하며 이름 해석을 반복하지
않는다. 이름/본문 없이 선언 ID와 연결 자원만 전달한다. 전체 service/product envelope의 서버 byte 상한과
정확한 한도/1byte 부족을 검사한다. key/plan 지문은 claim이나 실행 권한이 아니다.

357 비공개 helper 컴파일 실패/시험0과 종료 후 CPU94.47% 입력 미확인,358 임시 경로 실패/시험0·
840fresh/final840을 보존했다.359는 신규26+영향 기존3=29pass·842fresh/final842·진단/경고없음·cleanupTrue다.
원 자원 보호·두 Job 정리와 기존 문단 v1/v2/공통22계열을 유지했고, 전체 제품/공식249/선언19는 반복하지
않았다.359 시스템CPU최고32.16%·private최고933.64MiB/2.9304%·가용RAM최저25.9121%는 프리즈 해결
증거가 아니다. 문자 스타일 본문/전체 옵션·실제 실행/저장/게시·신뢰 registry·Native/Gate는 남는다.
고정6종 캡처는 사용자 선택 대기이며 승인/세션 자격 전 실행하지 않는다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[상세와 실패 원본](P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md),
[제품 선언 요청 계약](../../protocol/migrations/p09-named-style-declarations-product-v1.md).

## 원본 문단과 문자 스타일 선언의 이름 해석

SEARCH-025의 별도 선언 resolver는 기존 typed catalog에서 PARA/CHAR와 native/English 축을 명시해
정확한 기존 대상을 해석한다. named style ID와 글자/문단 모양·nextStyle 관계를 구분하며 공유 자원이나
같은 이름을 본문 스타일 동일성으로 추정하지 않는다. 원 reader/ID 규칙·문단 v1/v2·공통22계열은 그대로다.

354의17pass/1fail·830fresh/final830을 보존했다. 공개 응답 byte 상한과 private 지문 입력 상한을
분리한355에서 실패1+신규1+영향2=4pass·보존15로 선언 고유19개와 이전에 실행되지 않은 catalog3개를
확인했다.832fresh/final832·진단/경고없음·cleanupTrue다. 단일19개 재실행이 아니며 원본/제품 전체·공식249는
반복하지 않았다.355 시스템CPU최고24.43%·private최고1884.47MiB/5.9147%·가용RAM최저37.4163%이며
원 자원 보호/두 Job 정리를 유지했다. PC 프리즈 해결 증거는 아니다.

선언 해석은 문자 스타일 본문 위치·실제 적용/우선순위·Native 자격이 아니다. 적용 전후 원본 또는 고정6종
캡처의 사용자 선택이 대기 중이며 승인/세션 자격 전 실행하지 않는다. 문자 스타일 본문 결속/전체 옵션·
실행/저장/게시·신뢰 registry·Native/Gate는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·
P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[상세와 실패 원본](P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md),
[선언 해석 계약](../../protocol/migrations/p09-named-style-declaration-resolution-v1.md).

## 문단 스타일 필터의 제품과 공통 계획

선택적 style_filter와 필수 preview_only를 현재 저장/엄격한 v2·출력 폐기 preview와 공통22번째
변경 계열에 연결했다. 기존21개 순서·v1 필터 거부·폰트/문단 v1 preview API를 유지한다.
실제 문단 anchor/구조 owner와 전체 filtered/unfiltered output receipt를12개 잠금 인자 계획에
결속한다. 두 모드의 현재 권한/원본/writer·consumer 최종 head를 유지하며 미리보기는 JSON만 전달한다.

350은 신규28+영향4=32pass·815fresh/final815다.351 첫 import RecursionError는 guard/Cargo/시험0으로
보존했다. import 경로 분리 뒤 실제351은 신규18+영향9=27pass지만 후처리 AttributeError/전체FAILED다.
821fresh/final821·진단/경고없음·cleanupTrue와 실패를 유지했다. 도구 모듈 import 한 줄만 고친352는
26fresh/final26에서 원27개 결과/보호/정리를 대조했다. Cargo/제품 시험은 반복하지 않았으며 현재 전체
runtime 새 자격도 아니다. 기존 실행 기반/관측 함수 객체 동일성과 재귀 한도1000을 확인했다.

350/351의 시스템CPU최고는36.26%/26.56%, private최고923.07/924.94MiB이며 두 Job active0/empty/handle
closed다. 원 자원 보호를 유지했고 PC 프리즈 해결 증거는 아니다. 문자 스타일/전체 옵션·실제 적용/
실행/저장/게시·신뢰 registry·Native/Gate는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[상세와 원 실패](P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md),
[원 결과 대조](evidence/p09-361-compiled-named-style-options-reconciled352.v1.json),
[v2 계약](../../protocol/migrations/p09-named-paragraph-style-product-v2.md).

## 원본 서식으로 선택한 문단 스타일 이름 대체

SEARCH-025의 별도 filtered source profile은 기존 선언 참조/명시적 정의값 판정기를 공유한다.
전체 문단의 모든 인덱스 글자/NFC 기여 원본이 조건을 만족해야 하며 빈 문단은 일치가 아니다.
mixed run/다른 블록 불일치를 무시하지 않고 현재 필드/추적/잠금·범위·writer/readback을 유지한다.
원본 segment별 판정 캐시와 정의1회 해석·streaming 지문으로4096글자/1segment를1회 판정한다.

348은 신규18+영향 원본6+영향 기존 제품3=27pass·810fresh/final810·진단/경고없음·cleanupTrue다.
원본/제품 전체·giant suite·공식249는 반복하지 않았다. 전체179.766초·명령34.187+39.016초·
Job CPU32.375+37.609초·private최고1883.01MiB/5.9101%·시스템CPU최고32.94%·가용RAM최저35.5549%·
두 Job active0/empty/handle closed와 원 자원 보호를 유지했다. PC 프리즈 해결 증거는 아니다.

필터의 현재 저장/엄격한 별도 제품·preview·공통 계획과 문자 스타일/전체 옵션·실제 적용/실행/저장/게시·
신뢰 registry·Native/Gate는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·
P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[상세](P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md), [현재 필터 검증](evidence/p09-361-filtered-named-styles348.v1.json).

## 문단 스타일 이름 대체의 제품과 공통 계획

SEARCH-025의 문단 이름 대체를 현재 저장/엄격한 v1 제품과 출력 폐기 preview, 공통21번째 변경
계열에 연결했다. 기존20개 순서와 폰트 preview API를 유지하며 별도 NamedStylePreview는 JSON만
전달한다. 원본 읽기 전 preview compile 거부·현재 권한/원본/writer/consumer 최종 head를 유지하고
실제 문단 anchor와 실제 구조 owner·전체 output receipt를12개 잠금 인자 계획에 결속한다.

343 제품29pass와344 신규2+영향3pass/보존26으로 제품 고유31개다. 검증된 서버 result byte 한도와
4MiB 교집합을 outer receipt에 적용하며384문단·64KiB 초과 응답과 한도/1byte 부족을 확인했다.
345 시험 모듈 매크로 순서 컴파일 실패/시험0은 보존했다. 선언 위치만 옮긴346은 공통 신규19+
영향 제품3+영향 폰트/기존4계열9=31pass·806fresh/final806·진단/경고없음·cleanupTrue다.
기존 제품31개/폰트35개·giant suite·공식249 전체를 다시 실행하지 않았다.

전체134.766초·명령17.907+10.359초·Job CPU16.094+8.609초·private최고782.48MiB/2.4559%·
시스템CPU최고32.39%·가용RAM최저40.1649%·두 Job active0/empty/handle closed다. 원 자원 보호를
유지했으며 PC 프리즈 해결 증거는 아니다. 문자 스타일·서식 필터/전체 옵션·실제 적용/실행/저장/게시·
신뢰 registry·Native/Gate는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·
P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

[상세와 실패 원본](P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md),
[현재 공통 검증](evidence/p09-361-compiled-named-styles-recovery346.v1.json),
[제품과 공통 계약](../../protocol/migrations/p09-named-paragraph-style-product-v1.md).

## 문단 스타일 이름을 사용하는 원본 참조 대체

SEARCH-025의 별도 core는 원본 PARA 스타일 이름을 literal/regex/case/whole-word로 찾고 이미
선언된 유일한 대상의 styleIDRef로 문단 참조를 동시에 교체한다. native_name/english_name을 명시하며
본문 문자열·CHAR 스타일·암묵적 기본0/상속/별칭으로 대체하지 않는다. header 정의와 직접 paraPr/run/text
참조·본문/제어·비선택 bytes를 보존한다. 기존 문단 속성 compiler·필드/추적/하위 보호·writer/readback을 공유한다.

337 입력 범위 누락/Cargo0·338 regex 이름 충돌/시험0·339 23pass/3fail·340 2pass/1fail을 보존했다.
142 원본 시험 지문을 보완하고 외부 ::regex 두 참조만 고쳤다. 이후 production은 그대로이며
run 없는 문단의 Body 거부와 빈 run/명시적 빈 text/self-closing text를 구분했다. 탭은 검색 블록
경계가 아니므로 기존 bookmark fixture로 실제 경계와 전체 문단 범위를 확인했다.
341 마지막1pass+보존25로 신규19+영향7의 고유26개이며 단일26개 실행은 아니다.
마지막793fresh/final793·진단/경고없음·cleanupTrue다. 기존 통과23개, 이후 통과2개를 반복하지 않았다.

339 시스템CPU최고55.25%·Job private1870.18MiB를 보존했고 최종341 전체106.766초·명령3.516초·
Job CPU2.25초·private586.83MiB/1.8419%·시스템CPU12.43%·가용RAM최저45.1306%·Job active0/empty/handle closed다.
원 자원 보호를 유지했으며 PC 프리즈 해결이나 CPU 귀속 증거는 아니다.

다음은 현재 저장 서비스·엄격한 제품/preview·문자 스타일 의미·전체 옵션이다. 실제 한글 스타일 적용과
시각 결과·실행/저장/게시·신뢰 registry·Native/Gate는 미완료다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[구현 및 실패 복구 범위](P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md),
[원본 계약](../../protocol/migrations/p09-named-paragraph-style-source-v1.md).

## 폰트 v2 공통 계획과 비변경 미리보기

SEARCH-024의 v2 변경 전용 후보를 공통20번째 family에 연결하고 기존19개 순서/구현을 유지했다.
preview_only=true는 별도 SearchPreview이며 mutation/compile 진입을 원본 읽기 전에 거부한다.
미리보기는 현재 source/권한·consumer 최종 head를 거쳐 JSON만 전달하고 bytes/가짜 plan/실행
manifest 경로를 제공하지 않는다. 기존 font resource 검증과 실제 본문 owner를 재사용하며 v2의
전체 필터 output receipt를 계획 지문에 결속한다. 폰트 v1/v2는15개, 다른 기능은12개 잠금 인자를 유지한다.

335 신규23+영향 공통6+영향 v2 제품6=35pass·779fresh/final779·진단/경고없음·cleanupTrue다.
전체133.906초·명령32.094초·Job CPU30.016초·private최고900.62MiB/2.8267%·
시스템CPU최고30.18%·가용RAM최저42.1103%·Job active0/empty/handle closed다. 최종 head 경합5개와
preview compile 사전 거부·두 번째 실제 owner/공유 헤더 자원·필터별 계획 지문·현재 권한/한도를 확인했다.
기존 두 시험의 schema 개수/새 슬롯 기대만20으로 갱신했고 giant suite·공식249·원본24개는 실행하지 않았다.

전체 옵션·유효 서식/fallback·전체 보호 의미·신뢰 registry·실제 실행/저장/게시·Native/Gate는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[v2 공통 계약](../../protocol/migrations/p09-font-options-product-v2.md),
[신규23개와 영향12개](evidence/p09-361-compiled-font-options335.v1.json).

## 폰트 필터와 미리보기의 저장 및 제품 준비

SEARCH-024의 현재 저장 서비스와 엄격한 v2 JSON에 선택적 style_filter와 필수 preview_only를
연결했다. 원본 소유자는 이동하며 기존 v1 저장/제품 알고리즘은 module 선언 외에 그대로다.
미리보기는 같은 후보 생성·writer/readback 뒤 출력 artifact를 버리고 예측 메타데이터만 보관한다.
파일 요청은 PreviewOnly로 거부하고 저장 preview에는 bytes/inventory/compiler API가 없다.
메타데이터64KiB와 현재 document.write/scope/head/ACL/quarantine/AEAD·consumer 직전 head를 유지한다.

333 신규28+영향 v1 제품4=32pass·774fresh/final774·진단/경고없음·cleanupTrue다.
전체150.563초·명령49.891초·Job CPU47.766초·private최고1874.33MiB/5.8828%·
시스템CPU최고31.76%·가용RAM최저46.7797%·Job active0/empty/handle closed다. 두 모드의 마지막
head 경합6개·원본/head/ingest 불변과 미리보기 파일 거부·필터/상한/현재 권한을 확인했다.
기존80개 시험 본문은 보존했고 그중4개만 실행했다. 공식249·원본24개는 반복하지 않았다.

다음은 v2 변경 후보의 공통 준비/계획과 별도 비변경 preview dispatch다. 전체 옵션·유효 서식/fallback·
신뢰된 registry·실제 실행/저장/게시·Native/Gate는 남는다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[v2 제품 계약](../../protocol/migrations/p09-font-options-product-v2.md),
[신규28개와 영향4개](evidence/p09-361-font-options-product333.v1.json).

## 원본 서식 조건으로 선택한 폰트 대체

SEARCH-024의 별도 원본 필터 후보는 명시된 참조/정의 조건을 원본 segment마다1회 판정하며
NFC 단위의 모든 기여 원본이 만족해야 한다. 수용/제외 단위가 원본 scalar를 공유하면 Selection으로
거부한다. 기존 v1 후보·영수증·엄격한 제품 JSON은 유지하고 필터/inspection/선택 수와 원 receipt를
별도 profile/hash로 결속한다. 같은 선택에서 원 receipt/출력 bytes/inventory 일치를 확인했다.

331 신규18+영향 v1 원본6=24pass·769fresh/final769·진단/경고없음·cleanupTrue다.
전체133.719초·명령33.875초·Job CPU32.25초·private최고1855.82MiB/5.8248%·
시스템CPU최고35.55%·가용RAM최저35.8527%·Job active0/empty/handle closed다. 원 자원 보호를
유지했고 기존20개 시험 본문·과거 실패를 보존했다. 무관한 저장/제품 묶음·공식249는 반복하지 않았다.

다음은 필터의 현재 저장 서비스·엄격한 제품 JSON과 preview_only 연결이다. 유효 서식/fallback·
신뢰된 registry·실제 실행/저장·전체 계약·Native/Gate는 남는다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
[원본 필터 계약](../../protocol/migrations/p09-filtered-font-source-v1.md),
[신규18개와 영향6개](evidence/p09-361-font-style-filter331.v1.json).

## 메모와 필드 및 추적 변경 보호

폰트의 선택된 하위 text가 상위 run charTcId/문단 paraTcId를 상속하지 않던 누락을 수정했다.
328의 실제 후보 반환3개는 FAILED·763fresh/final763으로 보존한다. 새 guard는 기존 part별 순회에
관측 tracking map을 더해 ID0/1을 모두 표시로 취급하고 matcher/서식 복제/writer 전에 거부한다.
원 source/field/표 보호·patch/writer/readback·receipt는 유지했다. 부모별 XML 재파싱이나 선택마다 부모 walk는 없다.

326/327의 원 실패와 scope helper·미지원 p.lock/합성 중첩 DATE의 수입 단계 구분을 보존한다.
329 실패3+영향13+신규4=20pass·765fresh/final765·진단/경고없음·cleanupTrue다. 수입 거부4개를
보존한 대표 고유24개이며 단일24개 실행이 아니다. 정상 hidden/MEMO·캐시 보존/제외·outer DATE,
유효 표/셀 보호와 비선택 보존·두 축/공통 compiler의 추적 표시 거부를 확인했다. 기존56·공식249는 반복하지 않았다.

전체143.11초·명령44.406초/시험7.22초·Job CPU42.547초·private1860.77MiB/5.8403%·
시스템CPU최고70.90%·가용RAM최저37.5717%·Job active0/empty/handle closed다. 원 자원 보호를 유지했고
시스템 전체 CPU를 검증 Job에 귀속하거나 프리즈 해결을 주장하지 않는다.
style_filter/preview_only·전체 유효 서식/fallback·실제 실행/저장/Native와 전체 보호 의미는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN을 유지한다.
[관측 보호 계약](../../protocol/migrations/p09-font-review-tracking-guard-v1.md)을 따른다.

## 폰트 공통 준비와 계획 컴파일러

엄격한 폰트 schema를 공통 준비 표의19번째 family로 연결했다. 계획의 본문 splice는 실제 구조
소유자에 결속하며 헤더 count/append와 적용 profile은15개 필수 잠금 인자에 포함한다.
헤더는 임의 본문 operation이 아니라 같은 inventory 그룹에1회 적용할 자원이다. 실제 실행기는 남는다.
기존18개 family의12개 인자와 원 parser/owner/snapshot/receipt·현재 접근·최종 head는 유지했다.

323 입력 원장 중단은 Cargo 전이었다.249의 기존18종 스키마 시험 pin을 결속한324는
신규 폰트16+영향 기존4=20pass·753fresh/final753·진단/경고없음·cleanupTrue다. width/style/regex/sort
네 경로의12개 인자를 확인했고 기존36·공식249·과거 대형 모듈은 실행하지 않았다.
전체120.562초·명령22.797초/시험10.00초·Job CPU21.234초·private894.05MiB/2.8061%·
시스템CPU최고25.57%·가용RAM최저40.2436%·Job active0/empty/handle closed다. 원 자원 보호를 유지했다.

현재 연결은 후보준비·계획까지다. 전체 옵션과 review/field/protection 조합·실제 유효 서식/fallback·
registry/실행/저장/게시·Native/Gate는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN을 유지한다.
[폰트 공통 계획 계약](../../protocol/migrations/p09-compiled-font-resources-v1.md)을 따른다.

## 폰트 헤더 자원과 본문 편집 목록

폰트 후보의 실제 헤더 itemCnt 치환/기존 charPr 뒤 정의 추가와 최종 본문 run/text splice를
SourceFontEditInventory로 구분했다. 각 실제 part/anchor·byte 범위·치환 SHA/크기·fragment 수와
헤더 원/출력 정의 수를 결속하며 기존 compiled edit 지문과 독립 대조한다. 본문 소유자만 다루는
기존 공통 compiler에 헤더를 임의 문단으로 보내지 않는다. 원 영수증과 patch/writer/readback은 유지했다.

현재 저장/제품 metadata 전달은 원 현재 접근·원본·writer 무결성과 consumer 직전 head를 공유한다.
목록은4096편집/8MiB와 streaming hash를 사용하며 원본 clone/reimport·검색/치환을 추가하지 않는다.
319 원본9pass·제품 helper 컴파일 실패/시험0을 보존했고 공개 byte reader로 helper만 고친320은
신규12+영향 제품24=36pass·745fresh/final745·진단/경고없음·cleanupTrue다. 원본9개를 보존한 고유45개이며
45개 단일 실행이 아니다. 무관 원본11·바이너리24·공식249는 반복하지 않았다.

320 전체115.36초·명령19.437초/시험13.94초·Job CPU17.438초·private735.09MiB/2.3072%·
시스템CPU최고27.44%·가용RAM최저41.0091%다.319 빌드 포함 private1861.88MiB/5.8438%도 기록했다.
모든 Job은 active0/empty/handle closed이며 원 자원 보호를 유지했다. 프리즈 해결은 주장하지 않는다.
다음은 헤더 자원 의존성/실제 본문 소유자의 공통 compiler/dispatcher 결속이다. 실행/저장/게시·
전체 옵션/cascade/fallback·Native/Gate는 남고 공식158/249·잔여91·next165·P09/A12/A13 OPEN을 유지한다.
[편집 목록 계약](../../protocol/migrations/p09-font-edit-inventory-v1.md)을 따른다.

## 현재 저장 서비스와 폰트 제품 요청

이름·언어와 네 selector의 run/text 축 후보를 별도 현재 저장·엄격한 폰트 제품 API에 연결했다.
현재 write/scope/head/원본 SHA·ACL/격리/AEAD·whole-source proof·consumer 직전 head를 유지한다.
요청의 변경 수는 서버 검색 한도와 교집합을 취하고 query/regex/writer 상한을 그대로 전달한다.
소유권 이동으로 원본 clone을 추가하지 않으며 보관 후보 전달에서 이름 검색/lowering을 반복하지 않는다.

315 시험 콜백 컴파일 실패/시험0은 보존했다. 콜백·unused import와 실제 출력 검사를 고친316은
독립 제품24pass·739fresh/final739·진단/경고없음·cleanupTrue다. 제품 코드는315와 동일하며 기존20/24·
공식249는 반복하지 않았다. 전체107.782초·명령12.969초/시험8.39초·Job CPU12.266초·private736.46MiB/
2.3115%·시스템CPU최고16.93%·가용RAM최저41.2961%·Job active0/empty/handle closed다.
원 자원 보호를 유지했고 프리즈 해결을 주장하지 않는다.

다음은 실제 편집 inventory와 공통 operation compiler/dispatcher 연결이다. 폰트는 아직 기존 공통
준비 표의 구성원이 아니다. 전체 옵션·풍부한 review/field/protection 조합·cascade/fallback·실제 실행/
저장/게시·target/Native는 남고 공식158/249·잔여91·next165·P09/A12/A13 OPEN을 유지한다.
[별도 폰트 제품 계약](../../protocol/migrations/p09-stored-scoped-font-product-v1.md)을 따른다.

## 원본 폰트 참조 치환

이름 query/replacement와 네 selector의 명시적 run/text 축은 별도 scoped-font/v11 후보에 연결했다.
공유 charPr는 수정하지 않고 필요한 복사본을 한 번씩 생성해 선택된 원문만 재결속한다.
원본/출력 전체 서식 catalog·원문/제어·모든 run/text 참조·편집 밖 바이트와 실제 compiled bytes를 대조한다.
313은 원 실패8+영향3=11pass·731fresh/final731·진단없음·cleanupTrue이며 무관 통과9개를 보존해 고유20개다.
이름·언어·대상 모호성·NFC 원문/부분 범위·두 서식 축·공유 정의/비선택 보존·stale/한도·비노출을 확인했다.
전체20 단일 실행은 아니며 기존24·공식249는 반복하지 않았다. 다음은 현재 저장·엄격한 제품 입력 연결이다.
review/field/protection 조합·style_filter/preview_only·전체 cascade/fallback·실제 실행/저장/Native/Gate는 남는다.
아래309까지는 이 선택 범위 연결 전 이력이다.

별도 font-binary/v10과 현재 패키지 리소스 결속은 신규10+영향 기존14=24pass·716fresh/final716·진단없음·cleanupTrue다.
원 shape/v6의 미등록 참조 거부와 fixture의 실제 리소스 부재를 구분했다. 선언-only 원 형태는 거부 시험으로 유지하고
별도 manifest/opaque binary를 가진 메모리 파생 원본의 메타데이터/바이트 보존을 확인했다. 실제 유효 글꼴/활성화/Native 증거는 아니다.
기존 ID v1~v9 규칙·matching은 역변환 동일성을 확인했으며 원 reader/patch/writer·실패305를 보존했다.
원본 파트/manifest 색인을 한 번 공유하고 추가 원본 수입은 없다. 아래307까지의13pass/1fail은 이전 상태다.

SEARCH-024의 원본 편집 기반은 같은 원본·언어의 기존 폰트 선언 사이에서 공유 charPr의 fontRef를
동시에 교체한다. 원본 전체 바이트·유한 매핑/변경 상한·관측 보호 거부와 기존 patch/writer를 유지한다.
출력 전체 글자 모양/7언어 참조와 원 정의·편집한 속성 값 밖 바이트를 대조한다. 현재 서비스 권한은 부여하지 않는다.

303의12pass/2fail을 보존했고304는 잘못된 기대값을 고친 양성1개만pass·710fresh/final710·진단없음·cleanupTrue다.
고유13pass이며 통과12개·공식249는 반복하지 않았다. 305의 내장 폰트1개는 id_index_validation_failed로 실패했다.
해당 fixture는 실제 폰트 리소스 없는 선언이며 원 ID 규칙/유효 리소스 결속과 이름 검색·선택 범위·fallback·
현재 저장/제품 연결·Native/Gate는 미완료다. 기존 실패·원 reader/ID/보호 규칙을 보존했다.

304 전체117.859초·시스템CPU최고26.33%·가용RAM최저39.9289%·Job private최고1805.99MiB다.
Job active0/empty/handle closed와 원 한 코어·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작과 한글/접근 허용 미실행을 유지한다.
[원본 폰트 참조 계약](../../protocol/migrations/p09-source-font-reference-replacement-v1.md)과
[검증·미해결 범위](P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md)를 따른다.

## P09 검색 기능의 완료 경계

카탈로그 P09 소유 기능은 다음 19개다. 기존 참조 작업 9개와 별도로 범위를 대조한다.
설계상의 `DIRECT_FULL` 표기를 실제 제품 지원 증거로 올리지 않는다.

| ID | 기능 | 현재 완료 경계 |
|---|---|---|
| SEARCH-001 | 문자열 찾기 | 4종 source/v5와 review 선택 창/저장/v6 JSON 통과, 전체 필터 조합/계약 미완료 |
| SEARCH-002 | 정규식 찾기 | 사전 창 선택·4종 v5와 review 창/저장/v6 JSON 통과, 전체 필터 조합/계약 미완료 |
| SEARCH-003 | 모양 조건 찾기 | 4종 selector·review 서식 v7 및 직접 서식 해석 core/현재 저장/v9 JSON·cursor·ctrl 문맥 guard 검증, cascade/visibility·전체 계약 미완료 |
| SEARCH-004 | 개체·필드·조판 부호 찾기 | 실제 control_anchor의 4종 범위·review 정책·현재 저장/v8 JSON·region cursor 통과, 제어 의미·전체 계약 미완료 |
| SEARCH-005 | 다시 찾기 | 기존 결과·4종 selector의 v5/v6·v7 서식/v8 컨트롤/v9 직접 서식 해석 cursor·정책/현재 권한 검증 통과, 전체 계약/target 검증 미완료 |
| SEARCH-006 | 문자열 치환 | plain v1·혼합 v2·hidden/MEMO v3와 selector 창 core/저장/v4 JSON 통과, 전체 계약/transaction 미완료 |
| SEARCH-007 | 정규식 치환 | capture/템플릿과 빈 일치 source v2·현재 저장/엄격한 v2 JSON 통과, 전체 계약/transaction 미완료 |
| SEARCH-008 | 서식 치환 | 부분 run/text-style·문단/이름 스타일 core/저장/제품·실제 최종 splice와16계열 공통 operation compiler 검증, 유효 서식/실제 실행/전체 계약 미완료 |
| SEARCH-009 | 컨트롤 치환 | Tab/LineBreak 원본/저장/제품 검증, AutoNumber/NewNumber 원본67·현재 저장/엄격한 제품26개 검증, 다른 제어·전체 계약/실제 실행 미완료 |
| SEARCH-010 | 쪽·구역·문단·개체 이동 | 대상과 실제 문서 흐름/쪽 정보 결속 필요 |
| SEARCH-013 | 대소문자 변환 | 명시적 Unicode17 기본 upper/lower source 고유64개·현재 저장/엄격한 제품 JSON 신규22개 검증, 전체 통합/target 계약 미완료 |
| SEARCH-014 | 전각·반각 변환 | Unicode17 폭226쌍·가타카나28쌍·원본24개·현재 저장/엄격한 제품 JSON 신규24개 검증, 전체 통합/target 계약 미완료 |
| SEARCH-019 | 개인정보 바로 바꾸기 | source25·제품33·공통23번째 변경/분리 preview 신규19+영향13 및 독립 receipt SHA 영향1 검증, 실제 실행/저장·전체 개인정보 정책/문서 전체 익명화/SEARCH-020/target 미완료 |
| SEARCH-020 | 개인정보 찾아 바꾸기 | 명시적 형식 source23·저장/읽기 전용 제품32+영향3와 원 설치64패턴 카탈로그 source27+영향6 검증, 전체 카탈로그 저장/제품 선택·Native 일치 의미·전체 계약·실제 변경/저장/target 미완료 |
| SEARCH-021 | 텍스트·문단 정렬 | 단일 원본19·제품20·공통연결18과 다중 원본16·제품20·공통연결 신규20개 검증, 중첩·구조적 키·실제 실행/전체 계약 미완료 |
| SEARCH-022 | Unicode 정규화 | 선택 범위 v1 제품20개·일치 source 고유42개·현재 저장/엄격한 검색·서식 v2 제품22개 검증, 전체 통합/target 계약 미완료 |
| SEARCH-023 | 공백·탭·줄바꿈 정규화 | typed patch 고유43개·명시적 정책/원본24개·현재 저장/엄격한 제품 JSON 신규24개 검증, 전체 통합/target 계약 미완료 |
| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/엄격한 v2와 공통 준비/계획·분리 preview 신규23+영향12개 검증, 전체 옵션/유효 서식/폰트/fallback/보호·실행/저장/target 미완료 |
| SEARCH-025 | 스타일 일괄 대체 | 문단 이름/필터 v2 제품·공통22계열과 PARA/CHAR 선언19·catalog3 및 현재 저장/엄격한 선언 제품 신규26+영향3 검증, 문자 스타일 본문/전체 옵션·실제 적용/실행/저장/target 미완료 |

공통적으로 전체 SearchScopeSelector, 숨김/유효 스타일, target match_set·semantic diff·reopen,
공통 후보준비 이후 실제 실행 dispatcher와 저장·CAS·영속 멱등 실행·게시 및 요구되는 Native 증거가 남는다.
새 엄격한 제품 JSON과 현재 document.write/ACL/head 경계는 명시한 부분 원본 경로에 한정한다.
기존 단일 대상 selector를 전체 검색 엔진으로 취급하지 않는다. 나머지 기능에 기존 하위 구현이 있더라도
해당 기능의 전체 제품 계약에 연결됐다는 증거와 구분한다.

P11 소유 SEARCH-011/012/015~018은 이 P09 목록에 합치지 않는다. source API v12의
incomplete/미해결 4단계/report 없음/exit3, 고정 CROSSREF 8종 NOT_RUN,
Native011 미승인·미실행과 P10 미시작을 유지한다.
부분 run/text-style과 두 문단 축 및 직접 서식 요청축 해석의 core/저장/제품과 ctrl 문맥 guard, Unicode 선택 범위 및 검색/서식 일치와 명시적 대소문자·전각·반각 core/현재 저장/제품, 별도 whitespace/control patch와 정규화 core/현재 저장/제품 및 typed 텍스트 제어 치환 기반/원본 compiler/현재 저장/엄격한 제품24개를 검증했다. 별도 AutoNumber/NewNumber는 review-bound source67개와 현재 저장/엄격한 제품26개를 검증했다. 다른 제어와 참조/ID 보존·카탈로그 query/replacement·전체 유효 cascade/SearchScopeSelector·실제 저장/commit/CAS/영속 멱등/실행 dispatcher/게시·target/Native는 미완료다.

계약과 source profile은 [검색 카탈로그](../../docs/04_feature_catalog/03_search.md),
[검색 계약](../../docs/04_feature_catalog/contracts/03_search_contracts.md),
[원본 검색 프로필](../../protocol/migrations/p09-source-search-index-v1.md),
[제품 검색 요청](../../protocol/migrations/p09-source-search-product-request-v1.md)을 따른다.
