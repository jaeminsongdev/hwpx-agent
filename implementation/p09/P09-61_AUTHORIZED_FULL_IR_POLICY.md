# P09-61 승인된 전체 IR 커밋 정책

## 범위와 권위
- P09 저장된 전체 IR 경로의 **실제 PostgreSQL metadata component** 구현이다. P10 새 구현이 아니다.
- schema19를 기존1~18 뒤에 추가한다. 과거 migration/checksum/guard/fixture/실패 영수증은 변경하지 않는다.
- 운영 DB, 기존 컨테이너, 한글 COM/UI, 접근 허용, 보안 모듈, trust/registry/settings를 사용하거나 수정하지 않는다.
- SQL fixture의 verified/scanner/worker 값은 명시적인 테스트 metadata다. 실제 blob/AEAD, HWPX 전체 importer, native 읽기/쓰기, signed route, 제품 publication 또는 P09 Gate 증거가 아니다.

## 실제 승인 흐름
- 새 claim은 기존 v2 editor/source/head/identity/TTL/advisory-lock/job/audit 흐름을 그대로 유지하고, 읽기 가능한 적격 DocumentIr metadata와 예상 Result package digest를 추가로 확인한다.
- 같은 transaction에 full_document_ir_intents를 삽입한다. tenant/project/key + artifact/raw/package/graph가 admission 시 고정되며 UPDATE/DELETE가 거부된다.
- 동일 key 재실행은 기존 요청과 IR binding 모두 일치해야 한다. 새 API로 legacy job의 없던 IR을 사후 추가하는 것도 거부한다.
- worker 등록, lease, attempt, fence, 상태 전환 및 일회성 commit authorization 생성/소비는 **기존 실제 API와 guard**만 수행한다. fixture가 authorization row를 삽입하거나 authorization session flag를 설정하지 않는다.
- 새 commit wrapper는 scope/IR ACL/intent를 검증한 후 원래 v2의 실제 authorization 잠금/제시/정리 절차로 기존 schema18 IR CAS leaf를 호출한다.
- 새 receipt BEFORE INSERT trigger는 새 wrapper뿐 아니라 기존 wrapper/leaf도 검사한다. IR이 있는 revision에는 고정 intent가 필요하고, 고정 intent가 있는 job은 IR 없는 revision으로 우회할 수 없다.
- 기존 v2 receipt guard, immutable revision/seal, head CAS, source/result/receipt qualification과 성공 완료 guard는 보존된다.
- 원래 claim/commit 함수에 각각 정확히5개 additive transformation만 허용한다. 새 runner가 전체 함수 body를 원래 schema7과 대조하며 schema18 leaf도 원래 schema3 + 기존5개 추가와 대조한다.

## 검증/정리
- 로컬에 이미 있는 pinned PostgreSQL18.4 image만 사용한다. pull 없음.
- 고유 run label/name/image 확인, network none, host ports/mounts 없음, DB tmpfs. fixture app role은 NOSUPERUSER/NOBYPASSRLS이며 내부 helper/leaf/table write 권한이 없다.
- 전체 schema1~19 apply, 실제 registry 검증, 명시적 gate 없는 rollback 거부, 빈 intent rollback/reapply, 원래 P60 전체 fixture의 무승인 실패 보존, 원래28개 회귀와 새25개 실제 검사, 데이터가 있는 rollback 거부와 IR 링크 보존을 모두 수행한다.
- 실패는 별도 immutable 증거/원본 archive에 보존하고 새 코드/fixture만 수정한다. 로그 전체/비밀정보는 출력하지 않는다.
- 테스트 후 정확히 이번 run 소유 컨테이너만 제거한다. 운영 또는 사용자 자료는 삭제하지 않는다.

## 남은 경계
- 의도적으로 default PUBLIC EXECUTE/table rights는 없다. 실제 application-role grant/운영 적용은 이 검증에 포함되지 않는다.
- IR intents의 FK/immutability는 fail-closed 보존이다. 기존 retention/GC/동기화의 IR lifecycle 및 정식 만료/삭제 정책은 아직 qualification하지 않았다.
- 독립 session/transaction의 실제 동시성, live lease 만료 경쟁, crash/restart recovery를 새 IR 경로에서 검증하지 않았다. 기존28개 suite 통과를 새 IR 모든 동시성 증거로 확대하지 않는다.
- durable Rust revision adapter, 제품 최상위 전체 IR 요청 envelope, 실제 전체 HWPX importer/issuer/publication은 남아 있다.
- 현재 native source admission은 INPUT_CHANGED/RE_ADMISSION_REQUIRED다. 원래 전체 CLI 재실행과 새 admission 없이 dispatcher를 실행하지 않는다. 사용자 금지 중에는 접근 허용/COM을 띄우지 않는다.

