# P09 블록 참조 해석·작성·저장 후보 연결

2026-10-25.670/673/675/678의 성공과 실패 원본을 보존한다. P09/A12/A13은 OPEN이며 전체31개 closure 묶음/65기능과 official249=158수용·91대기·next165는 변경하지 않는다. 현재 외부 Native 실행 요청은 없다.

## 변경과 확인 경계

`fields/bookmark_crossref.rs`는 기존 point 이름 인덱스를 재사용하면서, 실제 BOOKMARK Prop2 필드가 있을 때만 블록 인벤토리를 추가한다. 이름이 두 종류에 함께 존재하거나 같은 종류 안에서 중복되면 ambiguous다. 블록 target state는676에서 쓰던 동일한 계산 함수를 공유한다. source 표시 해석과 작성 허용은 구분하며, 기존 점 Content의 저장된 command 관측은 버리지 않는다. 점 source만 있는 기존 직렬화에는 새 optional block receipt를 출력하지 않는다.

공통 insertion/command-change lowerer는676의 source 논리 ID 기반 대상 선택기를 사용한다. direct/stored wrapper의 일괄 POINT-only display 필터를 이 원래 protected lowerer의 실제 대상별 판정으로 교체했다. 쓰기 scope·fresh ACL/quarantine/AEAD/head·source reconstruction·문서 보호·최종 access·기존 후보 거부 latch는 유지한다. raw SDK 발견이 실행 권한이 되지 않는다.

### ID 규칙

실제670의8블록은 같은 fieldid를 공유한다. 기존 shape/v6의 FieldInstance 전역 고유성 규칙은 이 source를 거부한다. 기존 규칙은 변경하지 않고 `hancom_2020_block_bookmark_v12`를 별도로 추가했다. 이 규칙은 scoped-font union 위에서 Native670의 단일 문단 BOOKMARK Prop2만 취급한다. 각 필드의 다음 사항을 검증한 뒤 fieldid를 paired scalar로 분류한다.

- 유일한 numeric begin ID, 정확한 ctrl/run/p 위치와 parameters cnt1/name-empty/Prop2 구조.
- end의 beginIDRef가 실제 begin ID를 참조하며 begin 뒤·같은 문단에 존재함.
- 시작·끝 fieldid 값 일치, end 하나만 존재하고 열린 pair가 남지 않음.

begin ID는 계속 일반 ID 인덱스의 고유 식별자다. 다른 종류 필드의 fieldid 중복 거부는 유지한다. writer는 현재 source의 모든 BOOKMARK profile admission을 마친 뒤에만 공유값을 허용하고, 신규 begin ID/fieldid는 기존 최대값 밖에서 예약한다. 기존 point-only 문서는 기존 ID profile을 사용한다.

### 원본과 삽입 위치

실제670 원본의8본문 run은 control과 텍스트가 섞여 있다. 원래 plain-run 선택 경계를 완화하지 않는다. 테스트는 원본 whole-file SHA를 확인하고 메모리의 파생 source에 별도 마지막 문단/일반 텍스트 run만 추가한다. 원본 HWPX·기존 section 본문·나머지 part payload를 보존하며, 이를 새 Native source 성공으로 부르지 않는다.

## 검증680

대상은 새 core writer/ID profile10조건,676에서 직접 영향받는3조건, 새 stored3조건과 기존 POINT admission639의 직접 영향10조건이다. 무관한 기존676의9조건과675의11조건,249 대기열,Native670은 반복하지 않는다. 저장 테스트의 repositories/scanner/commits는 메모리 fixture이며 운영 DB·등록 issuer·실행 경로의 증거가 아니다.

첫 product001은 command-change receipt가 옛 target getter를 호출한 E0599로 테스트 전 컴파일에서 실패했다. 실패 영수증과 당시 변경 module/driver를 보존했다. product002는 새 target receipt의 같은 논리 ID 해시 필드에 접근하도록 한 줄을 수정하고 나머지 code/test 입력의 동일성을 확인한다.

product002/003은 새 테스트 보조 코드가 원래 crate-private XML 접근기를 사용한 오류(E0624) 및 테스트 error 변환(E0277)으로 테스트 실행 전에 멈췄다. 원본 source/test/driver와 실패 영수증을 보존했다. 제품 API를 공개하거나 결과 비교를 없애지 않고, fixture에 원래 ZIP bytes를 전달해 해당 part의 SHA가 parser의 original SHA와 같은지 확인한 후 같은 표시 텍스트 byte span을 비교하도록 수정했다. 제품 라이브러리는 이 fixture 수정에서 변경하지 않았다.

[680 product004](evidence/p09-361-block-bookmark-authoring680-product004.v1.json)은 새 core10·새 stored3·직접 영향받는 context3/기존 POINT10의 총26조건을 모두 통과했다. source931/931·세 실행 파일/dep-info6final·cleanup=true,225.485초·시스템 CPU 최고32.62%·가용 RAM 최저48.2802%다. 자원 보호 중단이 아니다. 기존 무관한 context9·core import675의11조건·249·Native670은 반복하지 않았다.

확인한 결과는 다음과 같다.

- 실제 원본은 v6에서 중복 fieldid로 거부되고 새 strict v12에서 시작 ID8개를 유지하며 통과한다. 잘못된 끝 scalar·begin ID 중복·다른 Prop·다른 문단 pair·다른 필드 종류의 중복 instance ID는 거부한다.
- Native670 파생 source에서 두 link 옵션의 Content 참조를 작성하고 source readback이 실제 블록으로 Bound된다.8개 블록의 이름·선택 내용은 보존되며 원래 혼합 run은 여전히 선택 불가다. command 변경도 새 block resolution을 사용하고 기존 cache를 갱신하지 않는다.
- 실제 ArtifactService/RevisionService 클래스를 쓰는 메모리 repository fixture에서 block Content 후보를 준비·반출할 수 있고 metadata/head를 변경하지 않는다. write scope가 없으면 거부하고, 최종 반출 전에 head가 바뀌면 거부·이후 재사용 latch를 유지한다.
- 기존 POINT의6유효 출력 byte digest, Content 거부, source drift·권한 우선순위와 저장 후보 동작은 유지된다.

상태는 `QUALIFIED680_BLOCK_SOURCE_BINDING_WRITER_AND_STORED_CANDIDATES_NOT_NATIVE_OR_P09`다. 이는 실제 source에 기반한 로컬 제품 후보 경로의 검증이며 Native Content 표시·운영 issuer/DB·등록/CAS·실행/출력 채택·전체 F11/P09 완료가 아니다.

다음은 제품 경로로 고정8조합의 파일을 준비하고 source/공통 writer 보존을 결속한 뒤, 새 Native 묶음에서 저장·독립 재열기·실제 Content 표시를 확인하는 것이다. 기존 Native670/과거 실패를 재실행하지 않는다. 전체 P09의 다른 기능·backend/출력·이동/이름 변경·탐색도 남으며 목표 ACTIVE다.
