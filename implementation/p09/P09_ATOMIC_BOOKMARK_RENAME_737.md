# 책갈피 이름과 연결 상호참조의 원자 변경737~742

2026-10-26. 직전731~736의 snapshot layout/메모리 상한 구현·검증은 progress다. 전체 P09~P20 목표와 P09/A12/A13 OPEN을 유지한다.

## 변경 계약

기존 command 변경은 대상을 선택하는 CROSSREF 수정이었다. 새737/738은 원본에 결속된 point/block 책갈피 자체의 이름을 바꾸면서 그 대상을 가리키는 모든 지원 CROSSREF의 Command·RefPath·dirty를 하나의 보존 패치로 바꾼다. 새 이름은 SDK 이름 제약과 XML 의미 값 제약을 통과해야 한다. 다른 책갈피/point 이름 또는 새 이름을 가리키던 별도 dangling reference를 뜻하지 않게 붙잡는 변경은 거부한다.

fresh 원본 전체 proof·현재 target/name SHA·관측 보호/리뷰·지원 field family·parameter 일관성·ID/부위/크기 budget을 확인한다. 지원 profile은 point/block bookmark와 bookmark CROSSREF이며 다른 field family는 거부한다. 출력의 실제 새 target/모든 연결 binding·Command/RefPath/dirty를 재확인하고, cache는 그대로 보존한다. 수정한 attribute/leaf 값 사이의 모든 원본 바이트와 비선택 부위/참조도 보존 검사한다. 표시값 새로고침/Native/서비스 실행/공개/현재 head 채택 자격은 만들지 않는다.

검증은 새9개 조건(블록/XML escaping·point·여러 연결·무관한 참조·이름 충돌/문법·stale 원본/이름·불일치 RefPath·보호·dangling capture 차단)과 Native reopened8종에서 새 이름 변경 HWPX 후보8개를 실제 생성·재열기하는 경로다. 이름 표시 cache가 새 이름으로 자동 평가됐다고 판정하지 않는 것도 기존 제품 oracle로 확인한다. 기존736/730/725/721/713/249 검사와 Native 실행은 반복하지 않는다.

변경 전 parent module2개는 source-archive/p361-bookmark-rename737에 보존했다. 단일 코어·낮은 우선순위·원 CPU/RAM/commit 보호와714 원 단계 표본 보존을 유지했다.

## 검증 결과

[742-product004 영수증](evidence/p09-361-bookmark-rename742-product004.v1.json): `QUALIFIED742_ATOMIC_RENAME_RETAINED8_CURRENT_ENTRY2_ACTUAL8_PRIVATE_OUTPUTS_NOT_NATIVE_REFRESH_OR_F11`, 169382 bytes, SHA256 `da36826af43cd85c933b1549204a3b29aefc7fac62e9619ec97be23324350cb3`.

- 현재 수정의 직접 영향인 보호 거부·point 진입2검사가 통과했다. 제품의 보호 검사를 strict body import보다 먼저 수행하고, fieldBegin/fieldEnd 전체 coverage도 같은 순회에서 센다. 보호 토큰 때문에 본문을 해석하지 못해도 변경 후보를 만들지 않는다.
- 기존002의 8개 성공 관측은 원본 영수증·정확한 코드와 함께 보존했다. 그중 point1개만 진입 변경 영향으로 다시 확인했고 나머지7개는 반복하지 않았다. 002 자체는 실패이며 종료 입력 해시가 0이므로 전체 검증 성공으로 승격하지 않는다. 실제 수정/보존/readback 로직이 동일한지 현재 검증기에서도 확인했다.
- Native reopened8종을 입력으로 제품 경로를 호출해 비공개 새 HWPX8개를 create-new 저장하고 실제 파일을 다시 읽었다. 모든 경우 target 이름·연결 CROSSREF Command·RefPath·dirty가 하나의 패치로 변경됐고, 원본·캐시·그 밖의 바이트가 보존됐다. `private/p09-361-bookmark-rename740-generated001/case-01.hwpx`~`case-08.hwpx`는 소비된 출력 경로이므로 덮어쓰거나 재실행하지 않는다.
- 입력1258/1258·산출물12 final hash·cleanup=true, 296.219초. 원guard587표본·시스템CPU최고28.12%·가용RAM최저32.5436%·보호중단0. Native process 집합은 동일했다. 과거 PC 프리즈 원인의 해결을 뜻하지 않는다.

## 실패 기록과 수정 경계

| 실행 | 결과와 조치 |
|---|---|
| 001 | 테스트 준비 코드가 비공개 XML API를 호출해 컴파일 실패. 공개 API를 넓히지 않고 ZIP의 정확한 원본 바이트/SHA로 수정했다. 제품 시험 실행0. |
| 002 | 9개 중 8개 성공, 잠금 검사 준비가 본문 해석에서 실패. 성공 관측·실패 모두 보존했다. |
| 003 | 잠금 표식 위치만 변경해 1개만 재검사했으나 여전히 준비 과정의 Body 오류. 같은 위치 변경을 더 반복하지 않았다. |
| 004 | 깨끗한 원본에서 선택자를 얻고, 제품의 관측 보호 검사를 본문 해석 앞으로 옮겼다. 현재2검사·실제8출력·최종 입력/산출물 경계 통과. |

001~003 영수증과 forensic 원본은 유지한다. 수정 전 파일은 `source-archive/p361-bookmark-rename742-001`~`003`, 문서 변경 전 원본은 `source-archive/p361-bookmark-rename742-docs`에 정확히 보존했다. 이 실패들은 자원 보호 중단이 아니다.

## P09에서 이어갈 범위

이름 변경 후보의 원자 결속만 구현·검증했다. 이름 표시 cache를 새 이름으로 자동 평가하거나 refreshed로 판정하지 않는다. 기존 oracle로 오래된 이름 cache가 불일치하는 것도 별도로 관측했으며, 한글 저장·재열기/표시·탐색 수용은 아직 없다.

F11 안에서 다음은 이동/내부 hyperlink·찾아가기와 필요한 대상 흐름, Saved의 정확한 extent·아래/다중쪽 조건, 원래 RouteUnqualified 조건을 충족하는 실제 로컬 진입/출력/현재 head 채택이다. 새 이름 후보를 실제 한글로 평가할 때는 다른 남은 실물 검증과 한 묶음으로 준비한다. 독립 catalog rename capability를 추가한 것이 아니며 P11의 전체 새로고침 구현을 앞당기지 않는다.

현재 외부 실행 명령은 필요 없고 목표는 ACTIVE다. P09/A12/A13 OPEN, 31 closure packages/65 features, 공식249는158수용·91대기·next165, 새P10 미시작을 유지한다.
