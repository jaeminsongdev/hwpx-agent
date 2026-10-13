# P09-75 source point-bookmark anchor와 fresh 이름 선택

- 상태: **generated whole source anchor / authenticated stored-service COMPONENT PASS; positive native bookmark/internal-link/name semantics/product/P09 Gate OPEN**.
- 정책: [P09-75_DOCUMENT_IMPORT_BOOKMARKS_POLICY.md](P09-75_DOCUMENT_IMPORT_BOOKMARKS_POLICY.md).
- 원본 P13은 static-section integration scope이며 이번 결과로 native/Gate에 승격하지 않았다.

## 구현과 증거 구분

기존 P13 `bookmark_projection`을 새 source-only envelope에서 그대로 재사용했다. 실제 HP `ctrl/bookmark` marker의 빈 point/name-only/parent/wrapper/whitespace/XML·name byte 한도 검사를 유지한다. 기존 parser/projection/typed lowering/domain name business 규칙을 수정하지 않았다. envelope는 name과 실제 wrapper/paragraph element 위치만 반환하며 native Para ordinal이나 jump 권위를 노출하지 않는다.

원래 opaque XML wrapper/common/resource/properties와 ControlRef를 보존하고 source-derived BookmarkAnchor/Reference/marker·paragraph·inline stream 위치를 연결한다. Reference.target_node_id는 실제 marker wrapper node이지 해석된 내부 hyperlink 목적지가 아니다. 모든 section HP marker와 관찰 anchor 집합이 정확히 일치해야 하며 malformed/hidden/unrepresented marker는 거부한다. 같은 이름·같은 XML을 가진 다른 source part/위치도 서로 다른 package/document/part/span-bound logical identity다. 편집 후 persistent/native-global identity로 주장하지 않는다.

원본 name은 raw 관찰로 유지한다. NFC/trim/case 변환이나 native 이름 의미를 추정하지 않는다. raw exact name 선택은 관찰이 정확히 하나일 때만 허용한다. 같은 이름이 여러 위치에 있으면 목록과 각 위치는 보존하되 absent/ambiguous 선택을 redacted error로 거부한다. 임의의 첫 항목을 고르지 않는다. 이름 선택은 readonly source 관찰이며 Hwp jump/link/쓰기/승인 경로가 아니다.

기존 field 의미 importer는 source bookmarks의 ID와 target wrapper를 별도로 확인하고 fields만 의미를 부착한다. reference 전체 수는 source fields+source bookmarks와 정확히 일치해야 한다. 임의 caller Reference를 허용한 것이 아니다. DATE는 Unsupported, 원래 HTTPS/수식 profile과 원본 range/parameters는 그대로다. Bookmarks가 없는 이전 입력은 새 bookmark metadata/reference/anchor를 만들지 않는다.

처음 default rg inventory78은 ignore된 원본을 포함하지 않아 전체 증거로 사용하지 않았다. `--no-ignore`의 fixtures/보존 native 파일 **1083개 bounded metadata scan**, 5d760f, supported HP bookmark 또는 BOOKMARK/CROSSREF field positive hits0이었다. 이는 regex metadata 조사 범위이며 모든 native 문법의 부재나 importer/native acceptance 증명이 아니다. 원본 XML/name/parameters는 출력하지 않았다. positive native fixture를 확인하지 못했으므로 내부 링크 파라미터를 추정·생성하지 않았다.

## 실제 실행한 생성 패키지·저장 서비스 검증

생성 whole ZIP/HWPX package8개에서 point marker10개를 Source→body/forms→fields→meanings로 읽고 forms/final whole fresh verify를 수행했다. ASCII/Unicode·entity name, duplicate point, DATE 혼합, note/table/note-table, 동일 XML의 두 section을 포함한다. 이 패키지는 **in-memory generated fixtures**, 실제 한글 저장으로 포획된 양성 책갈피가 아니다. 최소 synthetic header/fixture 패키징은 licensed native 문서의 전체 적합성을 증명하지 않는다.

- probe build b38bde; executable5829632 bytes/SHA `fd323e783060987a479909d85baf1746e1bcca3aec8c638198370f03c43cb5a6`.
- 독립 프로세스 e30974/7e6a54: 각각 exit0/전체 metadata payload 동일; generated packages8/bookmarks10.
- 실제 P09-14 HYPERLINK capture는 bookmarks0의 negative control1개로만 사용했다. positive native bookmark/name/internal link qualification은 false다.

