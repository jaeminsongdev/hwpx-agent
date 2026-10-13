# P09-95 원본 MEMO 문자열 메타데이터 보존 정책

## 목표와 범위

P09~P20 전체 제품 구현·검증 목표를 유지한다. P09 Gate 전에 P10 새 구현을 시작하지 않는다.
이번 단계는 실제 HWPX 댓글 출력에 앞서 원래 원본 읽기 경로가 MEMO의 metaTag를 거부하던
누락을 수정한다. 댓글의 작성자·시간·표시·해결·좌표·스타일 의미 또는 전체 댓글 제품 완료가 아니다.
사용자가 삭제한 root PLANS.md는 복원하지 않는다.

## 근거와 지원 경계

공식 로컬 OWPML cache commit 1453388472c703a4b299a0834f425cdac16644b9의
OWPML/Class/Para/fieldBegin.cpp는 parameters/subList/metaTag 자식을 등록한다.
MetaTag.h/.cpp의 CMetaTag는 CStringValueObject이며 문자열을 기록하지만 작성자·시간·해결 상태를
해석하지 않는다. HwpMetatagDef.h의 이름 선언도 그 의미를 입증하지 않는다.
공식 구현의 자식 등록은 전체 wire 순서나 설치된 한글에서의 의미 검증으로 승격하지 않는다.

이 제한된 읽기 profile은 MEMO에서 parameters? → subList? → metaTag? 순서를 허용한다.
metaTag는 한 개까지, 마지막에만 허용하며 hp namespace의 정확한 이름, namespace 선언 외
속성 없음, 자식 요소 없음, 원래 SafeXml 정책을 요구한다. 잘못된 순서·중복·다른 namespace·
속성·nested markup·CDATA는 거부한다. 모든 native metaTag 표현을 지원한다고 주장하지 않는다.
비-MEMO 및 hiddenComment의 지원 경계와 원래 typed paragraph reader/writer는 유지한다.

## 실제 제품 코드 경로

- 원래 TextFlowReader의 source-preserving MEMO 분기와 원래 parameters/body 검사를 재사용한다.
  metaTag 전체 XML bytes와 item을 기존 유한 text/item budget에 포함한다. 일반 typed writer에는
  opaque content를 출력할 권한을 부여하지 않는다.
- 원래 ImportedDocumentReviewBodies 관측에 선택적인 ImportedReviewMetaTag를 추가한다.
  원본 위치, 전체 요소의 SHA-256 및 bytes만 저장하고 문자열·JSON·작성자·시간은 노출/해석하지 않는다.
  원래 source_body_observation_sha256와 whole source/graph/observation/receipt 재구성에 결속한다.
- 원래 assembly는 기존 관측 전체를 복제하므로 별도의 importer나 대체 assembly/store를 만들지 않는다.
  메타데이터가 없으면 meta_tag 직렬화 항목을 생략해 기존 관측 wire 모양을 유지한다.
- 원래 StoredFormProvider의 source ACL/quarantine/AEAD/head/scope 재검증을 그대로 사용한다.
  cached sidecar가 현재 권한을 대신하지 않으며 ingest/head commit/publication을 추가하지 않는다.
- native metadata는 계속 UnverifiedNativeMapping이고 author/time 및 visibility/resolution binding은 false다.
  원래 full-document admission은 partial source projection을 계속 거부한다.

## 검증과 보존

신규 package 8개, 기존 경로 내부 budget 2개, 원래 stored provider의 신규 3개 검사는 synthetic
native-format 문자열과 기존 fixtures/services를 사용한다. 실제 captured 원본의 zero-review 검사는
원본 identity 및 부재를 확인할 뿐 positive native 댓글 의미 증거가 아니다. 실제 AES-GCM/권한/
head 코드는 실행하지만 저장소·actor/scanner/keys는 in-memory/synthetic이다.

원래 tests/guards와 whole source를 보존한다. 수정 부모 4개의 전체 preimage 및 실패 테스트
원문 3개를 별도로 보관한다. 기존 지문 고정 실행 파일을 덮어쓰지 않도록 target/p09-95-regression을
사용한다. 읽기 전용 verifier는 이전 checkpoint bytes/hash, 원래 1,149개 raw pin, 변경 부모,
기존 제품 테스트 역변환 및 기존 MEMO body guard 전체 일치를 확인한다. 과거 전체 qualification을
다시 실행했다고 주장하지 않는다. current-source 구성요소 검증은 원래 component 범위다.

한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설치·설정/commit/push를 실행하지 않는다.
실제 source-native author/time/state/style/좌표 결속, HWPX comment lowering, durable SQL 제품 통합,
trusted issuer/atomic execution/publication, P84 SQL 원인, 나머지 P09 의미 및 실제 한글 검증/Gate는 남는다.
