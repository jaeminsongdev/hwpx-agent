# CURRENT STATE

> 기준일: 2026-09-05
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 현재 상태

- 상태: `P05_IN_PROGRESS_AND_P15_IN_PROGRESS_CURRENT_PC_LOCAL_ONLY`
- 현재 phase: `P05_TEXT_PARAGRAPH_STYLE_LAYOUT` + `P15_REMOTE_MCP_CONTROL_PLANE`
- 구현 코드: P01 foundation, P02 signed source/registry pipeline, P03 bounded HWPX package/preserving XML core와 P04 DocumentGraph→selector/plan/router→transaction/diff/idempotency·CAS→VS-0 core CLI vertical이 build·test 가능하다. P05-01~06 typed text/style/layout core는 완료했고 P05-07~09 core는 실제 한글 2020 render evidence를 기다린다. P10 current-PC worker 기반은 일부 실제 의존성을 제외하고 진행됐다. P14-01~09와 P14 Gate는 local reference 및 disposable PostgreSQL 범위에서 통과했다. P15-01 bounded Auth/tenant resource-server middleware, P15-02의 18개 public MCP tool schema/snapshot, P15-03 공통 handler boundary, P15-04 durable Async job UX와 P15-05 bounded Artifact delivery가 통과했고 P15-06 Error mapping이 다음 비-UI 구현이다.
- 기준 입력: `HWPX_Agent_Product_Design_v2_2026-08-31`
- 설계 baseline: 16개 영역, 609개 feature, 609개 capability contract, P00~P20, 190개 WBS task
- root workflow skill: 9개
- 설계 정적 검증: P00-08 `PASS`; pinned dependency 기반 full validator 16 schema/609 feature/609 contract/190 WBS 오류 0
- generated 산출물 재현성: 23개 파일 연속 2회 재생성 후 SHA-256 비결정 파일 0

## P00 현재 상태

- target family: 한글 desktop 2020 이상 모든 release/build. 미등록 버전은 discovery만 허용하고 exact build/host evidence bundle별 qualification 전에는 `discovered_unqualified`.
- current primary target: 한글 2020 `11.0.0.9136` x86. 기존 evidence correlation 때문에 profile ID `hancom-hangul-2020-secondary`는 유지하지만 역할은 `primary_development`다.
- current use scope: 사용자가 확인한 정품 유효 한글 2020 seat의 개인 비상업·로컬 개발. Production, 사내, 서버/VM, 고객 배포는 disabled다.
- deferred compatibility targets: 한글 2022 `12.0.0.4605`, 한글 2024 `13.0.0.4049`. 프로필·공식 자료·pending request는 보존하지만 다른 PC가 가능할 때까지 `hold_unqualified`이며 현재 P00 blocker가 아니다.
- 2020 automation: exact x86/STA identity probe PASS. Reference run `98798b1801314a5e9bebf0f2505bc763`은 synthetic 문서 생성→HWPX 저장→종료→재열기→exact normalized readback→PDF export→`Quit()`→잔류 0 PASS다.
- remote diagnostics: request/session/inventory/events/manifest/verifier 6개 schema와 PowerShell 4개 구현. Windows PowerShell 5.1 상위 collector에서 probe `valid/pass`, discovery `valid/discovered_unqualified`; traversal/manifest tamper 포함 3/3 PASS.
- environment baseline: 현재 PC의 private machine binding, OS build/UBR, exact 한글 binary/Registry32, HCR Batang, Hancom PDF, oracle/source evidence를 deterministic digest로 고정하고 live verifier와 tamper/traversal negative test를 통과했다. Clean image는 주장하지 않으며 다른 PC/portable worker/production 범위로 연기했다.
- font/printer: HCR Batang이 HWPX 모든 언어 슬롯과 embedded PDF에 일치해 substitution 0. Hancom PDF `1.3.0.550` profile/driver를 잠갔고 redirected default printer는 제외·미변경. P00-03은 현재 범위 PASS.
- official source: 공식 원격 24개를 잠갔다. KS X 6101 reform 03 machine response 521 title/content records, HWP 공개 문서, 한글 2020 rights, HCR FAQ와 attribution 결정을 포함한다. P00-04는 현재 범위 PASS.
- source lock: `source-lock-P00-20260901-v9-final-current-scope`, PowerShell 7과 Windows PowerShell 5.1 모두 local 40/40, remote 24/24, 실패 0. P00-05는 현재 범위 PASS.
- automation/provider license: 정품 유효 2020 seat와 개인 비상업 로컬 목적 확인, production/provider disabled. P00-06/07 PASS.
- P00 Gate: v10은 사용자가 지정한 현재-PC 로컬 개발 범위에서 `PASS_SCOPED`; P01 scaffold를 이 PC에 한해 시작할 수 있다. v9의 clean-image `BLOCKED`는 이전 범위의 정확한 역사 기록으로 보존한다.

