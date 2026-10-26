> 현재 기준(2026-10-26): [원본 대상의 초기 결과 oracle726~730](P09_BOOKMARK_RESULT_ORACLE_726.md) 완료. 새8검사와 기존32파일의 새 의미 판정이 첫 실행 통과했다. 원본에서 유도한 책갈피 이름/본문은 Native 저장본12관측과 일치,후보4관측은 임시표시 불일치,Page/Relative16관측은 NeedsDocumentFlow 유지다. 관측 수를 기능/잔여 작업 수로 세지 않는다. source1226/1226·실행산출물4 final·cleanup=true,원guard566표본·CPU최고18.95%·가용RAM최저32.8390%·보호중단0. 기존725/721/713/Native/249 재실행0. 실제배치/다른대상·이동/탐색·실제host/출력/head·F11은 미완료. 목표ACTIVE·외부명령현재없음·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작. 아래는 이전 이력이다.

> 현재 기준(2026-10-25): [조건부 제목 입력702·주 Source32 검증706](P09_CONDITIONAL_HEADING_MODEL_702.md) 완료. 새9+영향제목13조건·일반빌드·실제32파일을 통과했다. 후보8개는 조건부3정의를 v16 unresolved/heading unavailable로 보존하고 Native24개는 기존 v15 partial을 유지한다. 주 Source field API/캐시가 독립 API·manifest와 일치하며 branch/effective heading/완전한 validation은 미검증이다. source1090/1090·compiled6final·cleanup=true·CPU최고33.2%·가용RAM최저35.9693%·보호중단0. 기존 strict importer/실패/BOOKMARK8부분상태·684/690소비명령 보존, Native/249/무관한통과9조건 재실행0. 목표ACTIVE·외부명령현재없음. 다음은현재P09 허용제품경로 C01/C02/C05와남은F11. P09/A12/A13 OPEN·31묶음/65기능·공식158/249·next165·새P10미시작. 아래는이전이력이다.

# P09 블록 참조 8종 실제 캡처와 32문서 필드 API·그래프

2026-10-25. 전체 P09~P20 목표를 유지한다. 684 실패와 부분7번은 그대로 보존하며, 공식249=158수용·91대기·next165, 잔여31개 closure 묶음/65기능, P09/A12/A13 OPEN·새 P10 미시작이다. 이 문서는 F11의 현재 고정 블록 대상/표시 조합에 관한 부분 증거다.

## 실제 한글 실행 완료

690의7~8번 실행은 `CAPTURED690_NEW_BLOCK_TAIL_TWO_PRODUCER_BOUND_SEMANTICS_UNQUALIFIED`, error=null, cleanup=true로 완료됐다. 영수증 `evidence/p09-361-prepared-bookmark690-native001.v1.json`은120,041B, SHA `6a402d7e8f14d7affb4e940b9f4d0c6e9adde7753891e75b979449d7e4e47a52`이다. 원시 metadata788,164B·SHA `98471100b6fbeab229a932e5b5349937e6ae101dd2974553fd3a8dfbf6c5fe14`를 별도 spool에 보존했다. 실행676.844초·CPU최고36.52%·가용RAM최저50.1367%다. 새 런은2종뿐이라 `fixed_eight_executed=false`가 맞고, `remaining_two_executed`와 보존6+새2 캡처 완결을 별도로 기록했다.

새2종의4세션·입력 경계·생성 주체/정리와 보존6종을 결속해 고정8종 전체의48산출물(HWPX24/BMP16/trace8)을 확인했다. 별도의 생성 후보8개와 합쳐32개의 HWPX를 검사했다. 새로운 한글/Native/249 실행은 하지 않았다.

693 영수증 `evidence/p09-361-block-bookmark693-capture-readback001.v1.json`은87,886B, SHA `63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3`, source1054/1054·cleanup=true·188.625초·CPU최고23.83%·가용RAM최저51.2717%다.8종의 Command SHA와 저장/재열기 parameter·cache는 일치했다. 모든 Native 결과의 dirty는0이다. Page 두종은 현재1쪽, BookmarkName 두종은 실제 source 이름, Content 두종은 실제 첫 블록 선택 텍스트의 SHA와 일치했다. RelativePosition 두종은 현재 캐시 일치 관측이며 이동/이름 변경·다른 위치·탐색 일반 수용으로 승격하지 않는다.

## 그래프 구현과 검증

기존 Command 해석기는 block target을 source-local `Bound`로 반환했지만, `fields/semantics.rs`의 edge 연결은 point wrapper만 찾았다. 이제 이미 엄격한 Command/block importer가 수용한 BOOKMARK Prop2의 논리 ID를 같은 fields inventory의 begin node에 연결한다. end node/다른 블록/호출자 node/다른 source는 사용하지 않는다. Missing/Ambiguous는 계속 None이며, point wrapper 연결과 기존 참조/캐시를 보존한다. BOOKMARK8개 자체의 일반 필드 의미는 계속 Unsupported로 남기며 complete meaning으로 바꾸지 않는다. graph profile partial-v3, field API v2, 전체 Source v15를 유지했다.

새 core6조건과 직접 영향받는 기존 point3조건을 통과했다. 첫696 product001은 기존 fixture가 요구한 root `base` 모듈 별칭이 빠진 E0432로 테스트 전에 실패했고, 별칭만 추가했다. product002에서9조건과 일반 빌드는 통과했지만 실제 읽기에서 전체 Source 거부가 발생했다. 당시 원본 code/실패 영수증/바이너리를 보존했다. 통과9조건은 이후 재실행하지 않았다.

700은 별도의 **독립 필드 API/그래프 범위**를 검증했다. 실제32파일에서 다음을 확인했다.

