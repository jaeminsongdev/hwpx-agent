# P01 Repository·CI·Security Foundation Gate Report

- Generated: 2026-09-01
- Audited source commit: `7915bc844dd75c8ff63b7c207f5ad5a81586ba51`
- Audit mode: `STRICT / max`
- Overall state: `pass_scoped_current_pc_local`
- P02 authorization: `authorized_current_pc_local_only`

P01-01~09를 현재 PC의 로컬 개발 범위에서 모두 구현하고 재현했다. 이 phase는 한글, COM, 사용자 문서 또는 다른 한글 버전을 실행하지 않았다. 일반 CI와 실제 한글 oracle을 분리했으며, GitHub-hosted workflow scheduler 자체는 실행하지 않았으므로 그 항목만 `unverified`로 유지한다. 동일한 5개 lane은 현재 Windows PC에서 통과했고 Linux core는 공식 Rust 1.96.0 컨테이너에서 저장소를 읽기 전용으로 마운트한 상태로도 통과했다.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P01-01 monorepo | `pass` | Rust/C#/TypeScript workspace build; clean clone `7915bc8`, post-bootstrap Git status 0 | None for current-PC local scope |
| P01-02 toolchain lock | `pass` | Rust 1.96.0, .NET 10.0.300, Node 24.16.0, pnpm 11.19.0 and security/codegen tools matched preflight | Reopen on version change |
| P01-03 schema/protobuf generation | `pass` | Vendored protoc, Rust/C#/TypeScript generation, Draft 2020-12 compile, generated drift and immutable v1 hash checks | Breaking changes require a new version and migration |
| P01-04 CI matrix | `pass_scoped` | linux-core, windows-worker, widget, docs, security local lane smoke all passed; pinned workflow references 15/15 | GitHub-hosted scheduler run is `unverified` until a remote is used |
| P01-05 secure workdir | `pass` | traversal, absolute/empty path, inserted link, atomic no-overwrite publish/quarantine, interruption cleanup tests passed on Windows and Linux | Windows uses safe file sync plus same-volume hard-link publication; no unsafe directory fsync claim |
| P01-06 dependency security | `pass` | secrets 0, vulnerabilities 0, forbidden licenses 0, SBOM 146 components | Transitive duplicate-version warnings for `hashbrown` and `syn` remain non-blocking and visible |
| P01-07 logging baseline | `pass` | allowlisted structured fields and keyed/inline secret, PII, bearer, signed-URL redaction tests passed | Raw document content remains forbidden |
| P01-08 fixture policy | `pass` | 3 schemas, one checksum-bound synthetic fixture, missing/privacy/license/private-redistribution negative validation | Licensed-private binaries remain local and Git-excluded |
| P01-09 bootstrap | `pass` | New clean clone completed the one-command bootstrap and remained clean | Host tools must match the pinned preflight |

## Validation summary

- Current Windows PC full bootstrap: 5/5 lanes passed.
- Rust tests: 10 passed, 0 failed, including 9 foundation security/logging tests.
- C# Release build: warnings 0, errors 0; semantic worker boundary smoke passed.
- TypeScript: format, typecheck, build and 3 tests passed.
- Design/docs: 16 schemas, 609 features, 609 capability contracts, 190 WBS tasks, errors 0.
- Foundation validation: 3 schemas, 1 fixture manifest, 15 pinned action references, errors 0.
- Security: tracked secrets 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, SBOM components 146.
- Official Linux check: `rust:1.96.0-bookworm@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc`, source read-only, linux-core passed.
- Clean-clone check: private evidence was absent by design; exactly 17 such links were classified `declared_local_evidence`, all other links valid, post-run Git status empty.
- Repository privacy: 399 tracked files; tracked user documents, P00/P01 private evidence and build output each 0; Rust `unsafe` and external Git dependencies each 0.

Local evidence is kept outside Git under `implementation/p01/evidence/`. The latest security report SHA-256 is `e3858b70a457214052a4a7f98300e6823c0b7b88a73d05a0ff2a89133b7c17c0`; the SBOM SHA-256 is `cc88da22004511b45bf4b3ff2837ae4da101eefee496a367d60e181ff59751aa`.

## Strict review

- Change risk: `high`, because the phase establishes protocol, publication, privacy and supply-chain boundaries.
- Verdict: `approve_scoped_current_pc_local`.
- Blocker/major/minor findings after remediation: 0/0/0.
- No synthetic, component or local smoke result is represented as an actual 한글 runtime/oracle result.
- No GitHub-hosted execution, other PC, Hangul 2022/2024, production, server/VM or distribution support is claimed.
- The original design ZIP and all user/private evidence remain outside the repository and were not modified.

## Failure fixtures and residual risks

- Traversal, absolute path, empty path, inserted-link, overwrite, interruption and invalid fixture-manifest cases are retained as negative tests.
- The first clean-clone audit exposed missing links to intentionally ignored local evidence. Validation now permits only `implementation/p00|p01/evidence/` when both private-evidence ignore rules exist; all other missing or escaping links still fail.
- The earlier temporary clean clone could not be removed because the execution environment rejected recursive deletion. It is not part of the repository or product output.

## Next exact task

Start `P02-01 SourceRecord schema`: define the common immutable official-source record, preserve source hash and locator, add valid samples and negative cases, and connect it to deterministic Rust/TypeScript codegen. Use reasoning effort `xhigh`; use `max` for the P02 final Gate. No local UI operation is required for P02-01.
