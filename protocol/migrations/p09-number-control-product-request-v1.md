# 자동번호 재시작 치환의 현재 저장과 제품 요청

`hwpx-agent.product-number-control-replacement-request/v1`은 현재 sealed 원본의 AutoNumber/NewNumber를
찾아 저장 i32 번호와 명시적 typed 서식을 바꾸는 후보 준비 요청이다. 네 selector와 review 정책을
[번호 source compiler](p09-source-number-control-replacement-v1.md)에 연결했다. 실제 번호 재계산,
카탈로그 query/replacement 전체 계약, 저장 커밋·Native 실행은 아니다.

## 엄격한 요청과 번호 서식

외부 필드는 schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector, operation이다.
원16KiB unique JSON/object parser와 selector shape 검증을 공유한다. 누락·미지·중복 필드와 잘못된
타입/범위/소문자64자리 SHA·revision 결속을 거부하며 generation은 양수여야 한다.

| operation 필드 | 허용 값 |
|---|---|
| kind | replace_number_controls |
| control_kind | auto_number 또는 new_number |
| max_replacements | 1~4096 정수 |
| stored_number | i32 정수 |
| format | 명시적 preserve 또는 replace 객체 |
| review_policy | 필수 include_hidden_explanations/include_memo_bodies Boolean |

format은 `{ "kind": "preserve" }` 또는 kind=replace와 필수 format/user_character/prefix/suffix/
superscript를 받는다. Replace의 세 문자 값은 String, superscript는 Boolean이다. Preserve도 미지
nested 필드를 거부하며 생략된 값을 원본/native default로 추정하지 않는다. 서식 없는 원본은 Preserve로
번호만 바꿀 수 있지만 Replace로 새 서식을 만들 수 없다.

서식 이름은 NumberFormat의22종에 정확히 대응한다. DIGIT, CIRCLED_DIGIT, ROMAN_CAPITAL,
ROMAN_SMALL, LATIN_CAPITAL, LATIN_SMALL, CIRCLED_LATIN_CAPITAL, CIRCLED_LATIN_SMALL,
HANGUL_SYLLABLE, CIRCLED_HANGUL_SYLLABLE, HANGUL_JAMO, CIRCLED_HANGUL_JAMO,
HANGUL_PHONETIC, IDEOGRAPH, CIRCLED_IDEOGRAPH, DECAGON_CIRCLE, DECAGON_CIRCLE_HANJA,
SYMBOL, USER_CHAR, SYMBOL2, IMAGE, 2DIGIT 외 값은 거부한다. 이는 저장 속성의 typed 대응과 readback이며
실제 한글의 표시·레이아웃·카운터 의미 자격은 아니다. 0/음수/i32 경계도 저장 값 그대로다.

알려진 다른 control 종류는 UnsupportedKind, 미지 enum 값은 요청 오류다. category·query·replacement·
regex/style_filter/direction/preview_only/locale·output·임의 XML 등 없는 필드를 무시하지 않는다.
요청·종류·서식 값과 한도 검증은 원본 읽기 전에 끝낸다. 기존 문자열/정규식/서식/변환/텍스트 제어
제품 스키마의 지원 종류나 입력 의미를 넓히지 않는다.

## 불변 값과 공유 원본 경로

ValidatedNumberControlValues는 kind·저장 번호·빌린 typed 서식·두 limit set과 한 번 계산한 서식/값
지문을 묶는 입력이다. source/access/execution 권한이 아니며 이후 limits를 넓힐 수 없다. 실제 lower는
해당 모델의 fresh source proof와 원 전체 선택·보호·review·번호 readback을 요구한다. 형식 문자열은
요청 소유 String에서 빌리고 원본은 Borrowed/Owned 이동으로 전달해 clone/reimport를 추가하지 않는다.

