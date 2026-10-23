# 문단 스타일 이름 대체의 서식 필터와 미리보기 제품 요청

`hwpx-agent.product-named-paragraph-style-replacement-request/v2`는 현재 sealed Result의 원본에
선택적 style_filter와 필수 preview_only를 결합한다. 기존 v1은 필터를 계속 거부한다. v2 변경 후보는
공통22번째 family이며 기존21개 순서와 폰트/문단 v1 preview API는 유지한다. 실제 한글 스타일 적용이나
전체 SEARCH-025 제품·실행/저장·Native/Gate 자격은 아니다.

## 입력과 한도

기존 v1의 scope/head/source SHA·project/document/revision/key/plan·네 selector와 이름 축·query/
replacement·regex/case/word·review 정책·변경 문단 상한을 명시한다. 추가된 style_filter는 생략할 수 있다.
명시한 경우 기존 SourceReviewStyleFilter의 비어 있지 않은 declared 참조 또는 축이 명시된 definition이다.
null/배열/빈 조건·미지/중복 필드·enum object·축 없는 정의값·caller XML/graph/승인은 읽기 전에 거부한다.
preview_only는 필수 bool이고 누락/null/문자열을 거부한다. 정확한16KiB와 escape 중복/후행 JSON도 검사한다.

변경 문단 요청1..10000과 검증된 서버 일치 상한의 교집합을 사용한다. 원본/query/regex/writer 한도는
미리보기에서도 유지한다. 전체 outer receipt는 서버 result byte 한도와4MiB의 교집합이며 정확한 한도는
수용하고1byte 부족은 거부한다.384문단의64KiB 초과 응답도 절단하지 않는다. 공통 계획의 별도4096편집·
metadata8MiB·plan16MiB·인자 한도는 [기존 compiler 계약](p09-source-search-operation-compiler-v1.md)을 따른다.

## 원본 필터와 현재 저장 경계

필터 생략은 기존 무필터 source 후보를 재사용한다. 필터를 명시하면
[원본 필터 계약](p09-named-paragraph-style-source-v1.md)의 모든 인덱스 글자/NFC 기여 원본 조건을 따른다.
혼합 run/제어 경계의 일부만 만족해서 문단 전체를 바꾸지 않는다. 빈 문단은 필터 일치가 아니며
무필터 빈 문단 변경은 유지한다. 유효 cascade/숨김이나 누락 참조 기본0을 추정하지 않는다.

현재 document.write·provider scope·head/ACL/quarantine/AEAD와 같은 원본 proof로 준비한다.
source owner를 이동하며 재수입/이름 질의/filter/writer를 반복하지 않는다. retained verify/전달도 같은
원본의 현재 접근·무결성과 consumer 최종 head를 다시 확인한다. 이것은 원자적 CAS가 아니다.

## 변경 계획과 출력 폐기 미리보기

변경 후보는 원 writer 검증을 거친 bytes를 전달한다. 미리보기도 같은 후보 생성/readback 뒤 출력
artifact를 버리고 source와 예측 receipt만 보관한다. 파일 요청은 PreviewOnly이며 consumer를 호출하지 않는다.
raw/canonical/scoped 요청 SHA와 filtered/unfiltered 원본 receipt·preview flag를 함께 결속한다.
key claim·ingest·CAS·게시를 수행하지 않으며 원본 bytes와 head는 그대로다.

`PreparedStoredNamedStyleOptionsMutation`만 compiler view를 갖는다. 별도
`PreparedStoredNamedStyleOptionsPreviewProduct`/`NamedStyleOptionsPreview`에는 bytes/inventory/compile/
실행 manifest API나 역전환이 없다. compiler와 변경 전용 요청은 preview를 원본 읽기 전에 거부한다.
공통 파일 요청은 PreviewOnly, 변경 후보의 preview JSON 요청은 PreviewKind로 거부한다.

실제 문단 anchor마다 가장 가까운 원본 graph 구조 owner를 기존 compiler에 결속한다.12개 잠금 인자를
사용하고 폰트 v1/v2의15개 인자/헤더 자원 경로는 바꾸지 않는다. 전체 filtered/unfiltered output receipt를
mutation SHA에 결속해 같은 출력이어도 필터가 다르면 계획 SHA가 다르다. 모든 route는 여전히 RouteUnqualified다.

## 검증과 실행기 복구

[350 신규28개/영향4개](../../implementation/p09/evidence/p09-361-named-style-options-product350.v1.json)는
32pass·815fresh/final815·진단/경고없음·cleanupTrue다.
[351 첫 import 실패](../../implementation/p09/evidence/p09-361-compiled-named-options-import351.v1.json)는
과거 실행기 연쇄 import의 RecursionError이며 guard/Cargo/시험0이다. 원 driver 역복원 지문도 보존한다.
기존 실행 기반을 먼저 불러오는 진입점을 사용한
[원351](../../implementation/p09/evidence/p09-361-compiled-named-style-options351.v1.json)은 신규18+영향9=
27pass·821fresh/final821·진단/경고없음·cleanupTrue지만 판정 헬퍼 참조 누락의 AttributeError/전체FAILED다.

도구 모듈 import 한 줄만 바로잡은 [352](../../implementation/p09/evidence/p09-361-compiled-named-style-options-reconciled352.v1.json)는
26fresh/final26에서 원27개 결과·원 Job 보호·정리를 대조했다. 원 실패를 PASS로 덮어쓰지 않으며
Cargo/제품 시험 재실행이나 현재 전체 runtime 새 자격이 아니다. 실행 기반/관측 함수 객체는 기존과
동일하고 재귀 한도1000·CPU/RAM 보호는 그대로다. source/index/원 reader와 초기 실패도 보존한다.

문자 스타일 의미·나머지 전체 옵션·실제 적용/실행/저장/게시·신뢰 registry·Native/Gate는 남는다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