원래 stored actual provider에 같은8개 generated package를 넣어 direct/stored whole graph와 관찰 equality/fresh verify/unchanged artifact.ingested2를 검증했다. 새 observed-name 선택은 원래 `fresh_source`를 호출해 scope/head/node/read ACL/scanner/quarantine/AEAD/digest/whole source graph를 다시 검사한다. ACL revoke/production AEAD fixture tamper/head advance/tenant·subject·project·branch·document substitutions는 fresh selection을 거부한다. duplicate raw names도 선택하지 않는다. 원래 새로 권한 있는 provider의 독립 read와 기존 model 재사용은 구분한다.

metadata/revision/blob/scanner/keys/sealed baseline은 **in-memory service fixtures**, 새 PG/실제 issuer/production scanner/native acceptance가 아니다. 정상 READ audit 외 ingest/CAS/seal/publication은 없고 두 head reads는 atomic CAS/idempotency가 아니다. 새 profile/scope 각각은 다른 partial markers 없이도 full product context를 거부한다.

## 검증 결과

| 검증 | 실제 결과 |
|---|---|
| new package tests | e48f03:10 PASS; source/wrapper/inline/reference/name/ambiguity/hidden·malformed/default·foreign namespace/table/note/part identity/fresh/privacy/actual negative |
| new stored service tests | 036505:5 PASS/55 filtered; 이후 전체 실행에서 filtered0 |
| current CLI+whole package | 86031a→c77c0b→12d9ca→e554cf:101 targets/CLI122+package894=1016 PASS/failed0/ignored0/filtered0 |
| original domain | ea85ca:document_graph9+form_control8+form_input_public15+link_reference10=42 PASS; named total1058 |
| strict lib/tests | 22b391:four crates `-D warnings` PASS |
| strict example | 11112f:`-D warnings` PASS |
| recursive format | 340688:11 entry files와 하위 modules PASS |
| seven whole code inverses | b3b331:이번 추가·국소 bookmark count 연결 제거 시 변경 전7개 파일 raw bytes/SHA exact |
| preservation | 0fff24의 동일 session24384를 c59f14에서 재개해 terminal PASS; prior2521/original1551/51047460 bytes/native75 exact,29 archive origins/Hwp0 |

기존 ZipWriter seek-limit negative diagnostics는 그대로 보존했다. named Rust checks는 whole workspace/Python/whole original qualification CLI replay/current admission/native tests를 대체하지 않는다.

## 보존과 다음 경계

`source-archive/p09-75-pre-source-bookmarks/`에 code7+PLANS 원본121 lines를 whole copy/SHA로 보존했다. 새 fixture의 strict duplicate_mod 실패98b18f와 당시 four whole files는 `p09-75-initial-duplicate-fixture/`에 보존했다. 수정은 새 helper가 원래 field fixture module을 공유하도록 바꾼 것이며 기존 fixture/tests/기대값이나 lint를 완화하지 않았다. 초기 unused table warning은 generated table/note-table coverage 추가로 해소했고 allow/skip을 만들지 않았다. P75 archives는 pre-change8+failed4=12 files다.

P74 source444 중436개는 unchanged이고 이번7개 code 변경은 전체 역복원이 exact다. 기존 dependency/Cargo.lock/SQL/parser/authorization/tests/guards/assertions/skips, 사용자 dirty worktree/원본 HWPX/비밀정보/기존 DB와 실패 증거를 보존했다. stage/commit/push/삭제·이동/trust·security·config 변조/Hangul/COM/UI/native dispatcher/접근허용을 수행하지 않았다.

다른 field/reference/comment/catalog/security 의미와 evaluation/approval/정식 Source-Result-IR input lineage/issuer/ExecutionManifest/publication/idempotency/IR lifecycle/concurrency/crash/recovery/whole original qualification/current admission은 OPEN이다. 실제 책갈피와 내부 링크의 포획 문법·native name/anchor/저장·재열기/렌더링/직접 differential도 OPEN이다. 원래 P26 note failed_semantic_non_green/0green, P73 meaning/P71 actual durable form evidence는 historical scope 그대로다.

P62 16fde8 원인은 UNRESOLVED/current admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN/0green/Goal ACTIVE/P09 Gate OPEN/no P10/prompts를 유지한다.

- [generated consumer](evidence/p09-75-document-import-bookmarks.generated-consumer.v1.json)
- [Rust regression](evidence/p09-75-document-import-bookmarks.rust-regression.v1.json)
- [실패 원장](evidence/p09-75-document-import-bookmarks.initial-failures.v1.json)
- [source progress](evidence/p09-75-document-import-bookmarks.source-progress.v1.json)
- [final audit](evidence/p09-75-document-import-bookmarks.final-audit.v1.json)