stored-number-control-replacement-candidate/v1과 product-number-control-replacement-preparation/v1은
현재 source/권한과 한 compiler를 사용한다. verify/bytes 때 검색·치환·출력 생성은 반복하지 않는다.
변경 anchor는 한 forward iterator의 ordered subset으로 대조하고 번호 노드를 한 순회로 집계한다.
선택 밖 ID 또는 문서/구역 시작값의 변경, 잘못된 역할/속성 변경량을 거부한다. 캐시된 작은 지문은
현재 권한을 대신하지 않으며 canonical payload는 binding check당 한 번 직렬화해 scoped digest에 재사용한다.

## 현재 접근과 닫힌 실행 경계

현재 document.write·project/document/branch/subject/tenant scope·head·ACL·quarantine·AEAD·원본 SHA,
source/index/selector/review/검색/값/출력과 raw/canonical/scoped/key/plan을 결속한다. borrowed/owned/
JSON 후보는 같은 source/compiler 결과를 사용한다. 출력 integrity와 consumer 직전 최종 head를
확인하며 revoke/quarantine/변조/경합 뒤에는 결과를 전달하지 않는다.

idempotency_key와 receipt는 key claim·CAS·실행 권한이 아니다. 실제 ingest/commit·DB revision CAS·
영속 멱등 실행·dispatcher·Native 번호 평가·게시를 열지 않았다. require_current_product_route는
현재 검증 후에도 RouteUnqualified를 반환한다.

## 검증 결과와 다음 작업

components203 신규 제품26pass·727fresh/final727·진단/경고없음·cleanupTrue다. 두 종류/i32 경계·22종
서식·원본 요청 drop·네 selector/구조 제어 사이 block 선택·review 네 정책/제외 후 상한·MEMO/cache·
no-op subset·strict/nested/중복/16KiB/legacy·지문·현재 write/외부5scope·ACL/격리/AEAD·세 단계
최종head 경합·borrowed/owned/JSON 동등성·stale source/head/index·보호/한도/서식 미추정·비노출/
닫힌route·256control·불변 입력의 foreign proof/limits 오용 거부를 확인했다. 추가 review 문단의 상한은
추가 control0개인 입력에서도 기존 strict import는 통과하고 review-bound import는 Limit로 거부함을 확인했다.

원 source compiler/공개 API와 control matcher는 additive 값 wrapper/읽기 전용 getter를 제거하면 전체
역변환된다. 두 product root와 기존 시험 parent도 선언 한 줄씩 제거로 복원된다. 원본67·이전 제품266·
공식249는 반복하지 않았다. 제품 고유292개이지 현재292개 단일 실행이나 공식 수용 증가가 아니다.

203 전체148.453초·명령55.484초/시험15.73초·Job CPU53.156초·private최고1784.36MiB/5.6005%·
시스템CPU최고34.96%·가용RAM최저27.7413%다. 소유 Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. 다른 앱/OS/Defender 변경이나 PC 프리즈 해결·benchmark 주장은 없다. 근거는
implementation/p09/evidence/p09-361-number-control-product-components203.v1.json이다.

다른 제어 종류와 참조/ID 보존·전체 query/replacement/selector/filter/유효 서식·실제 저장/commit/CAS/
영속 멱등 실행/dispatcher/게시·target match_set/semantic_diff/reopen·Native/Gate는 남는다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

## 공통 준비 진입점 연결

위203은 공통 dispatcher 연결 전 이력이다. 현재 StoredProductRequest의 SearchMutation 분기는
이 번호 스키마를 기존15개 치환·변환 스키마와 함께 원 파서/현재 저장 후보로 연결한다. 번호의 서버
ReferenceAuxiliaryLimits도 생략하지 않는다. 공통 후보준비 연결은 고유26개 시험으로 검증했으며
원205 실패·206 실패10개 복구·207 영향 한도1개 보강을 구분한다. 실제 실행/commit/CAS/영속 멱등/
Native/게시 자격은 여전히 없고 RouteUnqualified를 유지한다.
[공통 준비 계약](p09-common-search-mutation-dispatch.md)을 따른다.
