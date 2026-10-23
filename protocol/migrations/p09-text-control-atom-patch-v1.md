# 타입 지정 텍스트 제어 치환 기반

`ReplaceTextControlAtoms`는 SEARCH-009에 필요한 저수준 preserving patch다. 원본 qualified
TextSpan의 실제 Tab/LineBreak를 일반 Text·typed Tab/LineBreak로 교체하거나 명시적으로 삭제한다.
검색/선택·관측 보호는 별도 [원본 치환 compiler](p09-source-text-control-replacement-v1.md)에 연결했다.
현재 저장·엄격한 제품 요청은 별도 [제품 준비 프로필](p09-text-control-product-request-v1.md)에
연결했다. 모든 관측 제어의 치환·전체 문서 보호·실제 저장 커밋과 제품 실행 자격은 미완료다.

## 원본 대상과 출력

`TextControlAtomReplacement::new`는 original atom ordinal, 기대하는 TextControlKind와
`Vec<TextAtom>`을 받는다. TextControlKind는 기존 두 종류의 enum을 재사용한다. 실제 원본이
Text이거나 없는 atom이면 거부하며, 입력 Text를 삭제하는 기능은 열지 않는다. 빈 출력 벡터는
해당 control 전체의 삭제다. 비어 있는 Text 출력 atom, raw 제어 문자·허용하지 않는 noncharacter·
과도한 payload를 거부한다. 탭·줄바꿈은 raw 문자열이 아니라 typed 출력으로 지정해야 한다.

Text 출력은 XML처럼 보이더라도 문자 데이터로 escape한다. 임의 XML/QName/속성 이름을
실행하지 않는다. 출력 Tab 속성은 unsigned width/leader/tab_type이며 LineBreak는 정해진
종류다. native layout/tab stop/번호 평가 자격은 아니다. 다른 제어 종류나 ID·참조를 새로 생성하거나
재작성하는 경로는 없다. 검색으로 얻은 control start만으로 전체 control subtree의 편집 권한이
증명되는 것도 아니다. 상위 compiler에서 실제 선택 범위와 보호를 별도로 확인해야 한다.

## 편집과 보존

기존 qualified TextSpan reader로 부모 전체를 확인하며 opaque/미지 제어·잘못된 속성·foreign
namespace·주석/부적합한 Text를 조용히 건너뛰지 않는다. 실제 namespace prefix는 원본 t의
QName에서 가져오며 hp를 가정하지 않는다. 원본 control cursor를 한 번 전진시키며 실제 atom
번호와 기대 종류를 대조한다. 여러 control이 바뀌어 출력 atom 번호가 달라져도 뒤의 편집은
항상 원본 좌표를 사용한다. paired control 내부 공백은 그 control을 선택했을 때만 바뀐다.

원본 Text와 선택 밖 control/entity·run/t 서식·다른 ZIP entry는 보존한다. 원 ID profile과
preserving writer/validation을 유지하며 원본을 in-place 수정하지 않는다. 일반 TextAtom 편집의
control 변경 금지와 whitespace 편집의 공백 전용 조건은 그대로다.

## 공동 상한과 비용

새 TextControl과 기존 WhitespaceAtom/TextAtom/LeafScalar 네 편집 계열의 내부 범위 개수와
typed 출력 atom 개수·실제 escaped 출력 byte 예산을 공동 적용한다. 상위 intent 개수만으로
판정하지 않고 byte-disjoint라도 다른 계열이 같은 target을 공유하면 거부한다. 역순/중복 원본
control도 거부한다. namespace·control markup·multibyte/escape 확장을 값/fragment·공동 출력
상한에 포함한다. 실패한 작업은 부분 patch로 전달하지 않는다.

일반 Text escape를 유한 cap 아래 직접 출력해 원문5배 크기의 임시 escaped 문자열을 만들지
않는다. 한 부모의2천 control 시험을 포함하며 범위마다 원본 atom을 처음부터 다시 읽지 않는다.
새 intent가 없을 때 새 preflight는 즉시0을 반환하므로 기존 whitespace 예산과 기존 입력 거부
조건은 유지된다. 원 patch engine/ID profile/dispatch와 whitespace reader/renderer 본문은
추가 코드·export와 읽기 전용 getter를 제거해 원 파일 전체로 역변환했다.

## 검증과 다음 연결

components189는 시험 helper의 PackageGraph API명 오류 E0599로 시험0이며 원 실패를 보존했다.
제품을 유지하고 build API 호출 한 줄만 고친 recovery190은 신규18pass·708fresh/final708·진단/
경고없음·cleanupTrue다. Unicode/escape·typed mixed 출력/삭제·원본 atom/expected kind·alias/
default/shadowed namespace·stale/부적합 selector·네 계열 혼합 건수/escaped byte/출력 atom
한도와 byte-disjoint 동일 target 거부·2천 control·20만 ampersand의 작은 예산 거부·비노출/
결정성과 기존 텍스트/공백 경로의 거부 유지를 확인했다. 기존 patch/원본/제품242·공식249는
반복하지 않았다. 실제 사용자 문서나 한글 실물 결과의 수용 증거로 올리지 않는다.

190 전체94.453초·명령3.657초/시험2.07초·Job CPU3.438초·private최고574.8MiB/1.8041%·
시스템CPU최고38.49%·가용RAM최저30.3866%다. 소유 Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. OS/다른 앱 변경이나 PC 프리즈 해결·benchmark 주장은 없다. 근거는
implementation/p09/evidence/p09-361-text-control-patch-components189.v1.json과
p09-361-text-control-patch-recovery190.v1.json이다.

실제 control_anchor의 검색/선택·관측 보호 compiler와 변환 후 readback은 별도 신규24+영향12개를
검증했다. 현재 저장 서비스·엄격한 제품 JSON은 components194 신규 제품24pass·716fresh/final716으로
연결했다. 다음은 SEARCH-009 다른 제어 종류의 지원 조건과 참조/ID 보존이다.
카탈로그 query/replacement·전체 유효 서식/selector/filter·target
match_set/semantic_diff/reopen·dispatcher/DB/commit/CAS/영속 멱등 실행/게시·Native/Gate는
미완료다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을
유지한다.
