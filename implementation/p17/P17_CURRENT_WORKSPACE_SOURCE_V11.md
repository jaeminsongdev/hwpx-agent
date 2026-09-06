# P17 current workspace source qualification v11

Date: 2026-09-06

Scope: current-PC source-binding successor only

Decision: **qualified for the exact authenticated loopback checkpoint sources; no phase or product PASS**

The v1-v10 qualification contracts remain byte-for-byte unchanged. This v11 layer composes the
exact v10 contract with SHA-256
`210acd575d411d84f6bfd9395e26d42c80188a309aa28fecc6b49e09d65ada2d` and advances the source view
to clean commit `aa404c2bcdf8a627645c46dd188bea6129b1c856`.

Current-host source acceptance run `a42ea2f0cf5b4548a29c1a2ac162443e` passed all 11 checks. Its
canonical receipt SHA-256 is
`616b59cc5c2f255e8d6c5fd96bdc1c3eaf37c8d7adb36539b9da4b9c3d1daa9e`. The fourteen composed
predecessor successors remain exact. Locked/offline Cargo metadata is
`a80808d0aea3190f5d1ac4298d0b2c2fc3e1e3d443a3e1284f680372430fcd72` for 25 workspace members.

This successor binds 88 implementation files as exact regular-file bytes and exact Git blobs at the
base commit. It retains the v10 set, advances the changed local adapter/core, and adds the strict
checkpoint decoder, authenticated mirror admission, concrete history dispatch, shared frame crate,
loopback-only TCP client/server, protocol migrations, contracts and implementation reports. The
implementation commit passed the full workspace build and test suite, formatting, and all-target
Clippy with warnings denied.

The new sources prove only a bounded current-PC TCP component: the operating-system loopback socket
crosses strict framing, single-use credential handoff, authentication, exact mirror/head admission
and checkpoint dispatch. They also prove frame-size/deadline limits, trailing-byte rejection and
credential redaction/zeroization in the implemented boundary.

They do not prove a separately launched daemon, persistent credential custody, PostgreSQL-backed
service state, pull/push service handling, cross-machine TLS, a registered remote app, concurrent
Web/Codex execution, actual Hangul work, P17-06/P17-07 completion, another PC/version, phase
completion, production readiness or product completion. All corresponding claims remain false.
