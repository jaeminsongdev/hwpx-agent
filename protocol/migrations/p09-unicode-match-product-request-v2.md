# P09 검색 일치 Unicode 정규화 제품 요청

`hwpx-agent.product-unicode-normalization-request/v2`는 현재 sealed 원본에서 검색 조건에 맞는
글자만 정규화한 후보를 준비하고, 현재 접근·원본·최종 head를 확인한 뒤 전달한다. 기존 v1의
선택 범위 전체 정규화는 유지하며, v1은 query/filter를 계속 거부한다. 두 요청은 서로의
작업을 받아들이지 않는다. 전체 SEARCH-022 트랜잭션과 Native Gate는 별도 미완료 경계다.

## 요청과 검색 조건

envelope와 네 selector는 기존 v1의 project/document/revision/head/source SHA·key/plan 결속을
그대로 사용한다. 원16KiB unique JSON/object parser와 selector 검증을 공유하며, 누락·미지·
중복·잘못된 값은 원본 읽기 전에 거부한다. operation의 필수 값은 다음과 같다.

```json
{
  "kind": "normalize_unicode_matches",
  "query": "à",
  "regex": false,
  "case_sensitive": true,
  "whole_word": false,
  "max_matches": 100,
  "form": "nfc",
  "run_policy": "first_original_run_retain_all_runs",
  "review_policy": {
    "include_hidden_explanations": true,
    "include_memo_bodies": true
  }
}
```

query는 비어 있지 않은4096byte 이하 문자열, max_matches는1~10000이다. form은
nfc/nfd/nfkc/nfkd 중 필수 선택이며 기본 호환 변환은 없다. 선택적 style_filter는 기존
declared/definition tagged 원본 조건을 사용하고 빈/잘못된 조건을 거부한다. 생략과 null은
모두 필터 없음으로 canonical 결속하며 raw 요청 지문은 구별한다. 유효 cascade·resolved
조건을 추정해 대체하지 않는다. direction·replacement·승인 flag 등 미지원 옵션은 거부한다.

문자열 query만 NFC로 만들고 regex 문법은 NFC corpus 위에서 그대로 실행한다. 선택 창과
review 제외 및 모든 NFC 기여자의 서식 조건을 적용한 뒤 일치 상한을 검사한다. 일치마다
정확한 원본 scalar를 정규화하며 인접 일치를 합치지 않는다. 빈 일치·불완전/불연속 원본
역상은 거부하고 NoMatches·NoChange와 구분한다. 세부 정책은
[검색 일치 source 프로필](p09-source-unicode-match-normalization-v1.md)을 따른다.

## 현재 저장 서비스와 전달 경계

prepare_unicode_match_candidate는 현재 document.write·scope·head·ACL·quarantine·AEAD와
전체 원본 Form proof를 확인한 뒤 한 match compiler를 사용한다. into_unicode_match_candidate는
기존 Borrowed/Owned 소유자를 이동하므로 clone·원본 재수입을 추가하지 않는다.

저장 v2 receipt는 원본 검색 일치/region/필터와 원본/index/scope·정규화 형태·run/review 정책·
원본/출력 review·출력 hash/보존을 연결한다. 제품 receipt는 raw/canonical/provider-scoped
요청과 source/head·key/plan을 추가로 결속한다. receipt/key는 접근 권한·key claim이 아니다.

보관 후보 verify/bytes는 현재 접근·원본·writer integrity와 최종 head를 확인하며 matcher나
정규화를 반복하지 않는다. consumer 직전 head 검사는 원 writer-integrity callback 안에서
수행한다. 기존 v1의 source/receipt/parser/전달 본문은 module 선언 한 줄씩 제거로 전체
역변환된다. 원본 compiler·matcher·guard·writer와 그 시험은 변경하지 않았다.

실제 output ingest·commit·revision CAS·멱등 key claim·dispatcher·Native 실행·게시를 열지
않았다. require_current_product_route는 현재 후보를 확인한 뒤 RouteUnqualified를 반환한다.

## 검증 결과

components166 신규제품22pass·666fresh/final666·진단/경고없음·cleanupTrue다. literal/regex/
case/whole-word·네 형태·인접 일치 분리·네 범위/discovery·원본 모든 기여자의 선언/정의 필터·
review 제외 우선 상한/cache·cross-run/상이한 참조/entity/제어/재정렬, strict/typed filter/
escaped duplicate/16KiB/null canonical/v1 및 legacy 분리, query/mode/filter/form/policy/max/
scope/key/plan 지문, 현재 write/다섯 외부 scope·ACL 철회/복구·격리·AEAD, 준비/확인/전달의
최종 head 경합, borrowed/owned/JSON 동등성, 잘못된 source/head/revision/doc/project/index,
NoMatches/NoChange/빈 일치/역상/보호/no-op·패턴/일치/확장/응답/writer 한도, 비노출·닫힌
route·source/head/ingest 보존과128일치의 공유 map을 확인했다.

기존 source42·제품150·공식249는 재실행하지 않았다. v1의 원 두 모듈과 시험 parent는
선언 한 줄 제거로 전체 역변환했으며 source compiler와 다른 제품 입력은 모두 일치했다.
컴파일 대상에 기존150개가 포함된 것과 실제 재실행은 구분한다.

전체129.718초·명령44.547초·시험10.91초·Job CPU42.594초·private최고1703.56MiB/5.3469%·
시스템CPU최고32.33%·가용RAM최저23.3025%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초, Job active0/empty/handle closed와
전후 입력 확인을 유지했다. 다른 앱·OS·Defender 변경이나 프리즈 해결·benchmark 주장은 없다.
근거는 implementation/p09/evidence/p09-361-unicode-match-product-components166.v1.json이다.

## 남은 P09와 통합 계약

이 v2는 선택 창 안의 모든 비중첩 일치를 대상으로 하는 명시적 요청이다. 범용 카탈로그의
방향/유효 서식/숨김 의미·전체 selector/filter·보호·target match_set/semantic_diff/reopen,
dispatcher/DB/commit/CAS/멱등 실행/게시와 Native 증거는 미완료다. source API v12는
incomplete/미해결4/report없음/exit3이며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작을 유지한다. 고정 CROSSREF8종은 NOT_RUN, Native011은 미승인·미실행이다.

다음 접근 허용 불필요 작업은 SEARCH-013 대소문자 변환의 명시적 변환 정책과 원본 compiler다.
Unicode 경로의 남은 통합/target Gate를 보존하며 다른 P09 기능 구현과 함께 종료 조건을 충족한다.
