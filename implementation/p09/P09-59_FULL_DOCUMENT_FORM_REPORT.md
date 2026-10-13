# P09-59 전체 IR 폼 변경 준비 제품 모듈

2026-10-03. 접근 허용 금지 상태에서 실제 Rust 제품 library 경로를 구현했다.
목표는 ACTIVE이고 P09 Gate는 열려 있다. COM/Hwp/UI/native 실행은 하지 않았다.

## 결과

`form_value_operation::full_document`는 실제 typed 폼 operation을 받아 호출자가
제공한 전체 IR의 해당 컨트롤 상태만 변경한다. 기존 inventory projection을 full IR로
승격하지 않는다. 실제 전체 IR의 논리 ID/구조 경로에서 operation compiler를 다시
사용하며 source/target full graph digest를 plan에 결합한다. 문단·표·도형·각주·다른
폼, common fields/properties, catalogs/references/review/opaque 등을 보존한다.
누락/추가/종류/state 불일치, stale revision/document/package/graph, access 철회,
보호/암호화/서명된 IR을 거부한다. immutable receipt/debug에는 실제 문서 값이 없다.

현재 `RevisionNode`는 source/result/semantic_diff artifact만 연결하며 full IR artifact
연결은 없다. 따라서 이번 API의 full IR은 **호출자 제공·미인증 provenance**다.
실제 HWPX full import, persisted IR 조회, 저장소 제품 요청 연결, signed form route,
manifest/CAS/idempotency/publication, native 의미/렌더/차등/Gate는 구현 완료로 세지 않는다.
기존 VS0 signed attestation을 폼 출판 권한으로 재사용하지 않는다.

## 실제 검증

- 최종 실제 `cargo test --locked --offline -p hwpx-agent-cli --test form_value_operation
  --test form_value_preparation --test form_stored_provider --test form_stored_product_request
  --test form_product_request`: 5개 suite **54 PASS**, ignored/filtered/fail 0.
  최종 tool session82207/chunks93f03c,53ccbc,bfc930 exit0. 이전 동일5 suite43484도54 PASS.
- 추가9개 실제 public API tests: 5종6컨트롤, defaults/reset/empty/clear, 두 section,
  nested table→drawing, notes, 전체 form source/target state 일치, 전체 non-form JSON
  보존, 원본 graph/candidate bytes 보존, full graph compiler source identity/구조 경로,
  binding/state/security/access negative cases 및 현재 signed route 거부를 검증했다.
  이 IR은 테스트가 제공한 것이며 실제 importer/native 위치 증거가 아니다.
- 최종 `cargo clippy --locked --offline -p hwpx-agent-cli --lib --test form_value_operation
  -- -D warnings`: exit0(93f03c). 새 파일2개 rustfmt check exit0(0fe240).
  초기 compile/clippy 실제 실패들은 별도 initial-failures receipt에 남겼다.
  검사 약화/lint allow/부정 증거 삭제 없이 새 소스와 테스트를 고쳤다.
- 기존 source18168/SHA29f350da 및 integration test29526/SHA13c9be74 전체 bytes를
  새 source archive에 보존했다. 새 module declarations23/69 bytes만 제거하면
  archived originals와 **두 파일 모두 byte-exact**(0fe240)다. 사용자 기존 변경 보존.
- 수정 직전 기존 P58 actual `--current`는 exit0/NOT_RUN/0(01e9ff).
  수정 뒤 **같은 실제 command가 exit1/fail/ValueError**(c83169): frozen dependency
  source identity가 바뀌었으므로 정상적인 source rejection이다. 과거 source capsule,
  expected locks/guard functions를 변경하거나 old current PASS로 재작성하지 않았다.
- 과거 native75개는 실제 기존 binder로 다시 hash 확인, 전부 원래 SHA 일치(c12dc4).
  Hwp process count0. 전체 native dispatch/current 수락 증거는 생성하지 않았다.
- 원래 P48 capsule418689/SHA`d68d07c05a13422d58b35fda228e4ab6766418a8c10f70954871a37747b95d44`
  에 기록된 전체1551-file/51047460-byte source graph를 실제 한 번 순회했다(456fe4).
  변경2개는 새 byte-exact archive origins로만 결합하고 다른1549개는 원래 경로/해시로
  검사해 전부 일치했다. 이것은 완전한 **파일 hash 보존 검사**이며, old CLI/전체 test
  재실행이나 새 current admission을 대신하지 않는다. P58 원래 direct8 source pins도
  모두 동일하고 SDK17 attempt directories0/P56·P58 dispatch 및 P56 current 모두 없다(dd737c).
- 새 scoped source-progress receipt5453 bytes/SHA
  `7b591f5ff59837faebde7884e0b8dd2389a19ab46be62f783dc92ff81aab1b06`
  의 실제 source/archive8 pins를 독립적으로 재확인했고, 새2 파일 rustfmt와 PLANS
  diff-check가 exit0(4a59d7)다. receipt는 full source chain/native Gate 자격증이 아니다.

## 남은 작업과 다음 경계

1. 현재 source epoch에 대해 immutable changed-source archives를 실제 predecessor
   source graph origin에 결합하고 **원래 전체 CLI/source 재현** 및 새 native admission을
   검증해야 한다. 이번 receipt는 scoped source-progress일 뿐 whole chain 재현이 아니다.
   P48–P58의 과거 current PASS는 과거 source epoch 증거이고 현 full34 queue는
   `INPUT_CHANGED / RE_ADMISSION_REQUIRED`다. 실행 대기열이 현재 준비됐다고 말하지 않는다.
2. 저장소 full IR snapshot/artifact 계약과 genuine full importer를 연결한 뒤 기존 stored
   product request와 새 모듈을 이어야 한다. semantic_diff/result를 IR로 가장하지 않는다.
3. 접근 허용이 다시 명시 허용되면 먼저 현재 epoch 전체 admission을 닫고, 기존 승인된
   SDK17→automation15+2의 **한 번의 full34** 큐로만 native 검증한다. 작은 배치 금지.
4. SDK baseline은 human direct oracle이 아니다. 원래920pixel 차이의 수정/실제 의미,
   native lifecycle/package/full-page render/차등/출판/Gate는 여전히 미검증이다.
   P10으로 넘어가지 않는다. 이번 구현을 전체 P09 완료율 또는 green row로 환산하지 않는다.
