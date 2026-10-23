# 참조된 테두리 정의 검색

글자·문단 서식이 참조하는 실제 테두리 정의를 조건으로 검색한다. 같은 header 안에 조건에 맞는 테두리가
있다는 사실만으로 일치시키지 않고, 선택한 서식 축의 `borderFillIDRef`를 따라간다. 기존 P05 typed reader가
검증한 1부터 시작하는 조밀한 ID를 인덱스에서 직접 조회하며, 일치 위치마다 XML·ZIP을 다시 읽지 않는다.

## 요청과 비교 의미

`character_details.border_definition`과 `paragraph_details.border_definition`에 같은 조건 형식을 사용한다.
명시적 v3/v4·v7은 기존 source 축을 선택하고, v9는 기존 required direct 축의 완전성 검사를 먼저 수행한다.
전체 요청·범위·현재 저장 접근·결과·cursor 경계는 [명시적 제품 검색](p09-detail-definition-product-v1.md)을 따른다.

```json
{
  "character_details": {
    "border_definition": {
      "three_d": true,
      "left": {"line_type": "dash", "width": "mm0_3", "rgb": [1, 2, 3]},
      "fill_brush": {"kind": "window", "filter": {"alpha": 0}}
    }
  }
}
```

모든 조건은 AND다. 글자 축과 문단 축도 각각 참조하는 정의를 검사하며 서로 대신하지 않는다.
원본 ID를 비교하는 기존 `border_fill`·`border_fill_id_ref` 조건과 함께 사용하면 두 조건을 모두 만족해야 한다.
직접 서식 누락·불확정 text style·NFC의 여러 원본 기여자에 대한 기존 거부/일치 규칙은 유지한다.

| 조건 | 값과 중첩 조건 |
|---|---|
| `three_d`, `shadow`, `break_cell_separate_line` | bool, false도 조건 |
| `center_line` | none, vertical, horizontal, cross |
| `slash`, `back_slash` | slash_type: none/center/center_below/center_above/all, crooked, is_counter |
| `left`, `right`, `top`, `bottom`, `diagonal` | line_type, width, rgb |
| `fill_brush` | kind=absent 또는 kind=window/filter |
| window/filter | face_color, hatch_color, hatch_style, alpha: 0~255 |

선 종류는 기존 글자 선 종류 12개를 재사용한다. 굵기는 mm0_1, mm0_12, mm0_15, mm0_2, mm0_25,
mm0_3, mm0_4, mm0_5, mm0_6, mm0_7, mm1_0, mm1_5, mm2_0, mm3_0, mm4_0, mm5_0이다.
선 색은 RGB 세 정수이며 각 값은 0~255다.

`face_color`는 기존 kind=none 또는 kind=rgb/rgb 형식이다. `hatch_color`는 kind=absent 또는
kind=present/color이며, `hatch_style`은 kind=absent 또는 kind=present/style이다. 해치 종류는
horizontal, vertical, back_slash, slash, cross, cross_diagonal이다.
브러시 없음, 해치 속성 없음, 해치 색의 명시적 none, 조건 생략은 서로 다르다.
글자에 테두리 참조 자체가 없으면 `fill_brush.kind=absent`도 일치하지 않는다.

빈 테두리/선/대각선/window 조건, 알 수 없는 키·변형·범위 밖 값과 decoded duplicate는 거부한다.
absent 객체에 다른 필드를 붙이는 것도 거부한다. 새 조건이 없는 기존 세부 필터에는 새 키를 직렬화하지 않아
이전 정규형 bytes·identity를 보존한다. 같은 일치 집합이어도 조건이 다르면 cursor를 공유하지 않는다.

## 검증 결과와 한계

[498](../../implementation/p09/evidence/p09-361-border-definition498.v1.json)은 원본 검증 7개 통과 뒤
잘못된 중첩 요청 거부 1개가 실패했다. 원 실패·코드·실행기와 최종 입력 확인 누락을 보존했으며 정식 수용하지 않는다.
새 internally tagged absent 변형을 필드 없는 구조형으로 바꾸어 추가 필드를 거부하도록 수정했다.

[499](../../implementation/p09/evidence/p09-361-border-definition499.v1.json)은 수정 영향 원본 8개,
미실행 신규 제품 5개와 직접 영향 제품 회귀 4개의 총17개를 통과했다. 30개 양·음성 조건을 두 축과
v3/v4/v7/v9에서 확인했고, 엄격한 입력·현재 ACL·독립 AEAD·cursor 분리·원본 보존·닫힌 route를 확인했다.
824개 입력 전후 확인·실제 compiler dep-info 2개 최종 확인·cleanupTrue다.

258.75초, 시스템 CPU 최고38.02%, 가용 RAM 최저35.323%였다. 기존 한 코어·BelowNormal·Job CPU6.25%,
private8%/stop7%·RAM/commit95%를 유지했고 보호 중단은 없었다. 공식249·Native·003 실행은 포함하지 않는다.
지원하는 원본 typed window brush 검색이며, gradient/image·전체 유효 cascade/가시성·실제 실행·저장/재열기·P09 Gate는 미완료다.
