# 원본 형제 요소 순서 변경

PatchIntent::PermuteSiblingElements는 SEARCH-021 정렬에 필요한 원본 보존 편집 기반이다.
같은 불변 원본의 요소 바이트를 순열로 교환하며, 정렬 기준이나 문단의 편집 권한을 결정하지 않는다.

## 원본과 순서 계약

targets는 같은 part의 같은 부모에 속하는 최소2개 요소를 원본 순서로 받는다. 각 XmlElementSelector는
기존 selector 검증으로 원 part·원본 SHA·요소 위치/이름에 결속한다. root·중첩·서로 다른 부모·역순·중복
대상과 외부 원본/part를 거부한다. source_order[destination]는 해당 목적 slot으로 옮길 원본 targets의
0기준 인덱스다. 길이가 다르거나 중복/누락/범위 밖 인덱스가 있는 순서와 항등 순열은 거부한다.

이동하는 하위 요소만 원본 outer span 바이트로 교환한다. XML 재작성·namespace 삽입·caller XML은 없다.
같은 부모에서 교환하므로 상속 namespace·xml:lang·xml:space 문맥은 유지되고 지역 선언은 바이트와 함께
이동한다. 선택하지 않은 형제와 slot 사이의 텍스트·주석·공백은 제자리에 남는다. 주석을 다음 문단에
자동으로 붙여 옮긴다는 의미가 아니다. 고정 slot은 복사하거나 이동 byte 예산에 청구하지 않는다.

## 상한과 기존 검증

기존 max_intents를 전체 transaction의 확장 대상 수에 적용한다. max_fragment_bytes는 이 작업의
실제 이동 복사 바이트를 모든 순열 intent에 걸쳐 합산한 한도로 사용한다. 각각 permutation_targets와
permutation_bytes 오류로 거부하며, 출력 증가가 없다는 이유로 복사 비용을 무제한 허용하지 않는다.
인덱스·순열 확인·span 수집·복사는 대상 수와 실제 복사 byte에 선형이며 각 할당은 fallible reserve를 쓴다.

기존 overlap detector·ID/참조 검사·보존 검사·최종 XML/package 검증·PreservingWriter를 그대로 통과해야 한다.
원 SafeXml의 ProcessingInstructionForbidden을 유지한다. 문서 보호·필드·review 의미와 허용 문단 범위는
상위 source 정렬 계층에서 별도로 확인해야 하며, 이 원시 편집 intent가 그 자격을 만들지 않는다.

## 검증 결과

components227은 신규11+기존6=17pass/1fail이다. PI를 포함한 잘못된 양성 입력만 허용된 주석으로 바꾸고
정확한 PI 거부 음성 검사를 추가했다. 제품·보안 파서는 변경하지 않았고 원 실패는 보존했다.
recovery228은 그1개만pass·786fresh/final786·진단/경고없음·cleanupTrue다. 신규12+영향기존6=고유18개
통과이며 현재18개 단일 실행이 아니다. 통과17개·원 crypto/보호/compiler·공식249는 재실행하지 않았다.

서로 다른 길이·Unicode·entity·namespace, 비선택 요소와 간격, 고정 slot, 잘못된 순열/대상/부모/원본/part,
겹침, 누적 대상/byte 상한·정확한 경계, ID/참조 보존·dangling 거부,1000개 형제 요소의 결정적 결과 및
writer 출력의 재열기/무변경 part 해시를 확인했다. 근거는 다음 두 보존된 결과다.

- implementation/p09/evidence/p09-361-sibling-permutation-components227.v1.json
- implementation/p09/evidence/p09-361-sibling-permutation-recovery228.v1.json

227/228 전체77.312/104.297초·명령26.312/3.000초·시험1.32/0.01초다. 두 실행의 시스템CPU 최고18.89%·
private 최고1784.83MiB/5.60195%·가용RAM 최저26.1195%이며 두 Job active0/empty/handle closed다.
한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%와 명령300초·guard600초를 유지했다.
OS 변경이나 PC 프리즈 해결을 주장하지 않는다.

## 다음 제품 경계

SEARCH-021의 comparator·문단 소유/보호·전체 선택 범위·정렬 후보·엄격한 제품 요청·실제 실행/저장과
한글의 locale/표시 순서 검증은 남는다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·
잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
