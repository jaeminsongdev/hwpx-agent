# 폰트 서식 필터와 미리보기 제품 요청

`hwpx-agent.product-scoped-font-replacement-request/v2`는 현재 sealed Result의 원본에
선택적 style_filter와 필수 preview_only를 결합하는 별도 준비 요청이다. 기존 v1의 스키마와
저장/제품 알고리즘은 그대로이며 v1은 두 옵션을 계속 거부한다. v2 변경 후보는 공통20번째 family이며
미리보기는 별도 비변경 결과다. 실제 실행·저장 트랜잭션은 아직 연결하지 않았다.

## 요청과 한도

기존 v1의 project/document/revision/head/source SHA·key/plan·selector와 폰트 query/replacement,
regex/case/whole word·언어·서식 축·review 정책을 모두 명시한다. 추가 필드는 다음과 같다.

- `preview_only`: 필수 Boolean. 누락/null/문자열/숫자는 거부한다.
- `style_filter`: 선택적 `SourceReviewStyleFilter` object. 누락은 무필터이며 명시적 null은 거부한다.
  `declared`의 원본 참조 또는 `definition`의 명시적 정의값 조건만 받는다. 빈 조건·축 없는 값·
  미지/중복 키·enum object와 암묵적 fallback 조건을 거부한다.

전체 요청은16KiB, 원본 변경 scalar 상한 `max_changed_scalars`는1..10000이며 서버 상한과 교집합을
취한다. 이 수는 정규화 글자나 occurrence 개수가 아니고 카탈로그 max_replacements 100000 지원도
아니다. 원본·검색·정규식·writer 상한은 미리보기에서도 유지하며 초과를 부분 성공으로 만들지 않는다.
중복/escape 중복·형태·값·버전 오류는 source 읽기 전에 거부한다. 정규식 컴파일과 실제 폰트 대상
해석은 인증된 원본 경로에서 이루어지며 실패를 성공한 미리보기로 바꾸지 않는다.

## 현재 저장과 두 결과 모드

현재 document.write·provider scope·head/ACL/quarantine/AEAD와 같은 원본의 whole-source proof를
사용한다. 선택적 필터는 [원본 필터 계약](p09-filtered-font-source-v1.md)의 segment 캐시와 NFC 기여
원본 규칙을 따른다. 저장 receipt는 unfiltered/filtered를 구분하며 조건·원본·출력을 결속한다.
원본 owner는 준비 후 이동하고 원본 clone이나 font matcher/writer를 반복하지 않는다.

`preview_only=false`는 writer integrity와 consumer 직전 head 확인을 거쳐 후보 bytes를 전달한다.
이 후보가 현재 실행 자격이나 revision commit을 부여하지는 않는다.

`preview_only=true`도 같은 후보 생성·writer/readback까지 수행한 뒤 output artifact를 버린다.
`PreparedStoredFontPreview`는 원본 owner와 예측 receipt만 보관하며 bytes/inventory/compiler API나
후보 복구 전환을 제공하지 않는다. 제품의 파일 요청은 `PreviewOnly` 오류이고 consumer를 호출하지 않는다.
원본을 수정하지 않으며 artifact ingest·idempotency claim·CAS·게시도 하지 않는다. 빈 출력이나 가짜 plan을
생성하지 않는다. receipt의 output SHA와 변경 수는 예측값이며 저장된 출력이나 실제 수행 증거가 아니다.

제품 receipt는 preview flag, raw/canonical/scoped 요청 SHA와 저장 receipt를 함께 결속한다.
`candidate_output_retained`는 변경 후보에서 true, 미리보기에서 false다. 메타데이터 JSON은64KiB
상한이며 재전달마다 현재 write/ACL/source 무결성과 최종 head를 다시 검사한다. retained verify는
matcher나 compiler를 재실행하지 않는다. 최종 head 확인은 원자적 CAS나 반환 이후 권한 회수를 뜻하지 않는다.
실행·게시 권위와 key claim은 false이며 두 모드의 제품 실행 요청은 RouteUnqualified다.

## 공통 준비와 계획 및 비변경 미리보기

`StoredFontOptionsMutationRequest`는 strict v2의 preview_only=false만 원본 읽기 전에 수용한다.
그 결과인 `PreparedStoredFontOptionsMutation`만 compiler view와 실제 편집 inventory를 소유한다.
폰트 연결 당시 공통 mutation 표는 기존19개 순서를 유지한20개이며 `FontOptions`가 마지막이었다.
현재는 그20개 순서 뒤에 문단 스타일 이름 v1/v2를 추가한22개다. 폰트 v1/v2의 위치와 동작·인자·
기존 SearchPreview API는 그대로이며 [추가 계열 계약](p09-named-paragraph-style-product-v2.md)을 따른다.

preview_only=true는 공통 `SearchPreview`로 분기하고 `with_verified_preview_json`으로만 전달한다.
원본 읽기 전에 compiler가 이 모드를 거부하므로 preview에 빈 plan을 만들지 않는다. 저장 preview는
출력 artifact가 없으며 공통 preview에도 bytes/inventory/compile/실행 manifest API가 없다.
공통 bytes 요청은 PreviewOnly, 변경 후보의 preview JSON 요청은 PreviewKind로 거부한다.
현재 source/권한·consumer 최종 head와 기존 route 거부는 두 모드에서 유지한다.

변경 후보의 계획은 기존 [폰트 자원 계약](p09-compiled-font-resources-v1.md)의 본문 실제 owner와
두 헤더 효과를 사용한다. 폰트 v1/v2는15개 잠금 인자, 다른 기능은 기존12개다. 전체 편집 inventory의
legacy hash는 원 v1 source receipt에 계속 결속한다. v2의 mutation_receipt_sha256는 필터/정의까지
포함한 output receipt에 결속해 동일 출력/편집 inventory라도 다른 조건의 계획이 같아지지 않는다.
원본 소유자는 이동하고 matcher/수입/writer를 다시 실행하지 않는다. 실제 실행기는 별도다.

[공통 v2 검증](../../implementation/p09/evidence/p09-361-compiled-font-options335.v1.json)은
신규23+영향 공통6+영향 v2 제품6=35pass·779fresh/final779·진단/경고없음·cleanupTrue다.
preview compile 사전 거부·두 번째 실제 owner/공유 자원·정의/text/NFC·필터별 계획 지문·한도/현재
권한/변조와 최종 head 경합5개를 확인했다. 기존 두 시험의 schema 개수/새 슬롯 기대만20으로 갱신했고
giant suite·공식249·원본24개를 반복하지 않았다. 준비/계획/preview 검증이지 실제 실행 자격은 아니다.

## 이전 저장과 제품 검증

[저장 및 v2 제품 검증](../../implementation/p09/evidence/p09-361-font-options-product333.v1.json)은
신규28개와 영향 v1 제품4개, 총32개 PASS·774fresh/final774·진단/경고없음·cleanupTrue다.
필터/양 축/선택·무필터 v1 호환·예측값/파일 거부·원본/head/ingest 불변·엄격한 입력/한도·현재 권한과
양 모드 준비/verify/JSON 전달의 마지막 head 경합6개를 포함한다. 기존80개 시험 본문은 보존했고
그중4개만 실행했다. 공식249와 원본24개를 반복하지 않았다. scanner/키/서비스 fixture는 합성이다.

전체 옵션·유효 cascade/폰트/fallback/보호 의미,
신뢰 registry·실제 실행/저장/게시와 Native/Gate는 미완료다. RouteUnqualified/P02 routing_allowed=false,
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
