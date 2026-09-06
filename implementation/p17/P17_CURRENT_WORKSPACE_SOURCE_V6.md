# P17 current workspace source qualification v6

Date: 2026-09-06
Scope: current-PC source-binding successor only
Decision: **qualified for the exact P05-08 numeric paragraph-ID repair sources; no phase or product PASS**

The v1-v5 qualification contracts remain byte-for-byte unchanged. This v6 layer composes the exact
v5 contract and advances the source view to clean commit
`6b7237a4e77ae66384a9c288ba91f310970e63be`.

Current-host source acceptance run `4fd776f6b1384c599de66d2000013d54` passed all 11 checks. Its
canonical receipt SHA-256 is
`a4b5ea7603a69a472aaef932877ac2c1724394d7ecb6a6e236660b05069b33e0`.
The fourteen composed predecessor successors remain exact. `Cargo.lock`, workspace membership and
dependency metadata did not change; the projected metadata digest remains
`d956979b62019ff5b89a3c6b2ab506a7f102ae0fcb4f86ce70717ac2fca2d51d`
for 23 locked/offline workspace members.

This successor binds twenty P05 files as exact regular-file bytes and exact Git blobs at the base
commit. It retains all fifteen v5 files and adds the header/footer reader-lowerer implementation,
its package regression tests, the corrected P05-08 target builder, the header/footer policy and
the numeric paragraph-ID repair diagnostic. The v5 predecessor continues to bind its earlier
contract and evidence without rewriting them.

The repair proves that non-numeric nested paragraph IDs and numerically duplicate lexical forms
fail closed in the product model. It does not prove that Hangul 2020 opens or renders the corrected
fixture. The pending Hangul-authored reference and every ignored HWPX/PDF/PNG artifact remain
outside this source qualification. `actual_hangul`, registered-host execution, production,
another PC, Hangul 2022/2024, phase completion and product completion all remain false.
