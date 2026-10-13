# P09-59 호출자 전체 IR의 폼 변경 준비 계약

2026-10-03. SOURCE/component 범위만 다룬다. 실제 importer, persisted IR artifact,
제품 출판, CAS/idempotency claim, signed route, native 의미/렌더/Gate의 증거가 아니다.

## 실제 입력과 출력

- 실제 공개 `FormOperationPreparation`이 만든 non-deserializable operation만 받는다.
  새 child module은 해당 operation의 실제 typed source/target을 사용하고 fresh
  package/map/policy/access 재검증을 먼저 수행한다. 시험용 source include가 없다.
- `FullDocumentFormContext`는 호출자 제공 `DocumentGraph`, 정확한 canonical graph
  SHA256, source package SHA256, base revision을 결합한다. SHA 일치가 IR의 native
  provenance나 완전한 import를 증명하지 않는다. 현재 `RevisionNode`/artifact storage에
  전체 IR 링크가 없으며 source/result/semantic_diff artifact를 IR로 재해석하지 않는다.
- 직렬화 예산32MiB를 clone 전에 검사하고 default domain graph의 전체 구조/한도를
  재검증한다. 기존 명시적 inventory projection을 거부한다. 보호/암호화/서명된 IR은
  거부한다. 이는 실제 한글 보호 설정에 대한 attestation이 아니다.
- section, nested table cells, nested drawings, notes를 순회한다. 실제 source inventory의
  논리 ID/종류/canonical complete state와 정확히 일치하는 모든 폼이 있어야 한다.
  누락·추가·중복·다른 종류·non-text/비정규/오래된 state를 거부한다.
- typed 변경 컨트롤의 `complete_control_state_json`만 바꾼다. 다른 common fields,
  properties, 문단/표/도형/각주, metadata/settings/security/accessibility, resource/style,
  reference/review/opaque 항목을 유지한다. 변경 없는 폼은 그대로 유지한다.
- 실제 full graph `SelectorSnapshot` 위에 원래 capability/operation ID/원자 그룹/
  dependency/target state를 재컴파일하고 source/target full graph SHA를 arguments에
  결합한다. inventory compiled SHA나 위치를 full graph용으로 재사용하지 않는다.
  full graph 구조 경로는 native XML/COM 위치의 증거가 아니다.
- immutable target/compiled plan/receipt는 fresh 재구성 비교로 검증한다. receipt/debug에는
  문서 값/비공개 경로가 없다. `require_current_product_route`는 실제 기존 VS0 권한으로
  폼 출판을 허용하지 않는다. manifest/route decision/signature를 생성하지 않는다.

## 변경과 과거 증거

- 기존 operation source와 integration test를 수정 전 전체 bytes로
  `source-archive/p09-59-pre-full-document-form/`에 보존한다. 현재 두 파일에서 각각
  새 module declaration만 제거하면 보관 원본과 byte-exact로 일치해야 한다.
- P48–P58의 frozen caps/source guards를 바꾸거나 약화하지 않는다. 이번 선언 추가로
  이전 current guard가 source mismatch를 거부하는 것은 정상이다. 과거 PASS와
  `NOT_RUN` 결과는 과거 source epoch에만 유효하다. 현재 full34 queue 재승인 필요.
- 이번 source-progress receipt는 명시한 파일 hashes와 실제 bounded checks에 관한
  기록이다. whole archived predecessor CLI replay, whole ordinary suites, 모든 dependency
  immutable snapshot의 새로운 qualification을 주장하지 않는다.
- 접근 허용 금지 유지: COM/Hwp/UI/native dispatcher/preflight 호출도 하지 않는다.
  private 원본/후보/plan/과거 실패/native receipt를 덮어쓰기하거나 삭제하지 않는다.

## 검증

`cargo test --locked --offline -p hwpx-agent-cli --test form_value_operation
--test form_value_preparation --test form_stored_provider --test form_stored_product_request
--test form_product_request`의 실제 최종54개(추가9개)와 `cargo clippy --locked --offline
-p hwpx-agent-cli --lib --test form_value_operation -- -D warnings`를 기록한다.
새 파일2개 rustfmt check, 원본2개 exact inverse, 기존 P58 current command의 실제
source rejection을 기록한다. 모든 native/product/Gate 상태는 여전히 미검증이다.
