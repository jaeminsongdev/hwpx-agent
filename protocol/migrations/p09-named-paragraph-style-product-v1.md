# 문단 스타일 이름 대체의 제품 요청과 공통 계획

`hwpx-agent.product-named-paragraph-style-replacement-request/v1`은 현재 sealed Result의 원본에
이름 질의를 적용해 PARA styleIDRef만 바꾸는 별도 후보 준비 요청이다. 문단 직접 속성·CHAR 스타일·
폰트 요청을 확장하지 않는다. capability는 `search.replace_styles`이며 실제 한글 스타일 적용 동등성이나
전체 SEARCH-025 완료를 뜻하지 않는다.

## 엄격한 입력과 서버 한도

project/document/base revision/head generation/source SHA·key/plan·selector와 operation을 명시한다.
operation은 `replace_named_paragraph_styles`이고 query/replacement·regex/case_sensitive/whole_word·
name_axis(native_name 또는 english_name)·max_changed_paragraphs·review_policy·preview_only가 필수다.
review 정책의 hidden/MEMO 두 bool도 명시한다. 실제 이름/문단 선택은 [원본 계약](p09-named-paragraph-style-source-v1.md)을 따른다.

전체 JSON16KiB·유일한 object 키·string enum·정확한 schema와 네 selector 형태를 검증한다. unknown/
escaped duplicate/trailing JSON·caller IR/승인/원본 XML·미지원 style_filter를 원본 읽기 전에 거부한다.
변경 문단 요청은1..10000이며 서버의 검증된 일치 상한과 교집합이다. source/query/regex/writer 한도도 유지한다.
응답 전체 receipt는 서버 result byte 한도와4MiB 교집합이며, 한도 초과를 절단한 성공으로 반환하지 않는다.
공통 계획에는 별도로4096 편집/operation·metadata8MiB·plan16MiB와 기존 인자 한도가 적용된다.

## 현재 원본과 두 결과 모드

현재 document.write·provider scope·head/ACL/quarantine/AEAD와 같은 source proof로 한 번 준비한다.
원본 owner는 후보로 이동하며 원본 clone·이름 matcher·writer를 반복하지 않는다. retained verify/전달도
같은 원본의 현재 접근/무결성과 consumer 직전 head를 확인한다. 이 경계는 원자적 CAS가 아니다.

preview_only=false는 writer 검증된 후보 bytes를 전달한다. preview_only=true도 같은 writer/readback을
거친 뒤 output artifact를 버린다. 저장 preview는 source와 예측 receipt만 소유한다. output SHA·변경 수는
예측값이며 실제 저장/실행 증거가 아니다. 제품 metadata 재전달은 원본/권한과 최종 head를 다시 확인한다.
idempotency key claim·ingest·CAS·게시를 수행하지 않으며 원본 bytes/head는 그대로다.

## 공통 변경 계획과 분리된 미리보기

`StoredNamedStyleMutationRequest`는 preview_only=false만 수용한다. 결과인
`PreparedStoredNamedStyleMutation`만 compiler view를 가지며 기존20개 순서를 유지한21번째 family다.
전체 output receipt의 이름 질의/축·원본 catalog/index·selector·review 정책·실제 변화/출력을 계획에 결속한다.
같은 출력이어도 질의가 다르면 mutation receipt와 compiled plan SHA가 다르다.

실제 원본 문단 anchor마다 가장 가까운 graph 구조 owner를 원 SelectorSnapshot/OperationPlanCompiler로
해석한다. 임의 첫 node·문자 offset을 owner로 사용하거나 owner 전체를 변경 범위로 확대하지 않는다.
기존12개 잠금 인자를 공유하며 폰트 v1/v2의15개 인자/헤더 자원 경로는 그대로다.

preview_only=true는 별도 `PreparedStoredNamedStylePreviewProduct`/`NamedStylePreview`다. 이 타입에는
bytes/inventory/compiler/실행 manifest API나 역전환이 없다. 기존 폰트 SearchPreview API는 바꾸지 않는다.
공통 bytes는 PreviewOnly, 변경 후보에 대한 preview JSON은 PreviewKind로 거부한다. compiler와 변경 전용
요청은 preview를 원본 읽기 전에 거부한다. 두 모드 모두 현재 검증 후에도 RouteUnqualified다.

## 검증과 남은 경계

선택적 원본 style_filter는 [별도 v2 계약](p09-named-paragraph-style-product-v2.md)에서 처리한다.
v1은 계속 거부하며 v1의21번째 위치와 preview API는 그대로다. 아래는 v1 검증 이력이다.

[343 제품29개](../../implementation/p09/evidence/p09-361-named-style-product343.v1.json)와
[344 신규2개/영향3개](../../implementation/p09/evidence/p09-361-named-style-product-metadata344.v1.json)의
보존26개로 제품 고유31개다.384문단·64KiB 초과 metadata와 정확한 서버 한도/1byte 부족을 구분했다.
[345 시험 모듈 순서 컴파일 실패](../../implementation/p09/evidence/p09-361-compiled-named-styles345.v1.json)는
시험0인 원본으로 보존했다. production은 그대로, 선언 위치만 옮긴
[346 공통 신규19개/영향12개](../../implementation/p09/evidence/p09-361-compiled-named-styles-recovery346.v1.json)는
31pass·806fresh/final806·진단/경고없음·cleanupTrue다. 모든 기존 시험이나 공식249를 재실행한 결과는 아니다.

실제 한글 스타일 적용/시각 결과·문자 스타일·서식 필터/전체 옵션·신뢰된 registry·실행/저장/게시·Native/Gate는
미완료다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
