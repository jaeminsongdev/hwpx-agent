# 원본 글꼴 선언 조건 검색

원본 글자 정의가 참조한 언어별 글꼴 선언 조건을 기존 제품 경로에 연결했다. 신규 소스 시험8개·저장소 제품 시험5개와 직접 영향19개를 포함한 현재32개 범위를 검증했다. 실제 한글의 표시 글꼴, 설치 여부, font payload 유효성, 임베딩 활성화나 P09 Gate 통과를 의미하지 않는다.

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

바이너리 참조가 없는 입력은 기존 writer의 v6/v9 profile을 유지한다. 원 header의 font/substFont에 binaryItemIDRef가 있으면 이미 존재하는 scoped-font/v11의 명시적 font/text ID 규칙을 사용하며 manifest 대상이 없는 참조는 계속 거부한다. 검증 모형의 opaque resource는 참조 그래프만 닫으며 실제 글꼴 파일이 아니다.

변경 전 소스69개와 실패 직전 소스는 source-archive의 p361-font-definition503 및 p361-font-definition503-failure에 보존했다.
503은 소스24개 중23개 관측 뒤 변환 입력의 ID 검증에서 실패했다. 선언의 manifest 참조를 닫고 명시적 writer profile을 연결한504는 source writer6개와 stored7개를 관측했지만 v4 범위의 잘못된 기대값1개로 실패했다. 두 원 실패와 final fresh 누락은 보존한다.

v4 정의 호환 호출의 mapped_document는 기존 일반 본문 index이며 v7의 숨김·메모 포함 범위와 같지 않다. 수정한 시험은 같은 입력·같은 v4의 필터 없는 검색으로 일반 본문2개를 대조하고, v7의 네 범위·언어 AND 조건은 별도로 확인한다.

[현재505](../../implementation/p09/evidence/p09-361-font-definition505.v1.json)는 라이브러리·검증기·fixture와 다른 시험 본문이504와 같음을 대조해31개를 반복하지 않고 수정1개만 실행했다. 현재 source24+stored8=32개,944fresh/final944,실제 dep-info2개 final과 cleanup=true다. 실제 변환 후보9종의 영수증 비노출·출력 재읽기·원본 보존, 누락 manifest 거부와 현재 ACL/AEAD/cursor/닫힌 Native route를 포함한다.

505는126.203초·CPU최고28.52%·가용RAM최저37.652%이며 실제 단일 시험 단계는5.563초다. 나머지 약120.64초는 준비와 입력·산출물 마감 등을 포함한다.1코어·BelowNormal·Job CPU6.25%·RAM/commit95% 보호를 유지했고 보호 중단은 없었다.

외부003의 부모 Python 종료와 최종 실패를 확인한 뒤 한글에 연결하지 않는 Cargo 전용 검증만 분리 실행했다. 기존 한글 PID24780의 정리는 별도 승인 대기이며003 실패·claim 소비·cleanup=false는 변경하지 않았다. 새 Native 실행·003 재실행은 없었다. 공식158/249, P09/A12/A13 OPEN, P10 미시작은 그대로다.
