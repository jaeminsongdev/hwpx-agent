# P09-139 — issuer 서명·AEAD artifact·레지스트리 등록·제품 소비 연결

## 판정과 범위

P138 metadata 관리 adapter에 이어, 원래 ArtifactService와 Ed25519 verifier를 사용하는 trusted-server provisioning workflow를 구현했다. 판정은 **source/component only**다. root artifact 생성·등록·live readback, opaque source-generated policy에 대한 서명·approval artifact 생성·등록·live readback, 기존 제품 consumer 연결을 synthetic registry/clock/custody 아래에서 검증한다. 실제 PostgreSQL 접속, migration/role 설치, 운영 private-key custody 또는 native 한글 실행은 하지 않았다.

목표는 `active`, P09/A12/A13은 `OPEN`, 제품 완료는 `false`다. P10 새 구현은 없으며 큰 그룹 최소 6개 중 이 단계로 닫힌 그룹은 0개다. 최소 30개 조건은 전수 목록이 아니고 테스트 수를 완료율이나 남은 작업 수로 해석하지 않는다. native34는 `NOT_RUN / INPUT_CHANGED_RE_ADMISSION_REQUIRED`다. Codex 앱 멈춤 원인도 해결되었다고 판정하지 않는다.

## 구현과 권한 경계

- 새 `issuer/registry/provision.rs`는 호출자가 명시적으로 주입한 registry, 별도 관리 gateway, current policy repository, ArtifactService, fixed context, trusted clock, signer만 사용한다. endpoint/Deserialize/default key/private-key 생성·설치/env fallback은 없다. signer trait의 실제 운영 key custody는 여전히 미검증이다.
- root는 DocumentRead/DocumentWrite context, fixed tenant/subject, owner preflight, CAS/generation, 원래 trust bounds/live clock을 확인한다. 서버 UUID를 부여하고 원래 strict trust wire를 재사용한 뒤 실제 AEAD ingest/download·scanner·whole digest·whole bytes를 확인한다. named root writer를 한 번 호출한 후 registry metadata와 artifact/trust payload를 다시 읽어 동일함을 확인해야 receipt를 반환한다.
- approval은 opaque `FormulaPolicyRegistrationRecord`와 현재 policy의 완전한 equality를 요구한다. live root와 clock을 확인하고 원래 claims validator 및 active key 검사와 owner/editor preflight를 **서명 호출 전에** 수행한다. 기존 domain-separated signing bytes, envelope, strict decoder, 원래 claims validator, 실제 ring Ed25519 verification을 재사용한다. 서명 후 current policy/root/clock을 다시 확인하기 전에는 artifact를 만들지 않는다.
- 실제 AEAD artifact를 생성·download 검증한 뒤 current policy/root/clock을 재확인한다. source/policy/root artifact와의 alias를 거부하고 named approval writer를 한 번 호출한다. 등록 후 typed metadata equality, whole artifact bytes, 두 번의 approval 조회, 두 번의 current policy/root/clock 재확인을 모두 통과한 뒤 private receipt를 반환한다. 기존 math/protection/current product consumer와 publication 경로를 대체하지 않는다.
- Revision 관리 repository의 새 `check_project_role`은 이미 admission된 tenant-scoped `project_acl` read와 원래 ReadCommitted scoped context를 사용한다. Trust는 owner, Approval은 owner/editor이며 context/profile/scope를 먼저 확인한다. 새 GRANT, SQL migration/table write, 다른 reader/writer 권한은 추가하지 않는다. 이는 **preflight이지 lease나 atomic authority가 아니다**. 최종 named SQL write가 active tenant/project/current head/root/ACL/CAS를 다시 검사해야 한다. 실제 DB 설치·실행과 concurrency race 검증은 남아 있다.
- 부모 5개는 인증된 전체 변경 전 bytes를 보존했다. registry/test module 추가, provider validator의 sibling visibility, opaque record 내부 pre-sign validator, advisory role method만 추가했으며 unrelated 사용자 dirty 변경을 정리하거나 stage하지 않았다.

