# 원본 OUTLINE 선언과 제목 참조 대상

`hwpx-agent.source-direct-outline-targets/v1`은 원 header의 직접 문단 속성 선언과 실제 표현된 문단을
결속하는 source 단계다. 제목 대상의 원본 존재와 변경 지문을 제공하며 유효 서식 cascade·계산된 번호·쪽 위치·
Native 탐색이나 완전한 참조 상태를 판정하지 않는다. 실제 reference source API와 CLI는 v13으로 명시적으로
버전을 올려 이 inventory를 연결했다. 네 unresolved·incomplete·report없음·exit3은 유지한다.

## 실제 API와 CLI v13

`hwpx-agent.product.reference-source-assessment/v13`의 `heading_target_import`는 optional receipt다.
전체 XML에 HH heading 선언이 관측되지 않으면 null이며, 제목이 없다고 확인된 inventory를 뜻하지 않는다.
명시적 NONE 선언이 있는 유효 header는 제목0개인 실제 receipt를 반환하므로 null과 구분된다.
어느 XML에든 실제 HH heading이 관측되면 엄격한 importer를 호출하고 Binding·Coverage·Limit을 null로 숨기지 않는다.

실제 제품 진입점은 기존 Form의 immutable structure를 빌리고 기존 대상 뒤에 Heading 대상을 합친다.
ZIP/XML/Form을 두 번 수입하지 않는다. API에는 receipt와 기존 ValidationTarget만 노출하고 원 idRef/level·
문단 속성 ID·관측행·제목 원문은 추가하지 않는다. CLI는 같은 JSON과 exit3을 반환하고 오류는 exit2로 닫힌다.
확장된 전체 응답 byte 상한과 item 상한을 유지하며 책갈피·각주·개체·캡션의 기존 알고리즘은 바꾸지 않는다.

[424](../../implementation/p09/evidence/p09-361-reference-source-heading-api-closed-inputs424.v1.json)은
신규 core7+신규 API13+영향 API57+저장3의 고유80개가 경고 없이 통과했다. 세 실제 시험 바이너리의 Rust
의존 입력87개를 명시하고 빌드 전후 대조했으며 전체878fresh/final878·cleanupTrue다. 제품·문서 바인딩,
API/CLI 일치·원본 보존·부분 header/null과 명시적 NONE·잘못된 선언·전체 XML 누락·part별 local ID 분리·
기존 책갈피 결합·출력/항목 상한·비공개 원문 비노출을 포함한다. 기존 strict core24·공식249·Native는 반복하지 않았다.

전체126.281초, 저장/core/API 명령은10.531/0.250/2.141초이고 Job CPU는9.109/0.172/1.734초다.
private 최고1066.17MiB·시스템CPU최고22.73%·가용RAM최저40.0186%이며 모든 Job active0/empty/handle closed다.
한 코어/BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%는 그대로다.
프리즈 해결이나 실제 한글 검증 결과로 해석하지 않는다.

421은 core7/API70 통과 메시지 뒤 256KiB 영수증 상한 초과로 최종 row가 저장되지 않았다.
[출판 실패 관측](../../implementation/p09/evidence/p09-361-reference-source-heading-api421-publication-failure.v1.json)에
보존했고 저장3/최종 입력/정리 표본을 원래 증거처럼 재구성하지 않았다.
[422](../../implementation/p09/evidence/p09-361-reference-source-heading-api-recovery422.v1.json)은 저장3pass 뒤
공유 fixture의 package 미사용 경고로 실패했으며806fresh/final806·cleanupTrue다.
표본을 빠뜨리지 않는 inline 열·행 형식의 왕복/오류 거부6개를 검증했고 원 영수증 상한은 완화하지 않았다.
[423](../../implementation/p09/evidence/p09-361-reference-source-heading-api-final423.v1.json)은 이전 목록에 없던
공유 fixture의 baseline 조회 KeyError로 실행 전 실패·시험0·809fresh/final809·cleanupTrue다.
424는 실제 컴파일 의존 입력87개를 새로 명시해 이 누락을 닫았다. 공유 fixture에는 해당 함수만의 dead_code
허용 사유를 추가했으며 제품 코드·시험 단언·fixture 함수 본문은 바꾸지 않았다. 세 실패를 통과로 재표시하지 않는다.

424 영수증의 resource_sample_table은 모든251개 자원 표본을 보존한다. 읽을 때는
`tools/p09/resource_sample_table.py`의 unpack으로 원 resource_samples를 복원한다. source_pins와 시험 결과는
기존 형태이며 별도 외부 carrier나 표본 축약은 사용하지 않는다. 변경 없는 형식 시험6개는422에서 보존한다.

## 원본 선언과 문단 결속

