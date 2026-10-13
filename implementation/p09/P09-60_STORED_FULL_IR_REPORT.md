# P09-60 저장된 전체 IR의 실제 서비스 조회·폼 준비

2026-10-03. 이전 P59는 caller-supplied full graph 준비까지만 구현했다. 이번에는
IR 전용 artifact와 immutable revision binding, actual-service IR 조회·fresh 검증을
추가했다. 접근 허용 금지는 유지했고 Hwp/COM/UI/native dispatcher는 실행하지 않았다.

## 구현 결과

- 별도 `document_ir` artifact 종류/key namespace와 PostgreSQL decoder를 추가했다.
  source retention bucket을 사용한다. 실제 DB 정책/GC/mirror의 IR lifecycle은 미검증이다.
- revision request에 optional `FullDocumentIrBinding`4 fields를 추가해 canonical CAS
  digest에 포함하고 node seal 때 함께 보존한다. old None wire는 그대로 유지한다.
  source/result/diff alias와 중복 부착을 거부하고 strict wire parser를 유지한다.
- `StoredFormProvider::prepare_full_document_json`은 실제 현재 node의 IR만 선택한다.
  원래 source read와 별도로 IR ACL/available/verified/non-quarantined/media/전체SHA/
  AEAD를 검사한다. canonical JSON/schema/graph digest/result-package digest를 검사한
  뒤 P59 actual compiler/full graph 업데이트를 사용한다. 새 source/result/IR를 쓰지 않는다.
- fresh verify는 IR까지 실제 다시 다운로드한다. 독립적인 IR-only ACL 철회/암호문
  손상, 잘못된 IR kind/media/3digests, duplicate properties/비정규 JSON, 다른 document/
  inventory projection, stale head/access 철회를 거부한다. 현재 signed route는 거부한다.
- 실제 source package/IR와 graph의 non-form 내용이 보존되는 named service tests를
  추가했다. receipt/debug는 문서 값/경로/ID를 내보내지 않는다.

## 실제 검증 범위

- 최종 actual named product5 suites62 + service3 crates73 = **135 PASS**, fail/ignored/
  filtered0(terminal57443/chunk7133a4 및 최종 poll exit0). 신규14 = stored IR8 + revision
  binding/object-key5 + retention policy1. doctest3 suites는0 tests이며 통과 수에 넣지 않았다.
- 관련4 crates `cargo clippy --locked --offline ... --lib --tests -- -D warnings` exit0
  (8dad7b). 새Rust4 files rustfmt, scoped diff-check 및 임시 container/Hwp count0(5225ac).
  full workspace/whole ordinary suites/phase qualification을 주장하지 않는다.
- 최초 `E0599` ArtifactId type 혼동을 고쳤다. 추가 enum 때문에 늘어난 기존 PostgreSQL
  decode_record를 helper로 분리했고 retention 동일 match arms를 병합했다. lint allow나
  검증 약화는 없으며 실패 요약을 별도 evidence에 보존했다.
- 수정 전8파일 전체 bytes를 `source-archive/p09-60-pre-stored-full-ir/`에 보존했다.
  P59의2 origins와 합쳐 원래1551 inputs/51047460 bytes 전부 실제 original SHA와
  일치한다(66acd4). 과거 native75개도 actual original binder로 전부 hash 일치.
  이것은 archive-origin 전체 hash 확인이며 whole predecessor CLI 재현은 아니다.
- 새 source-progress receipt10490 bytes/SHA
  `63f05db52c0c99a6024bdb24f7f557a85ae20edcc12a27544e1b9504bd161b56`
  의 actual source21/archive10 pins를 독립 확인했다(13c56a). 같은 검사에서 current SQL
  fixture FAIL/Hwp0/owned SQL containers0와 PLANS diff-check exit0를 확인했다.

## PostgreSQL: 부분 통과와 실제 실패

새 `0018_p09_full_document_ir` migration은 과거17개를 수정하지 않는다. optional IR
revision columns/FK/shape/actual artifact binding guard와 원래v1 CAS의5 additive changes
아래 exact control-flow successor를 추가했다. 새 function은 PUBLIC에 공개하지 않는다.

기존 고정18.4 image만 사용한 **격리 Docker DB**에서 다음을 실제 확인했다.

- schema1..18 적용 및 실제 registry1..18 확인: 통과.
- explicit gate 없는 down 거부: 통과.
- IR 데이터가 없는 경우 explicit down 및 reapply: 통과.
- 전체9 assertion IR commit fixture: **FAIL**.
  처음에는 metadata artifact/ACL의 deferred manager invariant 때문에 실패했다. 테스트
  fixture 전체를 정상 단일 transaction으로 묶어 그 invariant를 유지한 뒤 진행했다.
  다음 실제 실패는 `IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED`였다. 현재 idempotency
  authorization gate가 새 CAS leaf도 정상 차단한다. gate/trigger/authorization row를
  조작하지 않았다. IR commit/데이터 보존 rollback assertions는 완료로 표시하지 않는다.

initial/current failure receipts와 최초 harness/fixture bytes를 보존했다. 총5개의 임시
owned-run 컨테이너는 exact label/name/image 확인 후 정리했고 network none/tmpfs만
사용했다. host ports/host file mounts/image pull/실제 제품 DB 변경은 없다.
실패 SQL stdout/stderr는 hash와 상수 code만 기록했으며 전체 로그/비밀 값은 내보내지 않았다.

## 남은 일과 다음 실제 작업

1. 실제 `commit_idempotent_revision_cas_v2`의 job/lease/fence/commit-authorization 경로를
   full IR successor에 연결하고 전체 SQL fixture를 통과시켜야 한다. fake auth row/session
   bit, 기존 guard 제거, schema3로 시험 범위를 줄이기 등으로 대체하지 않는다.
2. 현재 revision repository의 durable PostgreSQL Rust adapter/full IR node decode와
   top-level stored product request를 연결해야 한다. 이번 positive Rust service tests의
   revision repository는 in-memory 구현이며 durable end-to-end 제품 증거가 아니다.
3. IR 내용은 caller/test가 제공한 graph다. 전체 HWPX full importer/provenance, licensed
   native 의미/저장·재열기/full-page render/차등, signed form route/manifest/idempotent
   publication, original920pixel repair 및 P09 Gate는 미완료다.
4. P48–P58 native source admission은 여전히 INPUT_CHANGED다. 10 explicit archive origins
   를 genuine whole predecessor CLI/source replay에 결합하고 새 current epoch admission을
   닫아야 한다. 현재 full34가 실행 준비됐다고 말하지 않는다. 사용자 허용 후에도 작은
   permission batches 없이 SDK17→automation15+2의 한 번의 전체 큐만 사용한다.

Goal ACTIVE/0 green/P09 Gate open이며 P10으로 넘어가지 않는다.