## v2 핵심 변경

- capability-driven multi-backend
- Rust direct HWPX core + C#/.NET STA Windows automation worker
- exact 문서 크기·구역·다단, 고급 표, native 수식을 VS-1 필수 gate로 지정
- 대상 build별 signed capability binding과 실제 한/글 oracle
- 확장 DocumentGraph/OperationPlan/transaction
- async job·artifact·immutable revision·Web↔Codex continuity
- 상업 라이선스·보안·외부 기능의 명시적 release gate
- ChatGPT Web universal package와 Codex remote/local companion blueprint

## P01 완료 상태

- Gate: `PASS_SCOPED_CURRENT_PC_LOCAL`; authoritative report는 `implementation/p01/P01_GATE_REPORT.md`다.
- 검증: 현재 Windows PC 5/5 lane, 공식 Rust 1.96.0 Linux 컨테이너 read-only source lane, clean clone bootstrap와 post-run Git status 0.
- 보안: secrets/vulnerabilities/forbidden licenses 0, CycloneDX 146 components, private evidence와 사용자 문서 Git 추적 0.
- 범위: P01은 한글/COM/UI/사용자 문서를 실행하지 않았다. GitHub-hosted scheduler, 다른 PC/버전 및 production은 검증했다고 주장하지 않는다.

## P02 현재 상태

- P02-01 `PASS`: immutable `SourceRecordV1`, 5개 valid sample, 10개 negative case, Rust/TypeScript generated models와 additive catalog v2 lock.
- 검증: 현재 저장소와 clean clone의 전체 5/5 lane, 공식 Linux read-only source lane, schema/codegen drift와 이전 P01 catalog byte identity 통과.
- P02-02 `PASS`: source-locked read-only Help adapter, Windows/Linux 8개 test, 실제 restricted snapshot 4 records/private evidence/verifier errors 0.
- P02-03 `PASS`: SHA-locked PDF 4종에서 2,532 records(Action 937/Parameter 1,205/Object 363/Event 27), Windows/Linux combined 16 tests, actual verifier errors 0, deterministic output과 clean clone 5/5 lane을 통과했다.
- P02-04 `PASS`: locked KS X 6101 reform 03 machine response의 embedded authoritative XSD 7종과 OCF package table을 읽어 1,144 records(package part 22/schema 7/import 5/element 359/attribute 648/named complexType 82/named simpleType 14/attributeGroup 7)를 생성했다. 2024 namespace 7/7, actual verifier errors 0, Windows/Linux 23 tests, current/clean-clone 5/5 lane을 통과했다.
- P02-05 `PASS`: 3개 locked SourceRecord 출력 3,680개를 3,680 nodes/2,736 normalized labels/3,811 review edges로 전환했다. 호환 후보 746, collision review 3,065, auto-merge 0이며 independent verifier errors 0, Windows/Linux 29 tests, current/clean-clone 5/5 lane을 통과했다.
- P02-06 `PASS`: 609-row canonical matrix에 대해 3,680/3,680 node와 3,811/3,811 edge를 disposition했다. strict proposal 35건 중 34건을 semantic mapping하고 1건은 ambiguity로 거절했다. unresolved/auto-merge/runtime-qualified 0, independent verifier errors 0, Windows/Linux 36 tests, current/clean-clone 5/5 lane을 통과했다.
- P02-07 `PASS`: exact 2020 profile에 `AUTOMATION_FULL` 191 + `HYBRID` 345 = 536 capability를 전수 표현했다. candidate 32, unavailable-with-reason 504, missing/duplicate/runtime-qualified/routing-enabled 0이며 protocol catalog v2 byte identity, additive v3 codegen, independent verifier errors 0, Windows/Linux 43 tests, current/clean-clone 5/5 lane을 통과했다.
- P02-08 `PASS`: exact 2020 x86/STA disposable runtime probe에서 request/trace/receipt correlation, 32/32 disposition, 안전 canary 2건, save/reopen exact semantic match, `Quit()`, 잔류 process 0을 확인했다. `edit.go_to` default-read 실패 1건은 typed/hash negative evidence로 보존했고 independent verifier errors 0, Python 47/47, PowerShell 31/31을 통과했다.
- P02-09 `PASS`: Ed25519 private signed registry 963,624 bytes를 생성하고 독립 verifier signature/runtime errors 0, deterministic 2회 byte identity, no-overwrite, tamper/rollback/wrong-parent/drift tests를 통과했다. 536개 중 verified 2/failed 1/risk-blocked 17/not-run 12/unavailable 504, routing 0이다. Actual 다른-build drift는 `baseline_unavailable`다.
- P02 Gate `PASS_SCOPED_CURRENT_PC_LOCAL`: Windows/Linux P02 61/61, current/clean-clone FULL bootstrap 5/5, secret/vulnerability/forbidden license 0. Authoritative report는 `implementation/p02/P02_GATE_REPORT.md`다.

