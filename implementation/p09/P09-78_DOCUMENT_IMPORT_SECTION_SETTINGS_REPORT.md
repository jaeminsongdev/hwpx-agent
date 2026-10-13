# P09-78 페이지·단 설정의 실제 source 연결

- 상태: **actual source binding/fresh consumer/authenticated service/원본 보존 COMPONENT PASS. Rust 1089 PASS. 전체 settings/importer/product/native/P09 Gate OPEN**.
- 정책: [P09-78_DOCUMENT_IMPORT_SECTION_SETTINGS_POLICY.md](P09-78_DOCUMENT_IMPORT_SECTION_SETTINGS_POLICY.md).

## 구현 결과

원래 페이지·단 reader를 변경하지 않고 P77의 immutable security graph 뒤에 실제 section 설정을 연결했다. 전체 source-spine 순서, 실제 header secCnt, page/body metrics, 모든 column span과 기존 section/source-part ID를 함께 검증한다. 누락·중복·잘못된 count/여백/폭/gap은 거부하며 기본값이나 일부 section으로 대체하지 않는다.

graph에 추가한 2 metadata·2 settings·각 section의 4 source property만 제거하면 원래 P77 graph 전체가 동일하다. 기존 native security 상태·form·note·bookmark·style·body·resource를 바꾸지 않는다. 원래 reader의 WIDELY/Portrait 및 NARROWLY/Landscape mapping을 그대로 보존했고 이 결과를 native render 정답으로 승격하지 않았다. 공개 실행 action/raw XML/임의 caller 설정은 추가하지 않았다.

## 실제 입력과 확인된 검증

1. P77 잠긴 실제 36개: table generated/readback16 + note9 + historical hyperlink1 + native form source/output10. 페이지44·column span44·section 경계8·source anchor176을 확인했다. 모든36에서 원래 graph inverse가 exact다. 초기 filename-entry reader diagnostic은 따로 whole source를 보존했으며 final source-spine 소비 증거로 사용하지 않았다.
2. 현재 executable 두 독립 process의 전체 payload가 동일하다(2fc95c). executable6948864 bytes/SHA `9b2318472c645e4f3409aa46e0e7b92c28b992a489f1800c64810e674c019c50`. fresh 원본 전체 identity/이전 모델을 검증한 뒤 immutable source에서 새 settings를 결정적으로 재구성해 whole equality를 확인했다.
3. 새 package5: actual36 원래 reader/definition/metrics/출처/whole graph inverse, original26이 frozen36의 byte-exact prefix임을 확인, 잘못된 폭·여백·secCnt·gap 거부, missing/duplicate page 거부, fresh raw ZIP drift와 원래 security 상태 보존. 새 service5: direct/stored whole equality와 무쓰기, 생성·cached ACL/AEAD/head 거부, scope5 변조 거부, 각 partial qualifier 단독 full context 거부, actual form source/output10.
4. current full CLI136 + package911 + domain42 = 1089 PASS. CLI/package104 test targets, domain4 targets; failed0/ignored0/filtered0. terminal5c7e44 및 regression receipt의 전체 chunk/count 기록. strict4-crate lib/tests939d6a에 이어 실제 명령을 명시한 fresh5-crate lib/tests9b96c3, example strict/buildbdfead, format/diff checkcf5df9 모두 exit0. 5개는 hwpx-package/hwpx-agent-cli/artifact-service/revision-service/domain-ir다. 원래 reader/domain/dependency/tests/assertions/guards/skips를 바꾸지 않았다.
5. 서비스 최적화는 새 layer의 마지막 중복 순수 재구성만 제거하고 원래 authenticated source checkpoint를 유지했다. 먼저 기존 security/source 전체 검증, 새 settings 재구성, 마지막 live source 검사 순서다. 마지막 원래 checkpoint는 scope/head/artifact/descriptor/ACL/quarantine/AEAD/raw bytes/form/receipt를 그대로 검증한다. 같은5 tests는 최적화 전349.75초(862c5c), 후251.86초(d417d9)에 PASS했다. 동시 작업이 달라 통제된 benchmark나 일반 성능 개선율을 주장하지 않는다. 이는 in-memory 저장 service fixture이며 실제 PG/issuer/atomic transaction/production acceptance가 아니다.
6. 4개 source inverse3f0a68 exact: module declaration2, 새 test module, 새 partial helper/call만 제거하면 변경 전 전체 bytes/SHA가 같다. 원본5개를 whole archives로 보존했다. P77 unchanged472, predecessor4015 pin entries, original1551 files/51047460 bytes, native originals75 exact(e030f4). original graph archive25는 필요한 hash match의 실제 선택 수이며 모든 archive 수와 혼동하지 않는다. 보존 확인은 원래 전체 qualification 재실행을 뜻하지 않는다.

## 실패와 남은 작업

새 source helper121/100 및 full context101/100 strict lint 실패를 whole archive와 receipt에 보존했다. 새 helper 분리로 수정했고 기존 P77 guard는 새 helper가 먼저 호출한다. 보존 audit를 만드는 문자열 치환이 원래 byte total까지 바꿔 count guard가 거부한 실패77ac2f도 whole script로 남겼다. 원래 manifest/원본 총량51047460을 유지해 새 audit만 수정했으며 기대값이나 predecessor hashes를 갱신하지 않았다.

최종 audit 전의 regression 초안에서 strict 대상 목록을 잘못 추정한 것도 기록했다. 실제 명령을 명시한 fresh5-crate strict 검사를 통과한 뒤 기록을 수정했고 두 초안은 전체 bytes/SHA가 같은 별도 archive에 보존했다. 처음 복사에 console 최종 newline 1 byte가 추가된 실패d79b1f도 별도로 남겼다. 성공하지 않은 draft-copy를 exact로 간주하지 않았다.

이번에는 source page/columns 연결만 닫혔다. 전체 catalog/settings/security/importer와 다른 field/reference/comment 의미·값 평가·외부 승인, 실제 committed Source→Result→IR lineage·policy/scanner/issuer/ExecutionManifest, publication/idempotency/IR lifecycle/concurrency/crash/recovery/load, original whole qualification/current admission은 남아 있다. 다음에는 이 미완료 제품 경로를 구현·검증한다. 이미 닫힌 source wrapper를 반복하거나 native 결과를 추정하지 않는다.

P26 `failed_semantic_non_green`/0green, P62 `16fde8_UNRESOLVED`, `INPUT_CHANGED_RE_ADMISSION_REQUIRED`, full34 `NOT_RUN/0green`을 유지한다. Goal ACTIVE/P09 Gate OPEN/no P10. 한글·COM·UI·native dispatcher·접근허용·stage/commit/push·원본 삭제/이동·trust/config 변경을 실행하지 않았다.

- [actual consumer](evidence/p09-78-document-import-section-settings.actual-consumer.v1.json)
- [initial failures](evidence/p09-78-document-import-section-settings.initial-failures.v1.json)
- [Rust regression](evidence/p09-78-document-import-section-settings.rust-regression.v1.json)
- [source progress](evidence/p09-78-document-import-section-settings.source-progress.v1.json)
- [final audit](evidence/p09-78-document-import-section-settings.final-audit.v1.json)
