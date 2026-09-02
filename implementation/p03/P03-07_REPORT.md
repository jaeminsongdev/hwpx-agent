# P03-07 Preserving patch engine report

- Generated: 2026-09-02
- Audited source commit: `28f45a4857ac38c67f3d0110becb820257ffe46d`
- State: `pass_current_pc_local_core_and_disposable_2020_mutation`
- Reasoning/review mode: `max / untrusted mutation, atomic transaction and private artifact boundary`

`hwpx-package`에 P03-04 checked selector, P03-05 preservation evidence와 P03-06 typed ID를 결합한 pure in-memory `PreservingPatchEngine`을 구현했다. 8종 allowlisted intent를 모두 원본 byte span에 대해 계획하고, 모호한 overlap/dependency는 실행 순서를 추측하지 않고 거부한다. 결과는 private memory artifact로만 유지되며 P03-08 전에는 파일이나 ZIP bytes를 public으로 publish하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Intent allowlist | `pass` | `ReplaceAttribute`, `ReplaceText`, `InsertSibling`, `DeleteSubtree`, `ReplaceSubtree`, `AllocateId`, `AddRelationship`, `AddPart`만 공개 |
| Checked selectors | `pass` | source SHA-256, token/tree index, namespace-resolved name/kind을 bind하고 apply에서 preservation identity와 재대조; raw byte offset 입력 없음 |
| Safe values/fragments | `pass` | XML 1.0 text/attribute escaping; single-root declaration/BOM/DTD/entity/PI/CDATA-free validated fragment; namespace declaration 직접 교체 금지 |
| Conflict model | `pass` | overlap, ancestor/descendant, range boundary insertion, same-anchor insertion, same attribute mutation을 stable `patch_conflict`로 거부 |
| Typed allocation | `pass` | `(part, IdKind, handle)` deterministic reservation block, existing ID 재번호화 0, opaque handle reference, failed transaction retry digest 동일 |
| Relationship/part closure | `pass` | portable non-directory path, parsed media, exactly-one matching relationship, path/media/collision/orphan 검증 후 rebuilt graph closure |
| Atomic in-memory transaction | `pass` | immutable source copy에 전체 계획 적용 후 validation-only memory ZIP을 bounded reader/graph/preservation/ID로 재개봉; 실패 시 result/reservation 없음 |
| Private artifact | `pass` | values/fragments/relationship IDs/new and output bytes custom non-disclosing `Debug`; public path/size/hash record와 private artifact integrity 재검증 |
| Finite limits | `pass` | intent, changed+added part, value, fragment, added part, total positive growth의 apply-time current-limit 재검증과 checked arithmetic |
| Synthetic/property corpus | `pass` | P03-07 `5/5`, 8 intent 전부, malicious/conflict/rollback/order/limit cases, fixed-seed random sequence 64회; package 전체 `43/43` |
| Current 2020 disposable mutation | `pass` | 승인된 기존 fixture 2개: no-op 각 `11/11` part exact, ID `73/184`; typed `itemref@linear` memory mutation 각 `1 changed / 10 untouched`, full revalidation PASS |
| Versioned contract | `pass` | `implementation/p03/P03-07_PRESERVING_PATCH_POLICY.md`, `protocol/migrations/preserving-patch-v0-to-v1.md` |

## Transaction and disclosure boundary

- Input ZIP, graph and source part bytes remain immutable; the engine has no filesystem write API.
- `PatchResult` keeps the actual output parts private for P03-08. Public metadata contains canonical package path, disposition, size and source/output hashes only.
- Safe diagnostic accepts only explicit fixture paths, writes nothing, starts no 한글/COM/UI, and prints only ordinal/profile/counts.
- The internal validation ZIP is disposable memory-only evidence. It is not atomic publication and cannot be returned as document bytes.

## Validation evidence

- Current Windows exact commit: FULL bootstrap `5/5`; Rust workspace tests/Clippy/doc tests/generated drift, Windows worker, widget, docs and security passed.
- Core corpus: patch engine `5/5`; preserving XML/safe XML unit `12/12`; ID index `5/5`; PackageGraph `8/8`; preservation map `5/5`; malicious ZIP `8/8`; `hwpx-package` total `43/43`.
- Current 2020 actual diagnostic: approved disposable fixture `2/2`; each no-op `11/11` exact and private memory mutation `1/11` changed with graph/preservation/ID `73/184` revalidation.
- Linux exact toolchain: image `rust:1.96.0-bookworm@sha256:5e2214abe154fe26e39f64488952e5c991eeed1d6d6da7cc8381ae83927f0cfc`, `rustc 1.96.0`; source/Cargo registry read-only, Cargo offline, target tmpfs; `43/43`와 Clippy `-D warnings` passed.
- Clean clone: `D:\개발데이터\Temp\hwpx-agent-p03-07-clean-28f45a4`, exact audited commit, FULL bootstrap `5/5`, exit code 0, post-run tracked changes 0.
- Security: scanned files 492, secret findings 0, Rust/Node/.NET vulnerabilities 0, forbidden licenses 0, CycloneDX components 159.
- Library filesystem/network/process/`unsafe`, source/user document mutation, 한글 runtime 실행: 0. Diagnostic example만 명시 입력 파일을 read-only로 읽는다.

`cargo deny`의 기존 duplicate-version warning은 advisory/license/source/ban failure가 아니다.

## Strict self-review

- Change risk: `high` (document mutation and future writer input).
- 첫 review에서 added-part bytes가 total output growth에 포함되지 않은 경계를 발견해 기존 edit growth와 합산하고 changed+added part ceiling을 함께 적용했다.
- 둘째 review에서 object construction 때보다 apply 때 limits가 더 작을 수 있는 경계를 발견해 fragment/new part/relationship path·media·value를 현재 transaction limits로 재검증하고 negative tests를 추가했다.
- actual minified OPF에는 whitespace token이 없음을 확인해 probe 가정을 제거하고 typed `itemref@linear` checked-span mutation으로 바꿨다.
- private artifact가 버려지는 metadata-only 결과가 되지 않도록 P03-08 consumer용 bytes를 crate-private로 보존하고 public integrity check만 제공한다.
- Final blocker/major/minor findings: `0/0/0`.

## Scope and remaining boundary

이 task는 in-memory patch planning/application과 재개봉 validation까지 검증했다. public ZIP bytes, filesystem temp/fsync/atomic no-overwrite publication, compressed stream/timestamp preservation, normalized writer, crash recovery, 실제 한글 reopen/save/render, 사용자 문서 전체 또는 2022/2024 동작은 검증했다고 주장하지 않는다.

## Next exact task

`P03-08 Atomic ZIP writer`를 시작한다. `PreservingWriter`와 `NormalizedWriter`를 분리하고, explicit secure workspace에서 create-new staging→file sync/checksum→bounded reopen→same-volume atomic no-overwrite publication→published readback을 구현한다. failure injection에서 source 불변과 destination absent-or-complete를 검증하며 추론수준은 `max`다.