## P03 현재 상태

- P03-01 `PASS`: `hwpx-package`의 finite limits, strict portable path와 Unicode collision, classic ZIP central/local header consistency, bounded streamed size/CRC, nesting과 no-partial-publication policy를 구현했다. Windows/Linux malicious corpus 8/8, current/clean-clone FULL bootstrap 5/5, secret/vulnerability/forbidden license 0이다. 사용자 문서와 한글 runtime은 실행하지 않았다.
- P03-02~05 `PASS`: closed `PackageGraph`, finite safe XML, byte-span preserving token/tree와 complete evidence-ranked `PreservationReport`를 구현했다. graph `8/8`, preservation `5/5`와 이전 malicious corpus를 Windows/Linux/clean clone에서 유지했다.
- P03-06 `PASS`: exact 한글 2020 core profile의 typed part-scoped ID/reference index를 구현했다. actual disposable fixture `2/2`에서 각 declaration 73/reference 184/issue 0이며 package `38/38`을 통과했다.
- P03-07 `PASS`: 8종 checked `PatchIntent`, overlap/conflict, deterministic typed allocation, relationship/part closure와 atomic private transaction을 구현했다. actual fixture `2/2`에서 mutation `1 changed / 10 untouched`, package `43/43`을 통과했다.
- P03-08 `PASS`: `PreservingWriter`/`NormalizedWriter`, bounded/fallible ZIP buffer와 `AtomicPackagePublisher`를 구현했다. source order/compression/expanded bytes와 unavailable raw metadata를 구분하고, staged/full reopen, same-volume no-overwrite, absent-or-complete fault model을 Windows/Linux `45/45`, actual writer `2/2`, current/clean-clone FULL `5/5`로 검증했다.
- P03-09 `PASS`: `RoundTripVerifier`와 non-mutating `RepairDiagnostic`, 128 valid/128 mutation/128 truncation corpus, raw/structured ASan fuzz target을 구현했다. cross-platform semantic/writer digest가 일치하고 exact 한글 2020 output `4/4`, pair `2/2`, 잔류 process 0을 통과했다.
- P03 Gate `PASS_SCOPED_CURRENT_PC_LOCAL`: Windows/Linux `48/48`, current/clean-clone FULL `5/5`, security 0건, STRICT `max` 감사를 통과했다. Authoritative report는 `implementation/p03/P03_GATE_REPORT.md`다.

## P04 현재 상태

