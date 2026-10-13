# P09-62 실제 Rust PostgreSQL revision 구현 결과

- 일자: 2026-10-04
- 상태: **actual canonical root/full-IR metadata component PASS 관측 / 간헐 실패 원인·안정성 OPEN / P09 Gate 미완료**
- Goal ACTIVE, P10 보류. 접근 허용창/Hwp COM/UI/native dispatcher 활성화 없음.
- 정책: [P09-62_POSTGRES_REVISION_POLICY.md](P09-62_POSTGRES_REVISION_POLICY.md)

## 구현

revision-service에 loopback-only durable repository, subject-fixed service context 검사, 실제 lease와 전체 요청을 고정하는 immutable commit binding을 추가했다. 기존 schema1~19와 genuine v2/full-IR 승인 wrapper를 실제 Rust driver로 호출한다. canonical receipt를 생성하고, sealed revision을 읽을 때 실제 seal/receipt/parent 순서/full-IR 링크 및 canonical request/receipt digest를 재검사한다. COMMIT acknowledgement 손실은 success/retry와 다른 `REVISION_COMMIT_OUTCOME_UNKNOWN`이다. SQL의 raw backend 오류는 coarse category만 반환하고 버린다.

기존 in-memory 구현/요청 serialization 및 기존 SQL guard를 그대로 두었다. 새 startup 검사에서 role/schema/checksum/forced RLS/policy/8 guards/직접 쓰기 금지/실행 권한을 확인하며 typed request만 SQL parameter로 전달한다. 형식이 맞는 fake UUID는 실제 SQL에서 권한을 얻지 못한다. 공개 product envelope가 lease/auth fields를 받거나 임의 path/SQL을 실행하도록 만들지 않았다.

## 실제 실행과 실패 보존

모든 DB 실행은 고정 PostgreSQL18.4 image, 전체 schema1~19, 임시 app role/credential, 소유한 loopback ephemeral port 및 named volume을 사용한다. 기존 SQL28 및 P61 SQL25 기대값을 변경하지 않았다. 실제 verified/scanner/worker metadata는 synthetic이고 실제 blob/import/license authority가 아니다.

| 실행 | 실제 결과 | 의미 |
|---|---|---|
| 최초 SQL fd6fa7 | FAIL: seed ACL 중복; 당시 harness child capture 결손 | raw seed와 harness 보존; 이후 원본 seed를 실제 실행해 duplicate ACL 오류 재현 |
| 최초 Rust driver54960a | FAIL: coarse startup RepositoryFailure | closed startup stage diagnostics 추가 |
| 정책 wire928107 | FAIL: POLICIES stage | String parameter를 text로 받고 regclass로 변환; predicate/guard 불변 |
| 2b2ad0 / 8104a2 | 두 독립 DB PASS | pre-final-lint 소스의 역사적 증거 |
| 수정 후9d8592 | actual SQL53 + Rust31 PASS | coarse 오류 discard 수정 후 첫 관측 |
| 독립 fresh16fde8 | FAIL: prevalidation_commit_denied | 실제 underlying category/SQLSTATE 당시 미수집. **원인 미확정; 실패 유지** |
| 진단 추가809275 | actual SQL53 + Rust31 PASS | unexpected closed outcome 수집 추가; 위 실패를 해결했다고 주장하지 않음 |
| 최종4db76b / 7a6f7e | 동일35 source pins/동일 executable에서 두 독립 DB PASS | closed server error/timing 진단을 포함한 현재 소스의 실제 성공 관측 |

최종 각 실행은 genuine worker 등록→full-IR claim→lease/authorization→stage advance→실제 Rust CAS→token 소비→정상 완료를 수행한다. 별도 Rust 프로세스와 DB restart 이후 root generation1/부모0/정확한 canonical seal 및 full-IR 링크를 다시 읽는다. BYPASSRLS, NO FORCE RLS, 기존 receipt guard 또는 새 intent guard 비활성화, auth table 직접 INSERT 허용을 owned test DB 안에서만 적용하여 startup 거부를 확인하고 모두 복구한다.

