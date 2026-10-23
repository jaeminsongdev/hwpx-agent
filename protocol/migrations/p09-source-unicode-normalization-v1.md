# P09 원본 Unicode 정규화

`hwpx-agent.source-selector-unicode-normalization/v1`은 선택한 실제 HWPX 원본 글자를
변환한 별도 후보를 만든다. 검색 인덱스의 NFC 표현만 바꾸는 기능이 아니다.
현재 저장 서비스·엄격한 선택 범위 제품 JSON 연결은
[별도 제품 프로필](p09-unicode-product-request-v1.md)에서 검증했다. 검색어·서식 필터를
포함한 전체 SEARCH-022 계약과 저장 트랜잭션은 다음 경계다.

별도 [검색 일치 정규화 source 프로필](p09-source-unicode-match-normalization-v1.md)은 문자열·
정규식과 명시적 선언/정의 서식 조건을 원본 변환에 결합한다. scope 전체의 이 v1 동작과
receipt는 유지하며 새 일치 후보의 저장/제품 연결은 별도 작업이다.

## 명시적 변환과 선택 범위

`ImportedDocumentForms.lower_review_selector_unicode_candidate`와 call-local 원본 proof의
동명 메서드는 Document·Section·NodeSet·Selection 네 범위, hidden/MEMO 포함 정책,
Nfc·Nfd·Nfkc·Nfkd 중 하나와 FirstOriginalRunRetainAllRuns 정책을 필수로 받는다.
호환 정규화를 기본값으로 선택하지 않는다. NFKC/NFKD는 수학 기호나 서식상 구별까지
없앨 수 있으므로 요청자가 형태를 명시해야 한다. 형식의 의미는
[Unicode 정규화 표준](https://unicode.org/reports/tr15/)을 따른다.

실제 테이블은 Cargo.lock의 unicode-normalization 0.1.25, Unicode 17.0.0이다.
현재 웹 표준의 버전과 혼동하지 않으며 실제 사용 버전을 receipt와 요청 지문에 넣는다.
선택 좌표는 원본 index의 NFC scalar 좌표다. 원래 resolver에서 확인한 exact windows를
이동해 재사용하고 원본 scalar로 역매핑한다. 하나의 원본 글자의 정규화 결과를 일부만
선택하거나, 재정렬로 역상이 불연속이면 거부한다. 선택 밖 결합 문자를 끌어오지 않는다.

## 원본 위치와 서식 보존

정규화는 같은 선택 창의 run·인접 t 경계를 연결하되, 탭·줄바꿈·기존 source block 경계는
넘지 않는다. 원래 TextSpan을 segment별 한 번 읽고 atom별 UTF-8 위치 표를 만든다.
정준/호환 분해·안정적 결합 클래스 정렬·선택적 재결합은 원본 scalar의 기여자를 유지한다.
각 그룹의 출력 전체를 별도 streaming 라이브러리 결과와 대조한다.

입력과 출력의 기여 관계를 양방향으로 닫아 최소 연속 편집 성분을 계산한다. 실제로
바뀐 성분만 첫 원본 기여자의 위치에 출력하고 나머지 기여 부분을 제거한다. 변경되지 않은
성분은 원래 t/run 위치와 서식을 유지한다. 예를 들어 NFD의 `a + 0315 + 0300`은 기호만
재정렬하며 바뀌지 않은 a를 다른 run으로 옮기지 않는다. 여러 run의 한글 자모 결합은
하나의 성분으로 처리하고 원래 run/t shell과 모든 참조 속성은 보존한다.

원본 field/review/index는 각각 한 번 사용한다. 선택된 segment의 관측 가능한 잠금·보호와
상위 paraTcId/charTcId를 no-op 제거 전에 확인하며 part별 보호 맵을 공유한다. 필드 cache는
편집할 수 없다. MEMO는 기존 정확한 소유 payload 범위만 허용하며 다른 상위 필드 범위는
계속 차단한다. 전체 문서 선택에 cache가 포함되면 이미 정규화된 cache도 오류다.
이를 조용히 건너뛰지 않는다. review payload만 편집하려면 해당 원본 node를 선택한다.

기존 v9 text-style ID 규칙의 preserving writer를 한 번 호출하고 한 output import에서
TextSpan 값·review 구조·편집 slot 밖 전체 bytes를 검증한다. 기존 atom readback 본문은
공유 함수로 추출했을 뿐이며 전체 역변환으로 원 본문과의 일치를 확인했다. 기존 v6 writer와
검색용 NFC 알고리즘, 다른 제품 요청·권한·head 경계는 바꾸지 않았다.

## 자원 제한과 검증 결과

원본 scalar·전체 분해 scalar·변경 성분·patch range·누적 출력/응답 byte 제한을 적용한다.
원본·출력 위치는 단조 증가 cursor로 닫으며 일치마다 XML·원본·header를 다시 읽지 않는다.
초과·불연속·보호·무변경은 성공 후보 대신 오류다. receipt에는 본문 원문을 넣지 않는다.

components157은 새 시험의 assembly 모듈 import 누락 E0432로 컴파일 실패했고 시험0이다.
import만 추가한 recovery158은78pass/3fail이었다. 실패는 문단에 잘못 놓은 charTcId,
이미 NFD인 글자에 대한 잘못된 변경 개수 기대, 원 selector의 Scope 오류를 Selection으로
기대한 세 시험이었다. 제품을 바꾸지 않고 해당 세 시험만 고쳤고, 실제 호환 분해 확장이
제한을 넘기는 별도 검사를 같은 실패 시험에 추가했다.

failed-cases159는 수정3pass·654fresh/final654·진단/경고없음·cleanupTrue다. 158의78개와
현재3개를 결속해 신규24+영향기존57=고유81개를 검증했다. 이는 현재81개를 한 번에 다시
실행한 결과가 아니다. 통과78개·무관 제품·공식249는 재실행하지 않았다. 네 형태, run/t
경계 한글 결합, 결합 문자 재정렬과 서식 유지, entity/비BMP, 제어·문단 경계, 네 selector,
불완전 역상, review 정책과 cache, 보호/no-op, source/proof, 확장·출력 한도와 복합 문자
표본을 포함한다. 157/158의 원 실패는 그대로 보존한다.

159 전체87.469초·명령3.437초·시험0.42초·Job CPU2.578초·private최고580.07MiB/1.8206%·
시스템CPU최고33.2%·가용RAM최저27.0673%다. 소유 Job은 active0/empty/handle closed이며
한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·
guard600초와 전후 입력 확인을 유지했다. 이 측정은 PC 프리즈 원인 해결이나 benchmark가 아니다.

근거는 implementation/p09/evidence의
`p09-361-unicode-normalization-components157.v1.json`,
`p09-361-unicode-normalization-recovery158.v1.json`,
`p09-361-unicode-normalization-failed-cases159.v1.json`이다.

## 남은 제품 경계

현재 경로는 정확한 선택 창의 source 후보다. 검색어·style_filter를 포함하는 전체 SEARCH-022
요청 계약, 실제 실행·commit/CAS·멱등 key claim·게시,
전체 보호·match_set/semantic_diff/reopen·Native 검증은 미완료다. writer integrity와 지문은
현재 접근 권한이나 저장 실행 권한이 아니다. 고정 CROSSREF8종은 NOT_RUN, Native011은
미승인·미실행이며 source API v12는 incomplete/미해결4/report없음/exit3이다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작·목표ACTIVE를 유지한다.
