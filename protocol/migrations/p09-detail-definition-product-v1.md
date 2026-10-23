# 세부 서식 조건의 명시적 제품 검색

글자24개와 문단27개 조건을 기존 typed definition 검색 제품에서도 사용한다. v9의 요구 축 해석과 달리
명시적 definition 검색은 호출자가 run/text/named 또는 direct/named 축을 선택하며, 실제 표시 우선순위는 추정하지 않는다.

## 제품별 요청 경계

| 제품 | 세부 조건 위치 | 범위 | 축 의미 |
|---|---|---|---|
| v3 | `operation.definition_filter` | mapped_document, paragraphs | 사용한 character_source/paragraph_source를 명시 |
| v4의 기존 definition 호환 호출 | v3와 같음 | v3와 같음 | definition 호출에 review_policy를 혼합하지 않음 |
| v7 | `operation.style_filter`의 kind=definition/filter | document, section, selection, node_set | 명시한 축과 별도 review_policy |
| v9 | `operation.style_filter` | 네 selector 범위와 review_policy | 요청한 direct 축의 미해결을 검색 전에 거부 |

세부 값은 [글자 조건](p09-character-detail-search-v1.md)과 [문단 조건](p09-paragraph-detail-search-v1.md)을 따른다.
두 세부 조건의 `border_definition`은 [실제 참조된 테두리 정의](p09-border-definition-search-v1.md)를 비교한다.
기존 ID 조건·원본 축·요청 크기·현재 접근·cursor 계약을 유지한다.
명시적 축을 생략하거나 쓰지 않는 축을 넣으면 오류다. 없는 직접 참조를 ID0이나 named 정의로 대체하지 않는다.
v3/v7의 명시적 definition에서 선택 축 부재에 따른 불일치와 v9의 요구 축 Unresolved 오류를 같은 의미로 합치지 않는다.

예를 들어 v3의 definition_filter와 v7 definition/filter에는 다음 객체를 사용할 수 있다.

```json
{
  "character_source": "run_property",
  "character_details": {"underline_position": "bottom"},
  "paragraph_source": "direct_property",
  "paragraph_details": {"condense": 17}
}
```

## 정규형 크기 검사와 현재 접근

공통 v1~v4 parser는 raw16KiB 한도뿐 아니라 정규형16KiB 한도도 원본 접근 전에 확인한다.
중첩 필터의 생략 필드가 정규형에서 null로 늘어나 raw는 한도 안이지만 정규형은 초과하는 경우도 Limit 오류로 거부한다.
기존 원본·요청·결과 identity 확인은 그대로 유지하며 한도를 늘리지 않았다. 정확히16KiB인 공백 패딩 raw 요청은
기존처럼 canonical identity가 같고 raw identity만 다르다.16KiB+1은 계속 거부한다.

동일한 일치 집합이라도 필터·축·범위·policy는 요청과 결과에 결속된다. v7 retained cursor는 다른 세부 조건에 재사용할 수 없다.
현재 write/ACL/scope/head/quarantine/AEAD·최종 전달 경계를 유지하고 새 claim·ingest·CAS·실행·게시 권한을 만들지 않는다.
v3/v4와 v7은 기존 제품·저장 경로를 재사용하며 새로운 제품 구현체를 복제하지 않는다.

## 검증과 원본 보존

[496](../../implementation/p09/evidence/p09-361-detail-axes496.v1.json)의 신규10개 본문은 모두 exit0이었다.
공유 fixture의 blobs 필드를 사용하지 않는 전용 시험 호스트 경고 때문에 수용을 중단했으며 원 실패와 final fresh 누락을 보존했다.
공유 fixture를 수정하거나 경고를 숨기지 않고, 보호 사례1개에 별도 깨끗한 원본의 AEAD 변조 거부를 추가했다.

[497](../../implementation/p09/evidence/p09-361-detail-axes-recovery497.v1.json)은 원9개 본문·전체 helper의 역복원과
나머지 실행 입력 동일성을 확인하고 변경된1개만 실행했다. 현재10개를 수용하며809fresh/final809·실제 compiler dep-info1final·cleanupTrue다.
51개 조건의 v3/v7 양·음성, run/text/named·direct/named 구분, v3 두 범위·v4 호환·v7 네 범위,
엄격한 중첩/decoded duplicate·raw/정규형 한도·cursor·write/ACL/격리와 독립 AEAD·닫힌 route를 확인했다.

497은106.219초, 변경 사례 명령3.094초·시스템CPU 최고21.37%·가용RAM 최저41.016%다.
기존 한 코어/BelowNormal/CPU6.25%·private8%/stop7%·RAM/commit95%를 유지했다.
495의36개와 공식249·기존 Native·003 검사기 빌드는 반복하지 않았다. 전체 유효 서식·가시성·실제 실행/저장/Native/Gate는 미완료다.

## 반복 정의 비교 최적화

큰 세부 필터는 내부 matcher와 검증기에 참조로 전달한다. 각 검색은 자신이 빌린 원본 정의와 하나의 불변 필터에
한정된 캐시를 생성한다. 마지막으로 선택한 글자·문단 정의 ID 쌍과 bool 결과만 보관해 연속된 같은 정의의 비교를
재사용한다. ID0과 부재, 글자 축과 문단 축을 구분하며 사용하지 않는 축은 키에 넣지 않는다.

추가한 마지막 정의 캐시는 heap·문서별 테이블·전역 상태를 사용하지 않는다. 크기는 고정이고, 정의가 번갈아 나오면 해당 위치의
조건을 다시 평가한다. 모든 원본 NFC 기여자의 ID를 계속 확인하며 빈 기여 집합·없는 축·scope·review 정책의 기존
규칙은 유지한다. 다음 요청·다른 필터·새 원본·현재 접근 상태에는 재사용하지 않는다.
명시적 검색, review selector, required direct 검색, 글자·문단 교체와 필터된 글꼴·named 문단 교체가 같은 matcher를 사용한다.

[500](../../implementation/p09/evidence/p09-361-style-predicate500.v1.json)은 원본·교체 경로19개 본문 통과 뒤
공유 review fixture 함수 두 개의 미사용 경고로 수용을 중단했다. [501](../../implementation/p09/evidence/p09-361-style-predicate501.v1.json)은
보완 시험의 비공개 helper 접근 E0603으로 실행 전 중단됐다. 두 실패와 최종 입력 확인 누락을 보존했으며 경고나 공개 범위를 완화하지 않았다.

[502](../../implementation/p09/evidence/p09-361-style-predicate502.v1.json)은 원19개 본문·helper·제품 코드의 동일성을 확인해
본문을 반복하지 않고, 공개 package/ZIP reader로 원본 section bytes와 review 경계를 확인하는 새1개와 미실행 제품5개를 실행했다.
현재25개·854fresh/final854·실제 compiler dep-info2final·cleanupTrue다. 같은 쌍의 true/false 연속20,000회 호출은
실제 조건 평가2회였고, 번갈아 나오는10,000개 키·부재/ID0·다른 필터/원본·51개 복합 조건·NFC·현재 AEAD·cursor도 확인했다.

최종502는157.219초·시스템CPU 최고26.67%·가용RAM 최저37.825%였고 자원 보호 중단은 없었다.
원500의 시스템CPU 최고82.81% 표본은 별도 원본에 보존한다. 전체 작업 속도 향상률이나 PC 프리즈 해결을 입증한 결과는 아니다.
실제 글꼴 선언의 검색 조건 연결은 다음 구현이며 전체 유효 서식·Native·P09 Gate는 미완료다.
