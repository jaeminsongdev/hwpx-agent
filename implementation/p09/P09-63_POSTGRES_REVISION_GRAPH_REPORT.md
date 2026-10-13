# P09-63 실제 revision graph·동시 CAS 구현 결과

- 일자: 2026-10-04
- 상태: **bounded canonical SQL metadata DAG/CAS/ACL component PASS / 실제 제품·native·P09 Gate 미완료**
- Goal ACTIVE, P10 보류. 접근 허용창/Hwp COM/UI/native dispatcher를 실행하지 않았다.
- 정책: [P09-63_POSTGRES_REVISION_GRAPH_POLICY.md](P09-63_POSTGRES_REVISION_GRAPH_POLICY.md)

## 실제 결함과 수정

별도 PostgreSQL 연결 두 개가 같은 head에 barrier 동시 CAS를 수행했을 때 원래 RepeatableRead 쓰기는 한 성공+한 typed conflict 대신 RepositoryFailure를 반환했다. 실제9ac620 failure receipt에는 `concurrent_exactly_one_commit_one_conflict` 실패와 server SERIALIZATION_FAILURE category가 남았다.

**CAS 쓰기만 ReadCommitted로 수정**하여 기존 SQL branch FOR UPDATE 잠금 뒤 패자가 현재 head를 읽고 기존 typed conflict를 반환하게 했다. head/node의 sealed multi-query 읽기는 RepeatableRead를 유지한다. 기존 migration/authorization/receipt/IR intent/ACL/role/timeout guard나 기대 결과는 바꾸지 않았다. 오류를 임의 conflict로 매핑하거나 CAS를 자동 retry하지 않는다. 불확실 COMMIT acknowledgement는 기존 unknown 상태를 유지한다.

원래 P62 probe에 실제 graph 모드만 추가했고 source/archive를 보존했다. 새 runner는 원래 root31 executed assertions, SQL28/P61 SQL25, 위험 구성5/복구 검사를 그대로 수행한 뒤 graph 검사를 추가한다. app role에 추가한 것은 기존 legacy v2 claim wrapper 실행 권한뿐이며 PUBLIC/internal leaf/테이블 쓰기 우회는 없다.

## 현재 실제 실행

고정 PostgreSQL18.4 image에 전체 schema1~19, owned loopback ephemeral port/named volume을 사용했다. Rust genuine lease/authorization→advance→commit→complete로 아래 경로를 실행했다.

- 원래 full-IR root에서 **IR 없는 canonical legacy 자식**, 다음 **full-IR 자식**을 커밋하고 읽기.
- 다른 branch의 root와 main branch의 **두 부모 ordered merge** 생성 및 읽기.
- 두 독립 DB 연결에서 정확히 한 Committed+한 Conflict. winner receipt/request digest와 loser conflict의 project/branch/expected head/observed head/request digest 전체 일치, loser node 부재 확인.
- 별도 프로세스 및 DB restart 뒤 전체 bounded graph/두 branch head 읽기.
- actual project ACL 회수 뒤 같은 tenant/subject의 head/node NotFound, ACL 복구 후 재읽기.
- read-only SQL9 oracle: revisions/seals/receipts6, parent edges5, jobs/attempts7(성공6/진행1), loser authorization1의 정확한 lease 관계, IR intents5, branch generations5/1.

| 실제 실행 | 결과 |
|---|---|
| bd629b | ReadCommitted 수정 뒤 PASS; exact conflict 후속 검사는 추가 전 |
| 2403bb | 최종 source38 + 별도 executable pin; SQL62/Rust69 executed assertions PASS, exit0 |
| 2b7288 | 독립 새 DB에서 동일38 source hashes/동일 executable, SQL62/Rust69 다시 PASS, exit0 |

SQL62는 기존28+P61 25+graph9다. Rust69는 원래31+graph-write18+세 번 graph-read6+ACL denied2로 반복 읽기를 포함한다. 독립된 제품 기능131개 또는 전체 P09 수치로 세지 않는다. raw graph fixture는 synthetic metadata이며 blob/AEAD/HWPX importer/native/issuer authority는 아니다. source/result/IR metadata 재사용은 SQL graph 검사만을 위한 것으로 실제 이전 결과를 다음 문서 입력으로 사용하는 제품 chain은 미검증이다.

## 실패 원문과 회귀

