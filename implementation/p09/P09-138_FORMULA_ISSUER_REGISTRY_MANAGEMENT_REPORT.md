# P09-138 — SQL22 레지스트리 metadata 등록·폐기 관리 adapter

## 판정

P137 읽기 제품 연결에 이어 SQL22의 named root 등록/폐기, approval 등록/폐기 함수에 연결하는 실제 Rust 관리 adapter를 구현했다. 판정은 **source/component only**다. 실제 DB에 접속하거나 migration·권한·trust 설정을 적용하지 않았다. 운영 키 provisioning/custody, 서명 발급 제품 workflow, atomic publication, 실제 한글 저장·재열기와 P09/A12/A13 Gate 완료는 증거가 없으므로 `NOT_RUN`/unqualified를 유지한다.

목표는 `active`, P09/A12/A13은 `OPEN`, 제품 완료는 `false`, P10 새 구현은 없다. 남은 큰 그룹 최소 6개 중 이 단계로 닫힌 그룹은 0개다. 최소 30개 조건은 전수 목록이 아니며 새 테스트 수를 완료율 또는 남은 작업 수로 해석하지 않는다.

## 변경과 권한 경계

`crates/revision-service/src/postgres/source_formula_policy/issuer_registry/management.rs`를 추가했다. 기존 `issuer_registry.rs`에는 `pub mod management;`만 추가했으며 나머지 전체 bytes는 그대로다. 변경 전 파일 전체 22357 bytes와 SHA-256 `ecb8cfb918b020469de369e1a1c5267bc68e74f236f388c4fcfb10aeb90a0e97`를 `source-archive/p09-138-pre-registry-management/source-preimages.v1.json`에 보존했다. 기존 읽기 생성자나 SQL/migration/원본 fixture/키 설정은 변경하지 않았다.

- 별도 `LocalPostgresFormulaRegistryManagementRepository::connect`는 정확한 schema1~22 fingerprint와 기존 SQL19/20/21 role/RLS/guarded-write admission을 재사용한다. loopback, bounded timeout, fixed context, redacted DB error, credential 미보존을 유지한다. revision commit lease는 `None`이며 읽기 repository 또는 commit interface를 노출하지 않는다.
- `RegistryManagementCapability::Trust` profile은 root 등록·폐기 2개만, `Approval` profile은 approval 등록·폐기 2개만 추가 EXECUTE를 허용한다. 두 profile 모두 SQL22 read 함수 2개, helper 3개, 반대 관리 함수 2개를 거부한다. enum은 admission profile 선택이지 프로젝트 권한 부여가 아니다. 현재 프로젝트 owner/editor 권한은 named SQL 함수의 실제 tenant/subject/ACL 검사에 의해 결정된다.
- 레지스트리 4개 history table의 강제 RLS, 정확한 tenant policy와 WITH CHECK, immutable trigger, 직접 SELECT/write/TRIGGER 권한 금지, owner role SET/USAGE 금지를 확인한다. 9개 함수 각각의 SECURITY DEFINER·bounded search_path·PUBLIC EXECUTE 금지·owner role 금지와 예상 EXECUTE를 대조한다. 권한을 GRANT하거나 RLS를 해제하지 않는다. PostgreSQL 스킬의 최소 권한·강제 RLS 지침을 이 검토에 적용했다.
- 모든 관리 API는 먼저 원래 `authorize_context`와 해당 admission profile을 확인한다. 4개 typed request는 Deserialize를 구현하지 않고 내부 필드가 private이며 Debug는 redacted다. 등록 요청의 creator는 실제 fixed context subject와 일치해야 한다. 요청 metadata나 공개 artifact ID만으로 권한이 생기지 않는다.
- root 등록은 issuer/time/lifetime/version/generation bounds를 확인한다. 초기 CAS 0→1은 허용하고 이미 SQL bigint 최대인 generation에서는 새 등록을 거부한다. approval 등록은 current source/policy request와 정확한 branch/document/policy/version/generation binding을 갖고 SQL이 실제 current head/root, artifact alias 및 manage ACL을 재확인한다.
- 폐기는 latest version/generation의 positive bigint CAS를 전달한다. SQL bigint 마지막 generation도 폐기할 수 있다. approval 폐기 요청에는 source-head/live-root 전제 조건이 없으므로 head 이동 또는 root 폐기 후에도 관리 요청을 만들 수 있다. 이는 request shape 및 SQL source contract의 확인이며 실제 DB에서 head/root 변화 후 폐기가 성공했다는 증거는 아니다.
- SQL parameters는 원래 함수 계약 순서대로 tenant/subject를 fixed context에서 가져와 전달한다. 4개 함수의 arity는 각각 11/15/5/8이다. 원래 `scoped(..., ReadCommitted, ...)`가 transaction-local tenant/subject를 고정하고 commit을 확인한 후에만 결과를 반환한다. 재시도/reconnect/retry loop가 없으며 commit acknowledgement loss의 `CommitOutcomeUnknown`을 보존한다.

## Receipt의 의미

등록 결과는 INT8 scalar 한 column의 반환값이 expected+1인지 확인하고, 폐기 결과는 VOID 한 column의 형태를 확인한다. 이후 원래 scoped transaction의 commit acknowledgement를 통과해야 private-field `FormulaRegistryManagementReceipt`를 얻는다.

