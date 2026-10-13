# P09-60 실제 서비스의 저장된 전체 IR 폼 준비

2026-10-03. P59 호출자 graph 준비를 실제 artifact/revision 서비스 조회로 연결한다.
SOURCE/component 및 named regression 범위다. full importer, top-level product request,
durable Rust revision adapter, native route/manifest/CAS/idempotency/publication/Gate는
미검증이다. 새 PostgreSQL full-IR CAS의 실제 idempotency 연결 검사도 FAIL로 유지한다.

## 불변 연결과 실제 읽기

- `ArtifactKind::DocumentIr`/`document_ir`는 별도 encrypted object namespace/AAD 종류다.
  HWPX result/source/diff를 IR로 재해석하지 않는다. PostgreSQL artifact row decoder도
  새 종류를 인식한다. retention은 기존 source 정책 bucket을 사용하고 짧은 preview/diff
  TTL에 배정하지 않는다. durable IR 참조 등록/GC/mirror qualification을 주장하지 않는다.
- `FullDocumentIrBinding`의 artifact ID/raw SHA/result-package SHA/canonical-graph SHA를
  CAS request에 포함한다. None은 serialize하지 않아 옛 request wire/hash를 보존한다.
  strict deserialization/alias 거부를 적용하고 CAS로 seal된 node에 연결을 함께 보존한다.
  immutable node를 나중에 수정하지 않는다. metadata Verified는 실제 import 증거가 아니다.
- provider는 현재 head의 실제 immutable node가 선택한 IR만 조회한다. public action에서
  artifact ID/path/scanner verdict/권한 boolean을 받아 IR 선택을 바꾸지 않는다.
  tenant/subject/project/branch/document scope, head/generation/result ID, package digest를
  검사하고 **독립적인 IR ACL/state/media/digest/AEAD download**를 수행한다.
- IR media는 `application/vnd.hwpx-agent.document-graph+json`, available/verified/
  non-quarantined/1..32MiB다. 실제 전체 graph/schema/reference/limits를 검사한다.
  raw bytes가 exact canonical JSON이어야 하므로 duplicate key/공백 alias/추가값을
  단순 deserialize 결과로 승격하지 않는다. artifact SHA/graph SHA/package SHA를 결합한다.
- P59 실제 typed operation/full-graph compiler로 변경하고 source/target/receipt를 fresh
  재다운로드/재구성하여 비교한다. prepare/verify는 artifact ingest/head commit/key claim을
  수행하지 않는다. source graph/package는 그대로다. 현재 signed form route는 항상 거부한다.
- receipt/debug는 digest/count/qualification만 공개한다. 원본 문서 값/경로/native ID/
  artifact public ID를 노출하지 않는다. artifact scanner pass를 licensed native import로
  취급하지 않는다. 두 head read는 원자적 CAS나 atomic publication을 증명하지 않는다.

## DB 경계

- 기존17 migration은 수정하지 않는다. 새 schema18 `p09.full_document_ir_v1`만 추가한다.
  IR 종류/4개 optional revision columns/tenant FK/complete-or-null shape/typed available
  artifact binding guard를 적용한다. 기존 immutable revision trigger를 유지한다.
- 새 CAS leaf는 원래v1 control flow를 five exact additive changes 아래 보존한다.
  하지만 현 schema의 **idempotency authorization gate를 통과하지 못하므로 실제 커밋
  qualification은 FAIL**다. 실제 job/lease/authorization wrapper를 연결하기 전 실행 준비
  완료로 표시하지 않는다. session authorization bit/가짜 authorization row/trigger disable로
  테스트를 통과시키지 않는다. 새 DB function은 PUBLIC 권한을 부여하지 않는다.
- down은 explicit gate 및 exact version을 요구하고 IR artifact/link 데이터가 존재하면
  거부한다. 기존 empty-schema destructive rollback protocol은 격리 DB에서만 시험한다.
  실제 제품 DB에는 migration/up/down/fixtures를 적용하지 않는다.
- SQL metadata fixture의 가상 size/nonce/digest/Verified는 테스트 자료이지 실제 blob,
  HWPX 의미/native/import/issuer 증거가 아니다. 전체9-assertion marker는 실패 유지.

## 검증과 보존

- 변경 전 기존8 source 전체 bytes와 새 SQL harness/fixture의 최초 실패 bytes를 별도
  archive로 보존한다. P59의2 archive origins까지 결합해 원래1551-file/51047460-byte
  source graph의 전체 hash 보존을 검사한다. 이것은 whole old CLI 재현이 아니다.
- 실제 named product5 suites62 + artifact/revision/retention3 service suites73 =135 PASS,
  신규14 tests 포함. 관련4 crate strict clippy `-D warnings`, 새Rust4 files rustfmt 검사.
  full workspace/whole ordinary suites/P09 phase qualification으로 확대하지 않는다.
- 고정 PostgreSQL18.4 image를 재사용하고 network none, tmpfs, no host mounts/ports,
  exact owned-run label/name/image로 실행·정리한다. 기존 DB/컨테이너/원본에는 접근하지 않는다.
  migration1..18 및 empty-IR rollback/reapply는 실제 통과, IR commit fixture는 실제 FAIL.
- 모든 초기 Rust/SQL 실패를 보존한다. Hwp/COM/UI/native dispatcher는 실행하지 않는다.
  기존 native75 및 frozen receipts/guards를 보존한다. current source admission은 여전히
  INPUT_CHANGED/RE_ADMISSION_REQUIRED, P09 Gate open, Goal ACTIVE, P10 진행 금지다.
