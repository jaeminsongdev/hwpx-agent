# P09-63 실제 revision graph/CAS 정책

- 일자: 2026-10-04
- 범위: loopback PostgreSQL18.4 전체 schema1~19의 genuine lease/authorization API와 Rust repository를 통한 bounded canonical metadata DAG.
- P09 Gate/제품/import/native qualification이 아니다. Goal ACTIVE/P10 보류/접근 허용 및 Hwp 실행 금지 유지.

## 원본과 실행 경계

P62 repository/probe/PLANS와 새 fixture/probe의 실패 버전을 `source-archive/p09-63-pre-revision-graph/`에 보존한다. migration1~19, 기존 SQL28/P61 SQL25, P62 root/read/restart/위험 구성31 assertions 및 과거 실패 receipt는 바꾸지 않는다. 새 runner는 기존 runner를 monkeypatch하지 않고 동일 검사를 유지하며 graph 경로를 추가한다. 읽기 table/role/guard 제한은 그대로이고, 추가 권한은 owned app role의 기존 `claim_idempotent_job_v2` 실행만이다. PUBLIC/internal leaf/table 직접 쓰기 허용은 없다.

## 실제 CAS 수정

기존 `RepeatableRead` 쓰기에서 두 별도 DB 연결의 동시 CAS가 한 성공+한 typed conflict가 아니라 serialization 오류를 내는 실제 실패를 관측했다. server timing category도 SERIALIZATION_FAILURE다. SQL branch FOR UPDATE 및 실제 authorization/receipt guards는 그대로 두고 **CAS 쓰기만 ReadCommitted**, head/node의 multi-query sealed 읽기는 RepeatableRead로 유지한다. 기다린 쓰기가 현재 head를 받아 기존 typed conflict를 반환하게 하며, 오류를 conflict로 덮거나 CAS를 자동 재실행하지 않는다. 다른 오류와 COMMIT ack 불명확 상태는 여전히 실패/unknown이다.

## 요구되는 검사

- 원래 root/no lease/fake IDs/잘못된 stage/request binding/token 소비/완료/별도 read/DB restart/5 위험 구성 및 복구31 executed assertions를 그대로 수행한다.
- root의 IR 없는 canonical legacy wrapper 자식→full-IR 자식, 다른 branch의 root, 두 부모 ordered merge, 독립 두 연결의 barrier 동시 CAS를 실제 register/claim/lease/advance/commit/complete API로 수행한다.
- 동시 결과는 정확히 하나 Committed와 하나 Conflict여야 한다. loser conflict의 project/branch/expected head/observed head/request digest 전체와 winner receipt digest binding, loser node 부재를 확인한다. 패자를 RepositoryFailure로 허용하지 않는다.
- 실제 seal/receipt 재구성으로 legacy no-IR와 full-IR 노드를 읽고 parent 순서를 보존한다. 별도 프로세스 및 restart 뒤 전체 bounded graph를 읽는다.
- actual project ACL을 owned DB에서 회수하면 같은 tenant/subject의 head/node 읽기도 NotFound여야 한다. owner ACL을 복구하고 다시 읽는다.
- read-only SQL oracle은 revision/seal/receipt6, parent edge5, job/attempt7(성공6/validating-running1), loser authorization1 및 exact lease 연관, IR intent5, 두 branch generation5/1을 확인한다. fixture 값을 바꾸어 잔여 loser를 숨기지 않는다.

각 요청은 원래 transaction 고유성 제약을 지키는 별도 digest/receipt metadata를 쓴다. 새 artifact metadata와 ACL은 하나의 정상 transaction에서 생성하여 기존 시간 순서 및 deferred manager guard를 만족시킨다. synthetic scanner/verified/encryption metadata는 actual blob/AEAD/scanning/provenance 증거가 아니다. fixture가 원래 source/result/IR metadata를 재사용하는 것은 DB DAG 검사만을 위한 것이며, 실제 전 revision 결과→다음 문서 입력의 제품 처리 증거가 아니다.

## 증거 범위·정리

최종 각 DB 실행의 SQL assertions62는 기존28+P61 25+graph9다. Rust69 executed assertions는 기존31+graph-write18+세 차례 graph-read6씩+ACL denied2로, 반복 읽기를 포함한다. 독립 기능131개라는 뜻이 아니다. source38와 executable1을 별도로 pin한다. P62 서술의 source35는 실제 source34+별도 executable1이므로, 원래 manifest/실패/문서를 고치지 않고 P63에서 수량 표기를 정정한다.

owner label/name/image가 일치하는 정확한 자기 container와 volume만 제거한다. credential 및 전체 backend 로그는 출력/파일 저장하지 않는다. 오류는 closed phase/SQLSTATE/whitelist category/hash만 남긴다. 원래 소스/native 증거/실패 결과/운영 DB는 보존한다.

P62의 독립 prevalidation 실패16fde8은 underlying category 미수집으로 아직 UNRESOLVED다. P63에서 증명한 동시 CAS serialization 원인과 같다고 추정하여 닫지 않는다. 관측된 bounded DAG/CAS/ACL 성공은 실제 importer/Artifact provider/최상위 full-IR product request/issuer/manifest/publication/retention/GC/sync/DR 및 native 의미·render·direct differential/Gate를 대신하지 않는다. arbitrary legacy SQL opaque rows, 대규모 DAG/모든 반례/부하/전원·network ack loss는 별도 미검증이다. 원래 전체 CLI 재실행/새 source admission도 필요하고 native epoch는 INPUT_CHANGED_RE_ADMISSION_REQUIRED다.
