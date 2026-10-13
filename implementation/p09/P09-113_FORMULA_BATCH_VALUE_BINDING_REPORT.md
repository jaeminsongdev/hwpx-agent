# P09-113 — 다중 표·다중 구역 field-result source-position 대응 수정

## 실제 완료한 변경

기존 P112 source-backed 계산→HWPX candidate 출력의 다중 표 readback 오류를 수정했다.
표 anchor는 package/part/span hash를 포함하므로 결과 출력 뒤 hash-sorted 표 순서가 바뀐다.
기존 values zip은 서로 다른 표를 대조하여 유효한 출력을 Readback 오류로 거부했다.
유효한 source admission 이후 새 batch 검사6개 중4 통과/2 실패(c5cf3b/session83365→fca90c/exit1)로 재현했다.

원래 field importer가 실제 spine/element 위치로 정렬한 paired range마다 native kind/ID/header/end attributes,
독립적으로 resolve한 begin/end/parameters part+element 위치 및 각 버전의 계산값/좌표를 비교한다.
AST/format/grid/Unverified cache 및 whole expected leaf-edit 바이트 검사는 그대로 수행한다.
기존 evaluator/ID/namespace/보호/writer 한도를 완화하지 않았다.

빈 결과 text를 채우면 원래 normalized inline ordinal이 합법적으로 변하므로 그것을 지속 identity로 사용하지 않는다.
초기 binding에서 이를 과도하게 비교하여5 통과/1 실패했다(24f860/session93837→959042/exit1).
새 검사는 빈/일반 결과의 ordinal 차이와 동일한 math 값을 독립 확인하며 actual range/전체 바이트 검사를 유지한다.

## 최종 현재 소스 검증

| 실제 실행 범위 | 결과 |
| --- | --- |
| hwpx-package lib + 11개 integration suite | 136 통과 |
| 기존 실제 stored provider 경로1 suite | 170 통과 |
| 총 실행 / 서로 다른 fully-qualified 테스트 이름 | 306 / 306, 중복0 |
| 신규 검사 | 10 (batch6 + private position4), 위 합계에 포함 |
| 최종 strict lint | 경고를 오류로 처리하여 통과 |

package 시작000ca9/session33622 → b62fba/exit0, stored 시작91d187/session58869 →
d1ecb9/exit0(286.87초). 최종 production source는 두 실행 전 고정했고 실행 중 변경하지 않았다.
실제13 test executable의 --list에서306개 이름과 각 exit0을 확인했다.
고유 테스트 이름은 고유 fixture/제품 기능/semantic coverage 개수를 의미하지 않는다.
최종 Python9 및 raw source checkpoint 결과는 별도 final-audit에 기록한다.

## 파생 자료와 확인한 내용

immutable P77 manifest의 actual36 type/bytes/SHA guard는 그대로다. 새 자료는 실제 첫2행4열 표에서
A1 numeric, B1=D2+1, D2=A1+1을 만든 in-memory derivative이며 native 재캡처가 아니다.
같은 표의2개 formula 및 formula-to-formula dependency, 다른 값의2구역4개 formula batch8사례,
current/changed 혼합, closed/self-closing empty result2형식, 양쪽 구역의 current/changed 보호 필드,
stale 우선 거부, 두 번째 구역 invalid numeric dependency의 전체 evaluation 거부를 확인했다.
변경 없는 구역과 비구역 part는 독립적으로 원래 bytes와 비교한다.
보호/오류 검사에서 source bytes/graph를 유지하며 일부 candidate를 반환하지 않는다.

private position4 검사는 버전별 hash 변화 허용, 같은 text의 다른 구역/인접 요소 대체 거부,
old version/forged fingerprint anchor 거부를 확인한다.
stored170은 기존 authenticated actual source/result/ACL/AEAD/head/quarantine 경로의 회귀이며,
새 multi-section stored qualification이나 실제 SQL/durable publisher 증거가 아니다.

## 실패와 원본 보존

첫 fixture4 실패는 실제 표를3cell로 가정한 오류였다. 실제8cell/좌표를 확인하여 고쳤다.
이어 복사 subtree namespace context 누락6 실패, ZIP mimetype-first 규칙 누락1 통과/5 실패,
paragraph id=0 sentinel을 양수로 바꾸어 발생한 duplicate declaration(3 통과/3 Patch 실패 및
독립 source-index1 실패)을 수정했다. 원래 검증기는 바꾸지 않았다.
모든 단계의 source/failed executable을 보존했다. test helper는 실제 namespace context,
mimetype-first, 원래 paragraph zero sentinel을 유지하고 source ID admission을 독립 실행한다.

첫 lint의 method closure2/filter-map1 오류는 표현만 고쳤으며 억제나 budget 완화는 없다.
archive 목록 구성 중 fixture/test 경로를 혼동한 두 raw-pin 읽기 실패도 기록했고 checker 두 버전을 보존했다.
실제 bounded archive inventory로 정확한16개를 선언했다. 경로/개수/byte/SHA 검사를 생략하지 않는다.

P112 source997 중996 unchanged + 수정 부모1 whole preimage/정확한 역변환을 확인했다.
P112 unmodified audit를 exact preimage view에서 실제 실행해 inherited raw1958, old executable378 보존을 확인했다.
과거 모든 native qualification/executable을 재실행했다는 뜻은 아니다.
new source12 포함 current1009/delta13, archive16/predecessor2/current executable23을 원장에 고정한다.
23개는 final test13, 실행하지 않은 CLI copies2, 실패 diagnostic7, pre-lint diagnostic1이며 전부 PASS라고 하지 않는다.

current source conformance15 통과/green0(07ad4f), original default matrix_drift/exit1(29f900)은 유지했다.
private/reference locks/원본/실패/사용자 dirty 및 PLANS 삭제 상태를 보존했다.

## 잔여와 다음 경계

다중 표 candidate 검증 결함은 수정했지만 original full operation compiler/product envelope,
trusted field policy/issuer/atomic publication/durable integration은 미완료다.
다음은 원래 full product 경로와 실제 source-derived field-result batch의 연결 조건을 확인하고,
fresh authenticated stored multi-section result consumption을 검증하는 것이다.
caller-written map/IR/policy/authority나 native metadata를 추정해서 경로를 열지 않는다.

metadata/coordinates, full comment/rich compiler/source mapping, durable integration,
fields/date/external/document 의미, trusted protection/atomic publication, actual P84 SQL 원인·회귀의
최소6 큰 묶음은 유지하며 이번에 닫힌 묶음은0이다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED/product false/no P10/전체 목표active를 유지한다.
한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않았다.
