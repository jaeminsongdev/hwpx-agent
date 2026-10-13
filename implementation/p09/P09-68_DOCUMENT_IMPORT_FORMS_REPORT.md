# P09-68 실제 원본 기반 관측 폼 IR 결과

- 상태: **actual source-backed observed-form component PASS / defaults·validation policy·complete typed importer·persisted lineage·실행·native·Gate 미완료**.
- 정책: [P09-68_DOCUMENT_IMPORT_FORMS_POLICY.md](P09-68_DOCUMENT_IMPORT_FORMS_POLICY.md).
- 새 forms importer/test/fresh probe와 제품 거부 test를 추가했다. 기존 source module은 declaration1줄만, 제품 full context는 observed partial metadata 거부만 추가했다. 기존 native/package/body/text/table readers와 assertions, dependencies/Cargo.lock 변경 없음.
- caller map/graph/state 없이 실제 immutable source anchor에서 map을 만들고, unchanged NativeFormPackageReader로 whole actual package를 읽는다. 본문의 실제 XML object를 같은 node/common/inline 위치의 FormControl로 변환한다.

## 검증

| 검증 | 실행 근거 | 결과 / 범위 |
|---|---|---|
| 신규 actual form tests | c416b1 → 172201 / 6ecf72 | 최종10 PASS: locked10/actual anchor/non-form full parity/no policy inference/native malformed+catalog/duplicate ID/no form/fresh identity/privacy/real table16/prefix alias |
| package named Rust suites | 6ecf72 / e28257 | 189 PASS: lib35/form-import10/source10/structure14/binding1/color10/package-output19/package17/value22/root12/graph8/preservation7/text12/table12 |
| product CLI lib/tests | a4c7ab / 9ad883 / 602e06 | 89 PASS: 6/0/4/10/8/28/18/10/1/2/2; actual observed 5-kind graph의 기존/new partial marker 각 독립 거부 |
| strict lint/build | ece523 | package/CLI/artifact/revision lib/tests 및 fresh example `-D warnings`, consumer3 build PASS; allow/skip 없음 |
| fresh actual forms | 6f19a5 | 두 fresh processes, 모든 receipt exact, source10/typed forms50/kinds10·8·16·8·8/all node anchors176 |
| 기존 실제 본문·표 | 같은 실행 | unchanged P67 body10/table16 receipt 전체 exact; old executable/current-admission을 재승인한 것은 아님 |
| source compatibility | b1f768 | root module declaration-only inverse/product guard additive-only inverse exact; native_form_hwpx/package 및 P67 structure/text/table whole SHA exact |
| 포맷/공백 | c47c80 | Rust6 rustfmt check/scoped git diff check PASS |
| 이전 보존 | 744e3f | prior declared pins459/original graph1551 files·51047460 bytes via24 original archive origins/native75 files exact; whole original CLI replay 아님 |

최종 named Rust tests **278 = package189 + CLI89**, 신규11 포함. 범위 밖 전체 Python/legacy/current qualification/native/제품/Gate PASS가 아니다. 형식·참조·권한 validator를 약화하거나 기존 assertion을 삭제하지 않았다.

### 실제 관측과 남은 의미

- locked P09-42 source/output10 사례에서 누적 typed 폼50개: edit10/check8/radio16/combo8/list8. unique source SHA는8개이며 반복되는 source/output도 각 manifest path/bytes/SHA에 따라 검사했다. 50은 서로 다른 native 실행 또는 독립 폼50개라는 뜻이 아니다. 동적으로 만든 caller inventory를 원본처럼 사용하지 않는다.
- corpus는 캡처 원본을 사용하는 actual case1쌍과 기존 파생 5-kind/empty/reset/clear 사례4쌍이다. 현재 import는 모든 실제 파일 bytes를 읽지만, 파생 패키지를 새 한글 저장·native/UI acceptance로 승격하지 않는다.
- every form raw subtree SHA/actual element anchor/real paragraph+run+inline placement를 검증했다. source에 native ID가 없으면 Missing 그대로이며 내부 component 예약 번호가 IR/native identity로 노출되지 않는다.
- 비폼 전체 IR를 원래 노드로 되돌렸을 때 metadata/security의 명시적 추가 항목 외 original graph 전체와 exact하다. 본문·표·객체·원본 resource/opaque bag이 사라지지 않는다.
- P67 actual table16은 새 form API에서도 body/cell 구조를 보존하며 forms0/native bindingNone이다. synthetic namespace alias fixture는 원본의 namespace 의미를 유지하며 actual native values와 일치한다.
- 모두 기존 legacy reference state **id_index_validation_failed**이며 independently verified native overlay issues 총100을 그대로 receipt에 남겼다. legacy index PASS/전체 reference semantics PASS로 바꾸지 않았다.
- fresh executable SHA `b0ee4f6c68b6569c0d7f0d349a51e21498291ca59e8401d23fd87cc6f8ce124e`.
- typed form은 native 관측 값/속성만 가진다. default/reset/required/external validator 등의 완전한 정책이나 caller-qualified `complete_control_state_json`을 만들어내지 않는다. 따라서 새로운 observed profile/scope만 남겨도 product full context가 거부한다.

## 실패 보존

- 4a7264: 새 코드가 PropertyValue::Bool을 추측해 E0599 발생. 원래 Boolean enum variant를 사용하도록 수정, initial whole source 유지.
- 91c5f1: 새 import105줄 strict lint FAIL. 같은 observation helper로 분리, 검사 allow/skip 없음. whole source 유지.
- e80d13: 새 tests6PASS/2FAIL. derived test ZIP이 mimetype을 첫 entry로 넣지 않아 source Graph 거부, 그리고 5-kind fixture의 두 section에 모두 edit가 있다고 가정했다. product reader/거부 조건을 바꾸지 않고 test ZIP을 원래 HWPX 계약대로 만들고 실제 namespace-aware native form을 선택해 duplicate ID를 주입했다. 원래 native-ID rejection 기대값과 전체10 case 유지. failed test whole source 보존.
- helper extraction 첫 patch는 포맷된 import context 불일치로 원자적으로 거부됐다. 실제 function anchor로 재적용했으며 숨겨진 변경 없음.
- original three source/ledger와 failed/intermediate source를 `source-archive/p09-68-*`에 whole bytes로 보존했다. P67/P66 및 더 오래된 실패·private native 증거를 수정/삭제하지 않았다.

P62 `16fde8` 원인은 여전히 UNRESOLVED이며 전체 current qualification CLI replay/admission은 이번에 하지 않았다. P65 DB acceptance를 이번 actual importer→persisted full request 증거로 재사용하지 않는다.

## 다음 실제 작업

actual observed form에 명시적인 defaults/validation policy를 권위 있는 provider에서 연결하고, 필드·노트·참조·style/catalog/security의 완전한 typed document 의미를 구현해야 한다. 그 후 actual Source/Result/IR provenance/previous-result→input, issuer/ExecutionManifest/idempotent publication, IR lifecycle/복구/동시성/whole replay/current admission과 실제 native acceptance가 남는다.

한글/COM/UI/접근 허용창·DB·system/trust 변경·dependency 추가·stage/commit/push·P10 구현 없음. Goal ACTIVE/P09 Gate OPEN/current native admission INPUT_CHANGED/full34 NOT_RUN/0green.
