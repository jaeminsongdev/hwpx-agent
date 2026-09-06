# P17 current workspace source qualification v4

Date: 2026-09-06
Scope: current-PC source-binding successor only
Decision: **qualified for the exact P05-07 dense-flow implementation and tracked receipt; no phase or product PASS**

The v1-v3 qualification contracts remain byte-for-byte unchanged. This v4 layer composes the exact
v3 contract and advances the source view to clean commit
`75b4f32379cf47fa9e1f46951a9a5f5380d09dde`.

Current-host source acceptance run `707f3b7dd24f45c297f228914597ce64` passed all 11 checks. Its
canonical receipt SHA-256 is
`4f0eaf39bc72cfecaa459f2401ad9e3423429bc361bd581a2cb01a7a3c29e2a8`.
The fourteen composed predecessor successors remain exact. `Cargo.lock`, workspace membership and
dependency metadata did not change; the projected metadata digest remains
`d956979b62019ff5b89a3c6b2ab506a7f102ae0fcb4f86ce70717ac2fca2d51d`
for 23 locked/offline workspace members.

This successor binds eleven P05 dense-flow files as exact regular-file bytes and exact Git blobs at
the base commit: public profile exports, the typed layout builder and tests, the deterministic dense
fixture, the section/dense policies, actual attempt02 report, redacted qualification receipt,
two-page render expectation, coordinate-aware PDF verifier and its tests. The v3 predecessor
continues to bind the earlier sparse identity sources; they are not copied or rewritten here.

The tracked P05 receipt states that the fixed current-PC Hangul 2020 dense-flow subgate passed, but
this P17 qualification independently proves only that the receipt and implementation are the exact
committed bytes. It does not reopen ignored HWPX/PDF/PNG evidence and therefore keeps its own
`actual_hangul` claim false. It does not claim arbitrary-document support, P05 completion, actual
remote transport, registered-host execution, production readiness, another PC, Hangul 2022/2024 or
product completion.
