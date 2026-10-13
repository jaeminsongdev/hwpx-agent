# P09-74 원본 각주·미주 본문 가져오기 정책

## 대상과 권위

실제 HWPX section의 `hp:ctrl → hp:footNote|hp:endNote → hp:subList`를 원래 source-backed body mapper로 읽는다. caller가 만든 Note/graph/anchor/native ID를 주입하는 경로를 만들지 않는다. 문서 데이터의 source-local logical ID는 실제 source anchor에서 계산하며, `instId`는 관찰된 양의 정수일 뿐 native 전역·지속 identity나 번호 의미의 증거가 아니다.

원래 opaque wrapper node/common/properties/resources와 paragraph의 ControlRef는 보존하고 `source_note_id` 연결만 추가한다. 실제 Note table에 원본 subList의 paragraph/run/text/table/opaque flow를 보존한다. source/body/wrapper/paragraph anchors는 실제 source에서 resolve해야 한다. section에서 발견한 모든 HP note marker와 typed 관찰 집합이 일치하지 않으면 전체 import를 거부한다. 알 수 없는 구조 속의 note를 생략한 성공으로 처리하지 않는다.

## 입력과 문자 관찰

instId/flag/number와 userChar/prefixChar/suffixChar는 실제 존재하는 속성만 보존한다. 없는 flags/번호/기본값을 생성하지 않는다. instId=0, 범위를 넘은 번호, 잘못된 wrapper/namespace/parent/child, nested note, 빈 body, source/graph/budget 불일치는 거부한다. 기존 source/parser/domain 한도를 유지한다.

생성 파일의 단일 BMP 문자와 실제 저장 파일의 bounded decimal WCHAR 토큰은 raw 속성으로 관찰한다. decimal은 최대5자리/u16이며 zero sentinel 또는 XML-valid BMP scalar만 허용한다. surrogate/out-of-range/control/multi-character 값은 거부한다. 숫자를 렌더링 문자로 바꾸거나 모호성을 선택하지 않는다. **기존 note projection/plain-text parser와 typed lowering profile은 변경하지 않는다.**

## 필드·서비스 연결

기존 forms/fields/meaning overlay를 원본 Note body에도 순회한다. 필드 원본 범위와 parameters 및 미지원 의미는 유지한다. canonical Reference 순서와 source 관찰 순서는 다를 수 있으므로 실제 reference ID로 의미를 연결한다. 위치 zip으로 URI·수식 의미를 잘못 배정하지 않는다.

stored actual importer는 원래 sealed Result의 head/node/tenant/read scope/ACL/scanner/quarantine/AEAD/digest 검사와 fresh source read를 그대로 사용한다. 이미 읽은 모델의 tenant/subject/project/branch/document scope를 다른 provider로 바꿔치기하면 cached verify와 fresh bound derivation을 모두 거부한다. 별도 권한 있는 provider의 독립 읽기는 이 기존 모델의 재사용과 다른 계약이다. document/source lineage 전체 권위는 별도 OPEN이다. READ audit 외 ingest/commit/CAS/seal/publication을 수행하지 않는다. 두 head reads는 atomic lock/CAS/idempotency가 아니다.

## 완료하지 않은 범위

`note_import_profile` 또는 `note_import_scope` 중 하나만 있어도 full product context를 거부한다. 다른 partial marker를 제거해도 새 관찰을 실행 가능한 full document로 승격할 수 없다.

P24 생성 및 P26 저장·재열기 패키지는 원본 digest/size로 읽고 역사적 P26 `failed_semantic_non_green`/0green을 보존한다. source import 성공은 실제 한글 번호 재계산·body/style binding·렌더링·direct differential의 성공이 아니다. 이번 stored service metadata/revision/blob/scanner/keys/sealed baseline은 in-memory fixtures이며 새 PG/issuer/native/product acceptance가 아니다.

다른13 field kinds/reference/comment/catalog/security 의미, 평가·승인·정식 input lineage/issuer/ExecutionManifest/publication/IR lifecycle/concurrency/crash/recovery와 whole original qualification/current admission/P62 cause/native Gate는 별도 OPEN이다. Goal ACTIVE/P09 Gate OPEN/no P10를 유지한다. 접근허용 금지 동안 Hangul/COM/UI/native dispatcher를 실행하지 않는다.
