# 원본 개인정보 형식 탐지와 읽기 전용 선택

`hwpx-agent.source-personal-info-format-candidates/v1`은 SEARCH-020의 원본 형식 후보 탐지 기반이다.
명시한 형식을 찾고 기존 인덱스 좌표를 반환하며 파일·서비스·실행 권한을 만들지 않는다.

## 공식 기능과 제품 계약

2026-10-21 확인한 한컴 [multi 한글 찾아서 바꾸기 도움말](https://help.hancom.com/hoffice/multi/ko_kr/hwp/security/user_info_protection/protection%28search_hide%29.htm)은
9종 형식·기타 문자·사용자 정의 형식, 순차 찾기와 별도의 변경 동작을 구분한다. 내부 형식은 정규식이며
사용자 추가 형식을 PrivateInfo.ini로 보관한다고 설명한다. [사용자 정의 설정](https://help.hancom.com/hoffice/multi/ko_kr/hwp/security/user_info_protection/protection%28user_info_option%29.htm)은
형식 추가와 구분자를 설명하지만 이 원본 코어가 사용할 내장 정규식 전체를 제공하지 않는다.
개인 데이터 폴더/PrivateInfo.ini를 읽거나 수정하지 않았고 한글2020 exact target의 기본 패턴·겹침·표시
동작을 추정하지 않는다. 종류 label은 형식 후보 분류이지 실제 번호/인물의 유효성 판정이 아니다.

[기존 검색 계약](../../docs/04_feature_catalog/contracts/03_search_contracts.md)은 SEARCH-020을 read_only로
분류하면서 generic query/replacement와 transaction 절차를 함께 적고 있다. 이 별도 profile은 탐지·선택을
변경 후보/preview와 구분한다. 기존 전체 계약을 축소하거나 현재 제품 완료로 대체하지 않는다.

## 명시적 형식 정책과 검색

SourcePersonalInfoDetectionPolicy는1~16개 규칙을 순서 있는 묶음으로 받는다. 각 규칙은 안전한 ASCII ID,
전화번호/주민등록/외국인등록/전자우편/계좌/카드/IP/생년월일/주소/custom 종류, literal 또는 regex 질의와
명시적 case_sensitive/whole_word를 갖는다. 기본 패턴을 삽입하거나 모호한 종류를 자동 추정하지 않는다.
literal은 기존 NFC 의미를 사용하고 regex 문법은 그대로다. 빈/중복 ID·미지 필드/종류·빈 질의는 거부한다.

하나의 기존 review/NFC 인덱스를 공유하고 각 규칙을 독립적으로 유한 검증한 뒤 결합 expression으로1회
매칭한다. 규칙마다 XML/ZIP을 재수입하지 않는다. 일치는 leftmost nonoverlapping이고 동일 시작에서는
규칙 순서가 우선이다. 모든 겹친 형식의 합집합이나 한글의 겹침 정책이 아니다. 규칙별 inline flag는
격리하며 결합 후 capture 이름 충돌·잘못된 문법·관측된 zero-width 결과를 거부한다.

문서/구역/node/지문 결속 선택 창을 원본 전체에서 해석하고 hidden/MEMO 정책 제외를 매칭 전에 적용한다.
컨트롤·문단 경계를 합치지 않으며 regex의 anchor/word boundary는 기존 선택 창 검색 의미를 따른다.
규칙 질의 합계와 결합 expression 모두 서버 query byte 상한 안에 있어야 한다. 기존250000 원 scalar,
1000000 분해 scalar,10000일치,250000 보고 point,regex/DFA 각각2MiB,전체 응답4MiB ceiling을 유지한다.
응답 한도는 wrapper·규칙 분류·실제 원본 위치 전체에 적용하며 overflow를 잘라낸 성공으로 바꾸지 않는다.

## 결과와 원본 선택

결과는 전체 정책/요청 SHA, 원 source/index/scope/review 결속, 원본 위치 목록과 occurrence별 rule ID/종류다.
원문·질의·정규식·개인정보 값별 해시는 반환하지 않는다. 보관 결과의 앞/뒤 이동·순환은 기존 cursor와
정책/문맥에 결속하며 재수입/재검색하지 않는다. 다른 정책이나 문맥의 cursor는 거부한다.

SourcePersonalInfoDetectionSelection은 정확한 비어 있지 않은 원본 매핑만 제공한다. 역직렬화/파일/편집
API가 없고 좌표를 [기존 선택 마스킹](p09-source-personal-info-selection-mask-v1.md)에 넘겨도 fresh source,
정확한 NFC 기여,보호/필드/추적 상태·writer/readback을 다시 검사한다. 불연속 원본을 넓혀 선택하지 않는다.
raw source 자체를 변경하지 않으며 personal_identity_or_native_format_validated·whole_package_personal_data_removed·
mutation_or_execution_authority는 false다. 전체 문서 개인정보 검출/익명화 또는 현재 서비스 권한이 아니다.

## 검증과 남은 연결

[373](../../implementation/p09/evidence/p09-361-personal-info-detection373.v1.json)은 신규23+영향3 중25pass/1fail·
873fresh/final873·cleanupTrue다. 필수 tab 속성이 없는 합성 원본의 Body 수입 거부와 import 경고1을 보존했다.
유효 tab fixture와 미사용 import만 수정한 [374](../../implementation/p09/evidence/p09-361-personal-info-detection-recovery374.v1.json)는
실패1pass·이전25보존·875fresh/final875·진단/경고없음·cleanupTrue다. 현재 고유26개이며 단일26개 재실행이 아니다.
공식249·이전 전체 mask/product 시험을 반복하지 않았다.374 전체145.343초·명령28.550초·Job CPU26.812초·
private최고1893.80MiB/5.94395%·시스템CPU최고74.76%·가용RAM최저36.5547%와 Job 정리를 확인했다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했고 프리즈 해결 증거는 아니다.

다음은 현재 저장 권한·엄격한 읽기 전용 제품 요청과 native 기본 형식 정책의 자격이다. 전체 검색 옵션·
실제 변경/저장/게시·신뢰 registry·target match_set/semantic_diff/reopen·Native/Gate는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기와 RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3를 유지한다.