## 실패와 residue의 의미

실패는 Preflight/ArtifactIngest/ArtifactReadback/RegistryWrite/RegistryReadback stage와 NotAttempted/Denied/CommitOutcomeUnknown/Acknowledged를 구분한다. diagnostics와 Debug는 redacted다. writer는 정확히 한 번 호출하고 reconnect/retry/delete를 하지 않는다.

ingest 실패가 artifact ID를 반환하지 못했더라도 부분 저장 가능성을 부정하지 않는다. commit acknowledgement loss는 실제 row가 이미 저장된 상태를 synthetic writer에서 재현한다. acknowledged receipt mismatch 또는 post-commit readback 실패를 미등록·retry-safe로 표시하지 않는다. 실패 artifact와 모든 이전 실패 증거를 보존한다. receipt는 운영 key authority, atomic publication, native acceptance 또는 Gate 통과 증거가 아니다.

## 최종 검증

최종 Rust 소스는 `r7` workspace strict Clippy 이후 변경하지 않는다. 최종 Build/List/Test는 새 `form_stored_provider-p139-r7.exe`를 사용한다.

| 검증 | 범위 |
| --- | --- |
| source contracts | 8 PASS: whole parent deltas, role/context scope, original claims/key-before-custody, Ed25519-before-ingest, full artifact/readback ordering, failure residue, genuine negative cases, resource guards |
| Build/List/Test r7 | PASS. 새 최종 EXE, 고유 8개 inventory와 passed names/terminal summary 대조; failed/ignored/measured 0. 기존 stored 241개는 filtered이며 현재 재실행이 아님 |
| workspace strict Clippy r7 | PASS. 32 packages / 358 distinct targets, `--locked --offline --jobs 1 -- -D warnings`; metadata와 compiler-artifact identity 대조 |
| 실제 component 경로 | original source generation, 실제 Ed25519, 실제 AEAD/scanner/download/digest, 원래 changed/current product consumer |
| synthetic 경계 | registry SQL/clock/custody/role/commit-outcome는 test dependency이며 실제 DB 권한·운영 key custody 증거가 아님 |

8개 runtime case는 genuine root+approval→changed/current consumer, root scope/time/generation/role preflight, root denied/committed-unknown/ack mismatch/readback drift, unknown key/bad signature/unavailable signer/TTL/clock/backwards/role-before-signing, same-generation root/policy drift-before-ingest, approval denied/committed-unknown/ack mismatch/readback drift, scanner/AEAD tamper-before-writer, live registry denial→original consumer callback/publication 차단이다. 원본 revision/result publication을 생성하지 않는 assertions를 유지한다.

## 실패 보존과 수정

컴파일 r1은 기존 non-Clone issuer error를 포함한 새 enum의 잘못된 Clone derive(E0277 1건)로 실패했다. r2는 SubjectDigest import 2건과 FaultBlob의 잘못된 field 이름 2건으로 실패했다. 당시 전체 workflow/test bytes와 compiler diagnostic code/span, 4-parent manifest bytes를 보존한다. failed build의 전체 input freeze를 현재 상태로 재검증했다는 주장은 하지 않고, 원인 source와 당시 manifest를 해당 frozen hash에 대조한다.

초기 source guard는 rustfmt member-call whitespace를 고려하지 못해 4 PASS/4 FAIL이었다. 원래 guard와 finding을 보존하며 원래 Rust 시점의 in-memory view에서 정확히 4개 실패를 재현한다. whitespace 정규화만 한 수정 전 guard는 같은 시점에서 8개 PASS를 재현한다. 이후 borrowed readback 추출 시 오래된 by-value comparison marker 1건이 실패한 것도 원래 workflow/guard/finding으로 재현한다. actual Rust/SQL 검사를 약화해 통과시키지 않았다.