- 실제 public Command API의4표시/2hyperlink·정확한 source block ID/name 결속.
- public field-meaning API의9범위/책갈피 상호참조1개와 source-derived 의미.
- 독립 XML 관측과 캐시 SHA 일치, 원래8개 블록 이름·선택 텍스트 보존.
- 정확한 BOOKMARK begin node로 edge1개, graph JSON 재열기·whole source 재구성.
- Unsupported BOOKMARK8개 및 전체 검증/Native 권한 아님 유지.

성공 영수증은 `evidence/p09-361-block-bookmark700-field-api002.v1.json`,89,992B, SHA `e6a58b22e9d292f55f5ed432c57d1380bf8751e2a114053306380d4e6fe2394b`다. source1076/1076·test/example6 final·cleanup=true·260.047초·CPU최고40.62%·가용RAM최저41.2221%다. 696의 전체 Source 요구 실패는 FAILED로 남기며, 이 독립 필드 증거로 바꾸지 않는다.

## 전체 Source API의 정확한 잔여 경계

기존 `assess_package_source`는 생성 후보8개에서 `REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED`를 유지한다. 한글 저장 후 initial/saved/reopened24개는 부분 Source 응답을 반환하며 status=Incomplete·validation_report=None이다. 어느 쪽도 전체 참조 검증/실행 수용이 아니다. 최초700 field-api001은 모든 단계가 같은 Coverage 오류를 낼 것이라고 잘못 가정해 실패했다. 이를 보존하고 field-api002에서 각 실제 결과를 개별 기록했다. 전체 Source/heading importer의 거부 규칙은 수정하거나 무시하지 않았다.

701의 현재32파일 헤더 관측은 생성 후보마다23개 heading 중17개만 direct이고 나머지는3개 switch의 case/default6개임을 확인했다. Native 저장본은20개 모두 direct다. 조건은 `hp:required-namespace=http://www.hancom.co.kr/hwpml/2021/metatag`, case는 OUTLINE/level8·9·7, default는 NONE/level0이라 서로 동등하지 않다. URL 연도나 제품 이름으로 유효 분기를 추정하지 않는다. 후보 입력의 조건부 정의는 별도 명시적인 미해결/선택 불가 상태 설계가 필요하며, 원래 strict direct heading importer의 coverage를 완화하지 않는다.

701 영수증 `evidence/p09-361-block-bookmark701-heading-observation001.v1.json`은4,479B, SHA `e8d8bd8c508a2f07995c3a962007a6b7d21a55a37d03efadd9ea980ec814fce2`,35/35·cleanup=true·5.5초다. 실제 분기 선택이나 Native 제목 번호 검증은 하지 않았다.

## 이미지 관측 정정

693에서 initial/reopened BMP 전체 파일 SHA가8종 모두 달랐다. 한 번의 도구 미리보기도 흰 화면처럼 표시돼 실제 빈 이미지 여부를 추가 확인했다.697은 원본 BMP를 바꾸지 않고24bit RGB/크기/offset/stride·할당 범위를 확인한 뒤 header/padding을 제외한 top-down pixel rows를 해시했다. **8종 모두 초기/재열기 RGB가 같고, 양쪽 모두 nonwhite 내용이 있다.** 따라서 흰 미리보기를 실제 빈 문서로 판정하지 않는다. 차이는 픽셀 외 영역이며, 파일 전체 해시 차이 자체도 숨기지 않는다. 이 관측은 glyph/text oracle·이동·탐색 일반 수용이 아니다. 본문 참조 재열기 이미지에서는 실제 선택 텍스트가 보였다.

697 영수증 `evidence/p09-361-block-bookmark697-bitmap-observation001.v1.json`은2,928B, SHA `c63a2cb7d54bcab009aff7d734e17ef4d51d5820b1bf3a083b16dabc26c616f3`,18/18·cleanup=true·56초다. 초기 빈 이미지 문제로 남길 근거는 없으며, 일반적인 render/텍스트 평가·탐색 수용 경계는 계속 열린다.

## 다음 로컬 순서와 인계

목표 ACTIVE, 현재 외부 실행 명령·접근 허용 요청 없음.684/690은 모두 소비됐으므로 재실행하지 않는다.

1. 후보 헤더의 조건부 제목 선언을 직접/조건부/분기 미확정으로 명시하는 C02 입력 모델을 설계·검증한다. 임의 default 선택이나 unknown을 빈 제목 목록으로 바꾸지 않는다. 전체 Source 통합 잔여로 유지한다.
2. 이미 통과한 source/field/candidate/capture 증거를 재사용해 C01/C02/C05의 실제 허용 backend·현재 권한/head·입력/실행/출력 채택을 연결한다. 새로 바뀐 경로와 실제 전이만 검사한다.
3. F11의 다른 필요한 대상·이동/이름 변경·내부 hyperlink·필수 화면/의미 검증을 준비해, Native가 필요한 항목을 한 묶음으로 인계한다. 지금8종을 반복하는 작은 실물 재시도는 만들지 않는다.
4. F09/F10과 나머지 P09 closure를 원장 순서로 이어간다. metadata/역사 전체 재검사는 묶음 경계에 한정하고, 실행 code/현재 입력의 fresh 검사는 유지한다. 보호 중단 시 동일 검증 반복 대신 관련 코드/입력 범위를 먼저 최적화한다.

이 성공은32문서 필드 API/현재 고정 target graph 범위이며, 전체 Source 후보 입력·독립 운영 DB/등록/issuer/CAS/실행/출력 채택·F11/P09 완료로 승격하지 않는다.
