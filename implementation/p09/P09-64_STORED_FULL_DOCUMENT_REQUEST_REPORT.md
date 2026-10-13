# P09-64 저장된 전체 문서 IR 제품 요청 구현 결과

- 일자: 2026-10-04
- 상태: **실제 제품 라이브러리의 head-bound full-IR 준비 요청 연결·in-memory component PASS / actual DB·blob 통합과 제품 실행·P09 Gate 미완료**.
- Goal ACTIVE, P10 보류. 접근 허용창/Hwp COM/UI/native dispatcher를 실행하지 않았다.
- 정책: [P09-64_STORED_FULL_DOCUMENT_REQUEST_POLICY.md](P09-64_STORED_FULL_DOCUMENT_REQUEST_POLICY.md).

## 구현

새 `form_product_request::stored_full_document` API는 원래 strict v1 envelope/parser와 provider-owned bindings를 재사용하여 **현재 sealed revision에 연결된 package와 full-document IR**을 통해 준비한다. caller가 IR/artifact/graph/path/authority를 선택하는 새로운 필드는 없다. IR 누락이나 검증 실패는 inventory-only 결과로 대체하지 않는다.

Prepared object는 Deserialize가 없고 Debug는 redacted다. 메모리 HWPX 후보, 전체 target graph, 실제 full-graph compiled plan을 제공하며, fresh verify는 head/source/IR/ACL/AEAD/canonical graph/map/policies/access와 request scope/digest/plan/revision/document을 다시 확인한다. receipt는 별도 profile과 정확한 preparation-only qualification을 갖는다. 기존 하위 receipt의 역사적인 qualification 문자열도 바꾸지 않았다.

signed route는 기존 실제 authority 확인 뒤 계속 거부된다. 준비와 retry digest 계산은 key claim이나 exactly-once publication이 아니다. artifact READ audit 외 ingest/commit/publication/stream initialization이 없음을 검사했다. 현재 CLI executable에 새로운 실행 명령이나 승인 route를 추가한 것은 아니다.

## 실제 실행

- `cargo test --offline --locked -p hwpx-agent-cli --lib --tests`: **86 PASS**, failed/ignored/filtered 0. 6+0+4+10+8+28+18+10+2이며 0개 main target도 실제 실행했다. terminal b9d822/e35e06/252732, 마지막 exit0.
- stored-provider target 28 = 원래16 + 새12 tests. 최종 전체 CLI 실행에서 28 모두 다시 PASS했다. 앞선 단독28 PASS도 878780에 보존한다.
- `cargo test --offline --locked -p artifact-service -p revision-service -p retention-sync-service --lib --tests`: **78 PASS**, failed/ignored/filtered 0, dcd088 exit0.
- 합계 **164 scoped Rust tests PASS**. 테스트 수이지 독립 제품 기능 수나 P09 완료율이 아니다.
- strict four-crate lib/tests `cargo clippy ... -- -D warnings`와 새 Rust 2파일 `rustfmt --check`: 11313f exit0. lint allow/skip을 추가하지 않았다.

새12 tests는 4개 locked whole-package output oracle(5 kinds/empty/reset/clear), whole graph에서 control-state 이외 모든 필드의 정확한 보존, whole-graph selector/base digest/plan/revision, malformed27 cases의 read-audit 없음, provider identity6 substitutions, missing IR/wrong kind/media/3 digests, noncanonical/duplicate IR, projection/wrong document/3 security flags, source와 IR의 독립 ACL, IR AEAD 손상/복구와 source 손상, IR quarantine, 실제 fixture CAS head advancement, map/policies/access/provider drift, canonical retry/key/plan binding/receipt privacy를 검사한다.

fixture manifest SHA는 원래 `8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e` 그대로다. 고정 fixture/기대 output/원래16 assertions/parser/compiler/provider/SQL migration은 변경하지 않았다. 저장소와 scanner/keys/whole caller graph가 synthetic이므로 **actual PostgreSQL+암호화 파일 저장소 제품 통합 검증은 NOT_RUN**이다. P63 metadata DAG 검사에서 사용했던 source/result/IR 재사용도 실제 importer/input chain의 증거로 승격하지 않았다.

## 실패·보존

- 5a8d3e E0583: 새 test module의 path 해석 오류. 정확한 `#[path="full_document/product_request.rs"]`를 지정했다.
- d97953 E0609: 새 test가 control properties를 NodeCommon에서 찾음. 실제 FormControlNode.properties를 사용하게 수정했다. 검증 기대값을 제거하지 않았다.
- 9e2c9c strict lint: doc_markdown, too_many_lines. 주석 표기와 같은 전체 그래프 보존 assertion helper 분리로 수정했다. 모든 assertions를 유지했다.
- 조사 명령의 PowerShell brace-path/foreach pipeline 문법 오류(346975/aa1158)는 read-only 명령 구성 오류다. 정확한 명시 경로/배열 수집으로 재실행했다. 제품 결함이나 PASS로 기록하지 않는다.
- 첫 원장 patch는 hunk 순서 오류로 context 검증에서 거부되어 파일 변경이 없었다. 원래 파일의 줄 순서로 hunks를 정렬하여 다시 적용했다.

변경 전 원래4 files 전체와 실패 시점3 files 전체는 별도 byte-exact archive에 보존했다. 8c95b6에서 기존 source/test 3파일의 선언된 추가분만 제거하고 EOL-normalized 텍스트를 비교하여 원래 body/assertions 그대로임을 확인했다.

최종 보존 수치·source pins는 [P64 원장](evidence/p09-64-stored-full-document-request.source-progress.v1.json)에 있다. P59~P63의206 declared entries, P48 원래1551 files/51,047,460 bytes, native75 전체 hash 보존을 검사한다. 이는 byte 보존 검사이며 **전체 과거 qualification CLI 재실행이나 현재 native admission은 아니다**. 이번에 DB/container/volume을 만들거나 기존 DB/원본/실패 증거를 정리하지 않았다.

## 다음 실제 경계

actual PostgreSQL metadata/revision adapter와 LocalEncryptedBlobStore를 함께 쓰는 새 요청 경로를 실제 실행해야 한다. genuine sealed IR link/worker authorization 및 fresh connection/restart/ACL/AEAD/whole-package parity를 검증해야 하며 synthetic scanner/native importer/issuer 부재는 별도로 표시한다. 기존 P63 DB receipt를 새 경로의 실행 증거로 대신하지 않는다.

이후 complete HWPX importer/provenance, issuer/ExecutionManifest/idempotent publication, IR retention/GC/sync/recovery와 전체 과거 source CLI replay/새 admission이 남는다. earlier P62 16fde8의 underlying cause는 여전히 UNRESOLVED다. current native epoch INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green/P09 완료 false/P10 시작 false를 유지한다. 허용창 금지 동안 native 실행은 하지 않는다.
