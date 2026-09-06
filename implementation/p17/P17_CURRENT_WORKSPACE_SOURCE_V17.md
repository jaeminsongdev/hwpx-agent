# P17 current workspace source qualification v17

Date: 2026-09-07

Scope: current-PC source-binding successor only

Decision: **qualified for the complete fallback-negative regression; no phase or product PASS**

The v1-v16 qualification contracts remain byte-for-byte unchanged. This v17 layer composes the
exact v16 contract with SHA-256
`678999761f63c9a99f2b5b00fc0d4685ed35bf9e9325b2aabbeecae28f0fb92f` and advances the source view
to clean commit `d07b41273a794f4cea70633c1f93c34e2769a565`.

Current-host source acceptance run `97f6eb9cdecf4d51862983f2ba1474b6` passed all 11 checks. Its
canonical receipt SHA-256 is
`26fb79f2a86928816704b5b9346107f40a6531efada34a35009db3ae16b6103d`. The twenty-two composed
predecessor successors remain exact. Locked/offline Cargo metadata remains
`d7dd720fa29a88f5df06dc692b0a56c1d8c70142a88227b4c8ca5f14962bd856` for 25 workspace members.

The changed regression removes all three qualified replacement sources before asserting that the
artifact chain fails closed. This keeps the negative test meaningful after the frozen P15 context
bridge was added: removing only the dynamic P16 source map is no longer sufficient because the
independently frozen current-source and P15-context maps are intentional alternatives.

This successor binds 115 implementation files as exact regular-file bytes and exact Git blobs at
the base commit. It proves only the source and negative-test identity above. It does not prove the
complete docs lane, FULL repository Gate, actual Hangul work, another PC/version, phase completion,
production readiness or product completion. Those claims remain false until their independent
evidence runs pass.