Receipt의 identity는 요청 echo이며 **인증된 row readback이 아니다**. 신뢰 키/서명 승인/검증된 artifact/현재 read 가능성/native 실행/publication 권한의 증거로 사용할 수 없다. 특히 future-dated root를 등록할 수 있지만 이 receipt로 live root로 승격하지 않는다. 기존 제품 trust provider는 별도 read API·엄격한 payload/ACL/AEAD/hash/clock/Ed25519 검증을 계속 요구한다. Receipt와 trusted read record를 다른 타입으로 유지했다. 두 역할에 필요한 DB EXECUTE profile 설치도 이번에 하지 않았다.

## 검증과 실패 보존

| 검증 | 결과와 범위 |
| --- | --- |
| 제한된 Build | P138 suffix의 revision library EXE 생성 PASS |
| List→Test | 전체 revision library 32개 distinct case PASS, failed/ignored/measured/filtered 0 |
| 새 management unit case | 위 32개 중 8개: CAS bounds, root metadata, foreign tenant/creator, approval binding, 폐기 identity/bounds, head/root 비전제 shape, scalar ack mismatch, redacted Debug |
| Source contracts | 8 PASS: 전체 부모 preimage/정확한 module 추가, SQL arity·parameter 순서, profile 권한, 원래 scoped commit, bounds/receipt 의미, 폐기 경계, Debug/counterexample, resource runner |
| Workspace strict Clippy | 32 packages / 358 distinct targets PASS; compiler-artifact identity와 cargo metadata inventory 대조 |
| 역사적 감사 | P137 63 component executions 및 이전 stored 234 case 증거를 원본 bytes 시점으로 재감사; 현재 소스의 재실행으로 승격하지 않음 |

소스 계약 초기 실행은 7 PASS / 1 FAIL이었다. Rustfmt의 `query_one` 마지막 인자 쉼표를 검사 문자열이 고려하지 못했다. parameter 순서·개수·검사를 제거하지 않고 실제 formatted call과 정확히 대조하도록 고쳤다. Rust/SQL은 이 실패를 고치려고 바꾸지 않았다. 전체 초기 source 및 실패 finding을 보존했고 새 감사에서 정확히 같은 1개 실패를 재현한다.

정확한 결과는 `target/p09-121-resource-optimized/p138-revision-{build,list,test}-r1.json`과 `p138-workspace-lint-r1.json`에 있다. Build 이후 Rust source를 변경하지 않았다. 각 실행은 813개 고유 declared input의 전후 SHA-256과 이전 EXE 27개(원래 21 + P137 최종 4 + 이전 2)를 보존한다. 813은 전체 compiler dependency closure라는 주장이 아니다.

## 자원과 안전

Rust Build/Test/Clippy는 한 코어 affinity, BelowNormal, cargo jobs 1, 2초 sampling을 유지했다. 시작 전 CPU 85% 이상 또는 available RAM 4096MiB 미만은 미실행 보류다. 실행 중 CPU 85% 이상 3회 연속/RAM threshold/root WS 2048MiB/time limit에서 소유한 child tree만 중단한다. 다른 앱 종료나 threshold 완화는 없다.

Build 5.89초, List 0.32초, Test 0.31초, Clippy 14.86초. 네 receipt 전체 CPU 관측 최대 25%, available RAM 관측 최저 10876MiB다. Clippy child limit 확인은 25회였다. 짧은 List/Test는 양성 process working-set sample이 없어 peak 미관측이며 0MiB로 해석하지 않는다. root WS는 child tree aggregate memory가 아니다. 실행은 모두 terminal이고 Rust 검증 프로세스 부재를 확인했다. 이 결과로 코덱스 멈춤 원인을 해결했다거나 PC 전체 상태를 검증했다고 말하지 않는다.

접근 허용 창, COM/한글/native, 실제 DB, 설정/키/trust DB/cache, 설치, 원격 push, stage/commit, 삭제/이동은 실행하지 않았다. 사용자 소유 dirty 변경과 `PLANS.md` 삭제 상태를 보존했다.

## 감사 / 다음 경계

`tools/p09/verify_formula_issuer_registry_management.py`는 P137 checkpoint SHA-256, 인증된 전체 부모 bytes로 읽는 역사적 감사, 현재 계약 8개, 실패 계약의 재현·정확한 수정, 813개 입력/27개 이전 EXE, Build/List/Test inventory·summary·현재 EXE, strict Clippy 모든 target, 새 문서·원장 pins를 확인한다. in-memory 역사적 view는 실제 파일을 rollback하지 않으며 과거 검사를 약화하지 않는다. source inventory 개수는 기존 graph+선언 delta 관례이고 unique path union과 다르다는 표시를 유지한다.

다음은 issuer artifact 생성·검증·등록 workflow를 기존 AEAD ArtifactService 및 Ed25519 제품 경로에 연결하는 작업이다. 실제 DB role/profile 설치·migration·concurrency/CAS/권한 negative case, 운영 private-key custody와 발급 원천 admission, atomic publication/통합, native34 후보 재-admission·저장·재열기가 여전히 필요하다. native34는 `NOT_RUN / INPUT_CHANGED_RE_ADMISSION_REQUIRED`를 유지하고 이 metadata adapter로 Gate를 닫지 않는다.
