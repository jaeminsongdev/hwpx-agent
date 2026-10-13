# P09-137 — SQL22 발급자 레지스트리 typed read / 제품 경로 연결

## 판정과 범위

P136의 SQL22 metadata 설계에 실제 Rust typed read adapter와 기존 수식 검증 제품 경로 연결을 추가했다. 이 단계의 판정은 **source/component only**다. 실제 PostgreSQL 연결·migration·RLS 실행, 운영 발급자 설치·키 custody, 실제 한글 저장·재열기, atomic 실행·publication 또는 P09 제품 Gate 완료의 증거는 아니다.

P09 / A12 / A13 Gate는 `OPEN`, 제품 완료는 `false`, 목표는 `active`다. P10 새 구현은 시작하지 않았다. 남은 큰 그룹 최소 6개 중 이 단계로 닫힌 그룹은 0개이며 최소 30개 조건은 전수 목록이 아니다. 테스트 개수로 남은 작업이나 완료율을 계산하지 않는다.

## 구현

- `crates/revision-service/src/postgres/source_formula_policy/issuer_registry.rs`: loopback 및 제한된 timeout의 SQL22 전용 연결; 1~22 migration fingerprint와 기존 SQL21 권한 검사를 유지한다. 레지스트리 4개 immutable history table의 강제 RLS·tenant policy·직접 권한 금지와 9개 함수의 소유자/PUBLIC/search_path/EXECUTE 검사를 추가했다. 레지스트리 추가 권한은 root/approval read 2개만 허용하고 helper/관리 함수 7개는 허용하지 않는다. 고정된 context와 `RepeatableRead`에서 typed root/approval metadata를 읽으며 재시도·credential 출력·caller scope 대체를 하지 않는다.
- `crates/artifact-service/src/store/postgres_repository/source_formula_policy/issuer_registry.rs`: 기존 artifact ACL/role/policy/privilege 검사와 정확한 22개 migration admission을 가진 별도 연결 생성자다. 기존 SQL17/SQL21 생성자는 바꾸지 않았다. 이 생성자 자체가 새 레지스트리 함수·테이블의 권한을 모두 검사한다는 주장은 하지 않는다. 상세 레지스트리 검사는 revision adapter의 책임이다.
- `crates/product-cli/src/form_stored_provider/actual_import/source_policy/formulas/issuer/registry.rs`: 읽은 metadata를 기존 approval/trust provider 경로에 연결한다. policy·source head·version·generation·tenant/project/branch/document와 alias를 검사하고, root를 읽은 뒤 artifact ACL/AEAD download 및 SHA-256/size 확인 후 root 전체 metadata를 다시 대조한다. 신뢰한 clock의 역행·만료를 거부한다. 역사적 creator와 권한 있는 현재 reader는 구분한다.
- `.../issuer/registry/trust_wire.rs`: root 및 key의 object-only JSON, unknown/duplicate field, 타입 coercion, positional 배열, trailing payload, key 수/hex/identifier/bounds를 엄격하게 검사한다. 운영 private key를 추가하거나 raw trust payload/key를 Debug에 노출하지 않는다.
- `crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/registry.rs`: synthetic registry metadata/root를 사용하지만 기존 실제 Ed25519 verifier, ArtifactService ACL/AEAD, whole-byte 및 보호된 route 거부 경로를 그대로 실행한다. metadata 신뢰가 서명·보호 검사를 대신하지 않는다. 설치된 제품의 실제 DB 증거로 해석하지 않는다.

기존 부모 파일 4개는 module declaration만 추가했다. 원래 전체 bytes는 `source-archive/p09-137-pre-registry-reads/parent-preimages.v1.json`에 SHA-256과 base64 chunk로 보존했으며 감사가 정확한 변환을 대조한다. 기존 migration 및 이전 검증 runner는 수정하지 않았다. `PLANS.md`를 재생성하지 않았다.

## 최종 소스의 실행 검증

| 검증 | 범위 | 결과 |
| --- | --- | --- |
| Source contracts | 부모 원본·schema admission·SQL columns·scope·권한·strict wire·기존 소비자·resource guard | 8 PASS |
| Registry integration | 새 SQL22 metadata→기존 제품 컴포넌트 경로 | 7 PASS / 0 failed / 234 filtered |
| Revision library | 해당 crate library inventory 전체 | 24 PASS / 0 filtered |
| Product library | 해당 crate library inventory 전체 | 7 PASS / 0 filtered |
| Artifact library | 해당 crate library inventory 전체 | 25 PASS / 0 filtered |
| Workspace strict Clippy | `--workspace --all-targets --locked --offline --jobs 1 -- -D warnings` | 32 packages / 358 distinct targets PASS |

최종 소스 scoped runtime 실행은 총 63개다. Registry의 기존 234개는 이번 실행에서 filtered 상태다. P135에서 확인한 234개 역사적 증거와 보호된 이전 EXE 21개를 보존·재감사했지만, 기존 전체 stored 241개를 현 소스로 재실행했다고 주장하지 않는다. 네 suite 각각의 Build→List→Test receipt는 `target/p09-121-resource-optimized/p137-{registry,revision,product,artifact}-{build,list,test}-r6.json`이다. 최종 Clippy는 `p137-workspace-lint-r6.json`이다.

각 실행의 810개 고유 declared input freeze와 이전 EXE 21개의 실행 전후 SHA-256을 확인한다. 810은 전체 compiler dependency closure라는 주장이 아니다. 테스트 inventory와 실제 통과 이름을 집합뿐 아니라 개수·중복·terminal summary로 대조한다. Clippy는 cargo metadata target inventory와 compiler-artifact identity를 대조하며 경고를 완화하지 않았다.