기존 immutable `ImportedDocumentStructure`를 빌리고 ZIP/XML/graph를 다시 수입하지 않는다.
`Contents/header.xml`의 head/refList/paraProperties/paraPr/heading 관계를 한 번 인덱싱한다.
공식 Hancom 모델 commit145338의 `heading.cpp`는 type/idRef/level의 명시적 읽기를 정의하고,
`enumdef.h`는 NONE/OUTLINE/NUMBER/BULLET 네 종류를 정의한다. 생성자의0 기본값을 누락 속성의 원본 값으로 쓰지 않는다.

직접 paraPrIDRef가 OUTLINE 선언에 연결된 표현된 문단만 `ReferenceTargetKind::Heading`으로 반환한다.
논리 문단 ID·문단 source anchor·전체 문단 정의와 heading 선언 지문·원 property ID·raw idRef/level을 결속한다.
원 numbering idRef는 관측값이며 해당 번호 정의의 해석이나 존재 검증을 뜻하지 않는다. raw level은 u32 관측값이고
Native의 유효 수준 범위·표시 번호로 올리지 않는다. target의 active는 source 존재이며 anchor는 None이다.

NUMBER/BULLET/NONE을 제목으로 바꾸지 않는다. 직접 참조나 heading 선언이 없으면 기본값이나 이름 있는 스타일의
상속 결과를 만들지 않으며 직접 참조가 없는 문단 수를 기록한다. 미지 선언·중복/잘못된 ID·다중 heading·누락 속성·
정수 범위 초과·미지 속성/내용·다른 parent 위치는 거부한다. 외부 namespace의 동명 heading을 native 선언으로 해석하지 않는다.
기존 문단 파서가 거부하는 외부 참조 속성/잘못된 정수도 우회하지 않는다.

## 전체 원본 누락과 자원 상한

표현된 section/note/table/drawing 흐름을 방문하고 원본의 모든 XML part에서 직접 OUTLINE 문단을 대조한다.
header·nonspine·opaque 영역의 제목 문단이 구조 graph에 표현되지 않았으면 Coverage로 거부한다.
source hash와 part/span에 결속된 ID를 사용하므로 서로 다른 part의 같은 문단 local ID를 합치지 않는다.

header 정의 인덱스와 문단 방문·전체 XML scan을 공유한다. 문단마다 전체 XML을 재탐색하거나 제목 본문을
재해시하지 않고 기존 anchor 지문을 재사용한다. 기존 graph 깊이·section/item·전체 metadata byte 상한을 유지한다.
전체 envelope가 상한을 넘으면 부분 결과를 잘라내지 않는다. 원본 바이트/graph는 쓰지 않는다.

receipt와 Debug에는 제목 원문이나 XML이 없다. verify_source는 현재 전체 source/graph를 다시 확인하며
저장된 지문을 서비스 접근 권한으로 쓰지 않는다. effective_style_cascade_qualified·native_number_or_navigation_qualified·
complete_reference_state_qualified는 false다. reference edge·CROSSREF 매개변수·Native/실행/게시 권한은 만들지 않는다.

## 검증 결과와 다음 연결

[418](../../implementation/p09/evidence/p09-361-source-heading-targets418.v1.json)은 이전 카탈로그 입력 목록에
새 참조 시험 root가 있다고 가정한 검증기 KeyError로 시험0개에서 중단됐다.785fresh/final785·cleanupTrue로 보존했다.
해당 root는 기존 검증된 목록에 없으므로 과거 시험 결과를 재사용하지 않았고, [419](../../implementation/p09/evidence/p09-361-source-heading-targets-recovery419.v1.json)에서
신규22개와 기존 대상2개를 실제 실행했다.22pass/2fail·787fresh/final787·cleanupTrue다.

두 실패는 기존 문단 파서의 Paragraph 오류가 새 importer의 단언 전에 전파된 시험 문제다. 생산 코드를 바꾸지 않고
정확한 upstream 오류 종류와 새 importer의 dangling 참조 거부를 구분한 [420](../../implementation/p09/evidence/p09-361-source-heading-targets-test-recovery420.v1.json)은
실패2개만pass·이전22보존·현재 고유24개·789fresh/final789·진단/경고없음·cleanupTrue다. 원418/419 실패와
이전 통과 본문을 보존했고 공식249·다른 제품/Native 시험은 반복하지 않았다.

419 전체132.281초/명령31.360초·Job CPU29.594초/private1908.84MiB·시스템CPU최고34.09%·
가용RAM최저43.2945%다.420 전체106.203초/명령4.813초·Job CPU3.734초/private659.98MiB·
시스템CPU최고22.09%·가용RAM최저47.3919%다. 두 Job active0/empty/handle closed를 확인했다.
한 코어/BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%를 유지했고 프리즈 해결 판정은 아니다.

다음은 유효 제목 스타일 cascade와 남은 참조 대상·CROSSREF 의미 결속을 원본 증거에 따라 구현하는 것이다.
현재 v13·네 unresolved·incomplete·report없음·exit3은 그대로다. 직접 OUTLINE 연결만으로 OtherTargetFamilies
전체나 Native 자격을 닫지 않는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
