# Page setup v1 to v2: current Hangul 2020 orientation repair

Version 2 corrects a serializer/reader defect in `hwpx-agent.page-setup/1`. The English token names
were interpreted as direction labels without actual render evidence. P05-07 attempt21's source
and saved HWPX use WIDELY with physical dimensions 65197 x 87874 HWPUNIT; the actual Hangul 2020
PDF is portrait. The former reader incorrectly reported landscape and a landscape body width.

| Public orientation | Version 1 XML token (wrong) | Version 2 current-2020 token |
|---|---|---|
| Portrait | NARROWLY | WIDELY |
| Landscape | WIDELY | NARROWLY |

`PAGE_SETUP_PROFILE_ID` and new lowering/patch receipts become `hwpx-agent.page-setup/2`.
Public Rust enum variants, unrotated physical dimensions, checked integer conversion, margin
validation, gutter axes, bounded parsing and source-preserving patching do not change. No other
PC/version is qualified by this mapping. Fresh 2020 landscape save/reopen/PDF acceptance is pending.

Old version-1 receipts and byte hashes remain historical evidence and cannot qualify version 2.
Do not flip stored model orientation, edit original HWPX files in place, replay old plans or
silently migrate old receipts. Reinspect original XML with the corrected reader, retain the actual
stored token/dimensions, and explicitly recompile a new plan from current requested orientation.
The existing Rust API does not expose a serialized receipt importer, so no automatic converter is
introduced. Consumers that later persist these receipts must validate the profile and source hash.

The 128-case deterministic corpus has a new version-2 hash
`6a8a3e417e8cc992c5bafe1f45ea176aec6f15adf37cbb9589a9dd1f535bf2aa`.
The test retains the old hash `415b0a465a046f89d88481c3a9f8518e430517bbe3b46cb3564bc942ffbebc00`
after substituting only the reversed orientation token, proving no unrelated corpus byte changed.
