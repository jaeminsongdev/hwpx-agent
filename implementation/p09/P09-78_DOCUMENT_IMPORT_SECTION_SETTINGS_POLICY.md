# P09-78 실제 source-spine의 페이지·단 설정 연결

## 목적과 입력

전체 문서 제품 경로에서 누락된 section 설정을 기존 immutable Source→body/forms→ranges→meanings→catalog→active security graph에 연결한다. P77의 잠긴 실제 입력 36개만 사용하며 원본 PackageGraph와 원본 P05 `PageSetupReader`·`SectionColumnReader`·limits·metrics·enum 의미는 수정하지 않는다. caller page/column/graph, 임의 경로, 기본 설정이나 native 실행을 받지 않는다.

## 전체 원본 순서와 바인딩

- 원래 bounded ZIP에서 실제 source part를 읽어 길이와 전체 SHA에 묶인 출처를 사용한다. 실제 `Source.spine()` 순서로 HS section을 모두 취한다. 파일명 정렬이나 일부 section 선택으로 대체하지 않는다.
- header의 실제 `secCnt`와 전체 section sequence를 원래 `read_sequence_with_header`로 검증한다. 각 section에 원래 page reader와 실제 body width를 적용하고 모든 column span의 원래 definition·metrics·source 순서를 유지한다.
- 실제 section logical ID와 source-part resource ID가 원래 graph와 같아야 한다. section·secPr·pagePr·colPr anchor는 원래 source의 ordinal/fingerprint로 resolve한다. 누락·중복 page, 잘못된 크기·여백·gap·count는 원래 reader 오류를 유지하며 default/첫 항목/opaque fallback으로 숨기지 않는다.
- graph에는 source section order/count, page/column source tree, 원래 body width/height와 partial profile/scope만 추가한다. source tree는 anchor와 이미 검증된 document-data attribute/child 구조이며 XML 문자열·실행 action이 아니다. 원래 page/column types에 serialization derive를 추가하지 않는다.
- 원래 `WIDELY→Portrait`, `NARROWLY→Landscape` 관찰을 그대로 따른다. 이번 source binding이 native layout 방향·page-side start·렌더 정답을 새로 확인한 것은 아니다.

## 검증·권한·보존

원래 P77의 fresh whole-byte identity와 이전 전체 모델 재구성이 먼저 성공해야 한다. 그 immutable source bytes에서 새 settings를 결정적으로 다시 만들어 graph·typed records·receipt 전체를 비교한다. 또 하나의 독립 Source chain을 만들었다고 주장하지 않는다.

저장 서비스는 생성과 cached reuse에서 원래 security/source 검증을 먼저 수행하고, 새 settings 재구성 뒤 원래 authenticated source checkpoint를 다시 수행한다. 마지막 checkpoint는 original scope/head/ACL/quarantine/AEAD/descriptor, 전체 raw byte equality, imported form source와 whole receipt를 확인한다. 같은 immutable bytes에 대한 상위 순수 모델 전체 재구성만 마지막에 중복하지 않는다. 기존 검증 body·guard·assertion은 변경하지 않으며 READ audit 외 ingest/CAS/seal/head write/publication은 없다. 두 head read는 atomic lock이 아니다.

profile과 scope는 각각 단독으로 full-document product context를 거부한다. 새 추가를 제거하면 원래 P77 graph 전체가 동일해야 한다. 변경 전 5개 파일과 초기 오류·diagnostic·최적화 전 새 서비스 source를 whole archives에 보존하고, 4개 code inverse와 이전 source/receipt/원본/native hash를 검증한다.

## 미검증 경계

실제 입력 36개는 기존 generated/readback/historical/native source-output 입력이며 새 한글 실행이 아니다. source page/columns COMPONENT는 전체 settings/importer, 렌더·페이지 배치, native protection/encryption/document signature, 실서비스 PostgreSQL/issuer, committed Source→Result→IR lineage, publication/idempotency/lifecycle/concurrency/crash/recovery/load를 입증하지 않는다.

전체 original qualification/current admission, 남은 field/reference/comment/evaluation/approval, P26 `failed_semantic_non_green`, P62 `16fde8_UNRESOLVED`, `INPUT_CHANGED_RE_ADMISSION_REQUIRED`, full34 `NOT_RUN/0green`, P09 Gate OPEN을 유지한다. Goal ACTIVE이며 P10·한글·COM·UI·native dispatcher·접근허용·stage/commit/push·원본 수정/삭제/이동·trust/config 변경을 수행하지 않는다.
