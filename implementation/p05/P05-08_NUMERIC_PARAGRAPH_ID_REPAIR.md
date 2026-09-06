# P05-08 numeric paragraph-ID repair

- Date: 2026-09-06.
- Scope: current licensed Hangul 2020 `11.0.0.9136` x86 and the fixed synthetic P05-08 fixture.
- Decision: **product contract defect repaired; actual Hangul 2020 Gate remains UNVERIFIED**.
- Reasoning/review: MAX / STRICT, change risk HIGH.

## Confirmed contract defect

The policy-locked official Hancom `hwpx-owpml-model` commit
`1453388472c703a4b299a0834f425cdac16644b9` represents `PType.id` as a `UINT`. The local standard
record also identifies the paragraph `PType` and its `id` attribute as `xsd:000393` and
`xsd:000520`. The previous product model preserved the nested paragraph ID as a string and the
lowerer admitted non-numeric values such as `p05-08-paragraph-100`.

The lowerer/reader validation now requires every header, footer and master-page body paragraph ID
to be a bounded decimal value parseable as `u32`. Empty or unsafe identities retain their existing
identity failure, while a safe-looking non-number fails with `header_footer_invalid_number`.
Lexically different forms with the same `u32` value, such as `1` and `01`, fail as a duplicate
identity so a serializer cannot normalize them into an ambiguous document.
Header/footer `subList` IDs and master-page logical IDs remain bounded strings because the official
model represents those fields as strings.

The deterministic P05-08 target now uses numeric nested paragraph IDs and still has four body
pages, four header/footer definitions, eight page fields, one master page and the same canonical
visible-text SHA-256
`aa45c23687c9a6e94d33c40e13578c0b73905b48eb4bd1237bfe6893c6a08d15`.

## Preserved runtime attempts

The original-string attempt03 and numeric-ID v2 attempt01 both passed preflight and exact COM
creation, then returned `false` from `Open`. Neither produced an output HWPX or PDF, both preserved
their input, both quit their owned Hwp process, and neither has a positive user click receipt.
Therefore neither attempt proves an authorized rejection or a PASS.

| Artifact | SHA-256 |
|---|---|
| original input | `fda9547afe1326a5f2d9ebcea951a2dcf5345ef554eba846bb1e78e80a7bfe11` |
| original attempt03 trace | `f0969ce7c9dfe15c60aa6d56b4874653a1e033ca1f05604ccf4d2ac0be8fa5b9` |
| original attempt03 progress | `448637494a2ddbcae7481528970ffef6ef6d21bec279a94d4516bcac085b2c57` |
| numeric-ID v2 input | `4bf85975a06e05f5bf808e7d8ec3f7f61b8ee2dda417539890674c563de510d1` |
| numeric-ID v2 attempt01 trace | `7f8d5e4d7361fad3b1e4fb5942e75d108a74f63fc20625d8be2ebffffeb7aab1` |
| numeric-ID v2 attempt01 progress | `076f9cb50a20ffc180f94f11edec0798920d29628be2c9a6e7f2a93de20e31dc` |

The official model independently parsed the numeric fixture and saved a package, but its serializer
omitted the referenced master-page part while retaining the section/package references. That
output is deliberately not used as a compatibility rewrite or actual-Hangul substitute.

## Validation and next acceptance

`cargo fmt --all -- --check`, package-wide all-target clippy with warnings denied, and all 175
`hwpx-package` tests passed. The locked 128-case header/footer digest is now
`b1723d2df9135ab2a5051597cac64c50dc33b50d259c622fc975b24b89e6e4aa`.

The next diagnostic is a minimal reference created by Hangul 2020 itself through the documented
`HeaderFooter` action. Compare its saved control/body shape with the product fixture, then repair
the next exact incompatibility before another full P05-08 lifecycle attempt. The Gate still
requires authorized open/save/reopen, strict semantic inspection, four-page PDF coordinate/text
verification, original-resolution visual review and zero owned-process residue.
