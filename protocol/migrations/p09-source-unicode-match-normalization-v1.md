# P09 검색 일치 원본 Unicode 정규화

`hwpx-agent.source-match-unicode-normalization/v1`은 문자열·정규식과 명시적 원본 서식 조건에
맞는 부분만 실제 원본 위치에서 정규화한다. 검색한 NFC 문자열로 원본을 덮어쓰지 않는다.
이 source 후보의 현재 저장 서비스·엄격한 제품 요청은
[별도 v2 제품 프로필](p09-unicode-match-product-request-v2.md)에서 검증했다. 기존 선택 범위
전체 제품 v1은 query/filter를 계속 거부하며 전체 트랜잭션·Native와 구분한다.

## 검색 조건과 원본 선택

`ImportedDocumentForms.lower_review_selector_unicode_matches`와 같은 원본 proof의 동명
메서드는 query·네 selector·review 정책·선택적 SourceReviewStyleFilter·정규화 형태·run 정책을
받는다. 기존 문자열 또는 정규식 matcher 중 하나를 한 번 실행한다. 필터가 있으면 기존
find_style의 선언 참조 또는 typed 정의값 조건을 같은 검색에 결합한다. 정의 조건은
run/text/named 글자 축과 direct/named 문단 축을 명시하며 유효 cascade를 추정하지 않는다.

원 선택 창과 hidden/MEMO 정책을 먼저 적용하고 각 NFC 일치의 모든 원본 기여자가 서식 조건을
만족해야 한다. 제외된 후보는 일치 상한을 소모하지 않는다. literal query만 NFC 정규화하고
regex 문법·escape는 그대로 둔다. regex는 NFC 본문을 대상으로 하므로 원본 분해형 패턴을
자동으로 다시 쓰지 않는다. casefold·whole word·일치/패턴/응답 상한은 기존 검색 계약을 따른다.

NoMatches·NoChange·선택 오류를 구분한다. 빈 정규식 일치는 원본 글자를 선택하지 않으므로
Selection 오류다. 한 원본 scalar의 정규화 결과 일부만 고르거나 역상이 불연속이면 거부하며
일치를 넓히지 않는다. 일치 사이에 원본 기여자가 중복되는 경우도 거부한다.

## 실제 변환과 보존

일치마다 원본 scalar 집합을 얻고 같은 compiler에 전달한다. 각 일치는 별도 정규화 그룹이다.
인접한 일치도 합치지 않는다. 예를 들어 NFKC에서 `ㄱㅏ`를 두 개의 `.` 일치로 선택하면
각각 정규화한 `가`이고, 하나의 `.+` 일치로 선택하면 `가`다. 전자는 선택된 두 문자열의
정규화이지, 일치 경계를 없앤 문서 전체 정규화가 아니다.

탭·줄바꿈·기존 block은 계속 경계다. 변경 최소 성분만 첫 원본 기여자 위치에 출력하고
변하지 않은 scalar·서식·참조·entity·제어를 보존한다. part별 관측 보호3N과 segment별 한
TextSpan/atom 위치 표를 모든 일치에서 공유한다. 검색되지 않은 보호 내용이나 cache는
편집하지 않으며, 일치한 보호/no-op와 field cache는 기존 guard에서 거부한다.

한 원본 Form proof·field/review/index와 한 matcher branch·writer·output import를 사용한다.
typed 정의 필터는 기존 typed header reader를 한 번 사용하며 일치마다 header/XML을 읽지 않는다.
기존 scope compiler의 보호·기여자·정규화·patch·한도 본문은 공통 함수로 추출했고 전체
역변환으로 원 본문을 재구성해 대조했다. 검색용 NFC 알고리즘과 기존 matcher·제품·권한
경계는 변경하지 않았다.

receipt는 원본에 결속된 검색 일치·region·서식 관측/정의 receipt와 selector·정규화 형태·
run/review 정책을 함께 보관한다. 출력 profile은 source-selector-unicode-normalization/v2로
구분하고 request 지문을 검색 요청과 결속한다. 기존 source v1이나 저장 제품 v1의 의미를
조용히 넓히지 않는다. 본문·query 원문은 receipt에 넣지 않으며 후보는 실행 권한이 아니다.

## 검증 결과

components163은41pass/1fail이다. 실패한 새 시험은 분해형 regex 패턴이 NFC corpus에서도
일치한다고 기대했지만 실제 오류는 NoMatches였다. 제품과 통과41개를 보존하고 그 한 시험에
원 패턴의 정확한 NoMatches 검사와 NFC 패턴을 사용한 탭 보존 검사를 추가했다.
recovery164는 수정1pass·663fresh/final663·진단/경고없음·cleanupTrue다.

신규18+영향기존24=고유42개이며 단일 현재42개 실행으로 합치지 않는다. 통과41개·무관source57·
기존제품150·공식249는 반복하지 않았다. 네 형태/범위, literal/regex/case/whole-word,
선언·typed 정의·named 축, 모든 원본 기여자 필터와 제외 우선 상한, 불완전/불연속 역상,
빈 일치/무일치/무변경, review/cache·보호/no-op·제어, 인접 일치 분리, entity/범위 보존,
원본/proof·잘못된 필터·패턴/확장/출력 한도·비노출·128일치의 공유 map을 포함한다.

163 전체77.844초·명령34.985초/시험10.74초·Job CPU33.234초·private최고1694.05MiB/5.3170%·
시스템CPU최고65.23%·가용RAM최저24.8676%다. 164 전체86.672초·명령1.875초/시험0.19초·
Job CPU1.781초·private최고575.61MiB/1.8066%·시스템CPU최고24.62%·가용RAM최저26.8442%다.
시스템 표본을 소유 Job의 CPU 사용률이나 외부 원인으로 해석하지 않는다. 두 Job 모두
active0/empty/handle closed이며 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·
RAM/commit95%·명령300초·guard600초와 입력 전후 확인을 유지했다. 프리즈 해결이나 benchmark가 아니다.

근거는 implementation/p09/evidence의 p09-361-unicode-match-components163.v1.json과
p09-361-unicode-match-recovery164.v1.json이다. 원 실패163은 그대로 보존한다.

## 다음 제품 연결과 Gate

원 보호·patch·한도 본문은 [대소문자 원본 프로필](p09-source-case-conversion-v1.md)의 공통
mapper 연결에서 전체 역변환으로 대조했고 영향 정규화42개를 확인했다. 기존 정규화 의미는 유지한다.

이 match 후보는 별도 v2에서 현재 저장 서비스·엄격한 제품 JSON까지 연결했다. 기존
[선택 범위 제품 v1](p09-unicode-product-request-v1.md)은 query/filter를 계속 거부한다.
전체 유효 서식·selector/filter·보호·target match_set/semantic_diff/reopen·dispatcher/DB/
commit/CAS/멱등 실행/게시·Native는 미완료다. source API v12 incomplete/미해결4/report없음/
exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.
고정 CROSSREF8종은 NOT_RUN이며 Native011은 미승인·미실행이다.
