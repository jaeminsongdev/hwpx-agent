# P06-06 product-target Hangul 2020 attempt diagnostics

Date: 2026-09-07

Decision: **NOT PASS**. These runs prove bounded cleanup and the exact blocking phase only; they do
not prove formula evaluation, save/reopen, PDF rendering, or a product-target oracle.

## Exact target

All three runs used the create-new structural target at
`fixtures/target-build/p06-06-formula-target-20260907-01/target.hwpx`, SHA-256
`6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5`. The target transforms the
actual 1x3 source into a 2x4 table by inserting one column and one row. Its formula moves from C1 to
D2, the public AST changes from `SUM(A1:B1)` to `SUM(A2:C2)`, and the unverified cache changes from
42 to 52. The input stayed byte-identical through every failed run.

## Bounded attempts

| Attempt | Timeout | Trace SHA-256 | Progress SHA-256 | Last validated event | Result |
|---|---:|---|---|---|---|
| 01 | 600 s | `dbd53c64046d354f8959b52024790b0aa6b90423b3b04e9830c9959b83118e03` | `75484cc941f11c57b19c20fb68db9c9c8d96a244dac56e9ce990c2b00b8e95d4` | `open_input/running` | timeout |
| 02 | 900 s | `934ffeea7c6e86b2721fc99f4fadb96775bca26fc5a8ef47388af9dd51a91214` | `1524a4a683be1e1c71701930f3feff43f1c932a10c3d5a2c2e721d8dc407f515` | `open_input/running` | timeout |
| 03 | 900 s | `934ffeea7c6e86b2721fc99f4fadb96775bca26fc5a8ef47388af9dd51a91214` | `cc9bcda8a05fbef022b8dd549b5a973f3bf9f148069903fb952e9cd5424466e4` | `open_input/running` | timeout |

Each journal has exactly three validated events: preflight PASS, COM creation PASS with one owned
Hwp process, and input open RUNNING. The blocking COM call never returned before its deadline, so no
document text was read, no derived HWPX or PDF was emitted, and no semantic comparison ran. Every
watchdog cleaned exactly one owned automation process; refused cleanup, cleanup errors, and residual
Hwp processes are all zero. No user document, network, registry/system setting, or Computer Use
click/type was involved.

Attempts 02 and 03 have identical terminal trace bytes because their bounded outcomes and timeout
values are identical; their timestamped progress journals are distinct. This is expected and does
not merge the attempts.

## Diagnostic correction

The engine sets `XHwpWindows.Visible` before publishing `open_input/running`. When the blocking
`Open` call times out, however, the engine cannot publish its inner terminal trace. The old watchdog
fallback therefore reported `failed_phase=watchdog` and `window_visible_for_user_access=false`
despite the validated progress ordering.

The bounded wrapper now derives the observed failure phase from the bounded, schema-validated
journal and infers window visibility only from its exact three-event prefix. This changes
diagnostics only: it does not bypass access
approval, extend scope, weaken success criteria, or promote any failed attempt. The three historical
traces above remain immutable evidence produced before this correction.

## Exact next action

Do not retry automatically. When the user is present to approve every Hangul file-access prompt,
run one fresh attempt with new output, trace, progress, and PDF paths. P06-06 can close only if the
full lifecycle passes, the exact text digest remains stable, the saved HWPX passes the typed formula
and layout oracle, the PDF passes visual review, and Hwp residue is zero.
