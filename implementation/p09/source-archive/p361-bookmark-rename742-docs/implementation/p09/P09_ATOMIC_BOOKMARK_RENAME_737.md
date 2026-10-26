# 책갈피 이름과 연결 상호참조의 원자 변경737~742

2026-10-26. 직전731~736의 snapshot layout/메모리 상한 구현·검증은 progress다. 전체 P09~P20 목표와 P09/A12/A13 OPEN을 유지한다.

## 변경 계약

기존 command 변경은 대상을 선택하는 CROSSREF 수정이었다. 새737/738은 원본에 결속된 point/block 책갈피 자체의 이름을 바꾸면서 그 대상을 가리키는 모든 지원 CROSSREF의 Command·RefPath·dirty를 하나의 보존 패치로 바꾼다. 새 이름은 SDK 이름 제약과 XML 의미 값 제약을 통과해야 한다. 다른 책갈피/point 이름 또는 새 이름을 가리키던 별도 dangling reference를 뜻하지 않게 붙잡는 변경은 거부한다.

fresh 원본 전체 proof·현재 target/name SHA·관측 보호/리뷰·지원 field family·parameter 일관성·ID/부위/크기 budget을 확인한다. 지원 profile은 point/block bookmark와 bookmark CROSSREF이며 다른 field family는 거부한다. 출력의 실제 새 target/모든 연결 binding·Command/RefPath/dirty를 재확인하고, cache는 그대로 보존한다. 수정한 attribute/leaf 값 사이의 모든 원본 바이트와 비선택 부위/참조도 보존 검사한다. 표시값 새로고침/Native/서비스 실행/공개/현재 head 채택 자격은 만들지 않는다.

검증은 새9개 조건(블록/XML escaping·point·여러 연결·무관한 참조·이름 충돌/문법·stale 원본/이름·불일치 RefPath·보호·dangling capture 차단)과 Native reopened8종에서 새 이름 변경 HWPX 후보8개를 실제 생성·재열기하는 경로다. 이름 표시 cache가 새 이름으로 자동 평가됐다고 판정하지 않는 것도 기존 제품 oracle로 확인한다. 기존736/730/725/721/713/249 검사와 Native 실행은 반복하지 않는다.

변경 전 parent module2개는 source-archive/p361-bookmark-rename737에 보존했다. 단일 코어·낮은 우선순위·원 CPU/RAM/commit 보호와714 원 단계 표본 보존을 유지한다. 검증 진행 중이며 아직 완료로 판정하지 않는다.
