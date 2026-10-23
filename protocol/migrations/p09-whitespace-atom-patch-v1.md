# 공백과 구조적 탭 줄바꿈의 타입 지정 편집 기반

`ReplaceWhitespaceAtomRanges`는 SEARCH-023 원본 정규화를 위한 저수준 preserving patch 기반이다.
기존 텍스트 편집의 제어 변경 금지를 유지하면서, 공백 문자와 qualified tab/lineBreak만 바꾸는
별도 typed 경로를 추가한다. 검색/selector·정규화 정책·문서 보호는 별도
[원본 정규화 compiler](p09-source-whitespace-normalization-v1.md)에 연결했다. 현재 저장·제품 준비 요청은
별도 [제품 프로필](p09-whitespace-product-request-v1.md)에 연결했다. 순수 patch 결과를 문서 접근·
잠금 처리나 제품 실행 자격으로 올리지 않는다.

## 입력과 출력

WhitespaceAtomRangeReplacement의 text는 원본 Text atom/scalar 범위만 받으며 실제 선택된
글자가 모두 허용 공백인지 적용 시 확인한다. 일반 글자를 삭제하거나 공백으로 덮어쓰면 거부한다.
실제 Text 경계의 공백 삽입은 허용하지만 가상의 Text atom은 만들지 않는다. control은
원본 atom 번호와 기대하는 Tab/LineBreak 종류를 모두 확인한다. empty는 별도 명시적 요청이며
실제로 비어 있는 t만 허용한다. 중복·역순·겹침·모호한 삽입·다른 종류/없는 원본은 거부한다.

출력은 WhitespaceText·unsigned 속성의 Tab·LineBreak enum의 유한 벡터이며 빈 벡터는 삭제다.
임의 XML이나 일반 글자는 받지 않는다. [Unicode17 PropList](https://www.unicode.org/Public/17.0.0/ucd/PropList.txt)의
White_Space25개와 기존 Text reader의 제어 문자 거부 조건을 교차해19개 공백 문자만
WhitespaceText로 받는다. 원래의 raw TAB/LF/CR/VT/FF/NEL 입력 거부를 바꾸지 않았다.
TAB/LF는 별도의 구조적 출력으로 다루며 NBSP 등의 의미를 자동으로 바꾸는 정규화 정책은 아니다.

## 원본과 namespace 보존

기존 qualified TextSpan reader와 scalar boundary scanner로 원본 좌표를 확인한다.
숫자 entity·비BMP 문자는 원본 scalar 경계로 처리하고 선택 밖 바이트와 다른 ZIP entry는 보존한다.
탭·줄바꿈의 paired tag 내부 공백은 해당 control 전체를 명시적으로 교체할 때만 바뀐다.
미지/외부 control·주석·잘못된 속성·손상된 shape를 조용히 건너뛰지 않는다.

출력 control의 prefix는 원본 t의 QName에서 구한다. hp를 가정하거나 caller QName/XML을 받지
않으며 별칭과 default namespace를 유지한다. 빈 self-closing t는 기존 태그·속성·공백을 유지하고
마지막 닫힘만 확장한다. paired empty t의 경우 내용 위치에만 삽입한다.

## 비용과 혼합 한도

범위는 적용 전에 원본 atom/좌표 순서로 대조한다. requested scalar edges를 모아 기존 scanner를
공유하고 Text atom별 단일 char cursor로 선택 글자를 검사하므로 범위마다 처음부터 훑지 않는다.
2000개의 비BMP/entity 혼합 범위를 한 원본 atom에서 처리하는 시험을 포함한다.

새 작업과 기존 TextAtom/LeafScalar 범위 작업을 섞어도 범위 개수와 escaped 출력 byte 상한을
공동 적용한다. 새 output atom 개수에도 별도 같은 개수 상한을 적용한다. 출력의 namespace prefix·
control markup·빈 shell 확장까지 실제 byte 예산에 포함하고 value/fragment 상한을 확인한다.
서로 다른 편집 계열이 같은 target을 공유하면 바이트가 겹치지 않아도 거부한다.
실패 시 partial patch를 게시하지 않는다.

별도 [텍스트 제어 치환](p09-text-control-atom-patch-v1.md)과 섞는 경우 네 계열의 내부 범위·typed
출력 atom 개수·escaped 실제 출력 byte 예산을 공동 적용한다. whitespace의 공백 전용 입력/출력
검사와 기존 renderer 본문은 바꾸지 않고 읽기 전용 output 개수 getter만 추가했다.

원 patch 엔진의 ID profile·원래 dispatch/validation 본문은 변경하지 않았다. 새 enum/dispatch/
별도 preflight와 export를 제거하면 원 파일 전체로 역변환되며, old atom 모듈은 값 조회 getter
추가만 있다. 새 intent가 없는 경우 새 preflight는 즉시 반환한다. 기존 텍스트 경로는 여전히
control 문자열/atom 변경을 거부한다.

## 검증 결과

components180은 XmlByteSpan과 일반 Range 타입 변환 누락 E0308로 컴파일 실패/시험0이다.
한 타입 변환만 수정한 components181은 신규24+영향 atom10/leaf9=43pass·692fresh/final692다.
원 실패180을 보존했다. 이후 제품을 유지하고 새 시험 두 개의 경계를 강화했다.
상위 intent3개가 허용돼도 내부 range4개는 cap3에서 거부하고 cap4에서는 통과하며,
byte-disjoint 삽입이라도 다른 계열과 같은 target을 공유하면 거부하는 것을 확인한다.

strengthening182는 수정2pass·693fresh/final693·진단/경고없음·cleanupTrue다. 원본이 같은41개를
보존해 고유43개이며 현재43개 단일 실행으로 합치지 않는다. 변경 없는41개·기존제품218·공식249는
반복하지 않았다. 일반 공백·제어 교체/삭제·빈 요소·namespace·entity/비BMP·범위/종류/원본 검증·
표현 가능한19문자·잘못된 source/value·혼합 건수/byte·출력 atom/value/fragment/shell 상한·
비노출·결정적 출력과 기존 제어 거부를 확인했다. 실제 멱등 실행이나 전체 정규화 기능의 증명은 아니다.

181 전체117.937초·명령29.453초/시험3.77초·Job CPU27.781초·private최고1713.75MiB/5.3788%·
시스템CPU최고43.18%·가용RAM최저25.7669%다. 182 전체92.063초·명령3.188초/시험0.14초·
Job CPU2.141초·private최고575.36MiB/1.8059%·시스템CPU최고37.70%·가용RAM최저28.9681%다.
두 Job active0/empty/handle closed와 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/
stop7%·RAM/commit95%·명령300초·guard600초 및 입력 전후 확인을 유지했다. OS·다른 앱 변경이나
프리즈 해결·benchmark 주장은 없다. 근거는 implementation/p09/evidence의
p09-361-whitespace-patch-components180.v1.json, p09-361-whitespace-patch-components181.v1.json과
p09-361-whitespace-patch-strengthening182.v1.json이다.

## 다음 원본 연결과 Gate

별도 원본 compiler/readback과 현재 저장/제품 준비 요청은 각각 신규24개를 검증했다.
다음 접근허용 불필요 작업은 SEARCH-009 지원 제어별 원본 치환과 참조/ID 보존이다. 전체 유효 서식/숨김·
target match_set/semantic_diff/reopen·dispatcher/DB/commit/CAS/멱등 실행/게시·Native는 미완료다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