- P04-01 `PASS`: backend-neutral `DocumentGraph` v2 types, finite identity/reference/table validator와 deterministic canonical JSON을 `domain-ir`에 구현했다. Windows/Linux `9/9`, golden `2ab9ffef...f3c6`, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-02 `PASS`: official `1/7200 inch` HWPUNIT, exact rational conversion, checked half-away-from-zero receipt, coordinate space/anchor와 10종 typed ID newtype을 구현했다. Windows/Linux `18/18`, fixed-seed 10,000 round trips, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-03 `PASS`: revision/digest-pinned immutable snapshot에서 ID/name/path/text-context selector를 exact-one으로 해석한다. zero/multiple/stale/limit을 분리하고 Windows/Linux `27/27`, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-04 `PASS`: versioned bounded plan draft를 typed selector, checked unit/default normalization과 deterministic atomic dependency DAG로 compile한다. 1,000-op fixed-seed equality, Windows/Linux `36/36`, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-05 `PASS`: exact profile, signature-verified registry, support/policy/preservation/backend-health가 모두 맞는 단일 deterministic route만 허용한다. Windows/Linux `45/45`, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-06 `PASS`: immutable plan/route/source manifest, isolated working copy, bounded state machine, staged validation/no-overwrite publication/revision CAS와 rollback/quarantine을 구현했다. Windows/Linux `9/9`, fault `22/22`, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-07 `PASS`: validated graph 두 개에서 9개 category의 typed semantic delta, relative-order move, opaque visibility와 raw-value privacy를 구현했다. Windows/Linux `55/55`, golden `b12f8a54...9f7e`, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-08 `PASS`: exact key binding, secret owner/fencing, terminal replay, outcome-unknown reconciliation, checksum-bound revision CAS와 object-safe storage boundary를 구현했다. Windows/Linux `20/20`, 32/16/32 concurrency, current/clean-clone FULL `5/5`, security 0건을 통과했다.
- P04-09 `PASS`: bounded request를 DocumentGraph→selector/compiler→signed exact route→transaction→idempotency/CAS→deterministic P03-validated HWPX로 연결했다. Windows/Linux, current/clean-clone FULL `5/5`, actual-bundle verifier `5/5`와 exact Hangul 2020 open/readback/잔류 0을 통과했다.
- P04 Gate `PASS_SCOPED_CURRENT_PC_LOCAL`: STRICT `max` 감사에서 blocker/major/minor `0/0/0`; authoritative report는 `implementation/p04/P04_GATE_REPORT.md`다. P05를 현재 PC 로컬 범위에서 시작한다.

## P05 현재 상태

- P05-01~06 `PASS`: bounded text flow, character/paragraph styles, tabs, lists/numbering과 page setup이 각 typed contract, negative/fixed corpus, cross-platform tests와 해당 보고서의 범위에서 완료됐다.
- P05-07~09 core는 section/columns, header/footer와 layout model/test fixture를 갖췄지만 release 판정에 필요한 실제 한글 2020 save/reopen/PDF/render evidence는 열려 있다.
- P05-07 v2 시도 10~16은 모두 `open_input`에서 bounded timeout됐다. 입력은 불변이고 output/PDF는 없으며 owned `Hwp.exe`와 잔류 프로세스는 0이다. 따라서 P05-07~09와 P05 Gate를 PASS로 올리지 않는다.

## P10 현재 상태

- P10-01~04, P10-07, P10-09와 현재-PC 범위의 P10-10은 각 보고서 범위에서 통과했다.
- P10-05는 승인된 registered file-path security module이 없고, P10-06 actual production COM execution과 P10-10 general routability는 unverified다. P10-08은 현재-PC 개발 audit은 통과했지만 dedicated production isolation은 unqualified다.

## P14 현재 상태

