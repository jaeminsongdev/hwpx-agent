# P09-67 실제 원본 기반 본문·표 구조 변환 결과

- 상태: **partial source-backed body structure component PASS / complete typed importer·실제 저장 계보·제품 실행·native·Gate 미완료**.
- 정책: [P09-67_DOCUMENT_IMPORT_STRUCTURE_POLICY.md](P09-67_DOCUMENT_IMPORT_STRUCTURE_POLICY.md).
- 원본 source-stage module에 structure declaration 추가, 실제 typed mapper, 기존 문단 validator의 tree 기반 private 재사용과 명시적 source-preserving parameter profile, 기존 table validator의 private tree reader를 구현했다. 제품 full-document context에는 partial profile/scope 거부만 추가했다.
- 원본 위치가 연결된 문단·본문 내 객체·실제 grid/cell·중첩 표·Unicode/tab/break/run 경계를 변환한다. 미지원 의미는 원본 그대로 보존한다. resource SHA descriptor는 실제 persisted Artifact object가 아니다.

## 현재 범위 검증

| 검증 | 실행 근거 | 결과 / 정확한 범위 |
|---|---|---|
| package named Rust suites | b61294 / 1d8ab8 | 179 PASS: lib35/source10/structure14/binding1/color10/package-output19/package17/value22/root12/graph8/preservation7/text12/table12 |
| 제품 CLI lib/tests | 634004 / b9d4ae / af8e37 | 88 PASS: 6/0/4/10/8/28/18/10/2/2; 실제 partial importer의 full-context 거부 포함 |
| strict lint | 601975 | package/CLI/artifact/revision `--lib --tests -D warnings` PASS; allow/skip 없음 |
| example lint / format / scoped whitespace | 2c0f72 | 새 importer probe2 strict lint, 관련 Rust9 rustfmt check, scoped git diff check PASS |
| 현재 executable build | 957bdd | 실제 form/table consumer2 build PASS |
| 독립 fresh processes | f684e1 | form10와 table16 각각 두 fresh processes/동일 consumer executable/모든 결과 exact; 각 import는 whole source 및 graph fresh 재구성 수행 |
| 기존 검증·원본 보존 | fbfbe5 | P59~P66 declared pins379 / original graph1551 files·51047460 bytes via24 explicit archive origins / native75 files exact; whole original CLI replay는 하지 않음 |
| 기존 테스트·공개 reader 경계 | ad2274 | 기존 TextFlow/Table tests 수정 없음 / 앞선 structure11 테스트 전체 텍스트 exact / 공개 envelope 및 TypedParagraph default 유지 / parameter 보존은 explicit private opt-in |

총 named Rust tests **267**이며 16개 새 테스트(structure14/제품partial2)를 포함한다. 전체 Python/과거 qualification CLI/제품/native/Gate 테스트가 267 PASS라는 뜻은 아니다.

### 실제 HWPX 26개

- P09-42 locked source/output10: 실제 section18 / paragraph36 / opaque140 / resolved node anchors176 / retained parts118. 이 form corpus에는 표가 없다.
- P06-09 locked generated/saved table8쌍 =16: section16 / paragraph160 / table16 / cell128 / opaque144 / node anchors320 / retained parts176. 각 2×4 grid·master cells8은 기존 authoritative table evidence와 일치한다. 모든 셀 본문이 실제 원본 text를 가진다.
- 합계 section34 / paragraph196 / table16 / cell128 / opaque284 / node anchors496 / preserved parts294. case 수나 opaque node 수는 기능 완료율이 아니다.
- form executable SHA `6bc270e7aa25882ae96bfac2551275950a4fb2bfb729c759da9357b5023601e6`.
- saved-table executable SHA `78b7b5ba07d0e262ad4b63125c20a4f8aade58fbd0178292e17f4940a9077967`.
- table authority SHA `edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5`; 전체16 file bytes/SHA도 exact(44439c).

병합2×2/중첩1×1/본문 내 객체 순서와 section 간 duplicate native ID는 합성 complete ZIP으로 검증했다. 실제 저장된 병합·중첩 표 corpus 및 전체 table 기능 의미 acceptance로 승격하지 않는다. 필드/수식 parameter는 opaque로 남으며 평가·readback 의미 검증 결과가 아니다.

## 실패와 변경 보존

- initial actual table16은 2d36f4에서 모두 `text_flow_unsupported_shape`로 실패했다. 실제 fieldBegin의 parameters가 기존 typed paragraph reader의 empty-field profile 밖인 것이 원인이다. 초기16 FAIL receipt와 mapper/consumer whole source를 보존했다. 공개 reader를 느슨하게 바꾸거나 실패 case를 제외하지 않고 explicit private source profile을 추가했다. 이후 all16 import/grid/fresh checks PASS.
- 새 compiler/lint fixture 오류와 private API 오인, 새 테스트 closing brace 누락, raw-string/is_err lint 오류를 모두 new failure JSON과 whole archives에 유지했다. 원래 parser/unsafe XML/field stack/table grid/product routing guards 또는 기존 assertion 제거 없음.
- original five source/ledger 및 initial/intermediate sources를 `source-archive/p09-67-*`에 whole bytes로 보존했다. P09-66 source receipts와 모든 이전 epoch를 수정하지 않았다.
- 앞선 c54332의 문단 core text comparison은 parameter profile 추가 **전** 소스에 대한 기록이다. 최종 문단 소스가 단순 extraction만 바뀌었다고 주장하지 않는다. 최종 public compatibility 근거는 기존12 tests, explicit default/profile 분리와 parameter negative cases이다.
- P62 `16fde8` 원인과 whole current admission은 여전히 미완료다. old native full34는 NOT_RUN/0green, P09 Gate OPEN이다.

## 다음 실제 작업

실제 source의 폼·필드·노트·참조·스타일/resource catalog·security를 typed 의미로 변환하고 full-document provider와 연결해야 한다. 그 후 실제 Source/Result/IR provenance와 previous-result→input chain, issuer/ExecutionManifest/idempotent publication, IR lifecycle/동시성·복구·전체 replay/current admission이 남는다. signed route는 아직 허용하지 않는다.

실제 source-backed partial graph를 full-document 제품 input으로 넘길 수 없도록 추가 거부를 검증했다. arbitrary caller graph에 importer issuer 권위가 생긴 것은 아니다. P65 PostgreSQL/LocalEncryptedBlobStore 결과는 여전히 synthetic prior Source/caller IR/scanner/authority 범위다.

한글/COM/UI/접근 허용창·DB 생성·global/system/security setting·dependency 변경·commit/push·P10 구현 없음. Goal ACTIVE/P09 OPEN.
