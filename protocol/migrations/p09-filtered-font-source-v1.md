# 원본 서식 조건을 사용하는 폰트 대체

`hwpx-agent.source-selector-filtered-font-replacement/v1`은 원본 NFC 선택 창에
엄격한 `SourceReviewStyleFilter`를 결합한 별도 pure 후보다. 기존 scoped font v1과
저장/제품 JSON의 의미를 확장하지 않는다. 새 core 메서드는
`lower_scoped_font_filtered_candidate`이며 원본 Forms 또는 같은 원본의 검증 proof를 받는다.

## 조건과 범위

`declared`는 `paragraph_property`, `paragraph_style`, `run_character_property`,
`text_character_style` 중 하나 이상의 원본 참조를 지정한다. 조건은 AND이며 누락된 참조를
0이나 이름 있는 스타일로 대체하지 않는다. `definition`은 기존 typed 정의 필터의 명시한
글자/문단 축에서 굵게·기울임·크기·RGB·문단 정렬을 판정한다. 빈 조건·축 없는 값과 미지/중복
JSON 필드는 거부한다. 플랫폼 글꼴 가용성·상속 cascade·렌더링 숨김·fallback 판정이 아니다.

전체 원본 검증과 review 정책/selector 창을 유지한다. inspection은1회 만들고 정의 조건은
정의를1회 결속한다. 원본 segment마다 판정 결과를 캐시하므로 scalar/일치마다 ZIP/XML 수입이나
정의 결속을 반복하지 않는다. 한 NFC 단위의 모든 기여 원본이 조건을 만족해야 한다.
U+0344처럼 한 원본 scalar가 여러 NFC 단위에 기여하여 수용/제외가 겹치면 Selection으로 거부한다.
조건 불일치 원본은 변경 scalar 수에 포함하지 않지만 수입/색인/응답의 전체 자원 한도는 유지한다.

선택된 원본은 기존 필드 캐시·추적 표시·관측 보호와 두 서식 축의 guard를 그대로 거친다.
원본 글꼴 이름 query/replacement, 이미 선언된 언어별 대체 대상, 원본 정의 복제·비선택 보존과
출력 writer/readback은 기존 v1 경로를 공유한다. 모든 원본·XML·폰트 자원이 실제로 유효한 Native
폰트라는 자격은 추가하지 않는다.

## 후보와 영수증

`SourceFontFilteredReplacementCandidate`는 원 v1 후보를 private하게 소유한다. 별도 receipt는
원 v1 receipt, filter/inspection/선택 수, 필요할 때의 정의 receipt를 보관하고 이 전체를 새 profile의
`request_sha256`에 결속한다. 같은 원본과 출력이어도 필터가 다르면 이 hash는 달라진다.
기존 v1 receipt JSON에는 새 필드를 넣지 않으며 같은 전체 선택은 기존 receipt/bytes/inventory와 같다.

출력 bytes는 기존 writer integrity 검사를 거쳐서만 전달한다. 편집 inventory는 원 v1 receipt와 실제
헤더/본문 효과의 결속을 유지한다. 새 wrapper receipt를 v1 제품 요청이나 실행 허가로 소비할 수 없다.
`service_execution_or_native_qualified`와 `effective_style_visibility_or_execution_authority`는 false다.
별도 현재 저장 ACL/head/AEAD와 엄격한 v2 JSON·preview_only 연결은
[폰트 제품 옵션 계약](p09-font-options-product-v2.md)을 따른다. 이 원본 후보 자체는 현재 서비스 권한이 아니다.

## 검증과 남은 경계

[원본 필터 검증](../../implementation/p09/evidence/p09-361-font-style-filter331.v1.json)은 신규18개와
영향받는 기존 v1 원본6개, 총24개를 실행해 통과했다. 기존20개 시험 본문은 보존했으며 그중6개만
재실행했다. 769fresh/final769·진단/경고없음·cleanupTrue와 Job active0/empty/handle closed다.
원 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%는 유지했다.

전체 제품 옵션·전체 서식/폰트/보호 의미·신뢰 registry·실제 실행/저장/게시와 Native/Gate는
미완료다. RouteUnqualified/P02 routing_allowed=false, 공식158/249·잔여91·next165,
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