## 실패 / 보류 / 이전 실행의 보존

- 초기 runner는 PowerShell source 생성 시 문자열 치환 오류로 parse 실패했다. 전체 실패 source는 `p09-137-initial-runner-parse`에 보존했다. child build/test가 시작하지 않았으며 PASS로 기록하지 않는다.
- `p137-registry-build-r1.json`: `Uuid` import 누락, E0433 6건. 해당 전체 test source 보존.
- `p137-registry-build-r2.json`: `BranchId` import 누락, E0433 1건. 해당 전체 test source 보존.
- `p137-registry-test-r3.json`: 6 PASS / 1 FAIL / 234 filtered. 잘못된 artifact kind/media negative fixture가 같은 digest의 다른 domain으로 ingest되어 원래 content-address guard에서 충돌했다. 서로 다른 유효 JSON whitespace bytes로 fixture를 분리했으며 제품 content-address 검사를 약화하지 않았다. 실패 source 및 r3 EXE를 보존한다.
- r4 source index 관측은 10초 timeout으로 build/test 시작 전 종료했다. 실행 receipt/EXE가 없는 관측 실패이며 테스트 PASS나 runtime 완료로 세지 않는다.
- `p137-registry-list-r5.json`: 시작 전 전체 CPU 100%로 `DEFERRED_RESOURCE_PRESSURE_NOT_STARTED`. threshold 변경 없이 terminal/owned process 부재와 fresh resource를 확인한 뒤 r5b 새 receipt로 재개했다.
- r5b List/Test는 7 PASS였으나 이후 strict lint 수정 전 소스다. 이전 실행으로만 보존하며 현재 소스의 PASS로 승격하지 않는다. r5 EXE도 보존한다.
- `p137-workspace-lint-r5.json`: wildcard import / checked conversion의 2개 strict Clippy 오류. 변경 전 새 Rust source 5개 전체 bytes를 `p09-137-pre-strict-lint/source-preimages.v1.json`으로 보존하고 explicit import 및 checked conversion을 수정했다. 최종 r6은 clean PASS다.
- 초기 historical auditor가 부모 수정 파일까지 이전 source inventory에서 제외한 오류를 발견했다. 전체 실패 감사 source는 `p09-137-initial-historical-filter`에 보존했다. 변경 부모를 빼지 않고 전체 원본 bytes로 과거 시점을 읽는 방식으로 고쳤다. 과거 검사를 삭제하거나 권위 있는 파일을 rollback하지 않았다.

## 자원 / 앱 멈춤과의 구분

모든 Rust Build/Test/Clippy 실행은 CPU affinity 1개, `BelowNormal`, cargo jobs 1이다. 2초 sampling, 전체 CPU 85% 이상 3회 연속 / available RAM 4096MiB 미만 / 실행 root working set 2048MiB 초과 / duration 제한이면 소유한 child tree만 중단한다. 다른 앱을 종료하거나 threshold를 완화하지 않는다.

최종 12개 Build/List/Test receipt의 available RAM 최저는 10201MiB다. 전체 CPU 100%의 일시 sample은 있었지만 3회 연속은 아니었다. 그 부하를 이 테스트 때문이라고 단정하지 않는다. 최종 Clippy는 19.68초, 전체 CPU 최대 50%, available RAM 최저 18961MiB다. 짧은 실행에서 working set 양성 sample 부재는 peak 0 또는 메모리 사용 없음의 증거가 아니다. root working set은 child tree aggregate memory가 아니다.

사용자가 보고한 코덱스 멈춤은 Windows Application Hang 1002에 실제로 기록됐다. 최근 2026-10-06 03:19:35 KST 기록은 최종 Clippy terminal sample 약 14초 뒤지만 시작 시각과 인과관계는 미확정이다. 검증이 없던 구간의 앱 오류와 약 332MiB의 세션 파일도 후보다. CPU·RAM 기반 원인 확정이나 앱/PC 전체 정상 판정은 하지 않는다. 추가 빌드 대신 감사·문서 작업만 진행하며 앱 설정·trust DB·캐시·세션을 수정하지 않는다.

## 권위 있는 감사와 다음 경계

`tools/p09/verify_formula_issuer_registry_reads.py`가 P136 checkpoint fingerprint, 전체 부모 원본 시점의 기존 역사적 감사, 현 source guards, 모든 accepted receipt/executable/input, 실패 source와 receipt, 이전 EXE, strict lint target coverage 및 새 checkpoint pins를 대조한다. 감사는 실행 전후 파일 원본을 되돌리지 않는다. 과거 view는 인증된 전체 bytes의 메모리 read 대체이고 새로 추가한 경로만 과거 inventory에서 제외한다. 감사 대상 및 개수는 checksum 원장에 고정한다.

PostgreSQL 스킬의 최소 권한·강제 RLS 지침은 admission 검토에 적용했으며, 스킬 자체 또는 static check를 실제 RLS 실행 증거로 사용하지 않았다.

다음 구현은 SQL22 관리 write/register/revoke adapter와 발급·설치 경로다. owner/CAS/head/tenant/재시도 금지 및 original source 보존 경계를 갖춘 실제 제품 경로가 필요하다. 이후 실제 DB negative case, issuer provisioning/private-key custody, atomic execution/publication 통합, 실제 한글 저장·재열기와 native 후보 재-admission이 별도 남는다. 접근 허용이 필요한 작업은 이번 단계에서 실행하지 않았다. native34는 `NOT_RUN / INPUT_CHANGED_RE_ADMISSION_REQUIRED`를 유지한다.