Rust assertions31은 write14 + 별도 read4 + restart read4 + 위험 구성5 + restored read4로, 반복 읽기를 포함한다. SQL assertions53과 섞어 84개의 서로 다른 제품 기능으로 세지 않는다. 이미 관측한 fresh 실패16fde8의 원인은 아직 확인되지 않았으며, 두 후속 성공만으로 안정성 closure를 선언하지 않는다. 새 진단은 원문 서버 로그 대신 hash/닫힌 코드·timeout category만 남기며 기대 오류를 넓히거나 검사·guard를 skip하지 않았다.

## Rust 회귀·lint

- 최종 revision/artifact/retention lib/tests78 PASS: 25+10+18+1+14+5+5, 실제601ce7 exit0. 새 순수 boundary tests5는 config 제한/redaction, nil/attempt/fence, service의 read/write 전 context 검사, binding≠authority, uncertain commit category를 검사한다.
- 실제 product regression62 PASS: 같은 다섯 test targets10+8+16+18+10, terminal b2b5bd exit0. 78+62=140은 이 명시된 scoped suite만이며 전체 workspace/ordinary/native qualification이 아니다.
- strict4-crate lib/tests와 revision lib/tests/examples clippy PASS: 160af9 exit0. lint allow 추가 없음.
- 최초 doc/import/길이/unused-import/build 실패 원본, 마지막 coarse error needless-pass-by-value 실패db09f9, 진단 추가 후 write103/100 길이 실패f52664를 각각 보존했다. helper 추출과 explicit imports 및 오류 discard만 수정했다.
- 잘못된 package ID `hwpx-agent-product` 때문에 실패한1f873a invocation도 기록했다. 해당 실행의 service78은 실제 PASS이고 잘못 호출한 product test를 PASS로 세지 않았다. 올바른 `hwpx-agent-cli`의 동일5 targets를 재실행했다.

## 보존·정리

f29129 실제 hash audit에서 P59/P60/P61 source/archive55 pins exact, 원래 P48 graph1551 files/51,047,460 bytes는14개 선언된 archive origins를 통해 전체 exact였다. 변경된 현재 revision lib/types의 P60 원문은 P62 archive에서 대조했다. 원래 native75 hash도 모두 exact/Hwp.exe0였다. 이는 원문 byte 보존이며 **원래 전체 CLI의 재실행은 아니다**.

P62 전체10개 owned DB runs의 container와 volume은 각 영수증에서 제거를 확인한다. 초기5회와 이번5회 모두 label/name/image를 검사한 정확한 자기 test 자원만 제거했다. 기존 DB/사용자 원본/실패 증거/원래 native 결과를 삭제·이동하지 않았다. host file mount/image pull/remote operation/native activation 없음. credential 값 또는 전체 backend 로그를 영수증에 저장하지 않았다.

## 증거와 미완료 경계

- [현재 실제 PASS](evidence/p09-62-postgres-revision.diagnosed-current-pass.v1.json)
- [현재 독립 fresh PASS](evidence/p09-62-postgres-revision.diagnosed-current-fresh-pass.v1.json)
- [간헐 fresh FAIL, 원인 OPEN](evidence/p09-62-postgres-revision.current-fresh-driver-failure.v1.json)
- [최종 lint 실패 보존](evidence/p09-62-postgres-revision.final-lint-failure.v1.json)
- [source progress와 보존 영수증](evidence/p09-62-postgres-revision.source-progress.v1.json)
- 변경 전 전체 원문: `source-archive/p09-62-pre-postgres-revision/`

다음은 실패 원인·durable child/DAG/merge/legacy/concurrency 경계를 실제 증거로 닫고, 최상위 stored full-IR product request와 실제 Artifact/Revision provider를 연결하는 작업이다. 전체 HWPX importer/provenance, 실제 issuer/manifest/idempotent publication, IR retention/GC/sync/recovery, 전체 원래 source CLI replay/새 admission은 여전히 미완료다. 현재 adapter root SQL metadata의 PASS를 전체 importer/일반 legacy SQL/제품/native/Gate로 승격하지 않는다.

Native source epoch는 INPUT_CHANGED_RE_ADMISSION_REQUIRED이며 full34 batch/current SDK/native semantics/render/differential는 NOT_RUN/미검증이다. green0, P09 완료 false, P10 시작 false를 유지한다.
