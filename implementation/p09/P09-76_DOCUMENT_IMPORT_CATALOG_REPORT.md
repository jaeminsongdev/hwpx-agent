# P09-76 original typed header와 actual source style relationships

- 상태: **원본 reader/header/body/fresh authenticated service COMPONENT PASS; formatting cascade/render/security/full importer/정식 제품 실행/P09 Gate OPEN**.
- 정책: [P09-76_DOCUMENT_IMPORT_CATALOG_POLICY.md](P09-76_DOCUMENT_IMPORT_CATALOG_POLICY.md).
- 실제 입력: immutable P75 manifest의 `actual_inputs` 26개. 기존 table generated/readback 16개, note generated/saved/reopened 9개, historical HYPERLINK capture 1개다. 새로 한글을 실행하거나 생성한 native 증거가 아니다.

## 제품 경로 진전

기존 actual Source→body/forms→ranges→meanings 그래프에 없던 header 카탈로그와 실제 문단/run 정의 관계를 연결했다. `CharacterStyleCatalogReader`와 `ParagraphStyleCatalogReader`, 원래 cross-border/fill validation을 그대로 재사용한다. typed character/paragraph 모델도 immutable 파생 모델에 유지한다. 원래 reader가 수치·enum·shape·reference를 거부하면 새 단계도 거부하며 opaque/source-only fallback으로 통과시키지 않는다.

named style/paragraph property/character property 정의는 실제 header element anchor를 갖는다. 각 종류의 native numeric ID 공간을 구분하며 duplicate/count/missing/dangling 관계를 검사한다. logical identity는 원래 document/package/part/span에 묶인다. named style attributes는 raw source 관찰이고 전체 business/type/lock/name semantics 완료가 아니다. nextStyle 관계는 inheritance가 아니므로 `Style.based_on`은 None다. font installation/default substitution/cascade/native render를 추정하지 않았다.

문단 style은 실제 paragraph `NodeCommon.style_refs`에, para property는 원래 paragraph properties에, character property는 실제 source run segment에만 연결한다. run character property를 문단 전체 style에 넣지 않는다. 기존 run source anchor/inline range/text/control/note/bookmark/table body는 그대로 유지한다. 없는 attribute는 default0/caller value를 생성하지 않으며 원래 foreign namespace rejection도 유지한다. typed로 표현된 표·note·drawing의 문단을 순회하며 opaque 아래 문단의 완전한 typed import를 주장하지 않는다.

## 실제 검증

1. readonly bounded header metadata inventory ecb7ee: 입력26/style572/paraPr520/charPr183. 이름·attribute 값·원본 XML은 출력하지 않았다.
2. 원래 readers diagnostic 244983: character26/paragraph26 PASS/errors0.
3. final example strict lint+build af3018: PASS. current executable5917696 bytes/SHA `856353cd0c5655f38ecc1f91313a2ceb59f51260f5591e76b045d23d0a9a1eae`.
4. independent executable d56e3e/e699d4: 각각 exit0/전체 payload exact; 입력26/style572/para property520/char property183/typed paragraph195/run235. 각 original package SHA·header fingerprint·이전/새 graph SHA와 whole fresh receipt를 검사했다.
5. new package tests7 PASS: locked whole corpus, source IDs/relationships/paragraph/run anchors, whole source graph inverse, three body/three named-style dangling refs, duplicate/count, missing/no-default, original foreign rejection, original typed bad-value rejection, numeric bounds/fresh drift/privacy.
6. new stored service tests4 PASS: real original authenticated source services와 direct whole graph equality, no ingest/head write, AEAD tamper/ACL revoke/head advance/tenant·subject·project·branch·document substitutions 거부, 새 profile/scope 각각 독립 full-context denial.
7. full named Rust regression: current CLI126+whole package901=1027 PASS/102 targets/failed0/ignored0/filtered0, domain9+8+15+10=42 PASS, named total1069. terminal9700d6/domain03df38. strict four-crate lib/tests f7d593 PASS; recursive format/diff check c47781 PASS.
8. 이번 source additions를 제거하면 기존 code4 whole raw bytes/SHA가 정확히 복원된다(6a4417). package tests의 whole graph inverse는 새 catalog/style refs/relationship properties만 제거한 그래프가 이전 meanings graph 전체와 equality임을 확인했다.

metadata/revision/blob/scanner/keys/sealed baseline의 저장 테스트는 **in-memory service fixtures**다. 새 actual PG/production policy/scanner/issuer/native acceptance가 아니다. 기존 서비스 ACL/AEAD/source guards를 호출하고 생성 전·후 및 cached verify에서 전체 fresh 검증을 재사용한다. 정상 READ audit 외 ingest/CAS/seal/publication은 없다. 여러 checked head reads는 atomic transaction/lock/idempotency가 아니다.

## 실패 및 원본 보존

`source-archive/p09-76-pre-source-catalog/`에 원본 code4+PLANS122 lines를 whole copy/SHA 보존했다. 초기 probe metadata API 오류2, Flow 필드/audit helper 오류, 원래 foreign guard와 충돌한 새 테스트의 성공 가정, strict function-size/numeric/semicolon failures와 해당 whole new sources도 별도 archives에 보존했다. 새 코드를 refactor하고 새 테스트의 잘못된 가정을 수정했으며 기존 원본 reader/테스트/assertions/guards/skips/hash locks/Cargo dependencies/SQL/authorization을 변경하지 않았다. 이전 실패를 PASS로 덮어쓰지 않았다.

P75 own source454 중 authorized5를 제외한449 파일은 unchanged이며 변경된 원본은 whole archives/inverses로 구분한다. 전체 predecessor3003 pins/original graph1551 files·51047460 bytes/native originals75 파일을 그대로 확인한다. 이것은 preservation이지 원래 전체 qualification CLI의 새 실행이나 native/current admission/Gate PASS가 아니다. 최종 수치·hash·검증 scope는 source progress/final audit에서 고정한다.

## 남은 요구와 다음 경계

전체 catalog/settings/security/importer, 다른 필드·reference·comment 의미, 평가·외부 승인, committed Source→Result→IR input lineage, real policy/scanner/issuer/ExecutionManifest, 게시/idempotency/IR lifecycle/concurrency/crash/recovery/load, whole original qualification replay/current admission은 OPEN이다. 기존 P74 note/P73 meaning/P71 durable forms 및 P75 generated bookmarks는 각 historical scope로 보존한다.

P26 note failed_semantic_non_green/0green, P62 16fde8 UNRESOLVED, current admission INPUT_CHANGED_RE_ADMISSION_REQUIRED, full34 NOT_RUN/0green을 유지한다. Goal ACTIVE/P09 Gate OPEN/no P10. 한글·COM·UI·native dispatcher·접근 허용을 실행하지 않았고 원본 HWPX/trust/config/security/사용자 변경을 손대거나 stage/commit/push/삭제·이동하지 않았다.

- [actual consumer](evidence/p09-76-document-import-style-catalog.actual-consumer.v1.json)
- [Rust regression](evidence/p09-76-document-import-style-catalog.rust-regression.v1.json)
- [initial failures](evidence/p09-76-document-import-style-catalog.initial-failures.v1.json)
- [source progress](evidence/p09-76-document-import-style-catalog.source-progress.v1.json)
- [final audit](evidence/p09-76-document-import-style-catalog.final-audit.v1.json)
