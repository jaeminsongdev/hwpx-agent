# 공백 탭 줄바꿈 정규화 제품 준비 요청

`hwpx-agent.product-whitespace-normalization-request/v1`은 현재 저장된 원본에서 정확한 검색
일치를 정규화하는 후보 준비 API다. capability는 `search.normalize_whitespace`이며 원본 정책은
[source v1](p09-source-whitespace-normalization-v1.md)을 따른다. 현재 권한·원본·문서 head와
writer integrity를 검증하지만 revision을 반영하거나 전체 operation dispatcher를 실행하지 않는다.

## 요청과 정책

envelope에는 schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector와 operation이 필요하다.
selector는 기존 document/section/node_set/selection과 해당 revision·section/node/range 조건을
그대로 사용한다. expected source SHA는 lowercase64hex이며 head generation은 양수다.

operation은 아래와 같이 모든 동작 정책을 명시한다. style_filter만 생략하거나 null로 둘 수 있다.

```json
{
  "kind": "normalize_whitespace_matches",
  "query": " +",
  "regex": true,
  "case_sensitive": true,
  "whole_word": false,
  "max_matches": 100,
  "whitespace_policy": {
    "text": "ascii_space",
    "tabs": true,
    "line_breaks": false,
    "sequence": "collapse_each_matched_sequence",
    "output": {"spaces": {"count": 1}}
  },
  "run_policy": "first_original_run_retain_all_runs",
  "review_policy": {
    "include_hidden_explanations": false,
    "include_memo_bodies": false
  }
}
```

전체 요청은16KiB, query는1~4096bytes, max_matches는1~10000이다. 원 unique JSON/object parser와
selector shape 검증을 공유해 누락·미지 필드·잘못된 타입·escaped duplicate key·잘못된 정책과
서식 필터를 원본 읽기 전에 거부한다. 정규식 문법·일치 개수·역상은 bounded 원본 검색 단계에서
검사한다. 미지원 direction/locale/normalization/replacement를 무시하지 않는다. 기존 문자열/
정규식/Unicode/대소문자/폭 변환 요청의 의미를 넓히지 않고 잘못된 schema와 상호 거부한다.

text는 none/ascii_space/unicode17_breaking/unicode17_all_model_admitted이며 tabs/line_breaks는
필수 bool이다. sequence는 collapse_each_matched_sequence/each_original_scalar다. output은
spaces의 고정 count1~1024, tab의 unsigned width/leader/tab_type, line_break 또는 remove다.
typed 출력 내부 속성도 누락·미지 값을 거부하고 모든 입력 종류가 꺼져 있는 정책은 거부한다.
NBSP 등 비줄바꿈 공백은 all 정책에서만 포함한다. 고정 칸 수를 Native tab stop 계산으로 취급하지
않는다. 명시적 변환에서도 paragraph/run/t shell·일반 글자·참조와 선택 밖 바이트는 보존한다.

## 현재 저장 문서와 결과 전달

현재 document.write·외부 scope·head·ACL·quarantine·AEAD와 원본 Form proof를 확인하고 기존
원본 compiler를 한 번 호출한다. Borrowed/Owned 경로는 이미 import한 소유자를 이동하며 별도
clone/reimport를 추가하지 않는다. 후보를 verify하거나 bytes를 전달할 때 현재 원본 접근을 다시
확인하지만 matcher·정규화는 반복하지 않는다. writer 검증 callback 안에서 consumer 직전 최종
head를 다시 확인한다. 저장한 receipt나 원본 지문은 이후의 접근 권한을 대신하지 못한다.

source/index/selector·실제 검색/region/filter/review·정규화/run 정책·raw/canonical/scoped request
digest와 key/plan을 결속한다. filter 생략/null은 canonical에서 같고 raw 지문은 구분한다.
후보 원본·출력과 source/output review receipt의 package SHA 및 범위 개수를 확인한다.
request key는 영속 key claim이 아니며 issuer_execution_publication_authority,
idempotency_key_claimed와 full_whitespace_native_cas_execution_publication_authority는 false다.
require_current_product_route는 현재 검증 후에도 RouteUnqualified를 반환한다.

## 검증 결과

components187은 신규 제품24pass·703fresh/final703·진단/경고없음·cleanupTrue다. 명시적 정책·
typed 제어 생성/삭제·네 selector와 clipped regex·서식/whole-word·review/cache·cross-run/
alias/default namespace/entity/참조·strict/nested/중복/16KiB/null/legacy·지문·현재write/다섯 외부
scope·ACL철회/복구/격리/AEAD·준비/검증/전달의 최종head 경합·borrowed/owned/JSON동등성·
잘못된 source/head/revision/doc/project/index·보호/no-op/역상·한도·비노출·닫힌 route와 원본/
head/ingest 보존을 확인했다. 128일치는 한 part/segment map을 공유하며2만 공백은 한 patch다.
원본24·기존제품218·공식249는 반복하지 않았다. 테스트 root와 제품 두 root의 module 선언만
제거하면 원본 전체로 역변환되며 원본 compiler/보호/readback과 기존 제품/시험 본문은 그대로다.

전체141.219초·명령51.328초/시험12.42초·Job CPU48.828초·private최고1738.89MiB/5.4578%·
시스템CPU최고52.84%·가용RAM최저26.2659%다. Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. OS/다른 앱 변경이나 PC 프리즈 해결·benchmark 주장은 없다. 근거는
implementation/p09/evidence/p09-361-whitespace-product-components187.v1.json이다.

## 남은 제품 통합과 Gate

SEARCH-023 전체 유효 서식/selector/filter·target match_set/semantic_diff/reopen·dispatcher/
DB/ingest/commit/CAS/영속 멱등 실행/게시·Native/Gate는 미완료다. 이 JSON은 명시적 후보 준비
계약이며 전체 SearchScopeSelector·CLI dispatcher나 실제 revision 저장 완료가 아니다.
다음 접근허용 불필요 구현은 SEARCH-009 지원 제어별 원본 치환과 참조/ID 보존이다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
