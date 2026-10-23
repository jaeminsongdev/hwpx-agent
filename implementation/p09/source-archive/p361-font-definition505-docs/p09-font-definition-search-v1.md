# 원본 글꼴 선언 조건 검색

원본 글자 정의가 참조한 언어별 글꼴 선언에 조건을 적용하는 구현이다. 현재 소스 연결과 신규 소스 시험8개·저장소 제품 시험5개는 **UNVERIFIED / NOT_RUN**이다. 실제 한글의 표시 글꼴, 설치 여부, 파일 존재, 임베딩 활성화나 P09 Gate 통과를 의미하지 않는다.

## 요청과 선언 속성

v3와 v4의 definition 호환 요청은 `operation.definition_filter.font_details`, v7의 definition 요청은 `operation.style_filter.filter.font_details`, v9는 `operation.style_filter.font_details`를 사용한다. 명시적 definition에는 `character_source`가 필요하다. v9는 기존 required direct 축의 미해결 거부를 유지한다.

선택 언어는 `hangul`, `latin`, `hanja`, `japanese`, `other`, `symbol`, `user`다. 선택한 모든 언어와 각 속성은 AND 조건이다. 같은 숫자 ID라도 다른 언어의 선언을 조회하지 않는다.

| 대상 | 조건 |
|---|---|
| 글꼴 선언6개 | `face`, `font_type`, `is_embedded`, `binary_item_id_ref`, `substitute`, `type_info` |
| 대체 글꼴 내부3개 | `face`, `font_type`, `binary_item_id_ref` |
| 종류 정보 내부10개 | `family`, `serif_style`, `weight`, `proportion`, `contrast`, `stroke_variation`, `arm_style`, `letterform`, `midline`, `x_height` |

이19개는 서로 독립된 최상위 키19개가 아니라 중첩된 선언 속성의 수다. `is_embedded`와 바이너리 참조는 원 선언 값이며 실제 글꼴 파일의 가용성은 입증하지 않는다.

```json
{
  "character_source": "run_property",
  "font_details": {
    "hangul": {
      "face": {"query": "Example Font", "regex": false, "case_sensitive": true, "whole_word": false},
      "substitute": {"kind": "absent"}
    }
  }
}
```

`face`는 명시적인 네 필드의 literal/regex 조건이다. `font_type`은 `representative`, `true_type`, `hancom_font` 중 하나다. 선택적 문자열은 `{"kind":"absent"}` 또는 `{"kind":"present","value":"..."}`로 비교한다. 대체 글꼴과 종류 정보는 `absent` 또는 `present`이며, `present`의 `filter` 생략은 존재 여부만 비교한다. `filter`를 넣고 빈 객체를 주는 것은 거부한다.

빈 전체 조건·빈 선택 언어·알 수 없는 필드와 enum·정수 overflow·빈 문자열·제어문자·잘못된 regex를 거부한다. 글꼴명 패턴은 최대4096bytes, regex와 DFA 예산은 각각 최대1MiB이며 실제 검색의 더 작은 한도도 적용한다. 빈 문자열에 맞는 패턴은 요청 검증에서, 실제 선언명에 생긴 zero-width hit는 선언 평가에서 거부한다.

## 구현과 결과 경계

기존 typed catalog와 조밀한 ID 검사를 사용한다. 선택 언어별 원본 선언을 한 번 평가해 ID별 판정표를 만들고, 각 원본 문자에서는 ID 조회만 한다. 문자열 복제·regex 실행·XML 또는 ZIP 판독을 문자마다 반복하지 않는다. 원본 run/text/named 축과 NFC의 모든 기여자 조건은 유지한다.

문자열을 가진 필터는 `Clone`이지만 더는 `Copy`가 아니다. 반복 검색은 필터를 빌려 쓰고 요청과 후보가 각자 소유해야 하는 경계에서만 복제한다. 결과 JSON과 변환 영수증의 필터는 원문 글꼴명·바이너리 참조·serif 조건 대신 `hwpx-agent.source-font-definition-filter-binding/v1` 해시와 선택 언어를 출력한다. 요청의 정규형 직렬화는 원 조건을 보존해 identity와 cursor에 결속한다. 새 글꼴 조건이 없는 기존 요청·결과는 기존 직렬화 경로를 유지한다.

## 현재 검증 상태와 다음 순서

변경 전 소스69개는 `implementation/p09/source-archive/p361-font-definition503/`에 보존했다. 집중 시험 대상 `style_predicate_search`에 신규 소스 시험8개, `definition_detail_product`의 기존 host에 신규 제품 시험5개를 연결했다. 실제 통과 결과는 아직 없다. 이전502의25개 수용은 그때의 소스에 대한 기록이며 이번 변경의 검증으로 승격하지 않는다.

외부003의 실행 상태가 확인되기 전에는 공통 잠금 빌드·시험을 실행하지 않는다. 새003의 고정224개 입력과 분리된 소스·시험만 수정했으며 실행기·probe·원 자원 보호는 변경하지 않았다. 외부 결과 확인 후 새 조건과 직접 영향 경로를1코어·낮은 우선순위·기존 CPU/RAM 보호로 검증한다. 보호 중단 시 같은 검증을 반복하지 않고 관련 코드를 먼저 점검한다. 공식158/249, P09/A12/A13 OPEN, P10 미시작은 그대로다.
