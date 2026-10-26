# P09 점·블록 책갈피의 공통 source 대상 선택

2026-10-25. 실제670 source capture와673 XML readback,675 core import를 보존한다. P09/A12/A13은 OPEN이며 전체31개 closure 묶음/65기능과 official249의158수용·91대기·next165는 변경하지 않는다. 현재 외부 실행 요청은 없다.

## 구현 범위

`fields/bookmark_authoring_targets.rs`의 `SourceBookmarkAuthoringContext`는 같은 불변 fields에서 점 책갈피와 실제 Prop2 블록 책갈피의 논리 ID를 분류한다. 호출자가 원문 이름이나 block 플래그를 넘겨 대상을 바꿀 수 없다. 기존 POINT SDK 발견 API는 변경하지 않았다.

한 번의 context import에서 논리 ID와 이름 인덱스를 만들고, 점 책갈피만 있는 source에서는 블록 cached-inline 분석을 추가 실행하지 않는다. 전체 문서 그래프를 표시 종류마다 복제하거나 다시 import하지 않는다. 블록 target state는 실제 field import·시작/끝 source anchors·논리 ID·이름 해시·선택 내용 관측에 결속된다.

선택된 점 대상은 기존 세 표시(Page/BookmarkName/RelativePosition)의 명령과 target state를 유지하고 Content를 계속 거부한다. 실제 블록 대상에는 네 표시의 작성 후보를 만들 수 있지만 Native 또는 service 권한은 아니다. ObjectNumber는 두 종류 모두 거부한다. 점·블록 사이 이름 충돌과 같은 종류 안의 중복 이름은 ambiguous이며, 선택 ID만 믿고 이름 충돌을 우회하지 않는다. Debug·영수증에는 원문 이름·텍스트·명령을 노출하지 않는다.

이 코드의 결과는 source-bound SDK 작성 후보이며, 실제 저장 서비스의 권한·현재 head·출력 반영이나 Native Content 양성을 증명하지 않는다. 기존 POINT 경로의 flat display guard를 무조건 제거하지 않았으며 writer 연결은 다음 단계다.

## 678 검증

처음 product001은 라이브러리에서 dev 전용 `hex` 경로를 사용한 E0433으로 테스트 실행 전에 실패했다. 실패 영수증과 당시 새 module·driver 원본 바이트를 보존했다. 제품의 기존 `document_import::hex_digest`로 맞춘 한 줄 외에는 당시 module·검사·다른 제품 코드를 바꾸지 않았다. 불필요한 의존성을 추가하지 않았다.

새12조건은 실제 created/reopened 두 source의8대상×4표시×2hyperlink, 기존 점 여섯 명령·target state 일치, 점 Content 거부, 양쪽 ObjectNumber 거부, 같은 종류/다른 종류 사이 중복 이름, 잘못된 논리 ID, fresh source 변경, 비밀값 비노출, 한도, 선택 내용 변경에 따른 target state 변경, 미관측 parameter profile 거부를 검사한다. 이128개 조합은 source-bound 작성 후보이며 Native 실행128회가 아니다.

[678 product002](evidence/p09-361-bookmark-authoring-targets678-product002.v1.json)은 새12조건 모두 통과·source905/905·실행 파일과 dep-info2final·cleanup=true다.161.188초·시스템 CPU 최고42.77%·가용 RAM 최저44.3102%다. 실제 두 원본의8블록×4표시×2link=128개 source-bound 작성 후보가 예상 SDK 명령과 일치한다. 기존 점6명령과 target state도 기존 context와 일치한다.675의 통과11조건과 Native670은 재실행하지 않았다. 상태는 `QUALIFIED678_SHARED_POINT_BLOCK_SOURCE_TARGET_SELECTION_NOT_WRITER_OR_NATIVE`이며 writer/stored/Native Content 양성은 아직 미완료다.

## 다음 구현 순서

1. source CROSSREF 해석기의 이름 결속을 블록에도 연결한다. 현재 `fields/bookmark_crossref.rs`는 기존 point target import에서만 이름을 찾으므로 블록 command가 Missing으로 남는다. 표시를 읽는 것과 작성 허용은 구분하고, 과거 점 Content source 관측을 임의로 버리지 않는다.
2. `fields/bookmark_insertion.rs`와 command change lowerer가 공통 source 대상 선택기를 사용하도록 연결한다. fresh source proof·문서 보호·원래 선택 run·원본 보존·원자적 output readback은 유지한다.
3. writer의 native ID 예약을 수정한다. 실제670의8블록이 같은 fieldid를 공유하므로 검증된 BOOKMARK profile에서의 공유를 시작/끝 결속 실패로 오인하지 않아야 한다. begin id 중복·잘못된 beginIDRef·다른 미관측 profile은 계속 거부하고 신규 ID는 기존 최대값 밖에서 예약한다.
4. 실제670 원본의 모든 본문 run은 블록 control과 섞여 있다. 원래의 plain-run-only 선택 경계를 억지로 낮추지 않고, 검증용 파생 source에 별도의 삽입 위치를 준비하거나 source 선택 모델을 정식으로 확장한다. 원본 블록 XML과 범위의 바깥 보존을 검증한다.
5. direct/stored 후보·원래 권한·현재 head·출력 경계를 통합 검증한 후, 실제 Content 양성이 필요한 Native 묶음을 준비한다. 외부 실행이 필요해지면 명령을 안내하고 사용자 조건부 지시에 따라 일시정지한다.
