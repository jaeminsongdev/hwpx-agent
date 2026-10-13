# P09-85 source-bound 정책 등록 서비스 정책

## 범위

P09-83/84의 기존 source importer·정책 domain binder·strict decoder·실제 ArtifactService·SQL20 repository를 사용해 정책 준비→암호화 ingest→fresh readback→SQL current head/generation CAS registration을 연결한다. 이것은 로컬 server library 등록 경로이며 실제 외부 인증/issuer/scanner/registered app, 문서 operation/publication/native Gate 완료가 아니다. 이전 evidence 및 root PLANS.md 부재를 유지한다.

## 준비와 artifact

준비 입력은 현재 provider에 고정된 actual imported source, 기존 typed complete SourceFormPolicy set와 예상 policy generation이다. caller graph/artifact/source digest/version/creator/approval flag를 받지 않는다. provider DocumentWrite scope와 fresh whole source/원래 source receipt를 검사한다. 기존 domain binder로 ordered anchors/defaults/validation/group/state를 검증하고 SQL20 document/head bounds와 generation0..i64max-1을 확인한다. 새 UUID/source/version/creator binding은 source/context에서 생성한다.

직렬화한 정책은 기존 strict decoder로 round-trip 일치를 확인하고1MiB 상한을 적용한다. prepared/request type은 private fields·비역직렬화·redacted Debug이며 실행 권한이 아니다. 실제 issuer 인증은 provider/server가 이미 인증한 context라는 기존 전제다. 이 모듈이 token을 검증하거나 issuer trust를 만들지는 않는다.

등록은 DocumentWrite/fresh source를 다시 확인하고 생성한 정책 bytes만 Evidence/전용 media로 실제 ingest한다. descriptor/Verified/Available/no-quarantine/ACL/AEAD/raw digest/strict decode 및 전체 domain receipt를 다시 검사한다. 원본을 다시 확인한 후 private generated request를 trusted registration repository에 전달한다. 정책 내용과 원본은 in-place 변경하지 않는다.

## SQL와 outcome

새 SQL request는 source scope/예상 generation/새 version/artifact/raw digest 및 typed source digests를 받는 저수준 trusted server API다. nil version/alias/exhausted generation을 거부한다. named SQL20 register와 exact current readback을 원래 subject-fixed scoped transaction 안에서 수행한다. 원래 current membership/source head/package/artifact role/state/ACL/generation CAS를 재사용하고 반환 row 전체를 source/version/creator와 대조한 뒤 commit한다. 기존 migrations·role/helper grants·guard 구현은 변경하지 않는다.

commit acknowledgement loss는 기존 CommitOutcomeUnknown을 유지하고 제품 OutcomeUnknown으로 전달한다. trusted repository reply mismatch도 no-effect 확정으로 표현하지 않는다. 자동 retry/reconnect/권한 확대는 없다. 준비가 metadata CAS를 예약하지는 않는다. 실패 시 이미 생성된 unregistered/ambiguous encrypted Evidence는 보존한다. cleanup이나 retry idempotency/GC 정책을 발명하지 않는다.

등록 receipt는 그 source/version의 metadata 등록과 검증 관측을 기록한다. 미래 currentness·atomic execution lease·concurrent revoke 방지·native operation/product routing을 발급하지 않는다. 실행 소비자는 기존 fresh latest-policy/source 검증을 다시 해야 한다.

## 검증과 보존

새 Rust5개/검사 runner1개와 parent3개의 module 선언만 추가한다. 전체 parent preimages와 inverse를 보존한다. 실제 검사는 owned disposable pinned PostgreSQL18.4/127.0.0.1 ephemeral port/tmpfs/no mount 및 owned encrypted temp files만 사용한다. fixture actors/scanner/workers/정책 선택·baseline v1 등록은 synthetic이다. v2는 실제 새 준비/ingest/decoder/domain/SQL registration 서비스 경로다. 원래 worker lease/source CAS 및 이후 current policy 소비자·철회를 함께 검사한다.

SQL registry fault는 owned admin transaction에서만 주입하고 trigger를 복구한 뒤 application admission을 확인한다. 운영 DB/신뢰 DB/원본/실패/native/private evidence는 수정하지 않는다. temp ownership/정확한 대상·링크를 검사한 뒤 owned DB/ciphertext만 정리한다. 비밀 값/전체 로그는 기록하지 않는다.

P09 Gate/A12/A13 OPEN, 목표 active, P10 새 구현 없음. P26/P62/native re-admission/full native34 NOT_RUN, 기존 matrix_drift 및 과거 SQL intermittence 미확정은 유지한다.