strict Clippy r3은 needless_pass_by_value/too_many_lines 2건, r4는 too_many_lines 1건, r5는 needless_borrow 8건, r6는 expect_used 6건/collapsible_if 1건으로 실패했다. 모든 receipt와 해당 whole source preimage를 보존한다. 책임별 helper 추출, 정확한 reference 전달, unexpected success를 test error로 반환하는 `denied` helper를 적용했다. lint allow/suppression이나 검사 제거는 없다. r3/r4의 통과했던 8-case 실행은 수정 전 historical 결과이며 현재 재실행으로 승격하지 않는다. r5 EXE는 build-only historical이고 해당 소스로 case 실행을 했다고 주장하지 않는다. 이전 EXE 28개와 P139 이전 EXE 3개를 보존한다.

Windows PowerShell 5의 ProcessStartInfo.ArgumentList 부재로 컴파일 시작 전에 실패한 invocation도 별도 finding으로 남겼다. 실제 Rust process와 receipt가 없는 terminal 상태를 확인한 뒤 지원되는 PowerShell 7로 호출했다. runner나 resource threshold는 바꾸지 않았다.

## 자원·안전·감사

모든 Rust 실행은 한 코어 affinity, BelowNormal, cargo jobs 1, 2초 sampling이다. 시작 전 CPU 85% 이상 또는 available RAM 4096MiB 미만은 실행하지 않는다. 실행 중 CPU 85% 이상 3회 연속, RAM threshold, root WS 2048MiB, time limit에서는 owned child tree만 중단한다. root WS는 child aggregate memory가 아니며 짧은 실행의 WS 0은 peak 미관측이지 메모리를 사용하지 않았다는 뜻이 아니다. 다른 앱을 종료하거나 보호 조건을 완화하지 않았다.

최종 receipt는 `target/p09-121-resource-optimized/p139-provision-{build,list,test}-r7.json`와 `p139-workspace-lint-r7.json`다. 817개 고유 declared source input과 이전 28개 EXE의 전후 SHA-256을 대조한다. 817은 전체 compiler dependency closure라는 주장이 아니다. 소스 검사와 감사 결과는 runtime/native/Gate를 대체하지 않는다.

최종 Build 33.58초, List 0.34초, Test 26.98초, Clippy 8.84초다. 네 실행의 시스템 CPU 관측 최대는 20%, 사용 가능한 RAM 관측 최저는 14060MiB(약 13.7GiB)다. threshold stop은 없었고 terminal 확인 후 cargo/rustc/form_stored_provider 프로세스 부재를 확인했다. 실행 밖의 시스템 CPU는 다른 앱 작업으로 변할 수 있으며 이 결과는 앱 멈춤 원인 해결이나 PC 전체 무결성 판정이 아니다.

`verify_formula_issuer_registry_provision.py`는 P138 checkpoint SHA-256, whole parent preimages를 사용하는 변경 전 역사적 감사, 8개 현재 계약, 5개 실패 guard 재현, 원인 compiler/archive binding, 수정 전 source별 runtime/lint 실패, 현재 inventory/summary/EXE/817 inputs/28 EXE, strict target coverage, 새 report/checkpoint pins를 검사한다. 역사적 view는 in-memory이며 실제 파일을 rollback하거나 과거 검사를 수정하지 않는다. source inventory는 historical graph+declared delta 관례이며 unique path union과 다르다.

접근 허용 창, COM/한글/native, 실제 DB·migration·role 설치, 운영 key/trust 설정, Codex 설정/cache/로그 변경, stage/commit/push, 삭제·이동은 하지 않았다. 사용자 소유 dirty 상태와 PLANS.md 삭제를 유지한다.

## 다음 경계

이 연결은 실제 DB registry/read/write 권한과 CAS/concurrency negative case, 운영 key custody와 issuer 원천 admission, 원자적 publication/제품 통합, native34 후보 재-admission·저장·재열기 검증을 대신하지 않는다. P09 Gate가 권위 있는 실제 결과로 닫힐 때까지 P10으로 넘어가지 않는다.
