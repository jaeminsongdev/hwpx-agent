# P17 current workspace source qualification v15

Date: 2026-09-07

Scope: current-PC source-binding successor only

Decision: **qualified for the exact frozen P15 context bridge; no phase or product PASS**

The v1-v14 qualification contracts remain byte-for-byte unchanged. This v15 layer composes the
exact v14 contract with SHA-256
`ed4bff5f70b73b39b51cecf546bd444c4236140b997fd5380a6a3d0a182a5dfb` and advances the source view
to clean commit `e8b209a57f15cd94db0d8c8d5a6603f06a534d44`.

Current-host source acceptance run `bf3d71cdd1044b6995d7539af2959d43` passed all 11 checks. Its
canonical receipt SHA-256 is
`c5b6e33fcb560516ca4eef6bd5567af408bb830bb78b6d4c3f9cea36c6b8f3ab`. The twenty-two composed
predecessor successors bind the Artifact, Async, Error, Handler and Quota validators exactly.
Locked/offline Cargo metadata remains
`d7dd720fa29a88f5df06dc692b0a56c1d8c70142a88227b4c8ca5f14962bd856` for 25 workspace members.

This successor binds 115 implementation files as exact regular-file bytes and exact Git blobs at
the base commit. The added frozen P15 reader accepts only named contexts from the exact immutable
P15 source contract, verifies its SHA-256 and bounded shape, checks each predecessor against the
context's fixed audited Git revision, and returns a pair only when the current bytes equal the exact
successor. Unknown contexts, history drift, links, duplicate locks and digest drift fail closed.

The current validator chain passes independently from Inspector through Handler at the base commit.
That is component/documentation contract evidence only. This qualification does not itself prove
the complete P15 documentation lane, the FULL repository Gate, actual Hangul work, another
PC/version, phase completion, production readiness or product completion. All corresponding claims
remain false until their independent evidence runs pass.
