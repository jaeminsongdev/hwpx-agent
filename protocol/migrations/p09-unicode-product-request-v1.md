# P09 선택 범위 Unicode 정규화 제품 요청

`hwpx-agent.product-unicode-normalization-request/v1`은 현재 sealed 원본의 선택 범위 전체를
정규화한 후보를 준비하고 현재 접근 검사를 거쳐 전달한다. source core만 따로 호출하거나
이미 만든 후보를 접근 권한처럼 사용하는 경로가 아니다. 이 프로필의 작업은
`normalize_unicode_scope`이며 검색어·서식 필터를 포함한 전체 SEARCH-022 요청과 구분한다.

검색 조건을 사용하는 [별도 source 후보](p09-source-unicode-match-normalization-v1.md)는
[별도 제품 v2](p09-unicode-match-product-request-v2.md)에 연결했다. 이 v1 요청은 query/filter를
계속 거부하며 두 버전의 작업을 암묵적으로 섞지 않는다.

## 요청 형태

기존 strict 16KiB unique JSON/object parser와 selector 검증을 공유한다. envelope는
schema_version·idempotency_key·project_id·document_id·base_revision·expected_head_generation·
expected_source_package_sha256·plan_id·selector·operation을 필수로 받는다. 원본 SHA는
64자리 소문자 hex이며 selector.revision_id는 base_revision과 같아야 한다.

operation은 아래 네 속성만 받는다. 누락·미지·중복·잘못된 값은 원본을 읽기 전에 거부한다.

```json
{
  "kind": "normalize_unicode_scope",
  "form": "nfc",
  "run_policy": "first_original_run_retain_all_runs",
  "review_policy": {
    "include_hidden_explanations": true,
    "include_memo_bodies": true
  }
}
```

form은 nfc·nfd·nfkc·nfkd 중 하나이며 기본값은 없다. query·regex·style_filter·replacement·
승인 flag 등 미지원 옵션을 무시하지 않고 오류로 반환한다. 다른 검색·문자열·정규식·서식
요청 스키마도 새 작업을 받지 않는다. 생성된 범용 카탈로그 계약이나 operation dispatcher를
이 제한된 요청으로 대체하지 않는다.

selector는 기존 document·section·node_set·selection 의미를 그대로 사용한다. v6 scope
inventory JSON으로 요청을 구성할 수 있으며 호출자가 Form이나 XML을 따로 수입할 필요가 없다.
선택 범위는 index NFC Unicode scalar 좌표이며 원본의 분할 불가능한 역상은 거부한다.

## 현재 저장 원본과 결과 전달

`StoredImportedDocumentForms.prepare_unicode_candidate`는 current document.write·scope·head·
ACL·quarantine·AEAD와 전체 원본 Form proof를 확인하고 source compiler를 한 번 호출한다.
`into_unicode_candidate`는 기존 Borrowed/Owned 소유자를 이동하며 clone·원본 재수입을 추가하지 않는다.

제품 receipt는 raw/canonical/scoped 요청 지문과 source/head·정규화 형태·run/review 정책·
selector/index·원본/출력 review·출력 integrity를 결속한다. key·plan은 지문 입력이지 key claim이나
실행 권한이 아니다. 보관 후보의 verify/bytes는 현재 접근·원본·writer integrity와 최종 head를
확인하며 정규화나 질의를 다시 실행하지 않는다. bytes callback 안에서 consumer 직전에
head를 다시 검사한다. 이 확인은 원자적 revision CAS를 뜻하지 않는다.

변경 최소 성분·원래 run/t 참조·제어와 선택 밖 내용의 보존, cache와 no-op 보호는
[원본 정규화 프로필](p09-source-unicode-normalization-v1.md)의 규칙을 그대로 따른다.
실제 ingest·commit·CAS·멱등 key claim·Native 실행·게시를 열지 않으며
require_current_product_route는 현재 후보를 검증한 뒤 RouteUnqualified를 반환한다.

## 검증 결과

components161 신규제품20pass·657fresh/final657·진단/경고없음·cleanupTrue다. 네 형태·네
범위와 discovery 요청 구성, 요청 drop 후 owned 사용, cross-run 한글/상이한 참조/entity,
제어 경계·NFD 재정렬과 base 서식 유지, review 정책과 cache, strict/중복/16KiB/legacy 분리,
raw/canonical/scoped/key/plan/form/policy 지문, 현재 write/다섯 외부 scope·ACL 철회/복구·격리·
AEAD, 준비/확인/전달의 최종 head 경합, borrowed/owned/JSON 동등성, 잘못된 source/head/doc/
project/revision, 보호/no-op·한도·128성분, 비노출·닫힌 route·source/head/ingest 보존을 확인했다.

기존 두 root는 module 선언 한 줄씩, 기존 시험 parent는 새 child 선언 한 줄 밖을 전체
역변환해 대조했다. source81·기존제품130·공식249·무관 suite는 재실행하지 않았다.
컴파일 대상에 기존 시험이 포함된 것과 그 시험의 재실행은 구분한다.

전체127.188초·명령43.297초·시험8.20초·Job CPU41.344초·private최고1705.17MiB/5.3519%·
시스템CPU최고31.84%·가용RAM최저23.4919%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초와 Job active0/empty/handle closed를
유지했다. 다른 앱·OS·Defender 설정 변경이나 프리즈 해결·benchmark 주장은 없다.
근거는 implementation/p09/evidence/p09-361-unicode-product-components161.v1.json이다.

## 남은 SEARCH-022와 P09 경계

다음은 검색어·서식 필터와 원본 변환의 결합이다. 전체 selector/filter·보호·match_set·
semantic_diff·reopen, dispatcher/DB/commit/CAS/멱등 실행/게시와 요구되는 Native 증거는
미완료다. source API v12는 incomplete/미해결4/report없음/exit3이며 공식158/249·잔여91·
next165·P09/A12/A13 OPEN·P10 미시작·목표ACTIVE를 유지한다. 고정 CROSSREF8종은 NOT_RUN,
Native011은 미승인·미실행이다. 이 제품 요청의 통과로 전체 SEARCH-022나 P09 Gate를 닫지 않는다.
