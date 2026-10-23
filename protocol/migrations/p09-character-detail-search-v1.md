# 원본 글자 모양 세부 조건 검색

P09의 서식 검색에 선택적인 `character_details` 조건을 추가한다. 기존 typed character catalog의 원본 선언값을
그대로 비교하며, 설치된 글꼴 선택·대체 글꼴·렌더링·전체 유효 서식 우선순위를 추정하지 않는다.
기존 definition-axis 검색과 현재 저장 원본의 strict v9 직접 서식 검색이 같은 matcher를 사용한다.

v3/v4의 명시적 definition 호출과 네 범위 v7 제품 연결도 [세부 조건 제품 계약](p09-detail-definition-product-v1.md)에서 확인했다.
v9의 요구 direct 축 해석과 명시적 run/text/named 축 선택은 서로 다른 계약으로 유지한다.

## 조건과 결합

기존 24개 조건군은 다음과 같다. 추가된 `border_definition`은
[참조된 실제 테두리 정의](p09-border-definition-search-v1.md)의 값들을 비교하며 기존 ID 조건과 함께 AND로 사용한다.

- `shade_color`, `use_font_space`, `use_kerning`, `emphasis`, `border_fill`
- `underline_position`, `underline_shape`, `underline_color`, `strikeout_shape`, `strikeout_color`, `outline`
- `shadow_type`, `shadow_color`, `shadow_offset_x`, `shadow_offset_y`
- `emboss`, `engrave`, `superscript`, `subscript`
- `font_refs`, `ratios`, `spacing`, `relative_sizes`, `offsets`

마지막 5개 조건은 `hangul`, `latin`, `hanja`, `japanese`, `other`, `symbol`, `user`의 7개 언어 슬롯을 구분한다.
지정한 슬롯만 비교하고 여러 슬롯·조건·기존 굵게/기울임/크기/색/문단 정렬은 모두 AND로 결합한다.
`font_refs`는 해당 언어의 원본 font ID 선언을 비교하며 글꼴 이름이나 실제 표시 글꼴을 해석한 결과가 아니다.

`false`, `0`, 음수 자간·오프셋은 실제 값이다. 색은 `{"kind":"none"}` 또는
`{"kind":"rgb","rgb":[17,34,51]}`로 구분한다. 테두리 참조 부재는 `{"kind":"absent"}`이고
정확한 선언 ID는 `{"kind":"reference","id":2}`다. 밑줄/선/윤곽/그림자/강조는 기존 typed 모델에 대응하는
닫힌 snake_case enum 값만 받는다. 빈 세부 조건, 빈 언어 조건, 알 수 없는 키와 enum, 정수/RGB 범위 초과는 거부한다.

예를 들어 v9 요청의 기존 `operation.style_filter`에 다음 조건을 줄 수 있다.

```json
{
  "bold": true,
  "character_details": {
    "underline_position": "bottom",
    "spacing": {"hangul": -4},
    "engrave": false
  }
}
```

## 기존 요청과 현재 접근 보존

새 선택 필드가 없는 필터는 필드를 직렬화하지 않으므로 기존 canonical filter bytes와 해시를 보존한다.
새 필터를 쓰면 모든 조건이 요청·결과·보관 커서의 결속에 포함된다. 같은 match 목록을 만들더라도 다른 조건의
영수증/커서를 혼용할 수 없다. 기존 버전·envelope·query·selector·review 정책·16KiB 요청 상한과 decoded-key
중복 검사는 유지한다. 변경 가능한 JSON을 보관 접근 권한으로 사용하지 않는다.

definition-axis 경로는 원본 character source 축을 명시해야 한다. v9는 기존 run의 직접 참조와 요구 축의
해석 여부를 먼저 확인한다. 없는 직접 참조나 해석되지 않은 text/control 스타일 우선순위는 검색어가 없더라도
기존 typed Unresolved 오류다. 새 조건을 false match로 바꿔 불확정 영역을 누락하지 않는다.

기존 원본 인덱스·typed header 해석을 공유한다. 일치 건수별 ZIP/XML/header 재수입을 추가하지 않으며 NFC로
합쳐진 문자도 모든 원본 기여 조각이 조건을 만족해야 한다. 현재 source/head/ACL/quarantine/AEAD 확인과 JSON/next
전달 직전의 head 확인을 유지한다. 저장 원본이나 결과 문서를 수정·게시하지 않는다.

## 검증 범위

481은 core43개의 본문 진행 뒤 대형 제품 바이너리를 빌드하던 중 종료됐고 최종 발행에서
COMPACT_RECEIPT_PAYLOAD_LIMIT가 발생했다. 마지막 제품 진행 표본은291.4초이며 구현된 명령 한도는300초다.
원 제품 종료 오류와 전체 row/최종 입력 검사는 복원하지 않는다. 별도 실패 관측과 원 실행기/시험 부모를 보존했고,
본문43개를 다시 실행하거나 정식 수용으로 승격하지 않았다.

[482](../../implementation/p09/evidence/p09-361-character-detail-focused482.v1.json)는 신규 제품5·직접 영향20을
전용 호스트에서 통과했고883fresh/final883·실제 compiler dep-info1final·cleanupTrue다. 기존 fixture37줄의
정확한 추출 역변환과 head 경합 fixture 동일성을 확인했다. 원제품 시험 본문은 변경하지 않았고 다른 family를
함께 컴파일하는 호스트만 분리했다. 실제 명령21.860초·Job CPU19.375초·private최고753.49MiB다.
전체134.453초·시스템CPU최고74.40%·가용RAM최저37.269%이며 기존 자원 보호 중단은 없었다.

발행 한도는256KiB 그대로다. 원본 pin의 경로 디렉터리를 inline 표로 공유하고 모든 경로/크기/SHA를
정확히 복원하는 layout6 모형을 통과했다. 압축·외부 carrier·검사 생략을 사용하지 않는다.
이 결과는 `tools/p09/character_detail_receipt.py:unpack`으로 source_pins/resource_samples를 복원해 읽는다.
실행481의 원 row나43개 수용 증거를 이 표로 만들어낸 것은 아니다.

전체 유효 cascade/visibility·글꼴 이름/대체/설치 상태·보호/저장 트랜잭션·match_set/semantic_diff/reopen·Native와
P09 Gate는 별도 요건으로 남는다. 새 조건 구현이나 시험 통과로 공식249 큐의 수용 건수를 늘리지 않는다.
