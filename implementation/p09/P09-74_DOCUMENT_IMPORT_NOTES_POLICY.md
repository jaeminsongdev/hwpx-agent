# P09-74 원본 각주·미주 본문 가져오기 정책

## 제품 API의 본문 비노출 주석 선택

`reference-source-assessment/v11`의 `note_selections`는 실제 source note ID, marker subtree SHA256, 관찰된 NoteKind만 제공한다. forms.notes에서 가져온 원래 관측을 사용하고 별도 입력 import를 하지 않는다. 본문·원시 속성·marker 문자·native instId를 노출하지 않는다. 순서는 XML source 순서이며 Native 번호/전체 문서 흐름과 다르다. 항목 수와 최종 응답 bytes 한도를 그대로 적용하고 note 부재는 빈 배열로 보존한다. source ID는 원본 package·part·문서에 결속되며 전역 native identity나 승인 정보가 아니다.

실제 CLI v11 응답과 제품 JSON→저장 후보→출력 API를 검증했다. 별도 caller Form/Note import가 없어도 요청을 구성하지만 stale/foreign ID·지문·권한 변경은 원래 서비스/컴파일러 검사가 거부한다. source API5+영향46, 저장 연결/영향 lane2가 통과했으며 in-memory service 시험을 실제 DB/issuer/Native/정식 실행·게시 성공으로 확대하지 않는다. status incomplete·미해결4·report null·종료3과 현재 product route 거부를 유지한다.

## 저장 서비스 변환 후보의 접근 검사

`prepare_note_kind_candidate`는 기존 fresh source 접근과 전체 Form reconstruction proof를 재사용한다. caller graph·권한 있는 XML·새 artifact ID나 approval bit를 받지 않는다. 원본 package digest·요청 digest/count·출력 receipt를 결속하고 준비 종료에 head를 재확인한다. 후보의 verify/바이트 노출은 원본 scope/head/ACL/quarantine/AEAD와 전체 원본을 매번 다시 확인하며, writer callback 안의 최종 head 검사 뒤에만 소비자를 호출한다. 현재 read는 atomic lock/CAS가 아니고 정식 실행 경로는 항상 거부한다. ingest·commit·게시를 수행하지 않는다.

새8개 시험은 새 생성3종과 과거9개, 요청 형식의 기존 digest 일치와 각 필드 결속, ACL 회수·재부여, quarantine·AEAD 변조, scope5 대체, 최종 callback 직전 head 변경, 선택/보호/한도를 확인했다. 생산 코드와 in-memory service·scanner/key fixtures의 검증이며 actual DB/issuer/Native/번호 재계산·완전한 보호·P09 Gate를 증명하지 않는다. 014의433개 입력을 전후 확인했고 다른249개 시험은 실행하지 않았다. 당시 공용 fixture의 lane 미사용 경고는016에서 generated/saved/reopened 각3개를 확인하도록 시험을 보강해 해소했다. 014 원 기록은 변경하지 않았다.

## 원본 종류 변환 후보와 ID 충돌 거부

`structure::note_conversion`은 source note ID·원본 subtree 지문·typed NoteKind를 받는다. 새 closed patch intent는 원 envelope 검사 후 실제 시작·끝 태그 이름만 변환하며 caller XML/name이나 새 instId/번호/기본값을 받지 않는다. source 전체 fresh 검증 또는 원 Form reconstruction proof를 거친 뒤 batch 한 번으로 patch/writer/출력 구조 import를 수행한다. 모든 note의 원 part/element 위치·종류·관찰 속성·instId와 변경 section의 편집 밖 바이트 및 다른 part 지문을 확인한다. 보호 속성은 변경 part마다 한 번 계산한다. 후보는 메모리에만 있으며 저장 서비스 실행·게시 권위와 완전한 보호·번호 재계산·Native 의미는 미검증이다.

과거 혼합 fixture 생성기가 두 본문에 문단 ID 101/102를 반복한 것이 충돌 원인이다. 저장·재열기 파일의 같은 값은 주석별 ID 독립 범위의 근거가 아니다. 새 allocator는 원본 전체의 관찰 nonzero ID 뒤에 새 ID를 할당하고, 삽입 plan/lower는 source·payload 내부 중복과 서로의 충돌을 거부한다. v1~v8 IdIndex와 원본 ID/zero sentinel/저수준 ID 부재 의미를 보존한다.

