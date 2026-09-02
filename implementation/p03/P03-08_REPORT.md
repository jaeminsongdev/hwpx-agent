# P03-08 Atomic ZIP writer report

- Generated: 2026-09-02
- Audited source commit: `4b8205c37a2ea6f53523efd201127182094b48d2`
- State: `pass_current_pc_local_core_and_disposable_2020_writer_validation`
- Reasoning/review mode: `max / filesystem publication, output limits and post-visibility ambiguity`

`hwpx-package`에 분리된 `PreservingWriter`/`NormalizedWriter`와 `AtomicPackagePublisher`를 구현했다. P03-07 private artifact를 bounded/fallible seek buffer로 ZIP화하고, private staging 동기화·재개봉 후 same-volume hard-link no-overwrite 게시와 published readback을 완료해야 success receipt를 반환한다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Writer separation | `pass` | preserving은 source order/compression method/expanded bytes를 유지하고 normalized는 canonical order/fixed timestamp/deflate level 6을 명시적으로 선택; mode 암묵 혼합 0 |
| Private artifact | `pass` | raw ZIP bytes public getter 없음; custom `Debug`는 mode/count/hash/report만 표시; receipt는 relative output path와 검증 상태만 공개 |
| Bounded construction | `pass` | entry/total expanded limit 선검사, writer/package archive ceiling의 최솟값을 seek 가능한 fallible buffer가 write 중 강제; 1-byte ceiling stable rejection |
| Full pre-publication reopen | `pass` | staged size/SHA-256 readback 후 `BoundedZipReader`→`PackageGraph`→`PreservationReport`→`IdIndex` 전체 재검증 |
| Atomic no-overwrite publication | `pass` | create-new staging, file sync, same-volume hard link, existing destination 보존, published hash/full reopen receipt |
| Failure state model | `pass` | pre-publish 3 checkpoint는 destination absent+staging cleanup; post-publish 2 checkpoint는 complete destination 유지; source artifact hash 불변 |
| Post-visibility ambiguity | `pass` | hard link 후 parent durability/staging cleanup 실패를 `writer_published_incomplete`로 분리하고 destination을 미게시물처럼 삭제하지 않음 |
| Path/link safety | `pass` | absolute/traversal/empty, containment escape, link/reparse, alias/overwrite를 SecureWorkspace에서 fail closed; escape artifact 0 |
| Truthful metadata | `pass` | source/output order·compression과 expanded SHA 기록; source raw compressed stream/timestamp/extra는 `NotPreservedUnavailable`, normalized metadata만 `Normalized` |
| Determinism | `pass` | Windows synthetic와 current-2020 fixture에서 preserving/normalized 각각 repeated SHA equality; Linux 동일 crate corpus pass |
| Regression corpus | `pass` | writer checkpoint `1/1`, patch/writer integration `6/6`, ID `5/5`, graph `8/8`, preservation `5/5`, malicious ZIP `8/8`, package 전체 `45/45` |
| Current 2020 disposable writer validation | `pass` | 승인된 기존 fixture `2/2`; 각 mutation `1 changed / 10 untouched`, writer entry 11, ID `73/184`, 두 mode deterministic/full reopen |
| Versioned contract | `pass` | `implementation/p03/P03-08_ATOMIC_ZIP_WRITER_POLICY.md`, `protocol/migrations/package-writer-v0-to-v1.md` |

## Publication and durability boundary

- Source fixture와 P03-07 artifact는 immutable이며 기존 파일을 in-place 수정하지 않는다.
- Windows는 file `sync_all`과 same-volume hard-link atomic visibility를 증명한다. portable Rust API가 제공하지 않는 directory `fsync`를 주장하지 않는다.
- Linux는 destination 및 staging parent sync를 수행한다. hard link 이후 실패는 destination `complete but receipt incomplete` 상태로 분류한다.
- pre-publication failure는 해당 staged artifact 하나만 제거한다. cleanup 실패를 원래 오류로 숨기지 않는다.
- 이 task의 actual fixture 진단은 read-only/in-memory였다. 새 HWPX를 한글로 여는 runtime Gate는 P03-09다.

## Validation evidence

- Current Windows exact commit: actual fixture `2/2`; FULL bootstrap `5/5`; Rust workspace tests/Clippy/doc tests/generated drift, Windows worker, widget, docs and security passed.
- Core corpus: `hwpx-package` `45/45`; foundation `10/10`; writer failure checkpoints `5/5`와 deterministic/no-overwrite/traversal/output-limit integration passed.
- Linux exact toolchain: base `rust:1.96.0-bookworm@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc`, `rustc 1.96.0`. 공식 image에 빠진 1.96.0 Clippy만 설치한 local derived image `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`를 사용했다. 검증 시 network off, source/Cargo registry read-only, Cargo offline, target/tmp는 executable tmpfs였고 `45/45`와 Clippy `-D warnings`가 통과했다.
- Clean clone: `D:\개발데이터\Temp\hwpx-agent-p03-08-clean-4b8205c`, exact audited commit, FULL bootstrap `5/5`, exit code 0, post-run tracked changes 0.
- Security: scanned files 496, secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- Product library network/process/`unsafe`: 0. Filesystem write는 explicit `AtomicPackagePublisher`→`SecureWorkspace` 경로만 존재한다. 한글/COM/UI 실행: 0.

`cargo deny`의 기존 `hashbrown`/`syn` duplicate-version 메시지는 warn policy 안의 dependency graph 경고이며 advisories/licenses/sources/bans는 모두 pass다.

## Strict self-review

- Change risk: `high` (document bytes and filesystem publication boundary).
- 첫 review에서 hard link 성공 뒤 parent sync 또는 staging cleanup 실패가 일반 workspace 오류로 합쳐져 미게시물 cleanup 경로로 들어갈 수 있는 모호성을 발견해 별도 post-visibility 상태와 stable code를 추가했다.
- 둘째 review에서 새 internal path dependency에 version이 없어 `cargo deny` wildcard를 발생시킨 것을 확인해 repository version `0.1.0`을 고정했다.
- 셋째 review에서 archive size를 ZIP 완성 후 검사하면 중간 메모리 할당이 상한을 먼저 넘을 수 있음을 발견해 bounded/fallible seek buffer와 expanded-size 선검사를 구현했다.
- Windows/Linux path, overwrite, fault checkpoints, private `Debug`, `unsafe`/network/process, exact commit and clean clone을 재감사했다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 현재 PC의 core writer와 이미 승인된 disposable 한글 2020 fixture의 in-memory writer 호환성을 검증했다. 실제 한글 2020 open/save/render, 100+ round-trip corpus, repair diagnostics, fuzz baseline, OS/hardware power-loss durability, 사용자 문서 전체 또는 2022/2024 동작은 검증했다고 주장하지 않는다.

## Next exact task

`P03-09 Round-trip·repair Gate`를 시작한다. 100개 이상의 deterministic synthetic/rejection corpus와 현재 2020 disposable fixture를 round-trip CLI로 재개봉하고, untouched policy 위반 0, stable non-mutating repair diagnostics, bounded fuzz baseline을 확보한 뒤 생성된 preserving/normalized 산출물을 exact 한글 2020 fresh-process open/readback으로 검증한다. 추론수준은 `max`다.
