# 원본 검색 일치 대소문자 변환

`hwpx-agent.source-match-case-conversion/v1`은 SEARCH-013의 원본 후보 compiler다.
명시적 `Uppercase` 또는 `Lowercase`와 `UnicodeDefaultEachMatchedTextGroup` 정책으로
정확히 선택된 원본 글자를 변환하고 기존 run과 text atom의 서식을 유지한다.
현재 저장 서비스·엄격한 제품 JSON은 [별도 제품 프로필](p09-case-product-request-v1.md)로 연결했다.
실제 저장 실행과 한글 자격은 아직 미완료다.

## 변환 정책과 원본 범위

한 원본 Form proof에서 field/review/index를 구성하고 기존 literal/regex 또는 선언/typed 정의
서식 matcher 중 한 branch를 실행한다. 네 selector와 review 포함 정책을 먼저 적용하며
모든 NFC 기여자의 원본 범위를 확인한다. 불완전·불연속 역상, 겹치는 원본과 빈 일치는 거부한다.
검색용 NFC 글자로 원본을 덮어쓰지 않으며 인접한 별도 일치의 문맥을 합치지 않는다.

각 일치 안의 연속 TEXT 그룹 전체에 Rust 1.96 std의 문자열 변환을 한 번 적용한다.
탭·줄바꿈·기존 block은 문맥 경계이고 같은 그룹 안의 run/text 경계는 문맥을 끊지 않는다.
선택 밖 글자나 옆 일치의 글자는 문맥에 넣지 않는다. 예를 들어 AΣ에서 Σ만 선택하면 Aσ,
전체를 선택하면 aς이고 정규식 점으로 두 개의 일치를 만들면 aσ다.

Unicode17 기본 대소문자 변환과 case folding은 목적이 다르다. 문맥 의존 Final_Sigma와
언어별 tailoring의 구분은 [Unicode17 3.13](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/)과
[SpecialCasing](https://www.unicode.org/Public/17.0.0/ucd/SpecialCasing.txt)을 따른다.
이 프로필은 locale별 변환·titlecase·case folding·자동 정규화를 하지 않는다.
İ의 기본 소문자 결과는 i와 결합점이며 ß의 대문자 확장은 SS다. 한글 앱의 변환과 동등하다는
권위도 부여하지 않는다. char::UNICODE_VERSION이17.0.0이 아니면 거부한다.

로컬 rust-src의 alloc/src/str.rs, core/src/char/methods.rs,
core/src/unicode/unicode_data.rs 세 파일을 입력으로 pin하고 FinalSigma 구현·Unicode17 선언을
확인했다. 이는 소스 참고와 런타임 version 검사이며 설치 바이너리 재현 빌드의 증명은 아니다.
기존 regex의 검색 동작을 바꾸거나 다른 버전의 속성 테이블을 변환 판정에 혼용하지 않는다.

## 원본 보존과 자원 상한

문자별 확장 scalar·UTF8 byte 수를 먼저 계산하고 상한 안에서만 전체 문자열을 할당한다.
전체 문자열 결과를 원 글자별 확장 길이로 나눠 대조하며 Σ는 문맥 결과 σ/ς를 허용한다.
확장 글자는 원 text atom에 남고 다른 run으로 이동하지 않는다. 같은 atom의 연속된 변경만
한 범위로 합치며 변하지 않은 글자가 사이에 있으면 분리해 entity 표기를 보존한다.
2만 글자 연속 변환은 글자별2만 patch가 아니라 한 patch로 처리한다.

기존 Unicode compiler의 보호·field cache·patch·readback 본문은 공통 함수로 추출하고
원 본문 전체로 역변환해 대조했다. 기본 정규화의 의미·한도와 기존 writer는 바꾸지 않았다.
part별 보호 map과 segment별 TextSpan/offset을 공유하고 원본 proof·field/review/index·matcher·
writer·출력 import를 일치나 글자마다 재실행하지 않는다. no-op 제거 전에 보호와 cache를 검사한다.
receipt는 실제 변환 version·mode/policy·검색/selector/filter·원본·출력과 검증 범위를 결속한다.

## 검증 결과

components168은 Point import 누락 E0425로 컴파일 실패했고 시험0이다. 그 import 한 줄만
추가한 components169는63pass/1fail이다. 실패한 새 시험은 XML 전체의 k를 세어 lineBreak
태그의 글자까지 본문으로 계산했다. 제품과 다른 시험을 유지하고 이 한 시험을 정책4조합의
정확한 전체 section 및 다른 ZIP entry 보존 비교로 고쳤다.

recovery170은 수정1pass·673fresh/final673·stdlib참고3/final3·진단/경고없음·cleanupTrue다.
신규22+영향기존42=고유64개이며 현재64개 단일 실행으로 합치지 않는다. 통과63개·무관source57·
기존제품172·공식249는 반복하지 않았다. 원 실패168/169는 그대로 보존한다.
범위4종·literal/regex/case/whole-word·명시적 서식·review4정책·cache/보호/no-op·entity/제어/
참조/서식 보존·확장·FinalSigma/Case_Ignorable·match 문맥·다중문자계·입력/응답/writer 상한·
비노출·2만 글자 단일 patch·4096 결합문자의 문맥을 확인했다.

169 전체89.563초·명령45.438초/시험18.73초·Job CPU43.312초·private최고1706.36MiB/5.3557%·
시스템CPU최고62.31%·가용RAM최저27.1341%다. 170 전체91.188초·명령4.250초/시험0.84초·
Job CPU2.922초·private최고577.45MiB/1.8124%·시스템CPU최고75.59%·가용RAM최저29.4735%다.
두 Job active0/empty/handle closed와 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/
stop7%·RAM/commit95%·명령300초·guard600초 및 입력 전후 확인을 유지했다.
시스템 표본은 소유 Job 단독 사용률이나 외부 원인의 증거가 아니며 프리즈 해결·benchmark로 쓰지 않는다.
근거는 implementation/p09/evidence의 p09-361-case-conversion-components168.v1.json,
p09-361-case-conversion-components169.v1.json과 p09-361-case-conversion-recovery170.v1.json이다.

## 다음 제품 연결과 Gate

이 변환의 현재 저장 서비스와 엄격한 제품 JSON은 별도 제품 프로필에서 신규22개를 검증했다.
다음 접근허용 불필요 작업은 SEARCH-014 전각·반각 변환 정책과 원본 compiler다.
전체 유효 서식·selector/filter/방향·보호·target match_set/semantic_diff/reopen·dispatcher/DB/
commit/CAS/멱등 실행/게시·Native는 미완료다. source API v12 incomplete/미해결4/report없음/
exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행과 기존 Native 재실행 금지도 유지한다.
