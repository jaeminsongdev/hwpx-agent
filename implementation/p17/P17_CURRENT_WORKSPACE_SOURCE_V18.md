# P17 current workspace source qualification v18

Date: 2026-09-07

Scope: current-PC source-binding successor only

Decision: **qualified for the retention mirror source successor; no phase or product PASS**

The v1-v17 qualification contracts remain byte-for-byte unchanged. This v18 layer composes the
exact v17 contract with SHA-256
`3c4082a70f45d2359f46d78baffd17e6da53c48de80f315d73314c5344a59e7e` and advances the source view
to clean commit `15d8f9b2602f2b7793dc1195d6a19982fecb2fbf`.

Current-host source acceptance run `b025d97ee6cf49c1887363ed8125835d` passed all 11 checks. Its
canonical receipt SHA-256 is
`3febbec118cf424c733365d9724c902b73b7ef685309086b67213279bf0b5fb4`. The twenty-four composed
predecessor successors bind the exact P14-09 retention contract, its later mirror-checkpoint service
implementation and the validating bridge. Locked/offline Cargo metadata remains
`d7dd720fa29a88f5df06dc692b0a56c1d8c70142a88227b4c8ca5f14962bd856` for 25 workspace members.

The retention validator now accepts a changed source only when the exact current-source
qualification lists the contract digest among that path's accepted predecessors and lists the
observed file digest as its exact current successor. Unknown paths, unlisted predecessors, current
digest drift, unavailable qualification, links and non-files fail closed. The original P14 contract
and historical source remain immutable.

This successor binds 115 implementation files as exact regular-file bytes and exact Git blobs at
the base commit. It proves only the source-validation boundary above. It does not prove the complete
docs lane, FULL repository Gate, actual Hangul work, another PC/version, phase completion,
production readiness or product completion. Those claims remain false until their independent
evidence runs pass.
