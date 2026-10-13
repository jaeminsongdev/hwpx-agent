# P09-96 실제 memoPr 스타일 출력 정책

P09~P20 전체 제품 목표를 유지하며 P09 Gate 전에 P10 새 구현을 시작하지 않는다.
이번 단계는 댓글 HWPX 출력에 필요한 기존 memoPr 스타일 7개 속성의 실제 패키지 출력이다.
작성자·시간·표시·해결·숨은 설명 toggle·댓글 삽입/body/좌표를 추정해 출력하지 않는다.
전체 댓글 모델/컴파일러 준비와 native 출력의 완전한 통합 및 제품 acceptance는 남는다.

## 공식 근거와 실제 구현

공식 OWPML commit 1453388472c703a4b299a0834f425cdac16644b9의 MemoShapeType.cpp는
width/lineWidth/lineType/lineColor/fillColor/activeColor/memoType을 기록한다. enumdef.h의
LineWidthType16/LineType2 18/MemoType4를 원래 domain enums와 정확히 대응한다.
폭은 native unsigned 값이며, lineWidth는 mm 문자열이 아니라 ordinal 0..15다.
NOMAL spelling을 출력하고 None 색 및 명시적 24-bit RGB를 지원한다. 작성자·시간·상태의
저장 근거는 이 코드로 확인되지 않으므로 별개로 unverified를 유지한다.
근거 URL: https://github.com/hancom-io/hwpx-owpml-model/blob/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Head/MemoShapeType.cpp

원래 ID index에 head namespace의 memoPr/id를 기존 MemoShape declaration kind로 추가한다.
기존 memoShape 선언과 모든 중복·dangling·wrong-type·namespace 검사는 유지한다. 없는
스타일이나 section reference를 fake definition/default로 만들지 않는다.

원래 ImportedDocumentCatalog의 실제 memo definition anchor로만 선택한다. Caller는 XML,
byte offset, 새 ID, metadata 또는 권한을 주입하지 못한다. 기존 source/whole catalog를
재검증하고 원래 PreservingPatchEngine으로 선택된 7개 속성 값만 변경한다. 의미가 같은 숫자
표기/color casing은 정규화하지 않고 no-op 전체 요청은 거부한다. ID/unknown 속성/namespace/
다른 스타일/패키지 부분은 보존한다. 원래 source import → forms → fields → semantics → catalog로
출력을 다시 읽는다. 전체 패키지 graph/preservation/ID closure는 원래 writer가 검증한다.

일반 CoreV1은 실제 preview text/paired-field 문단을 지원하는 profile이 아니었다. 이 출력은
원래 Hancom2020 FormulaV3 ID profile과 preview-text-v2 preservation을 명시적으로 사용한다.
이는 원래 table/field/ID 검사를 추가 적용하는 profile이며 CoreV1을 약화하거나 unknown ID
검사를 건너뛰는 fallback이 아니다.

원래 PackageArtifact에 verify 후 callback으로만 bytes를 제공하는 API를 추가한다. 무검사 raw
getter나 새로운 ZIP writer는 없다. 원래 StoredImportedCatalog의 준비/조회는 기존 source
scope/ACL/quarantine/AEAD/head/catalog 검사를 전후 수행한다. Cached output은 full lowering
replay와 원래 artifact 검증 후에만 callback으로 제공한다. 권한/버전 변경 후 callback을 실행하지
않는다. 이는 atomic lease, 전체 보호 정책 또는 publication 권한이 아니며 제품 route는 거부한다.

## 검증·보존·미완료

기존 builder/memo fixture를 그대로 사용한 synthetic native-format 검사다. 16+18+4 각각의
enum 값을 검사하지만 그 Cartesian product 전체 또는 설치된 한글의 rendering 결과는 아니다.
기존 캡처36개의 memo definition 부재도 그대로다. 실제 native positive style capture로 세지 않는다.
원래 service/AES-GCM은 실행하지만 repositories/actor/scanner/keys는 in-memory/fixture다.

수정 전 부모6개 전체를 보관한다. 원래 ID 검사와 writer body, 두 catalog body, 기존 테스트 body는
정확한 역변환으로 확인한다. Fixture module은 중복 선언 없이 재사용하도록 parent-only visibility를
추가한다. 초기 Core profile 실패/새 테스트 warning/lint 실패를 기록하고 최초 새 파일4개를 보관한다.
target/p09-96-package와 target/p09-96-regression을 사용해 과거 실행 파일을 덮어쓰지 않는다.

최종 snapshot은 이전 whole checkpoint의 정확한 identity를 상속한다. source delta18,
부모/최초 실패 archive10, predecessor receipt2, 이번 실제 실행 test executable9의 경로
전체와 raw bytes를 요구한다. 일부 파일만 나열하거나 다른 정상 파일로 치환해도 거부한다.
815는 source803 중 변경6 + 신규12의 현재 목록 수이며 제품 기능/완료 수가 아니다.

HWPX 전체 댓글 출력, native metadata/좌표와 full typed state/compiler 연결, trusted issuer,
보호·atomic execution·게시·durable SQL 제품 통합, P84 SQL 원인, 나머지 P09 의미, actual 한글
저장·재열기/render/differential 및 P09 Gate는 남는다. 한글/COM/UI/접근허용/실제 SQL/운영·trust DB/
설치·설정/commit/push를 하지 않는다. root PLANS.md는 사용자 삭제 상태를 유지한다.
