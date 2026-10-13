# P09-71 실제 저장소의 원본 기반 폼 읽기 검증 정책

## 목표와 범위

P70의 `StoredFormProvider::import_actual_forms`와 fresh policy verification을 실제 `LocalPostgresMetadataRepository`/`LocalPostgresRevisionRepository` 및 `LocalEncryptedBlobStore`에 연결한다. 원래 P65 worker/job/lease/authorization/CAS/complete 절차로 만든 sealed Result를 읽으며, 이미 저장된 synthetic caller IR를 실제 원본 importer의 입력으로 사용하지 않는다.

실제 captured/derived HWPX 원본의 전체 graph/observations 및 명시적 TEST 정책 결합 상태를 원래 direct importer와 비교한다. 서로 다른 DB의 artifact UUID는 다르므로 receipt 동일성은 같은 DB의 독립 child process·PostgreSQL 재시작·ACL 복구 사이에서 검증한다. 새 모드의 `candidate_sha256`는 비워 두고, partial import/policy receipt SHA만 기록한다.

## 변경과 불변 조건

- 기존 probe root에는 새 child module 및 세 mode dispatch만 추가한다. 기존 seed/verify/denied/safety 본문과 fixture/worker/safety helper는 변경하지 않는다.
- 기존 Python driver는 명시적으로 receipt v2로 확장한다. 기존 SQL53, Rust116, read-only postconditions5, schema1~19, 역할 권한, protocol/check 순서, cleanup owner 검사는 유지한다. 새로운 actual import check는 별도 이름과 범위를 갖는다.
- 전체 pre-change root/driver/PLANS 및 새 helper의 실패 당시 소스를 별도 archive에 보존한다. 선언된 추가 부분을 역변환했을 때 원래 root/driver의 whole bytes/SHA가 정확히 일치해야 한다.
- 실제 Result read의 tenant/project/branch/subject ACL, descriptor/scanner/quarantine/AEAD/digest/head 검사를 완화하지 않는다. 잘못된 key, project ACL 철회, Result ACL 철회는 원래 service error로 실패해야 한다. Result ACL은 실패 여부와 무관하게 원래 permissions로 복구한다.
- source import와 policy verification은 head/ingest 수를 바꾸지 않는다. 기존 정상 read audit만 추가한다. 원래 synthetic IR의 quarantine 이후에도 실제 Result 원본 읽기는 독립적으로 성공해야 한다.
- 모든 actual policy-bound graph는 기존 `FullDocumentFormContext`에서 partial Projection으로 거부된다. 임의 source map/state/graph, raw path, relabel, dedup 우회 또는 새로운 signed route를 허용하지 않는다.

## 실행과 정리

기존에 설치된 digest-pinned PostgreSQL18.4 이미지만 사용하며 image pull·기존 DB·host file mount·외부 endpoint·한글·COM·UI·접근 허용창을 사용하지 않는다. 각 실행은 unique UUID label/container/volume, loopback ephemeral port, 자원 제한 및 exact temporary blob root를 갖는다. 기존 driver의 owner/image/name/root/link 검사 뒤 해당 실행의 disposable resources만 제거하고 결과에 existence 검증을 남긴다. 재생성 가능한 fixture ciphertext 제거이며 원본·private/native 증거·실패 기록 삭제가 아니다.

독립 DB 두 개에서 같은 current source/executable을 사용한다. 각 DB에서 새 actual checks139와 원래 Rust116을 구분한다. 반복 check 수를 서로 다른 기능·fixture·native 실행 수로 부풀리지 않는다. Rust named regression 및 strict lint는 별도로 실행한다.

## 승인하지 않는 주장

P65 prior Source/scanner/keys/whole caller IR/baseline execution authority 및 이번에 공급하는 정책은 synthetic/TEST다. 실제 PostgreSQL·AES-GCM 파일 읽기는 real scanner·external policy issuer·complete source/result/IR provenance·previous-result input commit·full field/note/reference/catalog/security importer·ExecutionManifest·publication·idempotency·IR lifecycle·crash/load·whole historical qualification replay·native/render/differential·P09 Gate를 증명하지 않는다.

P62 `16fde8` 원인은 UNRESOLVED로 유지한다. current native admission은 `INPUT_CHANGED_RE_ADMISSION_REQUIRED`, full34는 `NOT_RUN/0green`이다. Goal ACTIVE/P09 OPEN/no P10 및 접근 허용 금지를 유지한다.
