# 원본 검색 일치 공백 탭 줄바꿈 정규화

`hwpx-agent.source-match-whitespace-normalization/v1`은 SEARCH-023의 실제 원본 검색 일치에서
명시적으로 선택한 공백 문자와 구조적 Tab/LineBreak를 변환하는 source candidate다.
문서 전체·구역·노드 집합·선택 창과 review 포함 정책, literal/regex·선언/typed 정의 서식 필터를
기존 검색 경로에 연결한다. 현재 저장 서비스·엄격한 제품 JSON은 별도
[제품 준비 요청](p09-whitespace-product-request-v1.md)으로 연결했다. revision commit은 미완료다.

## 명시적 입력 정책

`SourceWhitespacePolicy`의 모든 필드는 필수이며 알 수 없는 필드는 거부한다.

| 필드 | 값과 의미 |
|---|---|
| text | None, AsciiSpace, Unicode17Breaking, Unicode17AllModelAdmitted |
| tabs | 구조적 Tab을 변환 대상으로 포함할지 여부 |
| line_breaks | 구조적 LineBreak를 변환 대상으로 포함할지 여부 |
| sequence | CollapseEachMatchedSequence 또는 EachOriginalScalar |
| output | Spaces의 고정 count 1~1024, unsigned 속성의 Tab, LineBreak 또는 Remove |

AsciiSpace는 U+0020만 포함한다. all은 기존 qualified Text reader가 허용하는 고정 Unicode17
공백19개를 포함한다. breaking은 그 집합에서 U+00A0, U+2007, U+202F를 뺀16개다.
NBSP·figure space·narrow NBSP를 암묵적으로 축약하지 않는다. U+200B/FEFF와 일반 글자는 대상이
아니다. 원 raw TAB/LF/CR/VT/FF/NEL 거부는 유지하며 구조적 Tab/LineBreak와 Text scalar의
U+2028/U+2029를 서로 다른 입력으로 다룬다. 모든 입력 종류를 비활성화한 정책은 거부한다.

CollapseEachMatchedSequence는 선택한 종류의 연속 부분만 한 출력으로 바꾼다. 일반 글자,
선택하지 않은 공백/제어, 다른 검색 일치와 원본 block은 경계다. EachOriginalScalar는 각 원본
scalar 또는 구조적 제어마다 지정 출력을 적용한다. 고정 칸 수는 가시적 tab stop 계산이 아니다.
Remove는 정확한 검색 범위 안의 해당 종류만 삭제하며 일반 글자를 삭제하지 않는다. 예를 들어
양끝 공백만 삭제하려면 해당 경계를 선택하는 regex를 명시해야 한다. 빈 일치는 거부한다.

`FirstOriginalRunRetainAllRuns`로 축약 출력을 첫 원본 기여자에 두고 나머지 기여자의 해당 공백만
지운다. 원 paragraph/run/t shell과 서식 참조를 없애거나 문단을 합치지 않는다. 원본 Text와
구조적 제어 사이의 변환은 [typed whitespace patch](p09-whitespace-atom-patch-v1.md)만 사용하며
임의 XML을 받지 않는다. no-op인 entity나 동일 속성의 control은 원래 바이트 그대로 둔다.

## 원본 선택과 보호

원본 Form proof·field/review/index·matcher를 각각 한 번 구성한다. 모든 원본 기여자가 정확히
선택되는지 확인하고 빈 일치·partial/noncontiguous NFC 역상·중복 기여자는 거부한다. 검색용
NFC 문자열로 실제 원본을 덮어쓰지 않는다. filter를 생략한 요청과 typed filter 요청을 구분하고
selector·query·filter·review·정규화 정책·run 정책과 실제 검색 결과를 request receipt에 결속한다.

선택한 source segment마다 한 TextSpan과 scalar byte offset map을 만들고 part마다 기존
관측 잠금/상위 추적 guard3N을 공유한다. guard 함수의 가시성만 넓혔으며 본문 전체는 역변환으로
대조했다. no-op이나 일반 글자만 포함한 선택이라도 보호·field cache 검사는 생략하지 않는다.
기존 ReviewWriteContext가 증명한 정확한 MEMO 본문만 field interval에서 제외하며 다른 외부
field가 다시 덮으면 차단한다. 전체 유효 서식·숨김·Native 보호 자격을 의미하지 않는다.

## 제어 변경 후 재검증

기존 readback의 전체 element 개수·slot 불변 조건은 변경하지 않는다. 별도 readback은 원본
scalar scanner/whole-control outer span으로 정한 sparse edit 목록을 사용한다. 원본 QName에서
얻은 namespace와 unsigned 숫자의 실제 길이를 합산해 출력 할당 전에 공동 byte 한도를 검사한다.
독립 canonical 출력 인코딩과 모든 선택 밖 바이트를 출력 XML 전체에서 대조한다. 새·삭제된
제어 때문에 뒤의 element index가 이동하더라도 t container 순서로 대응시키고 출력 TextSpan을
검증한다. 출력 Form/field/review를 다시 import해 review 수와 자격 경계를 확인한다.

원 writer의 text-style/v9·Hangul2020PreviewTextV2 profile을 그대로 사용한다. 추가 part가 없고
다른 ZIP entry의 바이트가 보존되는지 확인한다. 원본이나 현재 저장 문서는 수정하지 않는다.
범위 개수·typed 출력·값/fragment·공동 byte 한도와 검색/응답/writer 한도를 적용하고 실패 시
부분 후보를 전달하지 않는다. 2만 연속 공백은 개별 글자별 patch가 아니라 한 범위로 낮춘다.

## 검증 결과와 다음 작업

components184는 시험 fixture의 assembly import 누락 E0432로 시험0이며 원 실패를 보존했다.
그 import와 출력 할당 전 예산·nested output strictness를 보강한 recovery185는 신규 원본24개가
통과했다. 700fresh/final700·진단/경고없음·cleanupTrue다. 검색/네 selector/서식·review/cache·
잠금/추적/no-op·NFC 역상·typed 제어 생성/삭제·뒤 element index 이동·한도·비노출·독립 byte
tamper oracle·2만 공백 단일 patch와 축약 재적용 NoChange를 확인했다. 개별 scalar에 여러 칸을
내보내는 명시적 확장 정책까지 멱등이라고 주장하지 않는다. 기존 patch43·제품218·공식249는
반복하지 않았다.

185 전체122.266초·명령32.688초/시험6.15초·Job CPU31초·private최고1728.36MiB/5.4247%·
시스템CPU최고40.62%·가용RAM최저27.1205%다. Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. OS/다른 앱 변경이나 PC 프리즈 해결·benchmark 주장은 없다. 근거는
implementation/p09/evidence/p09-361-whitespace-source-components184.v1.json과
p09-361-whitespace-source-recovery185.v1.json이다.

현재 저장 서비스·엄격한 제품 JSON은 별도 신규24개를 검증했다. 전체 selector/filter/유효 서식·target
match_set/semantic_diff/reopen·dispatcher/DB/commit/CAS/영속 멱등 실행/게시·Native/Gate는
미완료다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을
유지한다. source candidate의 writer integrity는 현재 문서 접근 권한이나 실행 허가가 아니다.
