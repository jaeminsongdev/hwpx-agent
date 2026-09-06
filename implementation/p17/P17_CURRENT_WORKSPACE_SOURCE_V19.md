# P17 current workspace source qualification v19

Date: 2026-09-07

Scope: current-PC source-binding successor only

Decision: **qualified for the P15 auth source successor; no phase or product PASS**

The v1-v18 qualification contracts remain byte-for-byte unchanged. This v19 layer composes the
exact v18 contract with SHA-256
`accd545b2c32cbc578904f6583716209acabbd982d70cbbc1d1780013a692e4e` and advances the source view
to clean commit `4b7d6b1f0fd2ca5f16f42843abfdd56eda9f68f1`.

Current-host source acceptance run `8945f8951aa14b13b5757b63725bd71e` passed all 11 checks. Its
canonical receipt SHA-256 is
`b686f8d69e2a63b29bd45b3af75fbcc91ce63d91953b5773e7ab6984f9c9db46`. The twenty-five composed
predecessor successors bind the exact P15 auth contract and the later retention-validator source.
Locked/offline Cargo metadata remains
`d7dd720fa29a88f5df06dc692b0a56c1d8c70142a88227b4c8ca5f14962bd856` for 25 workspace members.

The auth validator now admits a changed lock only when the exact current-source qualification lists
that contract digest as an accepted predecessor and the observed bytes as the exact current
successor. Unknown paths, unlisted predecessors, unavailable qualification, links and digest drift
fail closed. The P15 auth contract and its historical sources remain immutable.

This successor binds 115 implementation files as exact regular-file bytes and exact Git blobs at
the base commit. It proves only the source-validation boundary above. It does not prove the complete
docs lane, FULL repository Gate, actual Hangul work, another PC/version, phase completion,
production readiness or product completion. Those claims remain false until their independent
evidence runs pass.
