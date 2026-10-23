# 원본 탭 정의 조건 검색

문단 모양 검색에서 선택한 문단 정의의 `tabPrIDRef`가 실제로 가리키는 탭 정의를 검사한다.
기존 v3/v4의 명시적 문단 축, v7의 네 가지 범위, v9의 필수 직접 문단 축에 `tab_details`를 연결한다.
검색과 변환 후보의 원본 조건이며, 렌더링된 탭 위치나 Native 저장 검증을 대신하지 않는다.

## 요청 조건

`SourceDefinitionStyleFilter.tab_details`에는 `paragraph_source`를 함께 지정한다.
`direct_property`와 `named_style`은 각각 원본의 다른 참조를 따라가며, 서로의 기본값으로 사용하지 않는다.
`SourceResolvedStyleFilter.tab_details`는 직접 문단 축을 요구한다. 직접 참조가 없는 선택 영역은
검색어가 없어도 `Unresolved`이며 이름 붙은 스타일로 대체하지 않는다.

```json
{
  "paragraph_source": "direct_property",
  "tab_details": {
    "auto_tab_left": true,
    "auto_tab_right": false,
    "stop_count": 3,
    "stops": [
      {"index": 0, "stop": {"kind": "direct", "item": {"position": 0, "unit": {"kind": "absent"}}}},
      {"index": 1, "stop": {"kind": "hwp_unit_char", "current": {"position": 100}, "fallback": {"position": 201}}}
    ]
  }
}
```

- 자동 왼쪽/오른쪽 탭, 탭 개수와 원본 순서의 각 탭을 AND로 검사한다. `false`, 위치0과 개수0은 실제 조건이다.
- `stops.index`는0부터 시작하며 오름차순·중복 없음이 필수다. 일부 순서만 지정할 수 있고, `stop_count`를 함께 지정하면 전체 개수도 일치해야 한다.
- 탭 항목은 위치·정렬·채움선·단위 선언을 검사한다. 정렬은 `left/right/center/decimal`, 채움선은 기존 `DefinitionLine`의12개 값이다.
- 단위는 `absent`와 `present`를 구분한다. 명시적 `character/hwp_unit`을 생략된 속성과 같은 기본값으로 처리하지 않는다.
- 직접 항목과 `hwp_unit_char` 호환 항목을 구분한다. 호환 항목의 `current/fallback`은 각각 검사하며 어느 분기가 화면에 적용되는지 추정하지 않는다.
- 빈 조건·빈 중첩 항목·알 수 없는 키/enum·음수 위치·정수 넘침·범위를 벗어나거나 중복/역순인 인덱스를 거부한다.

조건이 없는 기존 요청은 `tab_details`를 직렬화하지 않는다. 원본 탭 의미가 손상된 경우에는
해당 조건을 요청했을 때 정의 오류로 거부하며, 거짓 매치나 빈 카탈로그로 바꾸지 않는다.
글꼴 조건을 함께 사용하는 결과에서도 글꼴 원문 비노출을 유지하면서 탭 조건과 요청 식별자를 보존한다.

## 구현과 부하

기존 `TabDefinitionCatalogReader`의 제한·조밀한 ID·순서·호환 분기 검사를 재사용한다.
P00~P08의 탭 reader/writer와 기본 서식 판독 규칙은 변경하지 않았다.
요청에 탭 조건이 있을 때만 헤더를 판독하고 문단 카탈로그의 탭 ID 도메인과 대조한다.
정의별 판정을 한 번 계산한 뒤 고정된 ID 판정표를 조회하므로, 문자마다 XML이나 탭 조건 목록을 다시 읽지 않는다.
요청 인덱스를 오름차순·유일하게 제한해 정의별 비교량도 원본의 제한된 탭 수를 따른다.

## 검증 결과

`implementation/p09/evidence/p09-361-tab-definition510.v1.json`은 현재 소스11개·저장 경로8개, 총19개의 범위를 마감했다.
이 중10개는508에서 통과한 본문·라이브러리·보호 코드와 영향 없는 fixture의 동일성을 확인해 재사용했고,
참조 글꼴 조회를 수정한1개와 미실행 저장 경로8개만 실행했다. 탭 조건16종의 양성/음성은 v3/v7/v9의96개 저장 요청으로 확인했다.
네 v7 범위, v4와 이름 붙은 문단 축, strict JSON/escaped duplicate, 요청/커서 식별,
글꼴 비노출, ACL·AEAD·RouteUnqualified 유지도 포함한다.

탭 조건으로 선택한 실제 대소문자 변환 후보를 다시 import해 일치 문단만 바뀌고 원본이 유지되는 것을 확인했다.
이 결과를 다른 변환 family 전체나 실행·저장 coordinator의 수용으로 확대하지 않는다.

최종 검증은968개 입력의 전후 해시, 실제 dep-info2개와 산출물 전후 확인, `cleanup=true`를 기록했다.
186.422초 동안 시스템 CPU 최고24.41%, 가용 RAM 최저33.723%였고 보호 중단은 없었다.
1코어·낮은 우선순위·소유 Cargo CPU6.25%·RAM/commit95% 보호를 유지했다.

506의 비공개 fixture 메서드 컴파일 실패,507의 임시 경로 중복,508의 잘못된 글꼴 ID 기대,
509의 재사용 입력 목록 누락은 각각 원본 실패와 final fresh 누락을 보존했다.
실패한 원본이나 통과한10개 본문을 재실행하지 않았다. 변경 전 소스와 실패 당시 fixture/driver는
`implementation/p09/source-archive/p361-tab-definition506/`에 있다.

공식 시험은158/249·잔여91이며 P09/A12/A13은 OPEN이다. 실제 한글/COM·외부003·Native011·공식249는 실행하지 않았고,
외부003의 실패·소비된 claim·cleanup=false와 정확한 잔여 PID 정리 승인 대기는 그대로다. P10은 시작하지 않았다.
