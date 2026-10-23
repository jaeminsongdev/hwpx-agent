# 원본 문단과 문자 스타일 선언의 이름 및 연결 자원 해석

`hwpx-agent.source-named-style-declaration-resolution/v1`은 기존 ImportedDocumentCatalog에서
명시적 PARA/CHAR 종류와 native/English 이름을 해석하는 읽기 전용 기반이다. 본문 사용 위치를 찾거나
HWPX를 변경하지 않는다. 문자 스타일 일괄 대체·실제 한글 적용·현재 접근/실행 권한의 완료가 아니다.

## 공식 근거와 확인하지 않은 의미

한컴의 [고정 commit StyleType 구현](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Head/StyleType.cpp)은
스타일 ID·종류·이름과 charPr/paraPr/nextStyle 참조를 각각 읽고 쓴다. 같은 commit의 t/ctrl 모델은
charStyleIDRef 속성을 저장한다. 이러한 저장 어휘만으로 그 속성의 대상 domain이나 적용 우선순위를
확정하지 않는다. 검증 입력에는 로컬 고정 모델 StyleType.cpp·t.cpp·ctrl.cpp의 SHA를 결속했다.

[한글 2020 글자 스타일 도움말](https://help.hancom.com/hoffice110/ko-KR/Hwp/format/style/style%28font%29.htm)은
부분 글자 스타일 적용/해제와 문단 스타일 적용 시 동작을 구분한다.
[한컴 HWPX 파싱 설명](https://tech.hancom.com/python-hwpx-parsing-2/)은 run.charPrIDRef와 header.charPr의
직접 연결을 설명한다. 이 자료는 UI/저장 어휘의 근거이며 현재 대상에서 캡처한 본문 매핑·재열기 증거가 아니다.
2026-10-21에 원문을 확인했으며 실제 전후 원본 없이 named CHAR ID를 charPr/text-style ID로 치환하지 않는다.

## 질의와 원본 결속

SourceNamedStyleNameQuery는 kind(paragraph/character), name_axis(native_name/english_name),
query/replacement·regex/case_sensitive/whole_word를 명시한다. 이름 검색은 선택한 종류/축의 원본 선언에만
적용하며 대상은 같은 종류/축의 정확한 유일한 기존 선언이어야 한다. 다른 종류·축·부분 이름으로 fallback하지
않고 누락/모호/무일치/무변경/빈 regex 일치를 구분한다. 이름은 기존 typed catalog가 decode한 값을 사용한다.

각 결과는 원본 named style ID/anchor와 정확한 character property·paragraph property·next named style
ID/anchor를 별도 필드로 보관한다. 같은 charPr을 공유하는 스타일도 합치지 않으며 nextStyle을 based-on
상속으로 해석하지 않는다. 한 catalog ID map으로 모든 관계를 확인하고 문단/글자마다 header를 재파싱하지 않는다.
원 catalog/character/paragraph reader·ID admission과 기존 문단 제품/공통 compiler는 그대로다.

## 유한 한도와 결과

기본 최대128개 일치 선언·질의4096bytes·regex compile/DFA 각각1MiB·공개 결과4MiB다.
SourceNamedStyleNameLimits는0이나 고정 ceiling 초과를 거부하며 서버는 한도를 낮출 수 있다.
공개 응답 한도는 전체 receipt/원본 선언/대상 자원에 적용한다. 내부 지문 입력에는 출력하지 않는 원본
catalog metadata와 이름 질의가 들어가므로 별도 고정4MiB 상한을 사용한다. 두 계산은 streaming이며
원본/질의/대상/자원 전체를 결속한다. 정확한 공개 byte 한도와1byte 부족, 긴 유효 질의를 별도로 시험했다.

이름/본문은 receipt/JSON/Debug에 노출하지 않는다. 결과의 body_occurrences_or_target_semantics_qualified와
current_access_execution_or_publication_authority는 false다. 이 타입에는 파일/편집 inventory/compiler/Native
실행이나 현재 서비스 접근 API가 없다. 선언 정보는 현재 권한·임의 본문 ID 매핑·Native 재실행 권한이 아니다.

## 검증과 다음 경계

[354](../../implementation/p09/evidence/p09-361-named-style-declarations354.v1.json)는17pass/1fail·830fresh/final830다.
응답 byte 상한을 지문 입력에도 사용한 Limit 실패는 원본으로 보존했다.
[355](../../implementation/p09/evidence/p09-361-named-style-declarations-recovery355.v1.json)는 실패1+신규 긴 질의1+
영향2=4pass·보존15로 선언 고유19개와 이전에 실행되지 않은 기존 catalog3개를 확인했다.
832fresh/final832·진단/경고없음·cleanupTrue이며 단일19개 실행이나 전체 제품 회귀가 아니다.

다음은 실제 글자 스타일 적용 전후 HWPX와 대상 버전을 확보해 본문 ID domain과 적용 의미를 결속하는 것이다.
고정6종 추가 캡처는 사용자 선택 대기이며 승인과 세션 자격 전에 실행하지 않는다. 기존 승인된 CROSSREF8종과
별도이며 Native011 또는 이전 제품 시험의 재실행 권한도 아니다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
