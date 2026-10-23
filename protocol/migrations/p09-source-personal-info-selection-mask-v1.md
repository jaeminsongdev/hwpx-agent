# 원본 선택 본문의 개인정보 마스킹

`hwpx-agent.source-personal-info-selection-mask/v1`은 SEARCH-019의 명시적 원본 선택 마스킹 기반이다.
실제 HWPX에 별도 보존형 writer를 적용하지만 source-only이며 현재 저장·공통 실행·게시 권한은 없다.

## 공식 기능과 기존 카탈로그의 구분

한컴 [공식 multi 한글 도움말](https://help.hancom.com/hoffice/multi/ko_kr/hwp/security/user_info_protection/protection%28promptly_hide%29.htm)과
[2024 한글 도움말](https://help.hancom.com/hoffice130/ko-KR/Hwp/security/user_info_protection/protection%28promptly_hide%29.htm)은
바로 바꾸기를 종류별 개인정보 탐지가 아닌 선택 영역의 별표 변경으로 설명한다.2026-10-21에 원문을 확인했다.
한글2020 해당 URL은 읽지 못했으므로 exact2020의 저장 표현·별표 개수·적용 동등성을 추정하지 않는다.

[기존 카탈로그 계약](../../docs/04_feature_catalog/contracts/03_search_contracts.md)은 query/replacement·regex·
direction·style_filter의 일반 검색 계약을 적고 있으며 SEARCH-020은 read_only로 분류한다.
이 source profile은 일반 문자열 치환을 개인정보 기능 완료로 바꾸지 않으며 기존 계약을 대체/축소하지 않는다.
제품 통합 전에 선택 마스킹과 탐지/찾기 정책을 대조해 versioned 요청·migration·target 근거를 연결해야 한다.

## 선택과 정책

SourceIndexScopeSelector의 document/section/node/지문 결속 selection을 명시하고 review body 포함 정책을 받는다.
전체 원본 Form proof와 whole protection/field/review/index를 한 번 구축하고 기존 typed planner/writer/readback을
사용한다. NFC index unit의 모든 원본 기여 scalar를 선택해야 하며 재정렬의 불연속 선택·stale/foreign 원본을
거부한다. 컨트롤·문단 경계를 넘겨 마스킹 그룹을 합치지 않는다.

SourcePersonalInfoMaskPolicy의 PerOriginalScalarPreserveSlots는 원 Unicode scalar 하나당 별표 하나를 원래
run/text 슬롯에 둔다. ThreeAsterisksPerTextGroup은 연속 글자 묶음당 별표3개를 첫 원본 기여 위치에 놓는다.
byte/UTF16/grapheme 기준이나 실제 한글 기본값이 아니다. already masked·빈 선택은 NoChange이며 보호/
tracking/field cache는 no-op을 제거하기 전에 검사한다. 비선택 XML/entity·run/style/control/reference shell을 보존한다.

기존 기본 한도인 원 scalar250000·분해/작업1000000·변경 성분10000·전체 응답4MiB와 writer/patch 한도를 유지한다.
서버는 고정 ceiling 안에서 더 작은 제한을 선택할 수 있다. private binding hash는 별도 고정4MiB streaming
상한을 가지며 공개 receipt byte 한도를 내부 hash 입력에 재사용하지 않는다. 정확한 공개 byte와1byte 부족을 검증한다.

## 결과의 개인정보 경계

SourcePersonalInfoMaskReceipt에는 원본/출력 패키지 지문·범위·정책·집계·review import 결속만 들어간다.
원문·선택 조각·개인정보 값별 해시는 JSON/Debug에 넣지 않는다. 원본 scalar 수 등의 집계는 반환하므로
정보 이론적 비노출이나 비가역 익명화를 주장하지 않는다.

whole_package_personal_data_removed와 native_mask_semantics_or_service_execution_qualified는 false다.
header·메모 저자·미리보기·이미지·첨부·과거 이력까지 제거하지 않으며 비선택 개인정보도 남을 수 있다.
현재 서비스 검증/멱등 claim/CAS/실행/게시·target 검증은 별도다. 원본 소유 자료는 보존한다.

## 검증과 다음 경계

[362](../../implementation/p09/evidence/p09-361-personal-info-mask362.v1.json)는 fixture assembly 모듈 누락
E0432·시험0·848fresh/final848·cleanupTrue다. 마스킹 제품 코드는 수정하지 않았다.
[363](../../implementation/p09/evidence/p09-361-personal-info-mask-recovery363.v1.json)은 선언1개와 임시 경로 인자만
보완한 신규25+공유 경계3=28pass·850fresh/final850·진단/경고없음·cleanupTrue다. 이전 PASS/전체 제품/공식249는
반복하지 않았다. 전체121.765초·시스템CPU최고24.25%·private최고588.29MiB/1.8464%·가용RAM최저39.4991%이며
원 자원 보호·두 Job 정리를 유지했다. PC 프리즈 해결 증거는 아니다.

다음은 현재 저장/엄격한 제품 요청과 실제 실행·저장·전체 개인정보 정책 및 SEARCH-020 탐지/읽기 전용 선택이다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기를 유지한다.
