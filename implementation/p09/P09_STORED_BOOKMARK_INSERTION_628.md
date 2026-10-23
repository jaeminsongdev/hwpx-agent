# P09 628 — 현재 저장 원본 결속과 새 삽입 후보 8개

## 확인한 결과

[audit002](evidence/p09-361-stored-bookmark-insertion628-audit002.v1.json)은 627의 최초 삽입을 현재 저장 원본에서 준비하고, 고정8조합의 실제 HWPX 후보 파일을 새 비공개 작업 폴더에 생성한 결과다. 새 삽입의 source/ACL/head/AEAD/quarantine/권한 재확인을 기존 전달 경계에 연결했다.

- 고유 저장 조건8개: 이전 실제 통과7개는 제품·시험 본문의 동일성을 확인해 보존했고, metadata 불변성 확인을 강화한 양성1개만 다시 실행했다. 627의 core15/로컬 제품8개는 반복하지 않았다.
- 일반 빌드와 현재 저장 원본의8조합을 실행했다. 출력8개의 전체 바이트 SHA256은 각각 627의 검증된 후보와 정확히 일치한다.
- 입력930개 시작/종료 해시 일치, compiled/새 출력12개 최종 확인, cleanup true. 전체193.453초, 시스템 CPU 최고16.99%, 가용 RAM 최저45.2989%다.
- 실제 한글·COM·Native·운영 SQL을 실행하지 않았고 원본/head를 변경하거나 사용자 revision으로 게시하지 않았다.

새 준비 파일은 [고정8개 명세](evidence/p09-361-stored-bookmark-insertion628-prepared-batch.v1.json)에 결속돼 있다. 총117194bytes이며 비공개 `evidence/private/p09-361-bookmark-insertion628-prepared-001/case-01.hwpx`~`case-08.hwpx`에 보존했다. 이미 생성한 generation001은 덮어쓰거나 다시 실행하지 않는다.

## 제품 코드 경계

`StoredImportedDocumentForms::into_bookmark_insertion_candidate`는 모델을 소유권으로 인수하고, 현재 DocWrite 권한·provider scope·AEAD·quarantine·head·digest와 원본 전체 바이트를 확인한다. 새 출력은 기존 627 lowerer로 한 번만 만든다. 전달 직전과 writer callback 안에서도 기존 `final_access`의 동일한 검사를 적용한다. 권한 철회·원본 변경 등의 실패 이후 같은 후보를 복구/재사용하지 못하도록 차단한다.

기존 guard의 공개 범위만 `pub(super)`로 바꿨고 본문은 변경하지 않았다. 다른 기존 Rust 제품 본문과 627의 생성 경로는 동일함을 확인했다. 재전달 때마다 graph import·lowering·출력 복제를 반복하지 않는다. 기존 full-context/signed-route 거부는 해제하지 않았다.

공통 fixture는 실제 ArtifactService/AEAD/RevisionService 구현을 사용하지만 repository·scanner·키·sealed commit은 격리된 시험 모델이다. 운영 SQL·키 custody·등록된 실행 route/CAS 자격으로 확대하지 않는다. `require_current_product_route`는 현재 입력을 확인해도 계속 `RouteUnqualified`다.

## 원 실패 보존

[audit001](evidence/p09-361-stored-bookmark-insertion628-audit001.v1.json)의8개 시험 본문은 통과했지만 사용하지 않은 import 경고 때문에 전체 검증은 FAILED다. 경고를 숨기지 않고 양성 시험에 source artifact metadata 전후 동일성 확인을 추가했다. 수정한1개만 다시 실행했고 이전7개의 본문·helper·제품 소스와 executable/dep-info 증거를 결속했다. 원 영수증과 source/archive를 보존했다.

## 아직 확인하지 않은 것

새 field의 기존 표시 문자열은 **계산/갱신된 초기 결과가 아니다**. Native 초기 계산·표시/대상 이동·이름 변경 보존·저장/독립 재열기·렌더, 다른 P09 대상, 실제 허용 실행/출력 경계는 남는다. F11/C05 전체나 P09 Gate는 닫지 않는다.

단순 companion health 조회의 `automation_enabled:false`와 선언된 target profile은 실행 중인 한글의 세션·license·Native 자격이 아니다. 자동화를 켜거나 보호된 설정을 수정하지 않았다.

## 다음 검사

사용자가 실제 검증 지원 가능하다고 답했고 이후 “검사 준비되면 명령을 주고 목표를 멈추라”고 요청했다. [629 준비 검사](P09_BOOKMARK_NATIVE_PREPARATION_629.md)는 이8개 파일의 외부 실행 환경을 읽기 전용으로 조사한다. 실제8종 실행기는 별도 준비·검증과 실행 범위 확인이 남아 있다. 과거 소비001~010/Native008~011의 실행 권한을 재사용하지 않는다.
