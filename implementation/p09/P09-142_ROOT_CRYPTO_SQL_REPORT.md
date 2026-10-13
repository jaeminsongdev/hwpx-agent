# P09-142 — 원래 root AEAD + 실제 SQL22 통합 증거

## 현재 범위

P141의 credential-bound Rust metadata 증거를 보존하고, 같은 owned PostgreSQL 실행에서 원래 `ArtifactService`의 AEAD 저장/복호화와 `RegistryFormulaProvisioner::install_trust`의 등록·commit ack·재조회 경로를 연결했다. fixture SQL로 root의 artifact metadata를 대체하지 않는다. 새 root는 원래 서비스가 생성한 실제 암호문 metadata와 ACL/audit를 사용한다.

이는 제품 완성의 일부를 검증한 것이며 P09 목표를 root-only 목표로 축소하지 않는다. 승인 서명·원래 제품 consumer·durable blob storage·production key custody·원자적 제품 publication·실제 한글 저장/재열기·Gate는 여전히 미완료다. coarse 잔여 최소6개 그룹/이번에 닫힌 그룹0개, 최소30 세부조건은 전수목록이라고 주장하지 않는다. P09/A12/A13 OPEN, 제품 false, P10 새 구현 없음, goal active.

## 앞선 판단 정정

기본 artifact constructor가 migration1..17 prefix를 확인하는 것은 사실이지만, 이미 기존 `connect_formula_issuer_registry_schema22`가 정확한1..22 fingerprint와 replication 권한 거부를 제공하고 있었다. P142 초기 진행 문서의 “새 경로가 필요하다”는 판단은 불완전했다. 실제 통합은 이 **기존 전용 constructor**를 사용하며, 이를 추가된 `connect_schema22_diagnosed` 실행 증거로 주장하지 않는다.

추가 진단 API에는 기존 schema22 전용 경로와 동일하게 `rolreplication` 거부를 보완했다. 원래 parent는 module declaration 한 줄 외 전체 preimage와 동일하다. 새 API의 실제 DB 연결과 replication-negative 검증은 NOT_RUN이다. 앞선 unit5는 당시 validator 증거이며, 이후 변경된 module의 현재 unit 실행으로 승격하지 않는다. 현재 module과 테스트 소스는 전체 workspace strict lint에서 컴파일 검사됐다.

## 실제 실행과 한계

현재 build-r3와 runtime-run03을 연결한다. root9 검사는 기존 schema22 artifact admission, registry credential profiles, 원래 root workflow, tenant/project/owner/generation/artifact/digest 재조회, 실제 plaintext digest, ciphertext digest, plaintext 비노출, 무작위 생성 public key roundtrip, DB audit를 확인한다. 같은 실행에서 원래 full-IR fixture25, P140 SQL37, P141 Rust metadata42와 fingerprint 제어2도 통과해야 runtime receipt를 승인한다. root history4/max4, approval history3/max3, 양쪽 revocation history2가 남는다.

암호문은 `InMemoryBlobStore`에 존재하므로 재시작 후 durability를 입증하지 않는다. scanner는 제한된 테스트 trust JSON용이며 외부 원본·실제 문서 scanner qualification이 아니다. ephemeral Ed25519 public key 생성/roundtrip은 승인 서명이나 consumer 검증이 아니다. 비밀키·DB 비밀번호는 출력/receipt/소스에 저장하지 않는다. 원래 프로비저너의 historical qualification 문구 역시 현재 외부 DB 검증의 넓은 범위를 대신하는 증거로 사용하지 않는다.

## 보존한 실패와 재검증

- 초기 driver는 실행 파일 regex의 literal-dot 이중 escape 때문에 DB 생성 전에 fail closed했다. EXE bytes/SHA256는 build와 같았다. 초기 driver 전체와 실패 receipt를 보존하고 검사식만 수정했다.
- strict lint-r1의 `doc_markdown` 오류는 주석에 backtick을 추가해 수정했다. root workflow 조건은 변경하지 않았다.
- strict lint-r2의 `expect_used` 오류는 새 unit helper의 버전 생성에서 `expect`를 제거해 수정했다. 검사나 경고를 억제하지 않았다.
- 새 source guard의 초기 실패는 rustfmt 줄바꿈 때문에 발생했다. 공백만 정규화해 같은 필수 코드 token을 확인하며 실제 암호화·digest 조건을 약화하지 않았다. 실패와 guard preimage를 보존했다.

원래 build-r1/r2, runtime-run02, lint-r1/r2, P142 초기 unit/진행 receipt, P141 및 그 이전 실패는 덮어쓰지 않는다. 역사적 source freeze는 전체 preimage의 bytes/SHA256로 대조하고, 현재 build-r3/runtime-run03/lint-r3는 현재 파일에 직접 대조한다. 과거 전수 verifier 그래프를 이번에 다시 실행했다고 주장하지 않는다.

## 자원·운영 경계

빌드/strict lint/Rust probe CPU1, BelowNormal, cargo jobs1. CPU85%3회/freeRAM4096MiB/rootWS2048MiB 중단 guard와 bounded timeout을 유지한다. DB는 새 UUID/전용 label, 로컬에 이미 있는 고정 image, loopback-only port, read-only rootfs/tmpfs, CPU1/RAM512MiB/pids64로 격리한다. 기존 DB나 사용자 데이터에 접근하지 않고 정확한 ID/label/image/isolation을 확인한 자체 테스트 컨테이너만 제거한다. 완료 후 ID와 name 양쪽 부재를 별도로 확인한다.

PostgreSQL 스킬의 최소 권한·forced RLS 지침에 따라 artifact role에는 원래 서비스에 필요한 테이블별 권한만 준다. registry tables/helpers, schema-owner/superuser/bypass-RLS/replication 권한을 부여하지 않는다. 한글/접근 허용/trust·private key 설치/설정 변경/원격push/PLANS 재생성은 하지 않았다. 자원 guard 통과는 Codex freeze 해결 증거가 아니다.

다음 제품 경계는 실제 승인 서명과 원래 consumer를 동일 DB/AEAD 실행에 연결하고, durable storage/custody/원자적 publication 및 원본/native acceptance 증거를 채우는 것이다.
