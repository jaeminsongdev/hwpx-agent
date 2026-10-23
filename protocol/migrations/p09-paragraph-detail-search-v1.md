# 원본 문단 모양 세부 조건 검색

P09 SEARCH-003에 선택적인 `paragraph_details` 조건27개를 추가한다. 기존 P05 typed paragraph catalog가 읽은
원본 선언값을 비교하며 definition-axis 검색과 현재 저장 원본의 strict v9 제품이 같은 matcher를 사용한다.
실제 한글의 유효 서식·호환 분기 선택·쪽 배치·렌더링을 추정하지 않는다.

기존27개 외에 `border_definition`으로 [실제 참조된 테두리 정의](p09-border-definition-search-v1.md)를 비교한다.
테두리 ID·문단 오프셋과 별개의 조건이며 지정한 조건은 모두 AND다.

기존 v3/v4의 명시적 definition 호출과 네 범위 v7 제품에서도 같은 조건을 사용한다.
[명시적 제품 연결 계약](p09-detail-definition-product-v1.md)은 축 선택·정규형 사전 한도·현재 접근 및497의 수용 범위를 설명한다.

## 조건과 결합

모든 지정 조건은 AND다. 명시적 false·0·음수와 text direction의 부재도 값이며, 필터 조건 생략과 다르다.

- 기본 선언8개: `tab_property_id_ref`, `condense`, `font_line_height`, `snap_to_grid`, `suppress_line_numbers`,
  `checked`, `text_direction`, `vertical_alignment`
- 제목·나눔·자동 간격10개: `heading`, `latin_word`, `non_latin_word`, `widow_orphan`, `keep_with_next`,
  `keep_lines`, `page_break_before`, `line_wrap`, `auto_spacing_english`, `auto_spacing_number`
- 배치 분기2개: `current_layout`, `fallback_layout`
- 테두리7개: `border_fill_id_ref`, `border_offset_left`, `border_offset_right`, `border_offset_top`,
  `border_offset_bottom`, `border_connect`, `border_ignore_margin`

`text_direction`은 `absent`, `left_to_right`, `right_to_left`를 구분한다. `condense`는0..75이고,
나머지 정수는 기존 typed 값의 u32/u8/i32 범위를 따른다. `non_latin_word=hyphenation`은 원 모델처럼 거부한다.
참조 ID는 선언의 ID 값 비교이며 참조된 탭/테두리의 렌더링 동일성을 뜻하지 않는다.

## 배치와 제목 분기

두 layout 분기는 서로 독립적이다. 각 분기에서 `indent`, `left`, `right`, `previous`, `next`, `line_spacing`을 지정할 수 있다.
들여쓰기와 여백은 `value`와 명시적인 `unit` 쌍이며 `character`와 `hwp_unit`을 환산하거나 같은 값으로 취급하지 않는다.
`indent`는 기존 typed margin의 `intent`에 대응한다. 줄 간격은 `spacing_type`, `value`, `unit` 전체를 비교한다.
percent 값은 원 모델의0..500 범위를 따르고 나머지 spacing type은 기존 i32 값 범위를 유지한다.

제목은 `kind=direct`의 `heading` 또는 `kind=meta_tag`의 `current`/`fallback`을 명시한다.
각 제목 값은 `heading_type`, `id_ref`, `level`의 닫힌 객체다. 한 분기만 검색할 수 있지만,
direct와 meta_tag를 같은 의미로 합치거나 현재 분기가 실제 표시 결과라고 추정하지 않는다.
meta_tag의 두 선택이 모두 비었거나 layout 분기 객체가 비면 필터 오류다.

다음은 v9 요청의 `style_filter` 부분 예시다. 값은 시험 원본 선언의 값이며 실제 조판 결과가 아니다.

```json
{
  "alignment": "right",
  "paragraph_details": {
    "condense": 17,
    "snap_to_grid": false,
    "current_layout": {"indent": {"value": -720, "unit": "character"}},
    "fallback_layout": {"left": {"value": 1500, "unit": "hwp_unit"}},
    "heading": {
      "kind": "meta_tag",
      "current": {"heading_type": "outline", "id_ref": 0, "level": 4}
    }
  }
}
```

## 원본과 현재 접근 경계

명시적 definition 검색은 실제 사용할 `paragraph_source` 축을 요구한다. direct와 named의 정의값을 구분하고
어느 한쪽으로 자동 fallback하지 않는다. v9 resolved 검색은 선택한 원본의 direct paragraph 참조를 먼저 확인한다.
요청한 문단 축이 미해결이면 검색어가 없어도 원래 Unresolved 오류를 반환한다. 요청하지 않은 글자 축은 추정하지 않는다.

`paragraph_details`를 생략하면 기존 canonical filter bytes와 해시가 그대로다. 사용하면 모든 새 조건과 분기가
요청·결과·보관 cursor에 결속돼, 결과 일치 집합이 같아도 다른 필터의 cursor를 재사용할 수 없다.
현재 source/head/ACL/scope/quarantine/AEAD와 JSON·next 전달 직전 head 확인을 유지한다.
미지·중복 키, 빈 조건/분기, 단위 누락, 잘못된 enum/범위는 원본 읽기 전에 거부한다.
match별 ZIP/XML 재수입이나 header 재해석을 추가하지 않으며, 새 paragraph/layout matcher는 큰 조건을 참조로 받는다.

## 검증과 남은 범위

[495](../../implementation/p09/evidence/p09-361-paragraph-detail495.v1.json)는 신규 core8·제품6과 직접 영향 core12·제품10의36개를 통과했다.
조건27개의 양·음성, 양 layout의 모든 여백·단위·줄 간격, 제목 분기·엄격한 JSON/decoded duplicate,
네 범위·필수 축·기존 조건 결합·canonical 호환·cursor 결속·현재 접근/최종 head 경합을 확인했다.
기존 definition/resolution 본문과 제품 시험 부모를 전체 역복원 대조했고798fresh/final798·실제 compiler dep-info2final·cleanupTrue다.

전체194.062초, 코어 명령33.500초·제품 명령58.813초였다. 시스템CPU 최고33.98%, 가용RAM 최저38.081%이며
한 코어·BelowNormal·Job CPU6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 성능 벤치마크나 PC 프리즈 해결 판정은 아니다.
공식249 큐·기존 Native·통과한003 검사기 빌드는 반복하지 않았다. 전체 유효 서식·가시성·참조된 자원의 의미 조건,
실제 실행/저장/게시·Native·P09 Gate는 별도 미완료 범위로 남긴다.
