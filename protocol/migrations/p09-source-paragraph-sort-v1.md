# 선택한 원본 형제 문단 정렬

lower_selector_paragraph_sort_candidate는 실제 불변 HWPX 원본에서 선택한 완전한 형제 문단을 정렬한
후보 패키지를 만든다. SEARCH-021의 원본 경로이며 현재 저장 서비스·공통 실행/commit 경로는 별도다.

## 정렬 기준과 선택 범위

SourceParagraphSortSpec은 direction·comparison·max_comparison_bytes를 명시적으로 받는다.
NfcUnicodeScalarLexicographic은 기존 원본 인덱스의 NFC 텍스트를 Unicode scalar 순서로 비교하며
Ascending/Descending 모두 동등 키의 원본 순서를 유지한다. UTF-8 유효 문자열의 byte 순서가 같은
scalar 순서를 보존하는 성질을 사용한다. 로캘 정렬·숫자 정렬·대소문자 무시·trim을 암묵적으로 적용하지 않는다.
원본의 분해 한글·entity·run·Text·탭·줄바꿈 바이트는 그대로 이동하고 키 정규화를 원문 재작성에 사용하지 않는다.

Document/Section/NodeSet/Selection은 원 SourceReviewScopeIndex의 실제 원본 창을 그대로 사용한다.
선택된 문단의 모든 인덱스 블록이 완전히 포함돼야 하며 부분 선택을 전체 문단으로 넓히지 않는다.
명시적 review 정책으로 숨김/MEMO 본문을 포함/제외하고 원 scope digest와 제외 수를 기록한다.
선택된 모든 문단은 같은 part·부모에 속해야 한다. 비연속 형제 선택은 허용하지만 선택 밖 요소와 slot
사이 바이트는 제자리에 남는다. 여러 부모/중첩 그룹이나 불명확한 구조적 키는 일부만 정렬하지 않고 거부한다.
기존 reader가 허용하는 빈 Text 문단은 빈 키이며 자기 닫힘 문단의 UnsupportedShape 거부는 유지한다.

## 원본 보호와 출력 검증

ImportedDocumentForms의 fresh 전체 재구성 또는 같은 원본의 VerifiedFormReconstruction을 사용한다.
기존 field/review 수입·관측된 HP lock/TC/SZ 보호와 추적 변경 검사를 재사용하고, 문단 전체가 보호되거나
허용되지 않은 field 구간과 겹치면 거부한다. 명시적 MEMO payload 예외도 기존 ReviewWriteContext의
정확한 소유 envelope 확인을 통과해야 하며 cache나 외부 필드를 편집할 수 없다.

원 PatchIntent::PermuteSiblingElements와 text-style/v9 ID profile·보존 profile·PreservingWriter를 사용한다.
하나의 출력 package/Form/field/review 수입 뒤 원본 하위 요소 바이트가 각 목적 slot에 정확히 놓였는지와
모든 선택 밖 gap/tail 바이트를 독립 대조한다. 다른 part의 SHA와 원 ID/참조·원본 바이트를 보존해야 한다.
receipt에는 원본/index/scope/spec·문단 anchor·키/하위 요소 SHA·순열·작업량·출력 SHA를 결속한다.
locale_native_full_protection_or_execution_authority=false이며 정렬 후보가 현재 권한이나 실행 자격을 부여하지 않는다.

## 유한 작업량

비교 byte 예산은 1 이상32MiB 이하이며 prefix의 각 비교 위치와 문자열 종료 확인도 예산에 포함한다.
fallible 안정 병합 정렬은 예산 초과 즉시 ComparisonLimit로 거부하며 부분 결과나 비일관 비교기로 바꾸지 않는다.
원본 인덱스·응답 크기·최대4096 대상·원 순열의 누적 복사 byte·writer 상한도 그대로 적용한다.

## 검증 결과

components230은17pass/2fail이다. 표의 새 ID1이 바깥 원본 ID와 충돌했고 자기 닫힘 빈 문단은 reader
비허용 형태였다. diagnosis231은 id_index_validation_failed를 관측했으나 추가 닫힌 allowlist 검사에서 실패했다.
두 fixture만 고유 ID901/허용된 빈 Text 문단으로 고치고 원 UnsupportedShape 거부도 음성 검사로 확인했다.
제품·reader·ID 검사는 변경하지 않았고 원 실패/진단을 보존했다. recovery232는 그2개만pass·796fresh/final796·
진단/경고없음·cleanupTrue다. 신규 고유19개 통과이며 현재19개 단일 실행이 아니다. 통과17개·이전 patch18·공식249는 재실행하지 않았다.

네 selector·NFC 안정성·정확한 원문 이동·비선택 slot·proof/원본 거부·무변경·상한·비노출·보호/필드 거부·
다른 부모 거부·숨김/MEMO 명시 정책·표 셀/상속 잠금·128문단 결정적 출력을 확인했다. 근거는 다음과 같다.

- implementation/p09/evidence/p09-361-source-paragraph-sort-components230.v1.json
- implementation/p09/evidence/p09-361-source-paragraph-sort-diagnosis231.v1.json
- implementation/p09/evidence/p09-361-source-paragraph-sort-recovery232.v1.json

230/232 전체79.906/107.500초·명령26.985/3.360초·시험0.96/0.39초다. 231 진단까지 시스템CPU 최고29.10%·
private 최고1791.06MiB/5.62150%·가용RAM 최저26.6083%이며 세 Job active0/empty/handle closed다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했다.
OS 변경이나 PC 프리즈 해결을 주장하지 않는다.

## 남은 제품 경계

다중 부모/중첩 그룹 합성·구조적 키·현재 저장 서비스/엄격한 제품 요청·공통 compiler·실제 실행/commit/CAS·
locale/target/Native는 미완료다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
