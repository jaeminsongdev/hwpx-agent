# P09-62 실제 Rust PostgreSQL revision 경계

- 일자: 2026-10-04
- 범위: 기존 schema1~19/실제 승인 API를 사용하는 loopback Rust repository. 전체 P09 제품 및 native Gate가 아니다.
- 접근 허용창, Hwp COM/UI, native dispatcher를 실행하지 않는다. P10은 보류한다.

## 원본·권한

기존 migration/receipt guard/ACL/실패 증거는 그대로 둔다. 변경 전 revision 코드와 Cargo.lock/PLANS 전체, 새 코드의 실패한 버전을 `source-archive/p09-62-pre-postgres-revision/`에 보존한다. 기존 in-memory repository와 요청/노드/receipt wire serialization은 유지한다. 새 context hook은 기존 repository에 기본 Ok이고, 실제 DB adapter는 tenant와 subject를 고정해 service의 commit/head/node를 모두 검사한다.

현재 연결은 이름부터 `LocalPostgresRevisionRepository`다. 127.0.0.1, 제한된 DB/user 이름, 유한한 timeout만 허용한다. NoTls는 이 로컬 개발 프로필에만 해당하며 원격/운영 보안 qualification이 아니다. 소유한 password는 Zeroizing으로 감싸고 Debug는 redacted다. 외부 driver 내부 복사본 전체의 zeroization을 주장하지 않는다.

## 승인된 커밋·읽기

- 내부 `RevisionCommitLease`는 수신한 실제 lease IDs/attempt/fence와 전체 canonical request digest를 고정한다. 형식이 맞는 UUID는 authority가 아니다.
- 실제 v2 또는 full-IR 승인 wrapper만 호출하며, table 직접 쓰기/내부 leaf/session 승인 flag 조작/임의 auth row 주입은 하지 않는다. SQL이 실제 job/state/lease/fence/subject/intent/일회성 token을 재검사한다.
- 시작 시 정확한 19 migration registry/checksum, 비특권 role, 7 읽기 table의 forced RLS/정확한 tenant policy, 직접 쓰기 금지, 기존 및 새 8 guards, wrapper/internal 실행 권한을 검사한다. checksum registry와 이름/활성 trigger 검사는 악의적인 DB superuser의 함수 body 교체까지 증명하지 않는다.
- 매 작업은 subject-fixed RepeatableRead transaction에서 scope를 설정한다. bounded parent list/순서, canonical IDs/digests, sealed/verified node, 실제 receipt/graph seal, 요청 및 receipt digest를 다시 확인한다. 임의 row를 sealed node로 역직렬화하지 않는다.
- SQL의 opaque legacy digest를 Rust canonical digest라고 간주하지 않는다. 새 adapter의 실제 증거는 Rust canonical writer의 root/full-IR profile이다. 일반 legacy SQL row import, durable child/DAG/merge/concurrent writer는 별도 검증 대상이다.
- 자동 retry/reconnect는 없다. COMMIT acknowledgement 손실은 `REVISION_COMMIT_OUTCOME_UNKNOWN`으로 구분한다. 코드와 순수 경계 검사만 있으며 실제 network/power-loss qualification은 아직 없다.

## 실제 검증과 반례

runner는 고정된 기존 PostgreSQL18.4 image에 전체 schema1~19를 적용하고 원래 SQL28+P61 SQL25 검사를 실행한다. synthetic metadata는 실제 blob/scanner/AEAD/import/native/issuer 증거가 아니다. Rust probe는 genuine register/claim/lease/advance/commit/complete를 호출하고, 별도 프로세스 및 DB restart 후 exact canonical root/IR link를 읽는다.

한 실행의 실제 Rust assertions31은 write14 + fresh read4 + restart read4 + 위험 구성5 + restored read4다. 반복 읽기를 포함하며 31개의 독립된 기능으로 세지 않는다. 위험 구성은 이 runner가 만든 격리된 DB 안에서만 적용/복구하며, original guard와 새로운 intent guard의 비활성화도 반드시 adapter admission에서 거부해야 한다.

strict lint의 원문 DB 오류 discard를 수정한 뒤 첫 실제 실행은 PASS였지만 독립 fresh 실행 `16fde8`에서 `prevalidation_commit_denied` predicate가 FAIL했다. 실제 오류 category/SQLSTATE는 당시 수집하지 않아 원인이 미확정이다. 이후 통과가 이 실패를 지우거나 원인을 확정하지 않는다. 실패는 별도 immutable receipt에 남기고, 새 probe/runner에는 closed outcome code와 source-defined server error/timing category만 수집하도록 진단을 추가했다. 기대 error를 넓히거나 검사를 skip하지 않았다. 안정성 및 실패 원인 closure는 계속 OPEN이다.

## 산출물·정리·미완료

테스트 DB에는 무작위 임시 credential만 runtime environment로 전달하며 파일/로그에 값을 쓰지 않는다. runner가 label/name/image를 확인한 정확한 container 및 volume만 제거한다. 운영/기존 DB, 사용자 소스/원본 HWPX, native 증거는 변경하지 않는다. 백엔드 로그는 출력/보존하지 않고 hash와 whitelist category만 영수증에 남긴다.

전체 HWPX importer/provenance, 최상위 stored full-IR product request/Artifact 연동, 실제 issuer/ExecutionManifest/idempotent publication, IR retention/GC/sync/concurrency/recovery, 원래 전체 CLI 재실행/새 source admission, licensed semantic/render/differential 및 P09 Gate는 미완료다. 현재 native epoch는 `INPUT_CHANGED_RE_ADMISSION_REQUIRED`; native 실행/green0/P09 완료/P10 시작은 false다.