- 0f2647: 새 probe가 존재하지 않는 source getter를 호출한 E0599. getter 검사를 버리지 않고 실제 serialized node의 source ID를 typed request와 대조했다.
- 804399/e48c08: 새 fixture가 모든 요청에 같은 transaction receipt digest를 넣어 원래 고유성 제약23505에 거부됨. 각 요청의 서로 다른 digest/별도 receipt metadata로 수정; unique index/SQL은 그대로다.
- 832b18: 새 진단 helper manual_inspect lint. inspect_err로 결과를 변경하지 않고 진단하도록 수정; lint allow 없음.
- 7453cf: 새 artifact가 과거 verified_at을 복사해 원래 time-order guard에 거부됨. 새 metadata의 실제 transaction_timestamp로 수정.
- 84598f: 새 artifact와 manager ACL을 각각 autocommit하여 deferred manager guard를 만족시키지 못한 fixture 결손. 하나의 정상 BEGIN/COMMIT으로 생성; manager guard 불변.
- 9ac620: 실제 동시 CAS serialization 결함. production repository의 write isolation만 수정; 당시 실패/원문을 그대로 보존.
- aee9f3: read-only preservation 명령이 구 schema의 없는 optional property를 @($null)로 세어 null 경로를 조회한 호출 결손. 원장/guard를 변경하지 않고 선언된 실제137 entries 전체를 다시 검사했다.

순수 Rust lib/tests78(25+10+18+1+14+5+5)와 product5 targets62(10+8+16+18+10), 합140이 모두 PASS했다. 실제372271/a0bb99 exit0이며 ignored/filtered0이다. strict4-crate lib/tests 및 revision lib/tests/examples, 새 Rust formatting/Python compile/scoped diff check는 실제f00990 exit0이다. 이는 명시된 scoped suites이며 whole workspace/ordinary/native qualification이 아니다.

## 보존과 정리

실제81f7d9 audit에서 P59/P60/P61의55 entries와 P62의82 entries, 합137 원장 항목을 원문·필요한 archive origins로 모두 exact 대조했다. P62의 수정 전 repository/probe/PLANS는 P63 archive에 보존한다. 원래 P48 전체1551 files/51,047,460 bytes는14개 선언된 origins를 통해 전체 hash exact, native75도 모두 exact/Hwp.exe0이다. 이 검사는 원문 byte 보존이고 **전체 원래 CLI 재실행은 아니다**.

이번8개 owned DB 실행(실패5/성공3)의 container/volume은 모두 각 owner label/name/image 확인 뒤 제거했고 잔여 prefix0을 확인했다. 기존 DB/사용자 원본/private native 증거/실패 결과를 삭제·이동하지 않았다. image pull/host file mount/원격 호출/native activation 없고 credential이나 원문 backend 로그는 저장·출력하지 않았다.

P62의 source35라는 서술은 actual manifest source34와 별도 executable1을 합친 수량이었다. P63에서 이를 분리해 정정하며 원래 P62 manifest/문서/실패 receipt를 덮어쓰지 않았다.

## 증거·다음 경계

- [현재 실제 PASS](evidence/p09-63-revision-graph.actual-pass.v1.json)
- [독립 fresh PASS](evidence/p09-63-revision-graph.actual-fresh-pass.v1.json)
- [수정 전 동시 CAS FAIL](evidence/p09-63-revision-graph.concurrent-cas-failure.v1.json)
- [source·보존 원장](evidence/p09-63-revision-graph.source-progress.v1.json)
- 원문 archive: `source-archive/p09-63-pre-revision-graph/`

P62의 earlier16fde8 prevalidation 실패 underlying category는 당시 미수집으로 여전히 UNRESOLVED다. 이번 동시 CAS 원인과 같다고 추정하여 닫지 않는다. 두 연결/bounded DAG PASS는 모든 legacy SQL opaque row/모든 DAG 반례/대규모 부하/전원·network ack loss의 증거가 아니다.

다음 실제 구현은 최상위 stored full-IR product request와 actual Artifact/Revision provider 연결 및 전체 HWPX import/provenance이다. issuer/ExecutionManifest/idempotent publication/IR retention·GC·sync·recovery, 원래 전체 source CLI replay/새 admission, licensed 의미/readback/render/direct differential는 미완료다. native epoch INPUT_CHANGED_RE_ADMISSION_REQUIRED, full34 NOT_RUN/0green/P09 완료 false/P10 시작 false를 유지한다.
