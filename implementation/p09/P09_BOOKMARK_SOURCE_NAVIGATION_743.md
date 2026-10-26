# 책갈피 상호참조의 현재 원본 이동 대상743~748

2026-10-26. P09-F11의 내부 hyperlink/탐색과 reference_update를 위한 현재 원본의 destination 처리다. P09~P20 목표와 P09/A12/A13 OPEN을 유지한다.

## 구현 계약

제품 진입점은 원본 bytes·document ID·expected SHA·선택한 실제 field ID만 받는다. caller의 대상 이름/위치/Command/cache나 Native 허가는 입력으로 받지 않는다. 원본 전체·field coverage·reconstruction을 확인하고, source Command와 RefPath의 같은 문서 대상 결속을 확인한다.

하이퍼링크가 켜진 참조만 실제 point marker 또는 block begin/end source anchor를 반환한다. 꺼진 참조는 bound target이 있어도 destination이 없다. 없는 대상·이름 중복은 각각 MissingTarget/AmbiguousTarget이며 destination이 없다. Command/RefPath 불일치·중복 leaf·stale 원본·선택 중복/미존재·budget 위반은 거부한다. opaque fieldid나 표시 cache로 위치를 추정하지 않는다.

전체 batch를 준비할 때 원본/graph를 한 번 검증하고, field·binding·point target을 한 번씩 index한다. 현재 source destination을 소비하기 직전에 batch 전체의 fresh SHA/길이를 다시 확인한다. 선택 수와 결과 메모리·JSON output·전체 parameter 순회가 제한된다. metadata에는 해시/상태만 남기며 이름·Command·원본 내용·anchor를 내보내지 않는다.

이 결과는 현재 원본 token에 대한 커서 목적지다. 한글의 실제 커서를 이동시키거나 application/session 권한을 만들지 않는다. 화면 이동/링크 클릭/Native 표시·저장 수용, 실제 로컬 host·public output/head 채택, 일반 DocumentFlow와 전체 F11은 별도 필수 경계다.

## 검증 계획

새9검사와 기존 reopened8/이름변경후8의 16파일에 새로운 탐색 판정을 수행한다. 하이퍼링크 on8은 정확한 source begin/end, off8은 destination 없음이어야 한다. point marker를 다른 위치로 옮긴 fixture에서는 이전 준비 결과를 재사용할 수 없고 현재 source에서 새로 해석해야 한다. 이 fixture의 이동은 검증용이며 실제 제품의 이동 편집 구현으로 세지 않는다.

기존742/736/730/725/721/713/Native/249 시험은 반복하지 않았다. 원guard·단일 CPU·낮은 우선순위·CPU/RAM/commit 보호와714 단계 표본을 유지했다.

변경 전 parent module2개는 `source-archive/p361-bookmark-navigation743`에 보존했다. `evidence/p09-361-bookmark-navigation743-inputs.v1.json`은 기존 성공742와 Native 생산자693 입력에 결속한 파일 목록일 뿐 탐색/Native 수용 증거가 아니다.

## 검증 결과

[748-product003 영수증](evidence/p09-361-bookmark-navigation748-product003.v1.json): `QUALIFIED748_CURRENT_SOURCE_BOOKMARK_NAVIGATION_RETAINED8_CURRENT1_ACTUAL16_NOT_NATIVE_CURSOR_OR_F11`, 163272 bytes, SHA256 `20492ea412646ab337ebec810ff07dc2ac8269a147451798d42ed59090c7d008`.

- 002에서8조건이 성공했고 중복 RefPath fixture의 `cnt` 불일치로1조건은 준비 단계에서 실패했다. 003은 실제 중복 parameter까지 도달하는 유효 XML fixture로 고친1조건만 실행해 통과했다. 보호/거부 조건은 바꾸지 않았고 제품 코드는 동일하다. 이전8조건의 본문과 제품 입력/코드가 그대로인지 다시 확인했고 실행을 반복하지 않았다. 002는 종료 source hash0인 실패 묶음 그대로 보존하며 전체 자격으로 승격하지 않는다.
- 일반 제품 빌드에서 실제 기존 파일16개에 새로운 탐색 판정을 실행했다. reopened8와 이름변경후8 중 hyperlink on8개는 실제 source block begin/end에 도달하고 off8개는 destination이 없다. 각 파일의 해시·길이를 현재 입력과 일치시키고 판정 전후 원본 불변을 확인했다. 이름 변경 후보 생성이나 기존 의미 시험을 반복한 것이 아니다.
- 현재 원본1282/1282·실행 산출물4 final hash·cleanup=true, 257.375초. 원guard510표본·시스템CPU최고39.29%·가용RAM최저35.6817%·보호중단0. Native process 집합은 같으며 한글을 실행/탐색하지 않았다. 과거 프리즈 원인 해결을 뜻하지 않는다.
- 새9조건의 범위는 실제block 위치·off 이동차단·point 위치·이름변경 후 cache 미사용·point 이동 후 stale 준비결과 거부·없는/중복대상·불일치/중복 RefPath·stale SHA/선택/크기 거부·metadata 비노출이다. point 이동은 fixture 편집이며 제품 이동 편집 구현 수용으로 세지 않는다.

## 실패 보존과 다음 작업

001은 테스트에서 비공개 XML attribute API를 사용해 컴파일 실패했고 시험 실행0이다. ZIP의 정확한 XML part hash와 공개 value_span으로 의미 값을 읽도록 고쳤다. 공개 API를 넓히지 않았다. 002의 실패는 중복 parameter를 추가하고 `cnt`를 갱신하지 않은 fixture 오류이며, 실제 reader의 `text_flow.rs::validate_parameter_entries`가 올바르게 거부했다. 검증 조건을 낮추는 대신 count를 맞춰 의도한 중복 경로 거부를 확인했다.

001/002 영수증·forensic 원본·정확한 수정 전 파일은 보존했다. 수정 파일 archive는 `source-archive/p361-bookmark-navigation748-001`/`002`, 문서 archive는 `source-archive/p361-bookmark-navigation748-docs`다.

F11에 필요한 실제 한글 cursor/링크 탐색·이름 변경 후보의 표시/저장 수용, 정확한 Saved extent/아래·다중쪽·다른 필수 대상 흐름, 실제 로컬 host 진입/지속출력/현재 head 채택은 남았다. Source/Graph partial·기본 NeedsDocumentFlow·RouteUnqualified와 기존 독립 Native/249 결과는 유지한다. 전체 P11 refresh나 범용 운영 서비스 완성을 P09에 합치지 않는다.

현재 사용자 실행 명령은 없고 목표는 ACTIVE다. P09/A12/A13 OPEN, 31 closure packages/65 features, 공식158/249·91대기·next165, 새P10 미시작을 유지한다.
