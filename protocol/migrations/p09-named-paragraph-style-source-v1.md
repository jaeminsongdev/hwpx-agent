# 문단 스타일 이름 대체의 원본 계약

`hwpx-agent.source-named-paragraph-style-replacement/v1`은 원본 PARA 스타일 이름을 찾아 문단의
styleIDRef만 교체하는 pure 후보다. 새 제품 JSON/공통 실행 schema를 추가하지 않으며 기존
문단 속성/폰트 제품 요청을 확장하지 않는다. 실제 한글 스타일 적용 동등성은 미검증이다.

## 질의와 대상

`SourceNamedParagraphStyleQuery`는 query/replacement·regex/case_sensitive/whole_word와
name_axis의 native_name 또는 english_name을 모두 명시한다. literal은 escaped substring,
regex는 원본 이름에 대한 bounded Rust Unicode regex다. 대체 대상은 선택한 이름 축의 정확한
전체 문자열로만 찾으며 regex 치환 template이나 새 정의를 만들지 않는다. 다른 이름 축/CHAR
스타일/기본0/nextStyle 상속으로 fallback하지 않는다. 미지/없는/모호한 대상을 임의로 추정하지 않는다.

이름/pattern은1..4096 bytes, control 문자는 거부한다. regex compile/DFA는 서버 상한과1MiB의
교집합이며 일치된 원본 선언은128개까지다. no-match/no-change와 빈 regex 일치를 구분한다.
source/search/selector/변경 문단 수/편집 수/출력/writer의 기존 상한을 유지하며 부분 성공을 반환하지 않는다.

## 범위와 보존

전체 원본 proof와 typed catalog/review scope를 구성한 뒤 실제 문단 참조를 선택한다. source의
명시적 styleIDRef가 이름 일치 집합에 있을 때만 바꾸며 누락된 참조를 삽입하지 않는다. 네 selector
범위와 hidden/MEMO 정책을 적용하고 문단의 모든 블록이 범위 안에 있어야 한다. 빈 selection은
빈 문단 전체 변경 권한이 아니다. 탭/줄바꿈은 원래 index atom 의미를 따르고 bookmark처럼 실제
제어가 만드는 블록 경계를 임의의 글자 위치로 치환하지 않는다.

빈 run·명시적 빈 text·self-closing text는 원래 reader가 수용하는 형태에서 처리한다. run 없는
문단은 기존 Body admission 거부를 유지한다. reader를 완화하거나 가짜 텍스트 일치를 만들지 않는다.

기존 문단 compiler의 필드 캐시·상위/하위 추적 표시·관측 보호와 part별 선형 보호 맵을 공유한다.
header 스타일/폰트 정의·직접 paraPr/run/text 참조·텍스트/제어와 비선택 bytes는 보존한다.
출력은 같은 writer와 전체 문단 참조/원 scalar·두 글자 축·외부 bytes readback을 거친다.
실제 NamedStyle 적용이 직접 속성을 어떻게 바꾸는지나 렌더링 동등성을 추정하지 않는다.

## 원본 서식 필터를 사용하는 별도 후보

`hwpx-agent.source-filtered-named-paragraph-style-replacement/v1`과
`lower_filtered_named_paragraph_style_candidate`는 기존 core와 별개인 필터 receipt를 추가한다.
기존 v1 질의/출력/receipt와 제품 schema를 확장하지 않으며 v1은 필터 없는 동일 동작을 유지한다.

필터는 기존 `SourceReviewStyleFilter`의 비어 있지 않은 declared 참조 또는 축이 명시된 definition
조건이다. 선택된 전체 문단의 모든 인덱스 원본 글자/NFC 기여 원본이 만족해야 하며 필터 extent는
`all_indexed_source_units_of_whole_paragraph`다. 조건들은 AND이고 run/text/문단 축을 혼용하거나
누락 참조를0·named style로 대체하지 않는다. 빈 run/빈 text/self-closing text만 있는 문단은 원본
수입 자체는 가능하지만 필터 일치가 아니다. 필터 없는 원본 v1의 빈 문단 변경은 그대로다.

동일 원본 proof/review index를 사용하며 inspection과 필요한 정의를1회 구성하고 segment별로
판정을 캐시한다. 원본을 문단/글자마다 다시 수입하거나 이름 질의를 반복하지 않는다. 하나의 NFC
단위에 여러 run이 기여하면 모두 판정하고 다른 블록의 불일치도 문단 전체에서 고려한다. 부분 선택은
필터로 확대하지 않으며 기존 전체 문단 범위·필드/추적/관측 보호·writer/readback을 유지한다.

private 후보는 기존 artifact를 소유하며 별도 receipt에 filter/inspection/정의·extent·원본 판정 수와
기존 후보 receipt를 결속한다. 같은 출력이어도 다른 필터의 요청 SHA는 다르며 전체 metadata 한도는
streaming hash와 count writer로 적용한다. 유효 cascade/숨김/현재 서비스/실행 권위는 false다.
[필터 신규18개와 영향9개](../../implementation/p09/evidence/p09-361-filtered-named-styles348.v1.json)는
27pass·810fresh/final810·진단/경고없음·cleanupTrue이며 필터 저장/제품/preview/공통 연결 자격은 아니다.

필터의 현재 저장·엄격한 v2/preview·공통22번째 변경 계획은 [별도 v2 계약](p09-named-paragraph-style-product-v2.md)을
따른다.350 제품32pass와 원351 공통27pass의 후처리 실패/352 대조는 core348의 증거와 구분한다.
원본 filtered 후보 자체는 현재 접근·실제 실행/저장/게시·Native/Gate 자격을 부여하지 않는다.

## 후보와 검증

`SourceNamedParagraphStyleCandidate`는 artifact를 private하게 소유하고 writer integrity 검사를
거쳐서만 bytes를 전달한다. receipt는 원본/catalog/index/selector·body 정책·name 축·query 지문·
원본/대상 스타일 ID·실제 변화·출력을 결속한다. 이름과 원 본문은 receipt/Debug에 노출하지 않는다.
full_style_filter_character_style_native_or_execution_qualified는 false다. 현재 ACL/head/AEAD·저장/제품/preview와
공통 계획 연결은 [별도 제품 계약](p09-named-paragraph-style-product-v1.md)을 따른다. 문자 스타일·
서식 필터/전체 옵션과 실제 실행/저장/게시·Native/Gate는 미완료다. pure core 자체는 현재 실행 권한이 아니다.

[실패와 복구 현황](../../implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md)의
23개 보존+2개 복구+마지막1개로 신규19+영향7의 고유26개를 확인했다. 단일26개 실행은 아니며
마지막793fresh/final793·진단/경고없음·cleanupTrue다. 초기 실패 기록과 원 reader/guard는 보존했다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
