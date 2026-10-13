# P09-65 실제 DB·암호화 파일 full-IR 요청 검증 결과

- 일자: 2026-10-04
- 상태: **현재 제품 라이브러리 full-IR 준비 요청의 bounded actual PostgreSQL + encrypted filesystem acceptance PASS / importer·실행·publication·native·P09 Gate 미완료**.
- Goal ACTIVE, P10 보류. Hwp COM/UI/native dispatcher/접근 허용창을 실행하지 않았다.
- 정책: [P09-65_DURABLE_FULL_REQUEST_POLICY.md](P09-65_DURABLE_FULL_REQUEST_POLICY.md).

## 실제 경로

새 example은 실제 LocalPostgresMetadataRepository/LocalEncryptedBlobStore/LocalPostgresRevisionRepository와 기존 P64 strict product request/provider/full-graph compiler를 호출한다. source/result/IR/receipt 모두 **실제 ArtifactService ingest·암호화 파일·metadata·ACL**을 사용했다. revision root는 actual registered worker/job/lease/attempt/fence authorization과 원래 schema19 wrapper/CAS/complete를 통과하여 생성했다. raw artifact metadata insert나 가짜 authorization ID를 사용하지 않았다.

단, prior Source payload와 baseline operation/validation/receipt/manifest authority, scanner/keys, graph는 **synthetic fixture**다. Result는 원래 locked HWPX source이며 IR은 test-only caller graph다. 이것은 실제 native 전체 문서 importer/provenance나 이전 Result를 다음 input으로 쓰는 chain의 구현·검증이 아니다. 준비한 후보를 새로운 Result/IR로 ingest/commit/publication한 것도 아니다. CLI executable에 새 승인 실행 route를 추가하지 않았다.

## 독립 실제 실행

| 실제 실행 | 결과 |
|---|---|
| a042f6 | 최종 source59 + 별도 executable pin. SQL53/새 read-only postconditions5/Rust116 executed assertions PASS, exit0 |
| 70b1cd | 독립 새 DB에서 같은59 sources/같은 executable/같은4 HWPX candidate hashes. 동일 범위 다시 PASS, exit0 |

Rust116은 seed32 + independent verify24 + restart verify24 + project-ACL denied4 + restored verify24 + safety8이다. 반복 fresh checks를 포함하며 116개 독립 제품 기능이나 P09 완료율이 아니다. run 내부의 receipt/candidate digest는 프로세스/DB restart 뒤 exact였다. 서로 다른 DB에서 생성된 artifact UUID 때문에 전역 receipt identity까지 같다고 주장하지 않는다.

- 네 cases의 whole HWPX bytes는 기존 고정 output과 exact였다. whole-graph source/base digest/plan과 **test-only graph의 form state 이외 모든 필드**를 대조했다.
- 실제 암호화 파일에서 package/IR ciphertext를 읽어 plaintext와 다름/tag 길이를 확인했다. 잘못된 AES key의 실제 file-backed download는 거부됐다. 이것은 physical disk bit corruption/전원 손실의 검증은 아니다.
- 실제 project ACL 회수→네 요청 모두 거부→복구→fresh 프로세스 재검증.
- 실제 IR ACL 회수→fresh route 이전 거부→Result read 유지→ACL 복구 후 fresh verify.
- 실제 IR quarantine으로 encrypted object 이동/state 변경 후 fresh verify 거부, Result read/head/ingest count 유지.
- strict prepare/fresh verify/denied route에서 candidate ingest/commit/publication이 없음을 실제 metadata audit와 branch head로 검사했다. READ audits는 정상 추가됐다.
- root rows4/seals4/commit receipts4/IR intents4/jobs succeeded4를 admin read-only SQL로 확인했다. 원래 SQL28/P61 SQL25와 admission guards는 그대로다.

## 수정한 결손과 원래 실패