- P14-01~05는 각 exact clean source commit, digest-bound PostgreSQL 18.4 receipt, Rust/SQL negative tests, non-security CI, offline Linux와 current security evidence에 따라 scoped PASS다.
- P14-04의 이전 `pnpm audit` timeout 조건은 commit `3876679`의 현재 bounded security run에서 첫 timeout cleanup 후 동일 2차 시도가 성공해 해소됐다.
- P14-06은 core commit `205f4ac`에서 exact worker selection, bounded heartbeat/lease, late-worker/fence rejection과 qualified expiry를 Rust 및 disposable PostgreSQL로 증명했고, 후속 보안 run `9750c1226aa945ce98ad692b749f198e`가 모든 검사를 통과해 scoped PASS다.
- P14-07은 core commit `fbcdcef`와 durable commit `d84a442`에서 bounded retry, unknown-outcome freeze, exact revision/artifact oracle, unpredictable attempt capability와 atomic job/revision fencing을 구현했다. clean PostgreSQL 18.4에서 SQL 28/28×3, 동시 claim `1 new + 15 replay`, commit/retry 정확히 한 승자, rollback/reapply를 통과해 scoped PASS다.
- P14-08은 commit `8d03bb6`에서 safe cancellation, exact temp cleanup, source/reference-protected orphan quarantine, digest-bound interrupted-move recovery와 durable fenced receipt를 구현했다. clean PostgreSQL 18.4에서 SQL 18/18×3, P14-07 regression 28/28×2, 동시 claim `1 winner + 7 bounded misses`, 양쪽 fault window와 rollback/reapply를 통과해 scoped PASS다.
- P14-09은 commit `1d5de34`에서 7개 retention class, legal hold, tombstone, 3회 fenced purge, immutable receipt와 digest-only local mirror CAS/3개 conflict path를 구현했다. clean PostgreSQL 18.4에서 SQL 32/32×3과 P14-07 regression 28/28×3, rollback/reapply를 통과했고 P14 Python 132/132, Rust 15/15 Windows/Linux, 4개 non-security lane, security/SBOM 680이 모두 통과했다.
- P14 Gate는 `PASS_SCOPED_CURRENT_PC_LOCAL_REFERENCE_AND_DISPOSABLE_POSTGRES`다. Production DB/service/object store/remote transport/HA/legal suitability는 계속 unverified이며, authoritative report는 `implementation/p14/P14_GATE_REPORT.md`다.

## P15 현재 상태

- P15-01은 commit `8ac8d74`에서 exact issuer/audience/time/tenant/scope 검증, immutable
  issuer/subject tenant mapping, public user와 single-use internal service token 분리, finite
  key/principal/revocation/replay registry와 redacted diagnostics를 구현했다.
- Auth Rust 17/17, P15 contract/negative 13/13, 현재 exact commit과 독립 checkout의 전체 CI
  각 5/5, 두 security run, network-disabled read-only Linux Clippy/17 tests가 통과했다.
- 이 PASS는 현재-PC local reference resource server만 의미한다. Production IdP/JWKS,
  authorization-code/PKCE 실행, hosted HTTPS, refresh propagation, multi-process replay와 secret
  custody는 unverified다. Authoritative report는 `implementation/p15/P15-01_REPORT.md`다.
- P15-02는 commit `c3839df`에서 정확히 18개 public MCP tool의 closed Draft 2020-12
  input/output schema, exact OAuth scope mirror, conservative safety annotations와 deterministic
  descriptor/schema snapshot을 고정했다. raw XML/COM action/path/token/document bytes는 노출하지
  않고 현재 `hancom-hangul-2020-secondary` 프로필만 허용한다.
- P15-02 schema/negative 17/17, 전체 P15 30/30, 현재 exact commit과 독립 checkout의 CI 각
  5/5, 두 security run과 network-disabled read-only Linux 검증이 통과했다. 이는 contract-only
  PASS이며 handler/transport/hosted OpenAI connection은 unverified다. Authoritative report는
  `implementation/p15/P15-02_REPORT.md`다.
- P15-03은 commit `9e7ed73`에서 18개 도구 공통 auth→unique JSON→input schema→tenant/project
  policy→단일 gateway dispatch→output schema→correlation handler를 구현했다. 공개 bearer와
  argument/debug는 redacted/zeroized되고, cross-tenant/non-member는 missing과 구분되지 않는다.
- Handler Rust 16/16과 전체 P15 37/37, 현재 exact commit과 독립 checkout의 CI 각 5/5, 두
  security run, network-disabled read-only Linux Clippy/16 tests가 통과했다. 이는 current-PC
  in-process reference handler PASS이며 Streamable HTTP, real service adapters, async job UX,
  hosted OAuth/OpenAI connection은 unverified다. Authoritative report는
  `implementation/p15/P15-03_REPORT.md`다.
