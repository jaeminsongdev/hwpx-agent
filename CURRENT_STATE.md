# CURRENT STATE

> 기준일: 2026-09-02
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 현재 상태

- 상태: `P02_IN_PROGRESS_CURRENT_PC_LOCAL_ONLY`
- 현재 phase: `P02_OFFICIAL_CATALOG_IMPORTER_CAPABILITY_REGISTRY`
- 구현 코드: P01 Rust/C#/TypeScript foundation, secure workdir, safe logging, semantic worker boundary, schema/protobuf codegen, CI/security/bootstrap가 build·test 가능하다. P00 source 수집, 2020+ 원격 diagnostics, exact 2020 synthetic document smoke harness와 evidence도 보존한다.
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
- P02-06 `in_progress`: 3,680개 official node와 3,811개 edge를 609 canonical capability 기준으로 semantic disposition한다.

## 다음 작업

현재 PC에서 P02-06 semantic capability review를 수행한다. 구현·감사 추론수준은 `max`, 다음 P02-07 binding model은 `xhigh`다. 한글 UI 자동 조작, 사용자 문서, 다른 PC/버전, production/provider 경로는 열지 않는다.

## 현재 blocker

- 현재 blocker 없음. P02-06에서 semantic 근거가 부족한 node를 label-only로 매핑하지 않고 명시적 ignored-with-reason 또는 Gate blocker로 남긴다.

2022/2024 runtime과 production 상업/서버/VM·배포 라이선스는 현재 blocker가 아니라 deferred release blocker다.

## 검증 한계

제품 foundation 코드는 재현 가능하지만 문서 패키지 core와 전체 제품 기능은 아직 구현되지 않았다. Exact 2020 synthetic HWPX/PDF와 실제 한글 save/reopen/readback/export 증거는 이 Windows 설치의 로컬 개발만 승인하며 clean-image/다른 PC/지원 release를 증명하지 않는다. Native 수식 round-trip, 인쇄 경로, deferred 2022/2024 runtime, ChatGPT/Codex E2E는 수행하지 않았다. Offline bundle은 integrity/request correlation을 검증하지만 signed remote-host identity는 P10 범위다. P00/P01 실제 상태는 각 Gate report를 따른다.
