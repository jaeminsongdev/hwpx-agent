# 책갈피 상호참조의 현재 원본 이동 대상743~748

2026-10-26. P09-F11의 내부 hyperlink/탐색과 reference_update를 위한 현재 원본의 destination 처리다. P09~P20 목표와 P09/A12/A13 OPEN을 유지한다.

## 구현 계약

제품 진입점은 원본 bytes·document ID·expected SHA·선택한 실제 field ID만 받는다. caller의 대상 이름/위치/Command/cache나 Native 허가는 입력으로 받지 않는다. 원본 전체·field coverage·reconstruction을 확인하고, source Command와 RefPath의 같은 문서 대상 결속을 확인한다.

하이퍼링크가 켜진 참조만 실제 point marker 또는 block begin/end source anchor를 반환한다. 꺼진 참조는 bound target이 있어도 destination이 없다. 없는 대상·이름 중복은 각각 MissingTarget/AmbiguousTarget이며 destination이 없다. Command/RefPath 불일치·중복 leaf·stale 원본·선택 중복/미존재·budget 위반은 거부한다. opaque fieldid나 표시 cache로 위치를 추정하지 않는다.

전체 batch를 준비할 때 원본/graph를 한 번 검증하고, field·binding·point target을 한 번씩 index한다. 현재 source destination을 소비하기 직전에 batch 전체의 fresh SHA/길이를 다시 확인한다. 선택 수와 결과 메모리·JSON output·전체 parameter 순회가 제한된다. metadata에는 해시/상태만 남기며 이름·Command·원본 내용·anchor를 내보내지 않는다.

이 결과는 현재 원본 token에 대한 커서 목적지다. 한글의 실제 커서를 이동시키거나 application/session 권한을 만들지 않는다. 화면 이동/링크 클릭/Native 표시·저장 수용, 실제 로컬 host·public output/head 채택, 일반 DocumentFlow와 전체 F11은 별도 필수 경계다.

## 검증 계획

새9검사와 기존 reopened8/이름변경후8의 16파일에 새로운 탐색 판정을 수행한다. 하이퍼링크 on8은 정확한 source begin/end, off8은 destination 없음이어야 한다. point marker를 다른 위치로 옮긴 fixture에서는 이전 준비 결과를 재사용할 수 없고 현재 source에서 새로 해석해야 한다. 이 fixture의 이동은 검증용이며 실제 제품의 이동 편집 구현으로 세지 않는다.

기존742/736/730/725/721/713/Native/249 시험은 반복하지 않는다. 원guard·단일 CPU·낮은 우선순위·CPU/RAM/commit 보호와714 단계 표본을 유지한다. 검증 진행 중이며 완료를 주장하지 않는다.

변경 전 parent module2개는 `source-archive/p361-bookmark-navigation743`에 보존했다. `evidence/p09-361-bookmark-navigation743-inputs.v1.json`은 기존 성공742와 Native 생산자693 입력에 결속한 파일 목록일 뿐 탐색/Native 수용 증거가 아니다.
