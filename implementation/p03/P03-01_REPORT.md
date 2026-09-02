# P03-01 Bounded ZIP reader report

- Generated: 2026-09-02
- Audited source commit: `bb80bb8a557177ea7d51443729a422719c11b7c8`
- State: `pass_current_pc_local_core`
- Reasoning/review mode: `max / high-risk archive boundary`

`hwpx-package`에 유한 limit contract, portable package path, stable typed error와 read-only bounded ZIP reader를 구현했다. 원본 archive를 추출하거나 수정하지 않고, central directory preflight → `zip` primitive parse → central/local header cross-check → bounded streamed payload/CRC 검증 순으로 fail closed한다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Public limits/config/error contract | `pass` | `PackageLimitConfig`, validated `PackageLimits`, immutable hard ceilings, `PackageError::code()` |
| Archive/entry/name/depth/expanded/ratio limits | `pass` | central preflight와 local/streamed 재검증, checked arithmetic, fallible exact allocation |
| Portable path and collision policy | `pass` | strict UTF-8, traversal/absolute/empty/dot/backslash/control/ADS/reserved/suffix rejection, NFC + Unicode casefold + NFC collision key |
| Structural/integrity policy | `pass` | classic single-disk only, Stored/Deflate only, ZIP64/encryption/descriptor/symlink/special/preamble/trailing 거부, local/central/CRC/size/offset/range 검사 |
| Nested archive policy | `pass` | document/archive extension을 open 시 거부하고 ZIP/OLE signature를 verified payload publication 전에 거부 |
| No extraction/partial publication | `pass` | filesystem write/extract API 없음; `read_entry`가 완전 검증된 `Vec<u8>`만 반환 |
| Synthetic malicious corpus | `pass` | 8/8 test groups, limits/path/collision/structure/overlap/CRC/nesting/symlink/metadata/determinism 포함 |
| Initial contract migration | `pass` | `protocol/migrations/hwpx-package-reader-v0-to-v1.md` |

세부 허용/거부 정책과 default/hard ceiling은 `implementation/p03/P03-01_BOUNDED_ZIP_POLICY.md`가 authoritative다. ZIP64와 data descriptor는 current bounded HWPX profile에서 명시적으로 unsupported이며, 별도 version/corpus 없이 완화할 수 없다.

## Dependency boundary

- `zip = 8.6.0` exact pin, default features disabled.
- `deflate-flate2-zlib-rs`만 활성화해 Stored/Deflate 이외 codec과 encryption feature를 포함하지 않았다.
- `unicode-normalization = 0.1.25`, `unicode-casefold = 0.2.0` exact pin.
- `zip` crate는 ZIP parse/Deflate/CRC primitive만 담당하고 product limits, path, header consistency와 publication policy는 `hwpx-package`가 소유한다.

## Validation evidence

- Current Windows repository FULL bootstrap: `5/5` lanes passed.
- Rust workspace: format, `clippy --locked --workspace --all-targets -D warnings`, tests, doc tests와 codegen drift passed.
- P03-01 malicious corpus: Windows `8/8`, failures 0.
- Official Linux image: `rust@sha256:31ee7fc65186be7e0e0ccb3f2ca305f14e4739e7642a1ae65753aa5d7b874523`; repository toolchain `rustc 1.96.0`, source read-only mount, tmpfs target, corpus `8/8`와 Clippy passed.
- Clean clone at audited commit: FULL bootstrap `5/5`, post-run Git status changes 0.
- Security: secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 158.
- `unsafe` block, filesystem extraction/write, user document access and 한글 runtime execution: 0.

첫 Linux harness 시도는 login shell(`sh -lc`)이 image PATH를 재설정해 `rustc: not found`로 compilation 전에 종료됐다. Source나 test는 실행되지 않았고, 동일 digest에서 non-login shell(`sh -c`)과 read-only/tmpfs 조건으로 재실행한 결과가 authoritative하다.

## Strict self-review

- Change risk: `high` (untrusted archive parser boundary).
- Initial finding: central variable metadata가 product name limit 검사 전에 bounded 65,535-byte allocation을 시도할 수 있었다.
- Remediation: name/extra/comment upper bound를 allocation 전에 검사하고 metadata/output 모두 `try_reserve_exact`로 변경했다.
- Final blocker/major/minor findings: `0/0/0`.
- `cargo deny`의 `hashbrown`/`syn` duplicate-version messages는 기존 warn policy 안의 dependency graph 경고이며 advisories/licenses/sources/bans 결과는 pass다.

## Scope and remaining boundary

이 task는 synthetic package corpus와 core parser를 검증했다. 사용자 문서, 실제 한글 저장 HWPX corpus, PackageGraph/XML semantic correctness, writer/round-trip은 검증했다고 주장하지 않는다. 실제 한글 문서는 P03-09/phase Gate의 승인된 fixture 경계에서만 사용한다.

## Next exact task

`P03-02 PackageGraph`를 시작한다. `mimetype`, `META-INF/container.xml`, OPF manifest/spine과 relationship closure를 bounded part graph로 만들고 missing/duplicate/dangling/external-target negative tests를 통과시킨다. 추론수준은 `max`다.
