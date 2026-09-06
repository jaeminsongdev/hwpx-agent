# P05-07 dense automatic column flow: attempt02

- Date: 2026-09-06.
- Scope: fixed synthetic 31-paragraph fixture on the current licensed Hangul 2020
  `11.0.0.9136` x86 installation only.
- Qualified implementation commit: `536aabee6866154b1676cf09b9c49d202112eae7`.
- Result: current-PC dense automatic flow/balance subgate PASS.
- Reasoning/review risk: MAX / HIGH-STRICT.

## Preserved calibration failure

Attempt01 passed the complete Hangul lifecycle and strict saved-HWPX inspection. Its first PDF
verification failed with `PDF_PAGE_COUNT_MISMATCH` because the predeclared expectation required one
page while the fixed content rendered on two. The failed verification receipt
`f73d4a0c6467ff74650dc625089d4f73af275eada81dbac907e5b8924f2018ba` and original expectation
`785fe01f866f6b4a7db024447f6aecfeac9a88325fe9576af86596e9c9aabd1c` remain unchanged. Attempt01 is
not called PASS for PDF flow.

Coordinate-only calibration showed that both rendered pages contained text on both sides and ended
with comparable baselines. A two-page expectation was then defined and committed before attempt02.
It binds page 1 start/line 20 across the two columns, page 2 line 21/end across the two columns,
cross-page forbidden markers, at least eight fragments per side and a 12 mm maximum bottom-baseline
delta.

## Attempt02 actual lifecycle

The user granted the displayed access requests. The bounded x86 STA client passed COM creation,
input open/read, HWPX save, input close, saved-output reopen/read, PDF export, output close and quit.
All 21 progress events completed; the watchdog did not time out. The input digest and canonical
visible-text digest remained unchanged and zero Hwp processes remained.

| Artifact | SHA-256 |
|---|---|
| input HWPX | `eee4e18ec85f51592b574d02c21bbf59d20143f0ef78db9704b773724654ec23` |
| saved HWPX | `74ec063b3a222041c03509462f41210452235c503a4ed23fac95746f88d198e0` |
| execution trace | `9d79e85053f578c6f3845ac7d376f4deeba37e821b8e12a5a2581ee00f905fd8` |
| progress journal | `0a98fc3c32170d999965b48517def29b55c88b46cd2c4b89905ca376210c2cde` |
| exported PDF | `0bb647bb7685dd4fb9e8854503c6bab204cb06fcf429d0a776d3197f04d26ad4` |
| two-page expectation | `6ca7926efb1b9e6f9c1c8b0b5cce97cb8ae69ae91640b1bcc3cdbc62f67d0ad3` |
| PDF flow verification | `7d3e61f6497cae15ee97599f425e2f074e5ee3bcef8fb96b7331f54927126982` |
| page 1 PNG | `2169300a1960b1d4437a81d937a6cf7d89630c37c418bc3b1b183ccd01ad2135` |
| page 2 PNG | `9a0c307b0d839ec0f49857d940c24cf52d3a5ade28e84854bb6cb2e2cb3cb22e` |
| tracked combined qualification | `a11a32991998b928a6a3faea1d12d76b57f750ab190b1c525e4c040b6b756293` |

Ignored local evidence is under
`fixtures/target-build/p05-07-dense-current-2020-20260906-v1/`. A redacted combined receipt is
checked in at `implementation/p05/qualification/p05-07-dense-attempt02-qualification.json`.
No user document was opened or scanned.

## Saved semantic result

The strict dense fixture inspector reopened the actual saved HWPX and passed graph/ID/style/page/
column/text admission. It found the separate automatic-balance profile, 31 paragraphs, zero explicit
column breaks, body width 80,220 HWPUNIT, two equal columns, a 1,700 HWPUNIT gap and the exact
canonical text digest
`21c67a1e9786886923a8d803cee9cd46d2881967e1f17f91f5f93f872f838b83`.
This fixture uses the exact current-target empty backend column ID at source, so the saved document
needed no identity exception or rebinding.

## PDF position and balance result

The v2 verifier passed two `309739 x 229658` milli-mm landscape pages at rotation zero and rendered
both at `1756 x 1302` pixels.

| Page | Left fragments | Right fragments | Unclassified | Bottom delta | Required maximum |
|---|---:|---:|---:|---:|---:|
| 1 | 180 | 180 | 0 | 4,481 milli-mm | 12,000 milli-mm |
| 2 | 91 | 91 | 0 | 5,622 milli-mm | 12,000 milli-mm |

Page 1's left/right anchors were at x `52,998` and `159,331` milli-mm. Page 2's were at x `14,973`
and `172,739` milli-mm. Both satisfy the fixed 156,000 milli-mm split with a 3,000 milli-mm guard.
Required and cross-page forbidden marker checks also passed.

## Visual review

Both stored PNGs were reviewed at original resolution. Page 1 visibly flows paragraphs 01-10 down
the left column and 11-20 down the right, with the last wrapped line continuing onto page 2. Page 2
continues 21-25 on the left and 26-30 plus the end marker on the right. The blue separator is visible
on both pages. No clipping, overlap, unexpected blank column or portrait rotation was observed. The
two column bottoms are visually consistent with the measured balance deltas.

## Validation and boundary

Before actual execution, the complete `hwpx-package` all-target suite passed 215/215, all-target/
all-feature Clippy passed with warnings denied, the PDF verifier contract passed 20/20, formatting
passed, and the updated verifier replayed attempt23's v1 PDF evidence without changing its v1 schema
or PNG digests.

This closes the fixed current-PC Hangul 2020 dense automatic-flow/balance subgate only. It does not
qualify arbitrary documents, later Hangul versions, P05-08/P05-09, the full P05 phase Gate,
independent clean-checkout execution, publication or production. Current and independent FULL plus
the source successor qualification remain required for this implementation successor.
