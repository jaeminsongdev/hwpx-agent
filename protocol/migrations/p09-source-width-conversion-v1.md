# 원본 검색 일치 전각 반각 변환

`hwpx-agent.source-match-width-conversion/v1`은 SEARCH-014의 원본 후보 compiler다.
Fullwidth/Halfwidth와 Unicode17WidthPairsWithKanaPairs 정책, FirstOriginalRunRetainAllRuns를
명시해 원본의 정확한 검색 일치를 변환한다. 현재 저장 서비스·엄격한 제품 JSON은
[별도 제품 프로필](p09-width-product-request-v1.md)로 연결했다. 실제 저장 실행과 한글 자격은 미완료다.

## 폭 대응표와 변환 정책

폭 변환은 일반 NFKC나 글꼴의 실제 표시 폭 판정과 구분한다. Unicode17의
[UAX11](https://www.unicode.org/reports/tr11/tr11-44.html)은 명시적인 fullwidth/halfwidth
문자를 wide/narrow 호환 분해 관계로 설명하며 실제 glyph 폭에는 글꼴·배치가 관여한다.
이 프로필은 [Unicode17 UnicodeData](https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt)의
wide104+narrow122=226개 단일 대응쌍을 전부 사용한다. ASCII만의 부분 표나 East_Asian_Width
분류 전체의 임의 치환으로 대신하지 않는다.

원 UnicodeData는2198209bytes이며 SHA256은
`2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c`다.
tests/support/unicode17_width_pairs.tsv에 대응쌍과 표현 가능한 가타카나 행을 추출했고
runtime table과 독립적인 시험 입력으로 사용한다. 추출 fixture SHA256은
`5c5f8907d369cd1fd2187bd9e3a6fe1f677949fd61bb5196b0e18f98ae5fc239`다.
원본 식별·추출 범위·Unicode License V3를 보존하며 전체 UnicodeData를 runtime에 다시 읽지 않는다.

반각 대상이 존재하는 가타카나28개의 canonical base/탁점·반탁점 쌍도 사용한다.
Fullwidth는 ｶﾞ→ガ처럼 폭 대응이 실제로 바뀌는 쌍만 결합한다. 이미 전각인 カ+결합탁점은
그대로 두며 다른 정규화나 대소문자 변환을 하지 않는다. Halfwidth는 ガ→ｶﾞ로 확장한다.
반각 기본자가 없는 ヸ/ヹ/ヾ는 근사 치환하지 않고 그대로 둔다. 결합하지 못한 반각 탁점은
대응하는 결합탁점으로 바꾸며 삭제하지 않는다.

한글은 명시적 폭 대응쌍을 따라 ﾡ↔ㄱ처럼 호환 자모로 변환한다. 가 같은 음절을 분해하거나
위치 자모로 자동 정규화하지 않는다. 전각 macron은 반각 macron으로 대응하며 NFKC의 별도
분해를 적용하지 않는다. 원문자·합자·다른 canonical 텍스트는 폭 대응 대상이 아니면 유지한다.
한글 앱·ICU 변환 전체·일반 정규화와 동등하다는 권위는 부여하지 않는다.

## 원본 범위와 보존

한 원본 Form proof에서 field/review/index를 만들고 기존 literal/regex 또는 선언/typed 정의
서식 matcher 중 한 branch를 사용한다. 네 selector와 review 정책을 먼저 적용하고 모든 NFC
기여자의 정확한 원본 역상을 확인한다. 검색 NFC를 원문으로 쓰지 않으며 빈 일치·불완전·불연속
역상·겹친 원본을 거부한다. 별도 일치나 선택 밖 글자와 결합하지 않는다.

같은 일치의 TEXT 그룹 안에서는 run/text 경계를 넘어 가타카나를 결합할 수 있다.
탭·줄바꿈·기존 block은 경계다. 결합 결과는 첫 원본 기여자에 두고 다른 run shell과 선언 서식은
유지한다. 확장은 원 text atom에 남는다. 같은 원 atom의 연속 변경만 합치고 변하지 않은
글자·entity가 사이에 있으면 분리하며 제어·참조 shell·선택 밖 바이트를 보존한다.
원본 index·검색/selector/filter·mode/policy/run 정책·Unicode version·대응표 원본 SHA와
출력 지문을 receipt에 결속한다. receipt는 현재 접근이나 저장 실행 권한이 아니다.

## 비용과 보호

방향별 표와 가타카나 역방향 index는 정렬된 이진 탐색을 사용한다. 글자마다226개를 훑거나
XML을 재수입하지 않는다. 변환 scalar·UTF8 byte 상한을 먼저 확인하고 pending unit 한 개로
탁점 결합을 처리한다. 연속2만 글자와4096 가타카나 쌍은 각각 한 component·한 patch다.

기존 공통 plan/보호/field cache/patch/readback 본문은 변경하지 않았다. 한 원본 proof·
field/review/index·matcher·writer·출력 import와 part별 보호/segment별 TextSpan map을 공유한다.
no-op 제거 전에 보호·field cache를 검사하며 잘라낸 부분 성공 결과는 만들지 않는다.

## 검증 결과

components175 신규원본24pass·683fresh/final683·진단/경고없음·cleanupTrue다.
폭226쌍과 가타카나28개의 양방향 전수 시험, source fixture와 runtime table/이진 탐색 index
전체 대조, 네 범위·clipped regex·선언/정의·casefold 검색/whole-word·review4정책·보호/no-op/
cache·entity/참조/제어/서식·문맥 경계·역상·proof/source·한도·idempotent 후보·비노출·
2만 글자와 긴 가타카나 연속 변환을 확인했다. 이는 전체 target 계약이나 실제 멱등 실행의 증명이 아니다.

원 atoms root는 module 선언 한 줄 제거로 전체 역변환되며 기존 compiler/보호/writer/제품/
시험/fixture는 그대로다. 기존제품194·원본64·공식249는 반복하지 않았다.
전체120.656초·명령33.172초/시험7.69초·Job CPU31.547초·private최고1710.41MiB/5.3684%·
시스템CPU최고54.09%·가용RAM최저26.5859%다. 한 코어 affinity4·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초와 Job active0/empty/handle closed 및
전후 입력 확인을 유지했다. OS·Defender·다른 앱 변경이나 프리즈 해결·benchmark 주장은 없다.
근거는 implementation/p09/evidence/p09-361-width-components175.v1.json이다.

## 다음 제품 연결과 Gate

이 변환의 현재 저장 서비스·엄격한 제품 JSON은 별도 제품 프로필에서 신규24개를 검증했다.
다음 접근허용 불필요 작업은 SEARCH-023 공백·탭·줄바꿈 정규화 정책과 원본 compiler다.
전체 유효 서식·selector/filter/방향·보호·target match_set/semantic_diff/reopen·dispatcher/DB/
commit/CAS/멱등 실행/게시·Native는 미완료다. source API v12 incomplete/미해결4/report없음/
exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행과 기존 Native 재실행 금지도 유지한다.
