# P09-71 실제 DB·암호화 파일에서 원본 기반 폼 읽기 검증

- 상태: **actual stored Result→source-backed form/policy read DURABLE BACKEND COMPONENT PASS / full importer·input lineage·정식 정책·실행·publication·native·P09 Gate OPEN**.
- 정책: [P09-71_DURABLE_ACTUAL_FORM_IMPORT_POLICY.md](P09-71_DURABLE_ACTUAL_FORM_IMPORT_POLICY.md).
- 실제 현재 소스/executable로 독립 임시 PostgreSQL18.4/schema1~19 및 `LocalEncryptedBlobStore` 두 개를 실행했다. P70의 실제 importer가 원래 P65 sealed Result에서 읽은 source bytes를 사용하며, 기존 synthetic IR의 graph를 importer 입력으로 재사용하지 않는다.
- 신규 support helper와 세 probe modes, additive Python driver v2만 연결했다. production importer/service/SQL 권한/worker/fixture/safety 및 원래 tests/golden 기대값은 변경하지 않았다.

## 실제 실행 증거

| 검증 | 증거 | 결과·범위 |
|---|---|---|
| 독립 DB1 | [run1 v2](evidence/p09-71-durable-actual-form-import.postgres-run1.v2.json), e6b5e6 | exit0; 기존 SQL53/Rust116 및 신규 actual import139, read-only postconditions5 PASS |
| 독립 DB2 | [run2 v2](evidence/p09-71-durable-actual-form-import.postgres-run2.v2.json), 592697 | exit0; 동일66 declared sources·동일 executable로 같은 범위 PASS |
| current CLI/package lib/tests | 7d92b0/920179/5a3d94/9017eb/804aaf | 97 targets, CLI99+package850=949 PASS; failed/ignored/filtered0 |
| original domain public suites | 887d8f | form_control8+form_input_public15=23 PASS |
| strict lint | 84f820/531dda | actual example 및 product/package/artifact/revision lib/tests `-D warnings` PASS; allow/skip 없음 |
| format/Python syntax | b42439 | rustfmt recursive check 및 driver py_compile PASS |
| whole original inverse | 58af0e | root의 declaration+dispatch2 transformations/driver의 additive11 transformations를 제거하면 whole bytes/SHA exact |
| original P70 dependencies | 49cfa9 | PLANS 제외 원래85 sources whole bytes/SHA exact; production source와 원래 test 변경 없음 |
| 원본·과거 증거 보존 | 134fbe 및 최종 audit | prior735 pins/original1551 files·51,047,460 bytes/24 archived origins/native75 exact; whole original qualification CLI 재실행 아님 |

actual executable SHA: `a7f30849ae51d256e4a21f94b4634d9021e2484addbf3ee4547b1dd6f0839b96`. 고정 image는 `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`; 실제 server는 `18.4 (Debian 18.4-1.pgdg12+1)`다. schema19를 PostgreSQL server19로 부르지 않는다.

이번 named Rust 총972는 실행 범위를 넓힌 회귀 결과다. 기존 P70 지정 package203보다 많은 package 전체850을 실행했으며, 신규972 기능/테스트 작성 또는 workspace/Python/whole qualification/native/Gate PASS가 아니다. [회귀 요약](evidence/p09-71-durable-actual-form-import.rust-regression.v1.json)에 실행 command·suite별 실제 counts를 기록했다.

## 실제 원본 읽기와 실패 거부