- c698a8/866ea3: 새 fixture copy의 explicit imports가 실제 public export 위치와 달라 E0432/E0603였다. domain-ir root exports로 수정했다. package/domain exports는 바꾸지 않았다.
- c4be12/41fe09: 첫 실제 DB·진단 재실행은 RECEIVE_LEASE SQLSTATE23505. 새 helper가 매 case마다 동일 worker를 다시 register했다. 원래 register 함수는 WORKER_ALREADY_REGISTERED를 강제하므로, **한 worker 등록 뒤 네 job 순차 claim/lease/complete**로 수정했다. duplicate error를 삼키거나 registration guard를 약화하지 않았다.
- 3ae374: 새 요청의 seed/reopen/restart/ACL 92 assertions는 실제 PASS했으나 마지막 SQL oracle이 jobs.state에 wrapper returned_state `terminal_success`를 사용하여 FAIL했다. 실제 jobs table/P63 원래 oracle의 `succeeded` 상태를 정확히 사용하게 수정했다. 실패 receipt는 FAIL 그대로 보존했다.
- 5b00e8: unused import/wildcard/semicolon strict lint. explicit imports와 필요한 문장 종료를 수정했다.
- 7a14bd/60a075: 새 safety helper 149/114 lines strict lint. 같은 wrong-key/no-publication/ingest-count/state assertions를 helper로 분리했다. allow/skip/assertion 삭제 없음.
- 잘못 추정한 migration 파일명을 조회한 조사 오류는 실제 0019_p09_authorized_full_ir_intent 파일을 확인하여 바로잡았다. migration이나 SQL guard 변경 없음.

실패 source 전체와 실제 failure receipts는 source archive/P65 evidence에 보존한다. 실패→후속 PASS는 기대값/guard를 약화한 승격이 아니다. earlier P62 16fde8 underlying category는 당시 미수집으로 여전히 UNRESOLVED이며 이번 fixture 문제와 같다고 추정하지 않는다.

## 회귀·보존·정리

현재 CLI lib/tests86(dc8212/2785f4)와 artifact/revision/retention lib/tests78(d8ff8c), 합164가 모두 PASS했다. failed/ignored/filtered0이며 CLI main0 target도 실제 실행했다. source/archive pins의 최종 수치는 [P65 원장](evidence/p09-65-durable-full-request.source-progress.v1.json)에 기록한다. strict actual example b19174, four-crate lib/tests+rustfmt+Python compile/scoped diff 8e50b8은 exit0이다.

fdb26d에서 product Cargo.toml의 postgres dev-dependency 1행과 대응 lock entry만 추가됐음을 전체 원문과 대조했다. 기존 production dependencies 불변이다. 046ba9에서 원래 test로부터 복사한 fixture constructor의 body token/string literals가 visibility/formatting 이외 동일함을 확인했다. 원래 tests/golden outputs/manifest는 수정하지 않았다.

P59~P64 246 declared entries, P48 original1551 files/51,047,460 bytes와 native75를 전체 hash 대조한다. 이는 byte 보존이며 **전체 과거 qualification CLI 재실행이나 current whole source/native admission은 아니다**.

최종 c0f774에서 원장 변경 뒤에도246 entries/1551 files/51,047,460 bytes/native75가 모두 exact였고19 declared archive origins를 사용했다. 현재 driver docstring의 PostgreSQL19 표기는 schema19를 가리키며 실제 서버는 두 receipt의 postgres_version과 고정 image 검사가 증명하는 **PostgreSQL18.4**다. runtime/migrations를 변경하거나 version19 실행을 주장하지 않는다.

이번 실제 DB5회(실패3/성공2)의 owned container/volume/host blob roots는 각각 owner/identity/scope 검증 뒤 모두 제거했다. 최종 두 PASS는 각14 ciphertext files/79,278 bytes를 정리했다. 123e9b에서 전용 label container/volume 및 p65 temp prefix 잔여0/Hwp.exe0을 확인했다. 사용자 원본/기존 DB/실패 결과는 삭제·이동하지 않았고 credential/backend 전체 로그/원문 package나 IR 값은 출력·저장하지 않았다.

## 다음 실제 구현 경계

실제 full HWPX importer와 source/result/IR provenance 및 실제 previous-result→input chain을 구현해야 한다. 현재 Source payload와 IR graph가 synthetic인 baseline을 실제 입력 계보로 승격하지 않는다. issuer/ExecutionManifest/idempotent publication, IR retention·GC·sync·recovery도 남는다.

그 뒤 전체 과거 qualification CLI replay와 새 current admission, licensed 의미/readback/render/direct differential가 필요하다. native epoch INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green/P09 완료 false/P10 시작 false/Goal ACTIVE를 유지한다. 허용창 금지 동안 native 실행은 하지 않는다.
