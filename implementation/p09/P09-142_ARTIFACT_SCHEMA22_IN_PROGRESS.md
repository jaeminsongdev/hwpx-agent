# P09-142 — artifact 정확한 schema22 admission (진행 중)

P141 실제 credential-bound registry metadata44와 strict workspace359 evidence는 그대로 보존한다. 실제 AEAD/Ed25519/원래 consumer/DB를 한 실행에서 연결하는 다음 작업 중 artifact adapter가 migration1..17만 확인하는 prefix admission이라는 점을 확인했다. 기존 API가 schema22를 거부한다고 주장하지 않는다. 기존 API를 수정하지 않고 `LocalPostgresMetadataRepository::connect_schema22` 및 closed-stage `connect_schema22_diagnosed`를 명시적으로 추가했다.

새 constructor는 원래 `connect_diagnosed`의 loopback/fixed tenant/bounded timeout/non-owner role/forced RLS/privilege admission을 먼저 통과해야 한다. 그 후 원래 migration1..22 source fingerprint를 모두 검증하고, missing/changed/out-of-order/추가 version을 거부한다. 23행까지 읽어 future migration을 prefix로 숨기지 않는다. 원래 `scoped` 및 모든 artifact 저장·ACL·audit 연산은 변경하지 않는다. 연결 자격이 issuer authority/custody를 부여한다고 주장하지 않는다.

PostgreSQL 스킬의 최소 권한·RLS 지침을 적용해 기존 검사를 재사용했다. 기존 parent 전체 bytes를 source archive로 보존했고, 새 module declaration 한 줄 외에는 원본 parent가 같다는 guard로 확인한다. P141 과거 source pins의 parent는 이 preimage를 사용해야 하며, 이전 verifier/checkpoint를 현재 파일에 맞춰 덮어쓰지 않는다. 다음 P142 full-history audit에 해당 history view를 연결할 예정이다.

현재 bounded Rust build exit0/diagnostics0, 새 migration-validator unit5 PASS/25 filtered, source guard4 PASS다. prefix17 거부, 정확한22 허용, 22개 각각 changed fingerprint 거부, future23 거부, version ordering/gap 거부를 검사한다. 이는 **unit/소스 증거**이며 새 constructor의 실제 PostgreSQL 연결, 실제 AEAD/signing/consumer/registry 동일 실행, P142 전체 통합, 현재 workspace strict lint는 아직 NOT_RUN이다. 이번 빌드의 whole compiled-input pre-freeze는 수행하지 않았으며 post-build explicit source pins를 그 증거로 과장하지 않는다. 이전 P141 strict lint를 변경된 artifact adapter의 현재 strict lint라고 승격하지 않는다.

빌드 CPU1/BelowNormal/cargo jobs1/test opt1/debug assertions/overflow checks/codegen units1. 180초 상한과 기존 CPU85%3회/freeRAM4096MiB/rootWS2048MiB stop guard를 적용했다. 실제 빌드 약7.24초, CPU 샘플 최대44%, freeRAM 최저14291MiB. unit 실행은0.01초이고 preflight CPU19%/freeRAM14376MiB다. 원래 실패/소스/user dirty/PLANS 삭제를 보존한다. 한글/접근 허용/기존DB/trust/key 설치/원격push/삭제는 실행하지 않았다. Codex freeze 해결이라고 주장하지 않는다.

다음은 새 명시적 artifact constructor와 실제 registry를 동일 owned schema22 DB에 연결해, 원래 ArtifactService가 생성하는 real AEAD metadata/blobs와 issuer signing/consumer를 함께 실행하는 것이다. 부분 구현으로 목표를 축소하지 않는다. goal active, P09/A12/A13 OPEN, 제품 false, P10 새 구현 없음, native NOT_RUN 유지.