1. 원래 genuine worker/job/lease/admission authorization/CAS/seal/complete로 네 baseline roots를 만들었다. prior Source/scanner/keys/whole caller IR/baseline authority는 원래대로 synthetic이며, Result의 locked HWPX bytes만 actual captured/derived corpus다.
2. four cases의 actual Result source SHA 및 actual whole graph/all observations/receipt를 direct immutable source importer와 비교했다. 명시적 TEST policies를 원래 P69 binder에도 넣고 전체 graph/complete policy state/receipt exact를 검사했다. case는 native 독립 실행 수나 모두 서로 다른 source bytes를 의미하지 않는다.
3. 매 actual mode는 fresh service import/verify/policy verify를 실행한다. 독립 child process→실제 PG restart→ACL restore→원래 synthetic IR quarantine 뒤 같은 DB의 actual receipts가 exact였다. 다른 DB artifact UUID 때문에 전역 receipt equality는 요구하지 않는다.
4. 실제 project ACL 철회 시 four actual imports가 거부됐다. 실제 Result ACL 철회 시 fresh import, cached import verify, cached policy verify가 모두 원래 service error로 거부되고, 원래 permissions 복구 뒤 receipt가 exact였다. negative-test 실패 여부와 무관하게 ACL을 복구한다.
5. 실제 파일에 다른 AES key를 적용하면 source read를 거부한다. metadata record에 결합한 actual ciphertext는 plaintext와 다르고 GCM tag16 bytes 길이가 확인됐다. physical disk 손상/전원 손실/변조 전체를 이번 DB 실행으로 검증했다고 주장하지 않는다.
6. actual source import는 원래 synthetic IR quarantine와 독립적이며, head/ingest count를 바꾸지 않는다. 원래 read audit는 정상 추가된다. policy-bound actual graph는 모두 원래 full product context에서 partial Projection으로 거부된다.
7. 원래 SQL53와 Rust116/SQL postconditions5는 유지된다. 새 actual139는 네32-check imports의 반복128 + project-denial4 + Result ACL/key/partial safety7이다. 각 DB Rust 총255의 반복 체크를 서로 다른 제품 기능/완료율로 부풀리지 않는다.

새 mode의 `candidate_sha256`는 비어 있다. graph/state hashes를 published HWPX candidate라고 기록하지 않고, partial import/policy receipt SHA만 반환한다. original modes의 four whole HWPX candidates 및 fresh receipt/candidate equality 검사는 unchanged다.

## 실패·보존·정리

초기 compile025ce8에서 새 helper가 존재하지 않는 get_permissions API를 가정했다. original metadata record와 exact artifact identity 확인 뒤 permissions_for를 사용하도록 수정했다. strict lint a52c7f의 run111/safety126 lines와 semicolon 문제는 같은 검사를 helper로 분리하고 세미콜론만 추가해 해결했다. 전체 실패 당시 helper/root는 byte-exact archive에 보존했다. 초기 outer shell exit0은 뒤따른 py_compile 때문이므로 lint PASS로 쓰지 않았다. [실패 원장](evidence/p09-71-durable-actual-form-import.initial-failures.v1.json)은 실패를 그대로 유지한다.

원래 root23251 bytes/SHA `2e7fb212b5d16e2dd74c111d88b23b6cfe363feb7be2ffbe42b172cfeb7e17c4`, driver16675 bytes/SHA `0f28afb33cea415c0fb000efe11e272aebfd27dc38cda4e31f41bb06f1a3158e` 및 PLANS40309 bytes는 whole pre-change archive에 보존했다. inverse는 원래 source bytes 전체가 같다는 검사이며 assertion/guard/function 생략이나 old source lock 갱신이 아니다.

두 실행은 label/image/name/volume/exact temp root/link를 검증한 뒤 자신이 만든 container/volume/blob root만 제거했다. 각14 disposable ciphertext files/79,278 bytes, 합28files/158,556 bytes를 정리했고 existence checks 모두 true였다. fixture를 재실행하면 재생성 가능하다. 사용자 원본·기존 DB·native/private/실패 증거는 삭제·이동하지 않았다. password/credentials/whole logs/XML/graph/state/policy 원문 값을 출력·저장하지 않았다.

## 다음 실제 구현 경계

P70의 in-memory metadata 한계 중 **actual Result read/import의 실제 PG/file backend 검증**은 이번에 해소했다. 실제 Source/Result/IR provenance의 새 committed input chain, previous-result Source-only/dedup 종류 경계, full field/note/reference/catalog/security meaning importer, authoritative policy provider/real scanner/external issuer는 여전히 남는다. TEST 정책·source-local identity reservation을 native/persistent identity/issuer 증거로 바꾸지 않는다.

정식 ExecutionManifest/publication/idempotency, IR lifecycle/concurrency/crash/recovery, 전체 original qualification CLI replay/current admission, licensed semantics/readback/render/direct differential도 별도 미완료다. 기존 P62 16fde8 원인은 UNRESOLVED이며 후속 성공으로 원인 규명이 된 것이 아니다.

native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green/P09 Gate OPEN/Goal ACTIVE/no P10를 유지한다. 한글/COM/UI/접근 허용창·image pull·dependency/trust/security/config 변경·stage/commit/push 없이 실행했다.