기능 시험의 과거 개별7pass와 별도 원본9종 시험의6변환/3중복거부, 관련 삽입·생성기14pass 및 추가 경계5pass를 구분한다. 처음의 원본9개 전체 양성 기대는 잘못돼 source-archive에 보존했다. 수정 시험은 혼합3개의 독립 원본 ID 검증 실패와 변환 출력 거부를 반드시 요구하며 이3개가 변환됐다고 주장하지 않는다. 새 생성3종은 기존 ID 검사·종류 변환·독립 보존 검사를 통과했지만 Native 미실행이다. 변환 후보의 저장 서비스 접근 검사는 위 절에 연결했으며 정식 실행/게시·완전한 보호 및 실제 target 검증은 OPEN이다. 003/004 실패와 P26 Native non-green은 그대로다.

## 대상과 권위

실제 HWPX section의 `hp:ctrl → hp:footNote|hp:endNote → hp:subList`를 원래 source-backed body mapper로 읽는다. caller가 만든 Note/graph/anchor/native ID를 주입하는 경로를 만들지 않는다. 문서 데이터의 source-local logical ID는 실제 source anchor에서 계산하며, `instId`는 관찰된 양의 정수일 뿐 native 전역·지속 identity나 번호 의미의 증거가 아니다.

원래 opaque wrapper node/common/properties/resources와 paragraph의 ControlRef는 보존하고 `source_note_id` 연결만 추가한다. 실제 Note table에 원본 subList의 paragraph/run/text/table/opaque flow를 보존한다. source/body/wrapper/paragraph anchors는 실제 source에서 resolve해야 한다. section에서 발견한 모든 HP note marker와 typed 관찰 집합이 일치하지 않으면 전체 import를 거부한다. 알 수 없는 구조 속의 note를 생략한 성공으로 처리하지 않는다.

## 입력과 문자 관찰

instId/flag/number와 userChar/prefixChar/suffixChar는 실제 존재하는 속성만 보존한다. 없는 flags/번호/기본값을 생성하지 않는다. instId=0, 범위를 넘은 번호, 잘못된 wrapper/namespace/parent/child, nested note, 빈 body, source/graph/budget 불일치는 거부한다. 기존 source/parser/domain 한도를 유지한다.

생성 파일의 단일 BMP 문자와 실제 저장 파일의 bounded decimal WCHAR 토큰은 raw 속성으로 관찰한다. decimal은 최대5자리/u16이며 zero sentinel 또는 XML-valid BMP scalar만 허용한다. surrogate/out-of-range/control/multi-character 값은 거부한다. 숫자를 렌더링 문자로 바꾸거나 모호성을 선택하지 않는다. **원본 note projection과 plain-text 문자 의미는 그대로다. 새 삽입 plan/lower에는 위의 문단 ID 충돌 거부 조건을 추가했다.**

## 필드·서비스 연결

기존 forms/fields/meaning overlay를 원본 Note body에도 순회한다. 필드 원본 범위와 parameters 및 미지원 의미는 유지한다. canonical Reference 순서와 source 관찰 순서는 다를 수 있으므로 실제 reference ID로 의미를 연결한다. 위치 zip으로 URI·수식 의미를 잘못 배정하지 않는다.

stored actual importer는 원래 sealed Result의 head/node/tenant/read scope/ACL/scanner/quarantine/AEAD/digest 검사와 fresh source read를 그대로 사용한다. 이미 읽은 모델의 tenant/subject/project/branch/document scope를 다른 provider로 바꿔치기하면 cached verify와 fresh bound derivation을 모두 거부한다. 별도 권한 있는 provider의 독립 읽기는 이 기존 모델의 재사용과 다른 계약이다. document/source lineage 전체 권위는 별도 OPEN이다. READ audit 외 ingest/commit/CAS/seal/publication을 수행하지 않는다. 두 head reads는 atomic lock/CAS/idempotency가 아니다.

## 완료하지 않은 범위

`note_import_profile` 또는 `note_import_scope` 중 하나만 있어도 full product context를 거부한다. 다른 partial marker를 제거해도 새 관찰을 실행 가능한 full document로 승격할 수 없다.

P24 생성 및 P26 저장·재열기 패키지는 원본 digest/size로 읽고 역사적 P26 `failed_semantic_non_green`/0green을 보존한다. source import 성공은 실제 한글 번호 재계산·body/style binding·렌더링·direct differential의 성공이 아니다. 이번 stored service metadata/revision/blob/scanner/keys/sealed baseline은 in-memory fixtures이며 새 PG/issuer/native/product acceptance가 아니다.

다른13 field kinds/reference/comment/catalog/security 의미, 평가·승인·정식 input lineage/issuer/ExecutionManifest/publication/IR lifecycle/concurrency/crash/recovery와 whole original qualification/current admission/P62 cause/native Gate는 별도 OPEN이다. Goal ACTIVE/P09 Gate OPEN/no P10를 유지한다. 접근허용 금지 동안 Hangul/COM/UI/native dispatcher를 실행하지 않는다.