- P15-04는 implementation commit `f50c724`와 closing audit commit `4c6224f`에서 여섯
  long-running tool을 deterministic durable job ID, ordered bounded `_meta` progress, safe
  cancellation과 exactly one immutable terminal receipt에 연결했다. Append-only checksum journal은
  fsync-before-publish와 fail-closed restart replay를 적용하고 raw arguments, bearer, document
  content, paths와 raw cancel reason을 저장하지 않는다.
- Async Rust 11/11, handler 16/16, P15 Python 44/44, 현재 exact commit과 독립 checkout CI 각
  5/5, 두 security run과 network-disabled read-only Linux 검증이 통과했다. 이는 current-PC
  local durable journal reference PASS이며 production queue/database/transport, cross-process
  writer와 artifact delivery는 unverified다. Authoritative report는
  `implementation/p15/P15-04_REPORT.md`다.
- P15-05는 commit `dde79ff`에서 frozen `artifact_get`를 metadata, client-only signed preview와
  opaque attachment resource link에 연결했다. URL은 tenant/project/artifact/subject/content/
  request/binding-generation/time에 서명되며, redemption은 현재 P14 ACL/state/digest를 다시
  확인하고 엄격한 단일 byte range와 64 MiB 응답 한계를 적용한다.
- Artifact Rust 13/13, async 11/11, handler 16/16, P15 Python 51/51, 현재 exact commit과 독립
  checkout CI 각 5/5, 두 security run과 network-disabled read-only Linux 검증이 통과했다.
  이는 current-PC local delivery reference PASS이며 production HTTPS/object store/streaming,
  hosted attachment resolution과 key custody는 unverified다. Authoritative report는
  `implementation/p15/P15-05_REPORT.md`다.

## 다음 작업

비-UI 순서는 P15-06에서 auth/schema/policy/service/job/artifact 내부 오류를 하나의 stable public envelope/catalog로 매핑하고 retryability와 no-secret-leakage negative/E2E를 증명하는 것이며 추론수준은 `max`다. P05-07 actual render는 사용자가 즉시 모든 `모두 허용`을 누를 수 있다고 명시한 새 실행에서만 재시도하고, save/reopen/PDF/render가 실제로 완성되기 전에는 다음 P05 Gate로 승격하지 않는다.

## 현재 blocker

- NPM advisory endpoint는 간헐적 timeout 이력이 있지만 P14-09 exact commit 보안 run은 첫 시도 실제 응답으로 통과했으며 P15-01 blocker가 아니다.
- P05-07 actual render는 한글 2020의 수동 `모두 허용` 타이밍에 의존한다. v2 attempt 16도 `open_input`에서 안전하게 timeout됐고 잔류 프로세스는 0이다.
- P10-05/06과 P10-08 production 범위는 외부 보안 모듈·격리 환경이 제공되기 전까지 unqualified다.

2022/2024 runtime과 production 상업/서버/VM·배포 라이선스는 현재 blocker가 아니라 deferred release blocker다.

## 검증 한계

제품 foundation, P02 signed registry, P03 package/preserving/round-trip core, P04 typed model/transaction/diff/idempotency/VS-0 vertical, P05-01 bounded text flow, P05-02 bounded character styles, P05-03 bounded paragraph styles와 P05-04 bounded tabs는 재현 가능하다. 그러나 VS-0는 create-new 단일 문단이고 P05-01~04는 targeted text/header 계약이라 arbitrary package editing, complete list/page/section semantics, installed-font substitution, rendered fidelity, durable multi-process persistence와 public wire integration을 증명하지 않는다. P05-04 actual save/reopen은 exact current-PC semantic readback이며 visual tab layout이나 사용자 문서 호환성을 뜻하지 않는다. Signed registry의 general public routing은 0이고 VS-0만 task 전용 exact signed route다. Exact 2020 evidence는 이 Windows 설치의 개인 로컬 개발만 승인하며 clean-image/다른 PC/지원 release를 증명하지 않는다. Native 수식 round-trip, 인쇄 경로, deferred 2022/2024 runtime, ChatGPT/Codex E2E는 수행하지 않았다. Offline bundle은 integrity/request correlation을 검증하지만 signed remote-host identity는 P10 범위다. P00~P04 실제 상태는 각 authoritative Gate report를, P05-01~04는 해당 task report를 따른다.
